from rest_framework import serializers
from .models import FactureTravaux, PlanTraite, Traite
from .serializers import ClientSerializer
from django.db import transaction
from django.utils import timezone



class PlanTraiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanTraite
        fields = "__all__"

class TraiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Traite
        fields = "__all__"  
class PlanTraiteSerializer(serializers.ModelSerializer):
    traites = TraiteSerializer(many=True, read_only=True)
    facture_numero = serializers.CharField(source='facture.numero_facture', read_only=True)
    client_nom = serializers.CharField(source='facture.client.nom_client', read_only=True)
    
    class Meta:
        model = PlanTraite
        fields = '__all__'
class CreatePlanTraiteSerializer(serializers.Serializer):
    facture_id = serializers.IntegerField()
    nombre_traite = serializers.IntegerField(min_value=1, max_value=24)
    date_premier_echeance = serializers.DateField()
    periode = serializers.IntegerField(min_value=1, required=False, default=30)
    
    def validate_facture_id(self, value):
        if not FactureTravaux.objects.filter(pk=value).exists():
            raise serializers.ValidationError("La facture spécifiée n'existe pas")
        return value
class UpdateTraiteStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Traite.STATUT_CHOICES)