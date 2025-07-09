from rest_framework import serializers
from .models import Client, Traveaux, Produit, Matiere, MatiereUsage, Entreprise
from drf_extra_fields.fields import Base64ImageField
from django.db import transaction
from .models import MatierePremiereAchat
from decimal import Decimal

class MatiereSerializer(serializers.ModelSerializer):
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), source="client"
    )
    client_name = serializers.CharField(source="client.nom_client", read_only=True)
    prix_unitaire = serializers.FloatField(required=False)

    class Meta:
        model = Matiere
        fields = (
            "id",
            "numero_bon",
            "type_matiere",
            "reception_date",
            "client_name",
            "client_id",
            "description",
            "prix_unitaire",
            "date_creation",
            "quantite",
            "remaining_quantity",  # ✅ doit rester ici
            "derniere_mise_a_jour",
            "width",
            "length",
            "thickness",
            "surface",
        )
        extra_kwargs = {
            "type_matiere": {"required": True},
            "description": {"required": False},
            "prix_unitaire": {"required": False},
            "client_id": {"required": True},
            "numero_bon": {"required": False, "allow_null": True, "allow_blank": True},
            "quantite": {"required": True},
            "remaining_quantity": {"required": False},  # ✅ autorisé en écriture
        }
        read_only_fields = (
            "date_creation",
            "derniere_mise_a_jour",
          
        )


from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from .models import Produit

class ProduitSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Produit
        fields = [
            "id",
            "nom_produit",
            "description",
            "type_matiere",
            "prix",
            "image",
            "epaisseur",
            "longueur",
            "largeur",
            "surface",
            "date_creation",
            "derniere_mise_a_jour",
            "code_produit",
        ]
        extra_kwargs = {
            'image': {'required': False, 'allow_null': True},
        }

    def update(self, instance, validated_data):
        # Si image=null est envoyé, supprimer l'image existante
        if 'image' in validated_data and validated_data['image'] is None:
            if instance.image:
                instance.image.delete(save=False)
            instance.image = None
            validated_data.pop('image')

        return super().update(instance, validated_data)


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"
        read_only_fields = ("date_creation", "derniere_mise_a_jour")

        def validate_numero_fiscal(self, value):
            import re
            pattern = r'^\d{3}\s\d{4}[A-Z]/[A-Z]/[A-Z]/\d{3}$'
            if not re.match(pattern, value):
                raise serializers.ValidationError(
                    "Format invalide. Format attendu : 000 0000X/X/X/000"
                )
            return value


class MatiereUsageSerializer(serializers.ModelSerializer):
    matiere_id = serializers.IntegerField(write_only=True) # To acccept
    material_id = serializers.SerializerMethodField(read_only=True) # to return

    class Meta:
        model = MatiereUsage
        fields = ("matiere_id", "material_id", "quantite_utilisee", "source")

    def get_material_id(self, obj):
        if obj.source == "client" and obj.matiere:
            return obj.matiere.id
        elif obj.source == "stock" and obj.achat:
            return obj.achat.id
        return None


class TraveauxSerializer(serializers.ModelSerializer):
    client_id = serializers.IntegerField()
    produit_id = serializers.IntegerField()
    client_name = serializers.CharField(source="client.nom_client", read_only=True)
    produit_name = serializers.CharField(source="produit.nom_produit", read_only=True)
    matiere_usages = MatiereUsageSerializer(many=True, required=False)
    remise = serializers.FloatField(required=False, default=0)

    class Meta:
        model = Traveaux
        fields = (
            "id",
            "client_id",
            "produit_id",
            "client_name",
            "produit_name",
            "duree",
            "quantite",
            "description",
            "date_creation",
            "matiere_usages",
            "derniere_mise_a_jour",
            "remise",
        )
        read_only_fields = (
            "date_creation",
            "derniere_mise_a_jour",
            "client_name",
            "produit_name",
        )
        extra_kwargs = {"duree": {"required": True}, "quantite": {"required": True},"remise": {"required": False, "default": 0},}

    @transaction.atomic
    def create(self, validated_data):
        print("🔥 Validated Data:", validated_data)
        client_id = validated_data.pop("client_id")
        produit_id = validated_data.pop("produit_id")
        matiere_usages_data = validated_data.pop("matiere_usages", [])

        try:
            client = Client.objects.get(pk=client_id)
            produit = Produit.objects.get(pk=produit_id)
            validated_data["client"] = client
            validated_data["produit"] = produit
        except (Client.DoesNotExist, Produit.DoesNotExist):
            raise serializers.ValidationError("Client or Product not found")

        travaux = Traveaux.objects.create(**validated_data)

        # Process material usage
        for matiere_usage_data in matiere_usages_data:
            matiere_id = matiere_usage_data.get("matiere_id")
            quantite_utilisee = Decimal(matiere_usage_data.get("quantite_utilisee"))
            source = matiere_usage_data.get("source", "stock")  # Default to main stock

            if source == "client":
                try:
                    matiere = Matiere.objects.get(pk=matiere_id)

                    # Check if we have enough quantity
                    if matiere.remaining_quantity < quantite_utilisee:
                        raise serializers.ValidationError(
                            f"Not enough material available. Only {matiere.remaining_quantity} units of {matiere.type_matiere} remaining."
                        )

                    # Create the usage record
                    MatiereUsage.objects.create(
                        travaux=travaux,
                        matiere=matiere,
                        quantite_utilisee=quantite_utilisee,
                        source=source
                    )

                    # Update the remaining quantity
                    matiere.remaining_quantity -= quantite_utilisee
                    matiere.save()

                except Matiere.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Material with ID {matiere_id} not found"
                    )
            elif source == "stock":
                try:
                    achat = MatierePremiereAchat.objects.get(pk=matiere_id)
                    if achat.remaining_quantity < quantite_utilisee:
                        raise serializers.ValidationError(
                            f"Not enough stock: {achat.remaining_quantity} remaining for {achat.nom_matiere}"
                        )
                    achat.remaining_quantity -= quantite_utilisee
                    achat.save()

                    MatiereUsage.objects.create(
                        travaux=travaux,
                        quantite_utilisee=quantite_utilisee,
                        source=source,
                        achat_id=achat.id 
                    )

                except MatierePremiereAchat.DoesNotExist:
                    raise serializers.ValidationError(f"Stock material with ID {matiere_id} not found")

        return travaux
    
    def update(self, instance, validated_data):
        if "matiere_usages" in validated_data:
            matiere_usages_data = validated_data.pop("matiere_usages")

            # Reset quantities for existing usages first
            for usage in instance.matiere_usages.all():
                if usage.source == "client" and usage.matiere:
                    usage.matiere.remaining_quantity += usage.quantite_utilisee
                    usage.matiere.save()
                elif usage.source == "stock" and usage.achat:
                    usage.achat.remaining_quantity += usage.quantite_utilisee
                    usage.achat.save()
                usage.delete()

            # Re-add new usages
            for usage_data in matiere_usages_data:
                source = usage_data.get("source", "stock")
                matiere_id = usage_data.get("matiere_id")
                quantite_utilisee = usage_data.get("quantite_utilisee")

                if source == "client":
                    try:
                        matiere = Matiere.objects.get(pk=matiere_id)
                        if matiere.remaining_quantity < quantite_utilisee:
                            raise serializers.ValidationError(
                                f"Not enough client material. Only {matiere.remaining_quantity} units left of {matiere.type_matiere}."
                            )

                        MatiereUsage.objects.create(
                            travaux=instance,
                            matiere=matiere,
                            quantite_utilisee=quantite_utilisee,
                            source=source,
                        )

                        matiere.remaining_quantity -= quantite_utilisee
                        matiere.save()
                    except Matiere.DoesNotExist:
                        raise serializers.ValidationError(
                            f"Client material with ID {matiere_id} not found."
                        )

                elif source == "stock":
                    try:
                        achat = MatierePremiereAchat.objects.get(pk=matiere_id)
                        if achat.remaining_quantity < quantite_utilisee:
                            raise serializers.ValidationError(
                                f"Not enough stock material. Only {achat.remaining_quantity} units left of {achat.nom_matiere}."
                            )

                        MatiereUsage.objects.create(
                            travaux=instance,
                            achat=achat,
                            quantite_utilisee=quantite_utilisee,
                            source=source,
                        )

                        achat.remaining_quantity -= quantite_utilisee
                        achat.save()
                    except MatierePremiereAchat.DoesNotExist:
                        raise serializers.ValidationError(
                            f"Stock material with ID {matiere_id} not found."
                        )

        return super().update(instance, validated_data)


class EntrepriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entreprise
        fields = "__all__"

class MatierePremiereAchatSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatierePremiereAchat
        fields = '__all__'

from rest_framework import serializers
from .models import FactureAchatMatiere, Achat


class AchatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achat
        fields = ['id', 'nom', 'prix', 'quantite']


class FactureAchatMatiereSerializer(serializers.ModelSerializer):
    achats = AchatSerializer(many=True)

    class Meta:
        model = FactureAchatMatiere
        fields = ['id', 'numero', 'fournisseur', 'type_achat', 'prix_total', 'date_facture', 'achats']

    def create(self, validated_data):
        achats_data = validated_data.pop('achats', [])
        facture = FactureAchatMatiere.objects.create(**validated_data)
        for achat_data in achats_data:
            Achat.objects.create(facture=facture, **achat_data)
        return facture

    def update(self, instance, validated_data):
        achats_data = validated_data.pop('achats', [])

        # mettre à jour les champs de la facture
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # supprimer les anciens achats liés
        instance.achats.all().delete()

        # recréer les nouveaux achats
        for achat_data in achats_data:
            Achat.objects.create(facture=instance, **achat_data)

        return instance



from .models import BonLivraisonMatiere, Livraison


class LivraisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Livraison
        fields = ['id', 'nom', 'prix', 'quantite']


class BonLivraisonMatiereSerializer(serializers.ModelSerializer):
    livraisons = LivraisonSerializer(many=True)

    class Meta:
        model = BonLivraisonMatiere
        fields = ['id', 'numero', 'fournisseur', 'type_achat', 'prix_total', 'date_livraison', 'livraisons']

    def create(self, validated_data):
        livraisons_data = validated_data.pop('livraisons', [])
        bon = BonLivraisonMatiere.objects.create(**validated_data)
        for livraison_data in livraisons_data:
            Livraison.objects.create(bon=bon, **livraison_data)
        return bon

    def update(self, instance, validated_data):
        livraisons_data = validated_data.pop('livraisons', [])

        # Mise à jour des champs du bon
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Supprimer les anciennes livraisons
        instance.livraisons.all().delete()

        # Créer les nouvelles livraisons
        for livraison_data in livraisons_data:
            Livraison.objects.create(bon=instance, **livraison_data)

        return instance

from .models import Fournisseur

class FournisseurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fournisseur
        fields = '__all__'


from .models import Consommable

class ConsommableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consommable
        fields = '__all__'
