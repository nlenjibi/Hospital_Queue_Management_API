# departments/views.py
from rest_framework import generics, permissions
from .models import Department, DepartmentStaff
from .serializers import DepartmentSerializer, DepartmentStaffSerializer

class DepartmentList(generics.ListAPIView):
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

class DepartmentStaffList(generics.ListAPIView):
    serializer_class = DepartmentStaffSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        department_id = self.kwargs['department_id']
        return DepartmentStaff.objects.filter(department_id=department_id)
    
    # departments/views.py (add these)
class DepartmentDetail(generics.RetrieveAPIView):
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

class DepartmentCreate(generics.CreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAdminUser]

class DepartmentUpdate(generics.UpdateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAdminUser]