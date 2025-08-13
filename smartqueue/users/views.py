
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import RegisterSerializer, LoginSerializer
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class RegisterThrottle(UserRateThrottle):
	rate = '5/min'

class RegisterView(generics.CreateAPIView):
	serializer_class = RegisterSerializer
	permission_classes = [AllowAny]
	throttle_classes = [RegisterThrottle, AnonRateThrottle]

class LoginThrottle(UserRateThrottle):
	rate = '10/min'

class LoginView(TokenObtainPairView):
	serializer_class = LoginSerializer
	permission_classes = [AllowAny]
	throttle_classes = [LoginThrottle, AnonRateThrottle]
