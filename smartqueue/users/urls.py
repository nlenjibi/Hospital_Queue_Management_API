from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, PatientProfileView, UserProfileView,
    UserDetailView, PatientDetailView, UserListView, PatientListView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/patient/', PatientProfileView.as_view(), name='patient_profile'),
    path('profile/user/', UserProfileView.as_view(), name='user_profile'),
    path('user/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('patient/<int:pk>/', PatientDetailView.as_view(), name='patient_detail'),
    path('users/', UserListView.as_view(), name='user_list'),           # Fetch all users
    path('patients/', PatientListView.as_view(), name='patient_list'),  # Fetch all patients
]
