from django.urls import path
from .views import (
    DepartmentListView, DepartmentDetailView, DepartmentCreateView, DepartmentUpdateView,
    StaffListView, StaffDetailView, toggle_break_status
)

urlpatterns = [
    # Department endpoints
    path('departments/', DepartmentListView.as_view(), name='department_list'),                # List & create departments
    path('departments/<int:pk>/', DepartmentDetailView.as_view(), name='department_detail'),   # Retrieve department
    path('departments/create/', DepartmentCreateView.as_view(), name='department_create'),     # Create department (admin)
    path('departments/<int:pk>/update/', DepartmentUpdateView.as_view(), name='department_update'), # Update department (admin)

    # Staff endpoints
    path('staff/', StaffListView.as_view(), name='staff_list'),                                # List staff (filter by department with ?department=<id>)
    path('staff/<int:pk>/', StaffDetailView.as_view(), name='staff_detail'),                   # Retrieve staff member
    path('staff/<int:staff_id>/break/', toggle_break_status, name='toggle_break'),             # Toggle break status for staff
]
