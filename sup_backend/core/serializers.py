"""
Serializers for core app models and dynamic questions.
"""

from rest_framework import serializers
from .models import ScenarioProfile
from .questions import Question


class ScenarioProfileSerializer(serializers.ModelSerializer):
    """Serializer for ScenarioProfile model."""

    scenario_type_display = serializers.CharField(source='get_scenario_type_display', read_only=True)

    class Meta:
        model = ScenarioProfile
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')


class QuestionSerializer(serializers.Serializer):
    """
    Serializer for Question objects (not a model, just a data structure).
    """
    id = serializers.CharField()
    text = serializers.CharField()
    field_name = serializers.CharField()
    input_type = serializers.CharField()
    tier = serializers.CharField()
    scenarios = serializers.ListField(child=serializers.CharField())
    options = serializers.ListField(child=serializers.DictField(), required=False)
    validation = serializers.DictField(required=False)
    slider_config = serializers.DictField(required=False)
    help_text = serializers.CharField(required=False, allow_null=True)

    def to_representation(self, instance):
        """
        Convert Question object to dict for serialization.
        """
        if isinstance(instance, Question):
            return instance.to_dict()
        return super().to_representation(instance)
