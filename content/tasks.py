import os
import subprocess
import tempfile

from django.conf import settings
from django.core.files import File

from django_rq import job

from .models import Video


@job("default", timeout=7200)
def process_video(video_id):
    """Executes a background task to process videos using FFmpeg."""
    try:
        video = Video.objects.get(id=video_id)
        video.processing_status = 'processing'
        video.save()

        # Create output directories.
        base_output_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'processed', str(video.id))
        os.makedirs(base_output_dir, exist_ok=True)

        input_path = video.original_video.path

        resolutions = {
            '480p': {'width': 854, 'height': 480, 'bitrate': '1000k'},
            '720p': {'width': 1280, 'height': 720, 'bitrate': '2500k'},
            '1080p': {'width': 1920, 'height': 1080, 'bitrate': '5000k'},
        }

        for res_name, res_config in resolutions.items():
            output_dir = os.path.join(base_output_dir, res_name)
            os.makedirs(output_dir, exist_ok=True)

            # ffmpeg command for HLS convertion
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-vf', f"scale={res_config['width']}:{res_config['height']}",
                '-b:v', res_config['bitrate'],
                '-b:a', '128k',
                '-hls_time', '10',
                '-hls_list_size', '0',
                '-hls_segment_filename', os.path.join(output_dir, '%03d.ts'),
                '-f', 'hls',
                os.path.join(output_dir, 'index.m3u8'),
                '-y'  # overwrite existing files
            ]

            # Run ffmpeg
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"FFmpeg Error for {res_name}: {result.stderr}")

            # Save HLS path in model
            relative_path = os.path.join('videos', 'processed', str(video.id), res_name)
            if res_name == '480p':
                video.hls_480p_path = relative_path
            elif res_name == '720p':
                video.hls_720p_path = relative_path
            elif res_name == '1080p':
                video.hls_1080p_path = relative_path

        create_thumbnail(video, input_path)

        video.processing_status = 'completed'
        video.save()

    except Exception as e:
        print(f"Error processing video {video_id}: {str(e)}")
        video = Video.objects.get(id=video_id)
        video.processing_status = 'failed'
        video.save()


def create_thumbnail(video, input_path):
    """Create thumbnail of video."""
    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_thumbnail_path = temp_file.name

        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ss', '00:00:03',
            '-vframes', '1',
            '-vf', 'scale=320:180',
            temp_thumbnail_path,
            '-y'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and os.path.exists(temp_thumbnail_path):
            with open(temp_thumbnail_path, 'rb') as f:
                django_file = File(f)
                video.thumbnail_url.save('thumbnail.jpg', django_file, save=True)

            os.unlink(temp_thumbnail_path)
            print(f"Thumbnail created successfully for video {video.id}")
        else:
            print(f"FFmpeg error: {result.stderr}")

    except Exception as e:
        print(f"Error creating thumbnail for video {video.id}: {str(e)}")
        if 'temp_thumbnail_path' in locals() and os.path.exists(temp_thumbnail_path):
            os.unlink(temp_thumbnail_path)
