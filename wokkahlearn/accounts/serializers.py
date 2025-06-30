from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from .models import User, UserProfile, UserSkill, UserAchievement

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password', 'password_confirm')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not username and not email:
            raise serializers.ValidationError('Username or email is required')
        
        # Authenticate with username or email
        if email:
            try:
                user = User.objects.get(email=email)
                username = user.username
            except User.DoesNotExist:
                raise serializers.ValidationError('Invalid credentials')
        
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled')
        
        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    uid = serializers.CharField()
    password = serializers.CharField(validators=[validate_password])
    
    def validate(self, attrs):
        try:
            user = User.objects.get(id=attrs['uid'])
            if not default_token_generator.check_token(user, attrs['token']):
                raise serializers.ValidationError('Invalid token')
            
            # Set new password
            user.set_password(attrs['password'])
            user.save()
            
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid user')
        
        return attrs


# User and Profile Serializers
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'bio', 'avatar', 'github_username', 'linkedin_url', 
            'preferred_languages', 'skill_level', 'is_verified', 'is_premium',
            'timezone', 'language'
        ]
        read_only_fields = ['id', 'is_verified', 'is_premium']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'total_lessons_completed', 'total_exercises_completed',
            'current_streak', 'longest_streak', 'programming_skills',
            'weekly_goal_hours', 'ai_assistance_level', 'preferred_explanation_style',
            'public_profile', 'show_progress'
        ]


class UserSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSkill
        fields = [
            'id', 'skill_name', 'category', 'proficiency_level',
            'verified', 'evidence_count', 'last_assessed'
        ]


class UserAchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAchievement
        fields = [
            'id', 'achievement_id', 'achievement_type', 'title',
            'description', 'icon', 'earned_at', 'progress_data'
        ]
