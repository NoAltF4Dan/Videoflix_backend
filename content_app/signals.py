import os
import subprocess
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Video, VideoProgress, CurrentVideoConvertProgress
from django.conf import settings
import django_rq
import glob
import re
import time


RESOLUTIONS = {
        'videos': {
            '1080p': '1920x1080',
            '720p': '1280x720',
            '480p': '854x480',
            '360p': '640x360',
        },
        'thumbnails': '215:120'
    }

STEPS_FOR_VIDEO_CONVERT = 100/6


@receiver(post_save, sender=Video)
def generate_video_data(sender, instance, created, **kwargs):
    if not created or not instance.url:
        return
    queue = django_rq.get_queue('default', autocommit=True)
    queue.enqueue(generate_video_versions, instance)


def generate_video_versions(instance):
    output_dir = os.path.join(settings.MEDIA_ROOT, 'uploads/videos/converted')
    os.makedirs(output_dir, exist_ok=True)
    try:
        video = instance.url.path
        generate_video_thumbnail(instance, video)
        filename, file_ending = os.path.splitext(os.path.basename(video))
        filename = filename[0:20]
        for resolution, size in RESOLUTIONS['videos'].items():
            output_path = os.path.join(settings.MEDIA_ROOT, 'uploads/videos/converted', f'{filename}_{resolution}.m3u8')
            try:
                ffmpeg_converting_process(filename,  size, resolution, video, output_dir, output_path)
                add_progress_for_current_convert_state(instance)
            except subprocess.CalledProcessError as error:
                print(f"[ffmpeg] Fehler bei {resolution}: {error}")
        master_path = generate_master_playlist(filename, output_dir)
        save_new_video_path(instance, master_path)
    except Exception as error:
        print(f'something went Wrong! {error}')
    finally:
        CurrentVideoConvertProgress.objects.filter(video=instance).delete()


def ffmpeg_converting_process(filename,  size, resolution, video, output_dir, output_path):
        cmd = [
                'ffmpeg', '-i', video,
                '-vf', f'scale={size}',
                '-c:v', 'libx264', '-crf', '23', '-preset', 'medium',
                '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '2',
                '-g', '48', '-keyint_min', '48', '-sc_threshold', '0',
                '-force_key_frames', 'expr:gte(t,n_forced*2)',
                '-max_muxing_queue_size', '9999',
                '-f', 'hls',
                '-hls_time', '6',
                '-hls_playlist_type', 'vod',
                '-hls_segment_filename', os.path.join(output_dir, f'{filename}_{resolution}_%03d.ts'),
                output_path
            ]
        subprocess.run(cmd, check=True)
    

def save_new_video_path(instance, master_path):
    add_progress_for_current_convert_state(instance)
    relative_path = os.path.relpath(master_path, settings.MEDIA_ROOT)
    instance.url.name = relative_path
    instance.save()


def generate_master_playlist(filename,output_dir):
    master_playlist_path = os.path.join(output_dir, f'{filename}_master.m3u8')
    bandwidth_map = {
        '1080p': 5000000,
        '720p': 3000000,
        '480p': 1500000,
        '360p': 800000,
    }

    with open(master_playlist_path, 'w') as file:
        for resolution, size in RESOLUTIONS['videos'].items():
            bandwidth = bandwidth_map.get(resolution, 1000000)
            file.write(f'#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={size}\n')
            file.write(f'{filename}_{resolution}.m3u8\n')
    return master_playlist_path


def get_video_duration(video_path):
    try:
        cmd = [
                'ffprobe', '-v', 'error', '-show_entries',
                'format=duration', '-of',
                'default=noprint_wrappers=1:nokey=1', video_path
            ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
        duration = float(result.stdout)
        if duration <= 0.0:
            return '00:00:01'
        screenshot_time = duration / 3
        formatted = time.strftime('%H:%M:%S', time.gmtime(screenshot_time))
        return formatted
    except:
        print('Fehler beim Abrufen der Videodatei.')
        return '00:00:01'


def generate_video_thumbnail(instance, orignal_video_path):
    video = instance.url.path
    output_dir = os.path.join(settings.MEDIA_ROOT, 'uploads/thumbnails')
    os.makedirs(output_dir, exist_ok=True)
    name, file_Ending = os.path.splitext(os.path.basename(video))
    thumbnail_time = get_video_duration(orignal_video_path)
    thumbnail_path = os.path.join(settings.MEDIA_ROOT, 'uploads/thumbnails', f"{instance.id}_thumb.jpg")
    cmd = ['ffmpeg', '-y', '-ss', f'{thumbnail_time}', '-i', orignal_video_path, '-frames:v', '1', '-vf', f"scale={RESOLUTIONS['thumbnails']}", thumbnail_path ]
    try:
        subprocess.run(cmd, check=True)
        instance.thumbnail.name = f"uploads/thumbnails/{instance.id}_thumb.jpg"
        instance.save()
        add_progress_for_current_convert_state(instance)
    except subprocess.CalledProcessError as error:
        print(f"[ffmpeg] Fehler bei Thumbnail: {error}")


def add_progress_for_current_convert_state(instance):
    instance.current_convert_state += STEPS_FOR_VIDEO_CONVERT
    if instance.current_convert_state >= 100:
        instance.current_convert_state = 100
        instance.is_converted = True
    instance.save()


@receiver(post_delete, sender=Video)
def delete_file(sender, instance, *args, **kwargs):
    queue = django_rq.get_queue('default', autocommit=True)
    queue.enqueue(delete_video, instance)


def delete_video(instance):
    delete_thumbnail(instance)
    delete_video(instance)
    delete_all_progress(instance)


def delete_all_progress(instance):
    videoId = instance.id
    queryset =  VideoProgress.objects.filter(video = videoId)
    deleted_count, _ = queryset.delete()


def delete_thumbnail(instance):
    if instance.thumbnail:
        thumb_path = os.path.join(settings.MEDIA_ROOT, instance.thumbnail.name)
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
    

def delete_video(instance):
    if not instance.url:
        return
    original_path = instance.url.path
    filename, file_ending = os.path.splitext(os.path.basename(original_path))
    base_filename = re.sub(r'_(master|360p|480p|720p|1080p)$', '', filename)

    converted_dir = os.path.join(settings.MEDIA_ROOT, 'uploads/videos/converted')
    pattern = os.path.join(converted_dir, f"{base_filename}_*")
    matching_files = glob.glob(pattern)

    for file in matching_files:
        if os.path.isfile(file):
            os.remove(file)

    original_video_path = os.path.join(settings.MEDIA_ROOT, 'uploads/videos/originals', base_filename + ".mp4")
    if os.path.exists(original_video_path):
        os.remove(original_video_path)

    if os.path.exists(original_path):
        os.remove(original_path)