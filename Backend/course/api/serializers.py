from rest_framework import serializers
from course.models import LessonBlock, QuizBlock, QuizBlockQuestion, QuizBlockOption

class LessonBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonBlock
        fields = [
            'id', 'lesson', 'block_type', 'order', 'title',
            'text_content', 'video_url', 'video_file', 'audio_file',
            'image', 'file', 'embed_url', 'embed_code',
            'width', 'height', 'background_color', 'is_active'
        ]

class QuizBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizBlock
        fields = [
            'id', 'lesson', 'title', 'description', 'passing_score',
            'time_limit_minutes', 'attempts_allowed', 'show_results',
            'randomize_questions', 'is_active'
        ]

class QuizBlockQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizBlockQuestion
        fields = [
            'id', 'quiz_block', 'question_text', 'question_type',
            'explanation', 'order', 'points', 'is_active'
        ]

class QuizBlockOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizBlockOption
        fields = [
            'id', 'question', 'option_text', 'is_correct', 'order'
        ]
