from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Department, Staff
from .serializers import DepartmentSerializer, StaffSerializer
from .permissions import IsDepartmentAdmin, IsStaffOrReadOnly, IsDepartmentMember

# Department Views
class DepartmentListView(generics.ListCreateAPIView):
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

class DepartmentDetailView(generics.RetrieveAPIView):
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsDepartmentMember]

class DepartmentCreateView(generics.CreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsDepartmentAdmin]

class DepartmentUpdateView(generics.UpdateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsDepartmentAdmin]

# Staff Views
class StaffListView(generics.ListAPIView):
    serializer_class = StaffSerializer
    permission_classes = [IsStaffOrReadOnly]

    def get_queryset(self):
        queryset = Staff.objects.all()
        department = self.request.query_params.get('department')
        available_only = self.request.query_params.get('available')
        if department:
            queryset = queryset.filter(department_id=department)
        if available_only == 'true':
            queryset = queryset.filter(is_on_break=False)
        return queryset

class StaffDetailView(generics.RetrieveAPIView):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    permission_classes = [IsStaffOrReadOnly]

@api_view(['PATCH'])
@permission_classes([IsStaffOrReadOnly])
def toggle_break_status(request, staff_id):
    try:
        staff = Staff.objects.get(id=staff_id, user=request.user)
        staff.is_on_break = not staff.is_on_break
        staff.save()
        return Response({'is_on_break': staff.is_on_break})
    except Staff.DoesNotExist:
        return Response({'error': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)