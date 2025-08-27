from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import User, Patient

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    date_of_birth = serializers.DateField(required=False)
    phone_number = serializers.CharField(required=False)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default='patient')

    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'role', 'date_of_birth'
        )

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        date_of_birth = validated_data.pop('date_of_birth', None)
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Create Patient profile if role is patient
        if user.role == 'patient':
            Patient.objects.create(
                user=user,
                medical_id=f"MED{user.id:06d}",
                date_of_birth=date_of_birth
            )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'role', 'created_at', 'updated_at'
        )

class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Patient
        fields = (
            'id', 'user', 'medical_id', 'priority_level', 'date_of_birth',
            'emergency_contact', 'address', 'allergies', 'notes'
        )
