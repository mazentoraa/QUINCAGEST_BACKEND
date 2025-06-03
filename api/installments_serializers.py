from rest_framework import serializers
from .models import PlanTraite, Traite, Cd


class TraiteSerializer(serializers.ModelSerializer):
    numero_facture = serializers.CharField(source='plan_traite.numero_facture', read_only=True)
    nom_raison_sociale = serializers.CharField(source='plan_traite.nom_raison_sociale', read_only=True)

    class Meta:
        model = Traite
        fields = '__all__'
        extra_fields = ('numero_facture', 'nom_raison_sociale')

    def get_fields(self):
        fields = super().get_fields()
        for field_name in getattr(self.Meta, 'extra_fields', []):
            fields[field_name] = serializers.ReadOnlyField()
        return fields


class PlanTraiteSerializer(serializers.ModelSerializer):
    traites = TraiteSerializer(many=True, read_only=True)
    facture_numero = serializers.CharField(source='numero_facture', read_only=True)
    client_nom = serializers.CharField(source='nom_raison_sociale', read_only=True)

    class Meta:
        model = PlanTraite
        fields = '__all__'


class CreatePlanTraiteSerializer(serializers.Serializer):
    numero_commande = serializers.CharField(required=True)
    nombre_traite = serializers.IntegerField(min_value=1, max_value=24, required=True)
    date_premier_echeance = serializers.DateField(required=True)
    periode = serializers.IntegerField(min_value=1, required=False, default=30)
    montant_total = serializers.FloatField(required=False, allow_null=True)

    def validate_numero_commande(self, value):
        if not Cd.objects.filter(numero_commande=value).exists():
            raise serializers.ValidationError("La commande spécifiée n'existe pas.")
        return value


class UpdateTraiteStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Traite.STATUT_CHOICES)
