from rest_framework import serializers
from .models import Quiz, Question, QuizAttempt


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for Question model"""
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'options', 'order', 'points']


class QuizSerializer(serializers.ModelSerializer):
    """Serializer for Quiz model"""
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Quiz
        fields = ['id', 'course', 'title', 'description', 'passing_score', 
                  'created_at', 'questions']


class QuizAttemptSerializer(serializers.ModelSerializer):
    """Serializer for Quiz Attempt"""
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'quiz_title', 'score', 'answers', 'passed', 'completed_at']
        read_only_fields = ['id', 'score', 'passed', 'completed_at']
