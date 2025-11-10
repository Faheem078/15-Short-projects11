from rest_framework import serializers
from .models import Course, CourseContent, Enrollment


class CourseContentSerializer(serializers.ModelSerializer):
    """Serializer for course content"""
    class Meta:
        model = CourseContent
        fields = ['id', 'title', 'content', 'order', 'video_url']


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model"""
    contents = CourseContentSerializer(many=True, read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'category', 'difficulty', 
                  'duration', 'instructor', 'thumbnail', 'created_at', 
                  'contents', 'is_enrolled']
    
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Enrollment.objects.filter(user=request.user, course=obj).exists()
        return False


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for Enrollment model"""
    course = CourseSerializer(read_only=True)
    course_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Enrollment
        fields = ['id', 'course', 'course_id', 'progress', 'completed', 
                  'enrolled_date', 'completed_date']
        read_only_fields = ['id', 'enrolled_date', 'completed_date']
