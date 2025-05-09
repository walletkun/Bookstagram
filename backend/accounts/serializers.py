from rest_framework import serializers
from .models import User, UserProfile
from django.contrib.auth.password_validation import validate_password

# User registration
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name')
        # Making that email mmust be filled
        extra_kwargs = {
            'email' : {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"Password": "Password fields didn't match"})

        # Email uniquness checks
        email = attrs.get('email', '')
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({'email': 'email has already been used'}) 
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    profile_pic =serializers.SerializerMethodField()
    class Meta:
        model = UserProfile
        fields = ('bio', 'zip_code', 'social_links', 'username', 'profile_pic')

    def get_profile_pic(self, obj):
        # Get the profile picture from the user model
        return obj.user.profile_pic if obj.user else None
        
    def get_username(self, obj):
        # Get the username from the user model
        return obj.user.username if obj.user else None

# Password forget classes 
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()



class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)


    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match"})

        return attrs
    


