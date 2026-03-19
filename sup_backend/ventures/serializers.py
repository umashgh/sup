from rest_framework import serializers
from .models import Venture, StartupCost, FounderSalary

class StartupCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = StartupCost
        fields = '__all__'
        read_only_fields = ('venture',)

class FounderSalarySerializer(serializers.ModelSerializer):
    class Meta:
        model = FounderSalary
        fields = '__all__'
        read_only_fields = ('venture',)

class VentureSerializer(serializers.ModelSerializer):
    costs = StartupCostSerializer(many=True, read_only=True)
    salaries = FounderSalarySerializer(many=True, read_only=True)

    class Meta:
        model = Venture
        fields = '__all__'
        read_only_fields = ('user',)
