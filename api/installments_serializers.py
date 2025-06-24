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
    bank_name = serializers.CharField(read_only=True)
    bank_address = serializers.CharField(read_only=True)

    class Meta:
        model = PlanTraite
        fields = '__all__'


class CreatePlanTraiteSerializer(serializers.Serializer):
    numero_commande = serializers.CharField(required=True)
    nombre_traite = serializers.IntegerField(min_value=1, max_value=24, required=True)
    date_premier_echeance = serializers.DateField(required=True)
    periode = serializers.IntegerField(min_value=1, required=False, default=30)
    montant_total = serializers.FloatField(required=False, allow_null=True)
    rip = serializers.CharField(required=False, allow_blank=True)
    acceptance = serializers.CharField(required=False, allow_blank=True)
    notice = serializers.CharField(required=False, allow_blank=True)
    bank_name = serializers.CharField(required=False, allow_blank=True)
    bank_address = serializers.CharField(required=False, allow_blank=True)

    def validate_numero_commande(self, value):
        if not Cd.objects.filter(numero_commande=value).exists():
            raise serializers.ValidationError("La commande spécifiée n'existe pas.")
        return value

    def create(self, validated_data):
        commande = Cd.objects.get(numero_commande=validated_data["numero_commande"])
        client = commande.client

        plan = PlanTraite.objects.create(
            facture=commande.facture if hasattr(commande, 'facture') else None,
            client=client,
            numero_facture=commande.numero_commande,
            nom_raison_sociale=client.nom_client,
            matricule_fiscal=client.numero_fiscal,
            nombre_traite=validated_data["nombre_traite"],
            date_premier_echeance=validated_data["date_premier_echeance"],
            periode=validated_data.get("periode", 30),
            montant_total=validated_data.get("montant_total"),
            rip=validated_data.get("rip", ""),
            acceptance=validated_data.get("acceptance", ""),
            notice=validated_data.get("notice", ""),
            bank_name=validated_data.get("bank_name", ""),
            bank_address=validated_data.get("bank_address", ""),
        )

        return plan


class UpdateTraiteStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['PAYEE', 'NON_PAYEE'])

    def validate_status(self, value):
        return value.upper()

class UpdatePlanStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['PAYEE', 'NON_PAYEE', 'PARTIELLEMENT_PAYEE'])

    def validate_status(self, value):
        return value.upper()
