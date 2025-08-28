from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from .models import LabTest, LabDepartment, LabTechnician, LabSchedule, LabAnalytics
from .serializers import (
    LabTestSerializer, LabDepartmentSerializer, LabTechnicianSerializer,
    LabScheduleSerializer, LabTestCreateSerializer
)
from .services import LabManagementService
from .permissions import (
    CanOrderLabTest, CanManageLab, IsLabDepartmentMember, CanViewLabResults
)
from users.models import Patient
from hospital.models import Staff
from queues.models import QueueEntry

class LabTestListCreateView(generics.ListCreateAPIView):
    """
    List lab tests or create a new lab test.
    Permissions:
      - List: authenticated users (object-level CanViewLabResults)
      - Create: CanOrderLabTest
    """
    serializer_class = LabTestSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), CanOrderLabTest()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = LabTest.objects.all()
        # Filtering logic
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        lab_dept = self.request.query_params.get('lab_department')
        if lab_dept:
            queryset = queryset.filter(lab_department_id=lab_dept)
        # Object-level permission filtering
        user = self.request.user
        return [obj for obj in queryset.order_by('-ordered_at') if CanViewLabResults().has_object_permission(self.request, self, obj)]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LabTestCreateSerializer
        return LabTestSerializer

    def perform_create(self, serializer):
        staff = Staff.objects.get(user=self.request.user)
        service = LabManagementService()
        lab_test = service.order_lab_test(
            patient=serializer.validated_data['patient'],
            test_type=serializer.validated_data['test_type'],
            ordered_by=staff,
            priority=serializer.validated_data.get('priority', 'routine'),
            clinical_notes=serializer.validated_data.get('clinical_notes', ''),
            queue_entry=serializer.validated_data.get('queue_reentry', None)
        )
        return lab_test

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanOrderLabTest])
def order_lab_test(request):
    """Order a new lab test (alternative endpoint)"""
    staff = Staff.objects.filter(user=request.user).first()
    if not staff:
        return Response({'error': 'Staff profile not found'}, status=status.HTTP_404_NOT_FOUND)
    patient_id = request.data.get('patient_id')
    test_type = request.data.get('test_type')
    priority = request.data.get('priority', 'routine')
    clinical_notes = request.data.get('clinical_notes', '')
    queue_entry_id = request.data.get('queue_entry_id')
    patient = Patient.objects.filter(id=patient_id).first()
    if not patient:
        return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)
    queue_entry = QueueEntry.objects.filter(id=queue_entry_id).first() if queue_entry_id else None
    service = LabManagementService()
    try:
        lab_test = service.order_lab_test(
            patient=patient,
            test_type=test_type,
            ordered_by=staff,
            priority=priority,
            clinical_notes=clinical_notes,
            queue_entry=queue_entry
        )
        return Response(LabTestSerializer(lab_test).data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageLab])
def start_test(request, test_id):
    """Start a lab test (lab technician only)"""
    technician = LabTechnician.objects.filter(staff__user=request.user).first()
    if not technician:
        return Response({'error': 'Lab technician profile not found'}, status=status.HTTP_404_NOT_FOUND)
    lab_test = LabTest.objects.filter(
        id=test_id,
        lab_department=technician.lab_department,
        status__in=['ordered', 'scheduled']
    ).first()
    if not lab_test:
        return Response({'error': 'Lab test not found or cannot be started'}, status=status.HTTP_404_NOT_FOUND)
    equipment_id = request.data.get('equipment_id')
    equipment = lab_test.lab_department.labequipment_set.filter(id=equipment_id).first() if equipment_id else None
    # Permission: Only assigned technician or department member can start
    if not IsLabDepartmentMember().has_object_permission(request, None, lab_test):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    lab_test.start_test(technician=technician, equipment=equipment)
    return Response({'message': 'Test started successfully'})

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageLab])
def complete_test(request, test_id):
    """Complete a lab test with results (lab technician only)"""
    technician = LabTechnician.objects.filter(staff__user=request.user).first()
    if not technician:
        return Response({'error': 'Lab technician profile not found'}, status=status.HTTP_404_NOT_FOUND)
    lab_test = LabTest.objects.filter(
        id=test_id,
        assigned_technician=technician,
        status='in_progress'
    ).first()
    if not lab_test:
        return Response({'error': 'Lab test not found or cannot be completed'}, status=status.HTTP_404_NOT_FOUND)
    # Permission: Only assigned technician can complete
    if lab_test.assigned_technician != technician:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    results = request.data.get('results', '')
    normal_ranges = request.data.get('normal_ranges', {})
    abnormal_flags = request.data.get('abnormal_flags', [])
    service = LabManagementService()
    service.complete_test_workflow(lab_test, results, normal_ranges, abnormal_flags)
    return Response({'message': 'Test completed successfully'})

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanOrderLabTest])
def review_test(request, test_id):
    """Review and approve test results (doctor/nurse/staff only)"""
    staff = Staff.objects.filter(user=request.user).first()
    if not staff:
        return Response({'error': 'Staff profile not found'}, status=status.HTTP_404_NOT_FOUND)
    lab_test = LabTest.objects.filter(id=test_id, status='completed').first()
    if not lab_test:
        return Response({'error': 'Lab test not found or cannot be reviewed'}, status=status.HTTP_404_NOT_FOUND)
    # Permission: Only ordering staff or department member can review
    if lab_test.ordered_by != staff and not IsLabDepartmentMember().has_object_permission(request, None, lab_test):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    approved = request.data.get('approved', True)
    lab_test.review_test(staff, approved)
    return Response({'message': 'Test reviewed successfully'})

class LabDepartmentListView(generics.ListAPIView):
    """
    List all active lab departments.
    Permissions: authenticated users.
    """
    queryset = LabDepartment.objects.filter(is_active=True)
    serializer_class = LabDepartmentSerializer
    permission_classes = [IsAuthenticated]

class LabScheduleListView(generics.ListAPIView):
    """
    List lab schedules, filterable by date and technician.
    Permissions: CanManageLab.
    """
    serializer_class = LabScheduleSerializer
    permission_classes = [IsAuthenticated, CanManageLab]

    def get_queryset(self):
        queryset = LabSchedule.objects.all()
        date_filter = self.request.query_params.get('date')
        if date_filter:
            queryset = queryset.filter(scheduled_date=date_filter)
        tech_id = self.request.query_params.get('technician_id')
        if tech_id:
            queryset = queryset.filter(technician_id=tech_id)
        # Object-level permission: Only show schedules for user's department
        user = self.request.user
        if hasattr(user, 'staff_profile') and getattr(user.staff_profile, 'lab_department', None):
            queryset = queryset.filter(lab_test__lab_department=user.staff_profile.lab_department)
        return queryset.order_by('scheduled_date', 'scheduled_time')

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsLabDepartmentMember])
def lab_analytics(request, lab_dept_id):
    """Get analytics for a lab department (lab department member only)"""
    lab_dept = LabDepartment.objects.filter(id=lab_dept_id).first()
    if not lab_dept:
        return Response({'error': 'Lab department not found'}, status=status.HTTP_404_NOT_FOUND)
    # Object-level permission: Only members of department can view
    if not IsLabDepartmentMember().has_object_permission(request, None, lab_dept):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    recent_analytics = LabAnalytics.objects.filter(
        lab_department=lab_dept
    ).order_by('-date')[:7]  # Last 7 days
    analytics_data = []
    for analytics in recent_analytics:
        analytics_data.append({
            'date': analytics.date,
            'total_tests_ordered': analytics.total_tests_ordered,
            'tests_completed': analytics.tests_completed,
            'tests_pending': analytics.tests_pending,
            'tests_overdue': analytics.tests_overdue,
            'avg_turnaround_time': analytics.avg_turnaround_time,
            'avg_processing_time': analytics.avg_processing_time,
            'stat_tests': analytics.stat_tests,
            'urgent_tests': analytics.urgent_tests,
            'routine_tests': analytics.routine_tests,
        })
    return Response({
        'lab_department': LabDepartmentSerializer(lab_dept).data,
        'analytics': analytics_data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageLab])
def run_lab_maintenance(request):
    """Admin/lab technician endpoint to run lab maintenance tasks"""
    # Only admin, superadmin, or lab technician can run
    if not CanManageLab().has_permission(request, None):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    service = LabManagementService()
    service.run_maintenance_tasks()
    return Response({'message': 'Lab maintenance tasks completed successfully'})
