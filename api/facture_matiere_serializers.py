from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from .models import FactureMatiere, Matiere, Client


class MatiereReceptionSerializer(serializers.Serializer):
    matiere_id = serializers.IntegerField()
    type_matiere = serializers.CharField(read_only=True)
    quantite = serializers.IntegerField(read_only=True)
    prix_unitaire = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    surface = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)


class FactureMatiereSerializer(serializers.ModelSerializer):
    client_details = serializers.SerializerMethodField()
    matieres_details = serializers.SerializerMethodField()
    client = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all(), write_only=True)

    montant_ht = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    montant_tva = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    montant_ttc = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = FactureMatiere
        fields = (
            "id",
            "numero_bon",
            "client",
            "client_details",
            "matieres",
            "matieres_details",
            "date_reception",
            "notes",
            "tax_rate",
            "montant_ht",
            "montant_tva",
            "montant_ttc",
            "date_creation",
            "derniere_mise_a_jour",
        )
        read_only_fields = ("date_creation", "derniere_mise_a_jour")

    def get_client_details(self, obj):
        return {
            "id": obj.client.id,
            "nom_client": obj.client.nom_client,
            "numero_fiscal": obj.client.numero_fiscal,
            "adresse": obj.client.adresse,
            "telephone": obj.client.telephone,
            "email": obj.client.email,
        }

    def get_matieres_details(self, obj):
        return [
            {
                "id": m.id,
                "type_matiere": m.type_matiere,
                "description": m.description,
                "quantite": m.quantite,
                "prix_unitaire": float(m.prix_unitaire or 0),
                "surface": float(m.surface or 0),
            }
            for m in obj.matieres.all()
        ]

    @transaction.atomic
    def create(self, validated_data):
        client = validated_data.pop("client")
        matieres = validated_data.pop("matieres", [])

        if not validated_data.get("numero_bon"):
            today = timezone.now().strftime("%Y%m%d")
            count = FactureMatiere.objects.filter(numero_bon__startswith=f"MAT-{today}").count()
            validated_data["numero_bon"] = f"MAT-{today}-{count + 1:03d}"

        facture = FactureMatiere.objects.create(client=client, **validated_data)
        facture.matieres.set(matieres)
        facture.calculate_totals()
        facture.save()
        return facture


class FactureMatiereDetailSerializer(FactureMatiereSerializer):
    client_name = serializers.CharField(source="client.nom_client", read_only=True)

    class Meta(FactureMatiereSerializer.Meta):
        fields = FactureMatiereSerializer.Meta.fields + ("client_name",)
