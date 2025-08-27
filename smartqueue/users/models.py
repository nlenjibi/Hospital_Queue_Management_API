# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    """
    Custom user manager for the CustomUser model.
    """
    
    def create_user(self, username, email=None, password=None, **extra_fields):
        """
        Create and return a regular user with an email and password.
        """
        if not username:
            raise ValueError('The Username field must be set')
        
        if email:
            email = self.normalize_email(email)
        
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """
        Create and return a superuser with an email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)

class User(AbstractUser):
    """
    Custom User model with role-based authentication and additional fields.
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('patient', 'Patient'),
         ('staff', 'Staff'),
    ]

    email = models.EmailField(_('email address'), unique=True)
  
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')
    phone_number = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(default=timezone.now)
   
  
    objects = CustomUserManager()
 
    

    class Meta:
        swappable = 'AUTH_USER_MODEL'
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username



class Patient(models.Model):
    """
    Patient profile linked to a User account.
    Stores medical and contact information.
    """
    PRIORITY_EMERGENCY = 'emergency'
    PRIORITY_APPOINTMENT = 'appointment'
    PRIORITY_WALK_IN = 'walk_in'

    PRIORITY_CHOICES = [
        (PRIORITY_EMERGENCY, 'Emergency'),
        (PRIORITY_APPOINTMENT, 'Appointment'),
        (PRIORITY_WALK_IN, 'Walk-in'),
    ]

    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='patient_profile')
    medical_id = models.CharField(max_length=20, unique=True)
    priority_level = models.CharField(max_length=15, choices=PRIORITY_CHOICES, default=PRIORITY_WALK_IN)
    date_of_birth = models.DateField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    allergies = models.TextField(
        blank=True,
        help_text="List any known allergies (e.g., medications, foods, environmental). Leave blank if none."
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes or comments about the patient. For medical history, instructions, or staff remarks."
    )

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.medical_id}"
