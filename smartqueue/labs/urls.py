from django.urls import path
from . import views
from .views import (
    LabTestListCreateView,
    order_lab_test,
    start_test,
    complete_test,
    review_test,
    LabDepartmentListView,
    LabScheduleListView,
    lab_analytics,
    run_lab_maintenance,
)

urlpatterns = [
    # Lab Tests
    path('tests/', LabTestListCreateView.as_view(), name='labtest-list-create'),
    path('tests/order/', order_lab_test, name='labtest-order'),
    path('tests/<int:test_id>/start/', start_test, name='labtest-start'),
    path('tests/<int:test_id>/complete/', complete_test, name='labtest-complete'),
    path('tests/<int:test_id>/review/', review_test, name='labtest-review'),

    # Lab Departments
    path('departments/', LabDepartmentListView.as_view(), name='labdepartment-list'),

    # Lab Schedules
    path('schedules/', LabScheduleListView.as_view(), name='labschedule-list'),

    # Analytics
    path('departments/<int:lab_dept_id>/analytics/', lab_analytics, name='labdepartment-analytics'),

    # Maintenance
    path('maintenance/run/', run_lab_maintenance, name='lab-maintenance'),
]
