from rest_framework import serializers
from .models import (
    AssetMaster, IncomeMaster, ExpenseMaster,
    FamilyProfile, FamilyMember, Asset, Income, Expense
)

# --- Master Data Serializers ---

class AssetMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetMaster
        fields = '__all__'

class IncomeMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeMaster
        fields = '__all__'

class ExpenseMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseMaster
        fields = '__all__'

# --- User Data Serializers ---

class FamilyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyProfile
        fields = '__all__'
        read_only_fields = ('user',)

class FamilyMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyMember
        fields = '__all__'
        read_only_fields = ('user',)

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = '__all__'
        read_only_fields = ('user',)

class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = '__all__'
        read_only_fields = ('user',)

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ('user',)
