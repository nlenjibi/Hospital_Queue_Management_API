
from django.urls import path
from . import views

urlpatterns = [
    path('', views.DepartmentList.as_view(), name='department-list'),
    path('<int:pk>/', views.DepartmentDetail.as_view(), name='department-detail'),
    path('<int:department_id>/staff/', views.DepartmentStaffList.as_view(), name='department-staff'),
]