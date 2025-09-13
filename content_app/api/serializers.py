from rest_framework import serializers
from service_app.models import Video, Profiles, VideoProgress, CurrentVideoConvertProgress
import os


class VideosSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Video
        fields = '__all__'
    
    def validate(self, data):
        if 'url' in data and data['url']:
            self.validate_video_file(data['url'])
        return data

    def validate_video_file(self, file):
        allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
        
        file_name = file.name.lower()
        file_extension = os.path.splitext(file_name)[1]
        
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError( f"Ungültiges Dateiformat. Erlaubte Formate: {', '.join(allowed_extensions)}" )
    
    def create(self, validated_data):
        video = super().create(validated_data)
        CurrentVideoConvertProgress.objects.create(video=video)
        return video


class VideoProgressSerializer(serializers.ModelSerializer):

    class Meta:
        model = VideoProgress
        fields = '__all__'
        extra_kwargs = {
            'profiles': {'write_only': True,'required': False},
            'current_time': {'required': False},
        }
    
    def validate(self, data):
        video = data.get('video')
        if video is None:
            raise serializers.ValidationError({"error": "Video not found."})
        data['current_time'] = data.get('current_time') or 0
        data['is_finished'] = data.get('is_finished') or False
        return data

    def create(self, validated_data):
        return super().create(validated_data)


class ProfilesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profiles
        fields = '__all__'


class CurrentVideoConvertProgressSerializer(serializers.ModelSerializer):
    genre = serializers.SerializerMethodField()
    current_convert_state = serializers.SerializerMethodField()
    is_converted = serializers.SerializerMethodField()
    dataQuarryID = serializers.ReadOnlyField(default=None)

    class Meta:
        model = CurrentVideoConvertProgress
        fields = '__all__'
    
    def get_genre(self, obj):
        return obj.video.genre
    
    def get_current_convert_state(self, obj):
        return obj.video.current_convert_state

    def get_is_converted(self, obj):
        return obj.video.is_converted
