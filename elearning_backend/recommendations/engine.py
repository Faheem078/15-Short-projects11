import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from django.contrib.auth import get_user_model
from courses.models import Course, Enrollment
from users.models import UserActivity
from .models import Recommendation

User = get_user_model()


class RecommendationEngine:
    """AI-based recommendation engine using collaborative filtering"""
    
    def __init__(self):
        self.user_item_matrix = None
        self.similarity_matrix = None
    
    def build_user_item_matrix(self):
        """Build user-item interaction matrix"""
        users = User.objects.all()
        courses = Course.objects.all()
        
        # Create matrix with users as rows and courses as columns
        matrix = np.zeros((users.count(), courses.count()))
        
        user_ids = {user.id: idx for idx, user in enumerate(users)}
        course_ids = {course.id: idx for idx, course in enumerate(courses)}
        
        # Fill matrix with enrollment and activity data
        enrollments = Enrollment.objects.all()
        for enrollment in enrollments:
            if enrollment.user.id in user_ids and enrollment.course.id in course_ids:
                user_idx = user_ids[enrollment.user.id]
                course_idx = course_ids[enrollment.course.id]
                # Weight by progress and completion
                score = enrollment.progress / 100.0
                if enrollment.completed:
                    score = 1.5  # Boost for completed courses
                matrix[user_idx][course_idx] = score
        
        # Add activity data
        activities = UserActivity.objects.all()
        for activity in activities:
            if activity.user.id in user_ids and activity.course.id in course_ids:
                user_idx = user_ids[activity.user.id]
                course_idx = course_ids[activity.course.id]
                # Add small weights for different activities
                if activity.activity_type == 'view':
                    matrix[user_idx][course_idx] += 0.1
                elif activity.activity_type == 'enroll':
                    matrix[user_idx][course_idx] += 0.3
                elif activity.activity_type == 'quiz':
                    matrix[user_idx][course_idx] += 0.2
        
        self.user_item_matrix = matrix
        return matrix, user_ids, course_ids
    
    def calculate_similarity(self):
        """Calculate user-user similarity using cosine similarity"""
        if self.user_item_matrix is None:
            self.build_user_item_matrix()
        
        # Calculate cosine similarity between users
        self.similarity_matrix = cosine_similarity(self.user_item_matrix)
        return self.similarity_matrix
    
    def collaborative_filtering(self, user_id, top_n=10):
        """Generate recommendations using collaborative filtering"""
        matrix, user_ids, course_ids = self.build_user_item_matrix()
        
        if user_id not in user_ids:
            return []
        
        user_idx = user_ids[user_id]
        similarity = self.calculate_similarity()
        
        # Get similar users
        user_similarities = similarity[user_idx]
        
        # Calculate weighted scores for courses
        course_scores = np.zeros(len(course_ids))
        for course_idx in range(len(course_ids)):
            # Skip courses user has already enrolled in
            if matrix[user_idx][course_idx] > 0:
                continue
            
            # Calculate weighted score based on similar users
            weighted_sum = 0
            similarity_sum = 0
            for other_user_idx in range(len(user_ids)):
                if other_user_idx != user_idx and user_similarities[other_user_idx] > 0:
                    weighted_sum += user_similarities[other_user_idx] * matrix[other_user_idx][course_idx]
                    similarity_sum += user_similarities[other_user_idx]
            
            if similarity_sum > 0:
                course_scores[course_idx] = weighted_sum / similarity_sum
        
        # Get top N courses
        top_course_indices = np.argsort(course_scores)[::-1][:top_n]
        
        # Map back to course IDs
        course_id_map = {idx: cid for cid, idx in course_ids.items()}
        recommended_course_ids = [course_id_map[idx] for idx in top_course_indices if course_scores[idx] > 0]
        
        return recommended_course_ids
    
    def content_based_filtering(self, user_id, top_n=10):
        """Generate recommendations based on user interests and course categories"""
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return []
        
        user_interests = user.interests if user.interests else []
        user_skill_level = user.skill_level
        
        # Get courses not enrolled by user
        enrolled_courses = Enrollment.objects.filter(user=user).values_list('course_id', flat=True)
        available_courses = Course.objects.exclude(id__in=enrolled_courses)
        
        # Score courses based on interests and skill level
        scored_courses = []
        for course in available_courses:
            score = 0
            
            # Match interests with category
            if user_interests:
                for interest in user_interests:
                    if interest.lower() in course.category.lower():
                        score += 2.0
                    if interest.lower() in course.title.lower():
                        score += 1.0
            
            # Match skill level
            if course.difficulty == user_skill_level:
                score += 1.5
            elif user_skill_level == 'beginner' and course.difficulty == 'intermediate':
                score += 0.5
            elif user_skill_level == 'intermediate' and course.difficulty == 'advanced':
                score += 0.5
            
            if score > 0:
                scored_courses.append((course.id, score))
        
        # Sort by score and return top N
        scored_courses.sort(key=lambda x: x[1], reverse=True)
        return [course_id for course_id, _ in scored_courses[:top_n]]
    
    def hybrid_recommendations(self, user_id, top_n=10):
        """Combine collaborative and content-based filtering"""
        collab_recs = self.collaborative_filtering(user_id, top_n=top_n)
        content_recs = self.content_based_filtering(user_id, top_n=top_n)
        
        # Combine recommendations with weights
        combined_scores = {}
        
        for idx, course_id in enumerate(collab_recs):
            combined_scores[course_id] = combined_scores.get(course_id, 0) + (top_n - idx) * 0.6
        
        for idx, course_id in enumerate(content_recs):
            combined_scores[course_id] = combined_scores.get(course_id, 0) + (top_n - idx) * 0.4
        
        # Sort by combined score
        sorted_courses = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        return [course_id for course_id, _ in sorted_courses[:top_n]]
    
    def generate_recommendations(self, user_id, top_n=10):
        """Main method to generate recommendations"""
        recommended_course_ids = self.hybrid_recommendations(user_id, top_n)
        
        # Save recommendations to database
        Recommendation.objects.filter(user_id=user_id).delete()
        
        for idx, course_id in enumerate(recommended_course_ids):
            try:
                course = Course.objects.get(id=course_id)
                Recommendation.objects.create(
                    user_id=user_id,
                    course=course,
                    score=top_n - idx,
                    reason="Based on your interests and learning patterns"
                )
            except Course.DoesNotExist:
                continue
        
        return recommended_course_ids
