# analytics/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.contrib.auth import get_user_model

from .models import (
    LearningAnalytics, StudySession, PerformanceMetric, LearningInsight,
    CourseAnalytics, InstructorAnalytics, PlatformAnalytics
)
from .serializers import (
    LearningAnalyticsSerializer, StudySessionSerializer, PerformanceMetricSerializer,
    LearningInsightSerializer, CourseAnalyticsSerializer, InstructorAnalyticsSerializer,
    PlatformAnalyticsSerializer
)
from courses.models import Course, CourseEnrollment, ExerciseSubmission

User = get_user_model()


class LearningAnalyticsViewSet(viewsets.ModelViewSet):
    """API endpoints for learning analytics"""
    serializer_class = LearningAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return LearningAnalytics.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Get or create analytics for the current user"""
        analytics, created = LearningAnalytics.objects.get_or_create(
            user=self.request.user
        )
        if created:
            analytics.update_analytics()
        return analytics
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get comprehensive dashboard data"""
        analytics = self.get_object()
        
        # Get recent activity
        recent_sessions = StudySession.objects.filter(
            user=request.user,
            started_at__gte=timezone.now() - timedelta(days=30)
        ).order_by('-started_at')[:10]
        
        # Get current enrollments
        current_enrollments = CourseEnrollment.objects.filter(
            student=request.user,
            status='enrolled'
        ).select_related('course')
        
        # Get recent achievements
        recent_achievements = request.user.achievements.order_by('-earned_at')[:5]
        
        # Calculate weekly progress
        week_ago = timezone.now() - timedelta(days=7)
        weekly_study_time = StudySession.objects.filter(
            user=request.user,
            started_at__gte=week_ago
        ).aggregate(
            total_time=Sum('duration')
        )['total_time'] or timedelta(0)
        
        # Get skill progress
        skills_data = []
        for skill_name, skill_level in analytics.skill_progression.items():
            skills_data.append({
                'skill': skill_name,
                'current_level': skill_level.get('current', 0),
                'start_level': skill_level.get('start', 0),
                'improvement': skill_level.get('current', 0) - skill_level.get('start', 0)
            })
        
        dashboard_data = {
            'analytics': LearningAnalyticsSerializer(analytics).data,
            'recent_sessions': StudySessionSerializer(recent_sessions, many=True).data,
            'current_enrollments': [{
                'course_id': enrollment.course.id,
                'course_title': enrollment.course.title,
                'progress': float(enrollment.progress_percentage),
                'status': enrollment.status
            } for enrollment in current_enrollments],
            'recent_achievements': [{
                'title': achievement.title,
                'type': achievement.achievement_type,
                'earned_at': achievement.earned_at
            } for achievement in recent_achievements],
            'weekly_study_time': weekly_study_time.total_seconds() / 3600,  # hours
            'skills_progress': skills_data
        }
        
        return Response(dashboard_data)
    
    @action(detail=False, methods=['get'])
    def study_patterns(self, request):
        """Analyze user's study patterns"""
        analytics = self.get_object()
        
        # Get study sessions from last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        sessions = StudySession.objects.filter(
            user=request.user,
            started_at__gte=thirty_days_ago
        )
        
        # Analyze patterns
        daily_patterns = {}
        hourly_patterns = {}
        
        for session in sessions:
            day = session.started_at.strftime('%A')
            hour = session.started_at.hour
            
            if day not in daily_patterns:
                daily_patterns[day] = {'sessions': 0, 'total_time': 0}
            if hour not in hourly_patterns:
                hourly_patterns[hour] = {'sessions': 0, 'total_time': 0}
            
            daily_patterns[day]['sessions'] += 1
            daily_patterns[day]['total_time'] += session.duration.total_seconds()
            
            hourly_patterns[hour]['sessions'] += 1
            hourly_patterns[hour]['total_time'] += session.duration.total_seconds()
        
        return Response({
            'preferred_study_times': analytics.preferred_study_times,
            'most_productive_days': analytics.most_productive_days,
            'daily_patterns': daily_patterns,
            'hourly_patterns': hourly_patterns,
            'learning_velocity': float(analytics.learning_velocity),
            'current_streak': analytics.current_streak,
            'longest_streak': analytics.longest_streak
        })
    
    @action(detail=False, methods=['post'])
    def update_analytics(self, request):
        """Manually trigger analytics update"""
        analytics = self.get_object()
        analytics.update_analytics()
        
        return Response({
            'message': 'Analytics updated successfully',
            'last_updated': analytics.last_updated
        })


class StudySessionViewSet(viewsets.ModelViewSet):
    """API endpoints for study sessions"""
    serializer_class = StudySessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return StudySession.objects.filter(user=self.request.user).order_by('-started_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def start_session(self, request):
        """Start a new study session"""
        session_type = request.data.get('session_type', 'self_study')
        course_id = request.data.get('course_id')
        lesson_id = request.data.get('lesson_id')
        
        session_data = {
            'user': request.user,
            'session_type': session_type,
            'started_at': timezone.now(),
            'ended_at': timezone.now(),  # Will be updated when session ends
            'duration': timedelta(0)
        }
        
        if course_id:
            try:
                course = Course.objects.get(id=course_id)
                session_data['course'] = course
            except Course.DoesNotExist:
                pass
        
        session = StudySession.objects.create(**session_data)
        
        return Response({
            'session_id': session.id,
            'message': 'Study session started',
            'started_at': session.started_at
        })
    
    @action(detail=True, methods=['post'])
    def end_session(self, request, pk=None):
        """End a study session"""
        session = self.get_object()
        
        ended_at = timezone.now()
        duration = ended_at - session.started_at
        
        session.ended_at = ended_at
        session.duration = duration
        session.focus_score = request.data.get('focus_score', 50)
        session.productivity_score = request.data.get('productivity_score', 50)
        session.satisfaction_level = request.data.get('satisfaction_level')
        
        session.save()
        
        return Response({
            'message': 'Study session ended',
            'duration': duration.total_seconds(),
            'session': StudySessionSerializer(session).data
        })
    
    @action(detail=False, methods=['get'])
    def weekly_summary(self, request):
        """Get weekly study session summary"""
        week_ago = timezone.now() - timedelta(days=7)
        sessions = self.get_queryset().filter(started_at__gte=week_ago)
        
        total_sessions = sessions.count()
        total_time = sessions.aggregate(
            total=Sum('duration')
        )['total'] or timedelta(0)
        
        avg_focus = sessions.aggregate(
            avg=Avg('focus_score')
        )['avg'] or 0
        
        by_type = sessions.values('session_type').annotate(
            count=Count('id'),
            total_time=Sum('duration')
        )
        
        return Response({
            'total_sessions': total_sessions,
            'total_time_hours': total_time.total_seconds() / 3600,
            'average_focus_score': round(avg_focus, 1),
            'sessions_by_type': list(by_type)
        })


class PerformanceMetricViewSet(viewsets.ModelViewSet):
    """API endpoints for performance metrics"""
    serializer_class = PerformanceMetricSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PerformanceMetric.objects.filter(user=self.request.user).order_by('-period_start')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get performance trends over time"""
        metric_type = request.query_params.get('metric_type')
        granularity = request.query_params.get('granularity', 'weekly')
        days = int(request.query_params.get('days', 30))
        
        start_date = timezone.now() - timedelta(days=days)
        queryset = self.get_queryset().filter(
            period_start__gte=start_date,
            granularity=granularity
        )
        
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)
        
        metrics = list(queryset.values(
            'metric_type', 'value', 'change_percentage',
            'period_start', 'period_end'
        ))
        
        return Response({
            'metrics': metrics,
            'period': f'{days} days',
            'granularity': granularity
        })
    
    @action(detail=False, methods=['get'])
    def comparison(self, request):
        """Compare user's performance with averages"""
        user_metrics = self.get_queryset().filter(
            period_start__gte=timezone.now() - timedelta(days=30)
        )
        
        # Get platform averages (simplified)
        platform_averages = {
            'completion_rate': 75.0,
            'average_score': 82.5,
            'learning_velocity': 3.2,
            'engagement_score': 68.0
        }
        
        user_averages = {}
        for metric in user_metrics.values('metric_type').distinct():
            metric_type = metric['metric_type']
            avg_value = user_metrics.filter(
                metric_type=metric_type
            ).aggregate(avg=Avg('value'))['avg']
            
            if avg_value:
                user_averages[metric_type] = float(avg_value)
        
        comparison = {}
        for metric_type, platform_avg in platform_averages.items():
            user_avg = user_averages.get(metric_type, 0)
            difference = user_avg - platform_avg
            comparison[metric_type] = {
                'user_average': user_avg,
                'platform_average': platform_avg,
                'difference': difference,
                'better_than_average': difference > 0
            }
        
        return Response(comparison)


class LearningInsightViewSet(viewsets.ModelViewSet):
    """API endpoints for learning insights"""
    serializer_class = LearningInsightSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return LearningInsight.objects.filter(user=self.request.user).order_by('-priority', '-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent insights"""
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        insights = self.get_queryset().filter(
            created_at__gte=start_date,
            is_read=False
        )
        
        serializer = self.get_serializer(insights, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark insight as read"""
        insight = self.get_object()
        insight.is_read = True
        insight.save()
        
        return Response({'message': 'Insight marked as read'})
    
    @action(detail=False, methods=['post'])
    def generate_insights(self, request):
        """Generate new insights based on user data"""
        # TODO: Implement AI-based insight generation
        # For now, create some mock insights
        
        analytics, created = LearningAnalytics.objects.get_or_create(
            user=request.user
        )
        
        insights_to_create = []
        
        # Check for low activity
        if analytics.current_streak < 3:
            insights_to_create.append({
                'insight_type': 'behavior',
                'priority': 'medium',
                'title': 'Consider establishing a daily study routine',
                'message': 'Your current streak is low. Regular daily practice can significantly improve learning outcomes.',
                'confidence_score': 85,
                'recommended_actions': ['Set a daily study time', 'Start with 15-minute sessions']
            })
        
        # Check for performance issues
        if analytics.average_exercise_score < 70:
            insights_to_create.append({
                'insight_type': 'performance',
                'priority': 'high',
                'title': 'Focus on foundational concepts',
                'message': 'Your exercise scores suggest you might benefit from reviewing fundamental concepts.',
                'confidence_score': 90,
                'recommended_actions': ['Review previous lessons', 'Practice more exercises']
            })
        
        created_insights = []
        for insight_data in insights_to_create:
            insight = LearningInsight.objects.create(
                user=request.user,
                **insight_data
            )
            created_insights.append(insight)
        
        serializer = self.get_serializer(created_insights, many=True)
        return Response({
            'message': f'Generated {len(created_insights)} new insights',
            'insights': serializer.data
        })


class CourseAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for course analytics"""
    serializer_class = CourseAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only show analytics for courses the user is enrolled in or teaching
        user = self.request.user
        
        if user.can_teach:
            # Instructors can see analytics for their courses
            return CourseAnalytics.objects.filter(course__instructor=user)
        else:
            # Students can see analytics for enrolled courses
            enrolled_courses = CourseEnrollment.objects.filter(
                student=user
            ).values_list('course_id', flat=True)
            return CourseAnalytics.objects.filter(course_id__in=enrolled_courses)
    
    @action(detail=True, methods=['get'])
    def detailed_stats(self, request, pk=None):
        """Get detailed course statistics"""
        course_analytics = self.get_object()
        course = course_analytics.course
        
        # Get enrollment data
        enrollments = course.enrollments.all()
        
        # Calculate additional statistics
        completion_by_month = enrollments.filter(
            status='completed'
        ).extra(
            select={'month': "DATE_FORMAT(completed_at, '%%Y-%%m')"}
        ).values('month').annotate(count=Count('id')).order_by('month')
        
        # Get difficulty analysis
        bottleneck_lessons = course_analytics.most_difficult_lessons[:5]
        helpful_lessons = course_analytics.most_helpful_lessons[:5]
        
        return Response({
            'course': {
                'id': course.id,
                'title': course.title,
                'total_lessons': course.total_lessons,
                'total_exercises': course.total_exercises
            },
            'enrollment_stats': {
                'total': course_analytics.total_enrollments,
                'active': course_analytics.active_students,
                'completion_rate': float(course_analytics.completion_rate),
                'dropout_rate': float(course_analytics.dropout_rate)
            },
            'performance_stats': {
                'average_grade': float(course_analytics.average_grade),
                'exercise_success_rate': float(course_analytics.exercise_success_rate),
                'average_completion_time': course_analytics.average_completion_time.total_seconds() / 3600
            },
            'engagement_stats': {
                'forum_activity': float(course_analytics.forum_activity_score),
                'collaboration_rate': float(course_analytics.collaboration_rate),
                'satisfaction_score': float(course_analytics.satisfaction_score)
            },
            'content_analysis': {
                'difficult_lessons': bottleneck_lessons,
                'helpful_lessons': helpful_lessons,
                'bottleneck_exercises': course_analytics.bottleneck_exercises
            },
            'trends': {
                'completion_by_month': list(completion_by_month),
                'enrollment_trend': course_analytics.enrollment_trend,
                'engagement_trend': course_analytics.engagement_trend
            }
        })