from rest_framework import serializers
from .models import FactureTravaux, PlanTraite, Traite


class TraiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Traite
        fields = '__all__'


class PlanTraiteSerializer(serializers.ModelSerializer):
    traites = TraiteSerializer(many=True, read_only=True)
    facture_numero = serializers.CharField(source='facture.numero_facture', read_only=True)
    client_nom = serializers.CharField(source='facture.client.nom_raison_sociale', read_only=True)  # Assure-toi que ce champ existe

    class Meta:
        model = PlanTraite
        fields = '__all__'


class CreatePlanTraiteSerializer(serializers.Serializer):
    facture_id = serializers.IntegerField(required=True)
    nombre_traite = serializers.IntegerField(min_value=1, max_value=24, required=True)
    date_premier_echeance = serializers.DateField(required=True)
    periode = serializers.IntegerField(min_value=1, required=False, default=30)

    def validate_facture_id(self, value):
        if not FactureTravaux.objects.filter(pk=value).exists():
            raise serializers.ValidationError("La facture spécifiée n'existe pas.")
        return value


class UpdateTraiteStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Traite.STATUT_CHOICES)
