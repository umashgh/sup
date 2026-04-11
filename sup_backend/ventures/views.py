from rest_framework import viewsets, permissions
from .models import Venture, StartupCost, FounderSalary
from .serializers import VentureSerializer, StartupCostSerializer, FounderSalarySerializer

class BaseUserViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class VentureViewSet(BaseUserViewSet):
    queryset = Venture.objects.all()
    serializer_class = VentureSerializer

class StartupCostViewSet(viewsets.ModelViewSet):
    queryset = StartupCost.objects.all()
    serializer_class = StartupCostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(venture__user=self.request.user)

    def perform_create(self, serializer):
        venture_id = serializer.validated_data.get('venture')
        if venture_id and not Venture.objects.filter(id=venture_id.id, user=self.request.user).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Venture does not belong to you.")
        serializer.save()

class FounderSalaryViewSet(viewsets.ModelViewSet):
    queryset = FounderSalary.objects.all()
    serializer_class = FounderSalarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(venture__user=self.request.user)

    def perform_create(self, serializer):
        venture_id = serializer.validated_data.get('venture')
        if venture_id and not Venture.objects.filter(id=venture_id.id, user=self.request.user).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Venture does not belong to you.")
        serializer.save()
