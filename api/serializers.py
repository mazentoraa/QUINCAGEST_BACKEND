from rest_framework import serializers
from .models import Client, Traveaux, Produit, Matiere, MatiereUsage, Entreprise
from drf_extra_fields.fields import Base64ImageField
from django.db import transaction
from .models import MatierePremiereAchat

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
    matiere_id = serializers.IntegerField()

    class Meta:
        model = MatiereUsage
        fields = ("matiere_id", "quantite_utilisee")


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
            quantite_utilisee = matiere_usage_data.get("quantite_utilisee")

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
                )

                # Update the remaining quantity
                matiere.remaining_quantity -= quantite_utilisee
                matiere.save()

            except Matiere.DoesNotExist:
                raise serializers.ValidationError(
                    f"Material with ID {matiere_id} not found"
                )

        return travaux

    def update(self, instance, validated_data):
        if "matiere_usages" in validated_data:
            matiere_usages_data = validated_data.pop("matiere_usages")

            # Reset quantities for existing usages first
            for usage in instance.matiere_usages.all():
                matiere = usage.matiere
                matiere.remaining_quantity += usage.quantite_utilisee
                matiere.save()
                usage.delete()

            # Add new usages
            for matiere_usage_data in matiere_usages_data:
                matiere_id = matiere_usage_data.get("matiere_id")
                quantite_utilisee = matiere_usage_data.get("quantite_utilisee")
                try:
                    matiere = Matiere.objects.get(pk=matiere_id)

                    # Check if we have enough quantity
                    if matiere.remaining_quantity < quantite_utilisee:
                        raise serializers.ValidationError(
                            f"Not enough material available. Only {matiere.remaining_quantity} units of {matiere.type_matiere} remaining."
                        )

                    # Create the usage record
                    MatiereUsage.objects.create(
                        travaux=instance,
                        matiere=matiere,
                        quantite_utilisee=quantite_utilisee,
                    )

                    # Update the remaining quantity
                    matiere.remaining_quantity -= quantite_utilisee
                    matiere.save()

                except Matiere.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Material with ID {matiere_id} not found"
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
        fields = ['id', 'numero', 'fournisseur', 'type_achat','mode_paiement', 'prix_total', 'date_facture', 'achats']

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


from rest_framework import serializers
from .models import BonRetourFournisseur, MatiereRetourFournisseur, Matiere, Fournisseur


class MatiereForRetourFournisseurSerializer(serializers.ModelSerializer):
    """Serializer for materials available for return to fournisseur"""

    nom_matiere = serializers.CharField()
    quantite_retournee = serializers.IntegerField(min_value=1)

    class Meta:
        model = Matiere
        fields = [
            "nom_matiere",
            "quantite_retournee",
        ]
        read_only_fields = [
            "id",
            "type_matiere",
            "description",
            "thickness",
            "length",
            "width",
            "surface",
            "remaining_quantity",
        ]

    def validate_quantite_retournee(self, value):
        if hasattr(self, "instance") and self.instance:
            if value > self.instance.remaining_quantity:
                raise serializers.ValidationError(
                    f"Cannot return {value} units. Only {self.instance.remaining_quantity} remaining."
                )
        return value


class MatiereRetourFournisseurFreeSerializer(serializers.Serializer):
    nom_matiere = serializers.CharField()
    quantite_retournee = serializers.IntegerField(min_value=1)

    class Meta:
        model = MatiereRetourFournisseur
        fields = ["id", "matiere_id", "matiere_details", "quantite_retournee"]

    def validate_matiere_id(self, value):
        try:
            matiere = Matiere.objects.get(id=value)
            return value
        except Matiere.DoesNotExist:
            raise serializers.ValidationError("Material not found.")

    def validate(self, attrs):
        matiere_id = attrs.get("matiere_id")
        quantite_retournee = attrs.get("quantite_retournee", 1)

        if matiere_id:
            try:
                matiere = Matiere.objects.get(id=matiere_id)
                if quantite_retournee > matiere.remaining_quantity:
                    raise serializers.ValidationError({
                        "quantite_retournee": f"Cannot return {quantite_retournee} units. Only {matiere.remaining_quantity} remaining."
                    })
            except Matiere.DoesNotExist:
                raise serializers.ValidationError({"matiere_id": "Material not found."})
        return attrs


class FournisseurBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fournisseur
        fields = ["id", "nom", "adresse"]


class BonRetourFournisseurSerializer(serializers.ModelSerializer):
    fournisseur_details = FournisseurBasicSerializer(source="fournisseur", read_only=True)
    matiere_retours = MatiereRetourFournisseurFreeSerializer(many=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = BonRetourFournisseur
        fields = [
            "id",
            "numero_bon",
            "fournisseur",
            "fournisseur_details",
            "status",
            "status_display",
            "date_reception",
            "date_retour",
            "date_emission",
            "notes",
            "date_creation",
            "derniere_mise_a_jour",
            "matiere_retours",
        ]
        read_only_fields = [
            "id",
            "date_creation",
            "derniere_mise_a_jour",
            "date_emission",
        ]

    def create(self, validated_data):
        matieres_data = validated_data.pop("matiere_retours", [])
        bon_retour = BonRetourFournisseur.objects.create(**validated_data)

        for mat_data in matieres_data:
            MatiereRetourFournisseur.objects.create(
                bon_retour=bon_retour,
                nom_matiere=mat_data["nom_matiere"],
                quantite_retournee=mat_data["quantite_retournee"],
            )
        return bon_retour

    def update(self, instance, validated_data):
        matiere_retours_data = validated_data.pop("matiere_retours", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if matiere_retours_data is not None:
            instance.matiere_retours.all().delete()
            for mat_data in matiere_retours_data:
                MatiereRetourFournisseur.objects.create(bon_retour=instance, **mat_data)

        return instance


class BonRetourFournisseurListSerializer(serializers.ModelSerializer):
    fournisseur_name = serializers.CharField(source="fournisseur.nom", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total_materials = serializers.SerializerMethodField()

    class Meta:
        model = BonRetourFournisseur
        fields = [
            "id",
            "numero_bon",
            "fournisseur_name",
            "status",
            "status_display",
            "date_reception",
            "date_retour",
            "total_materials",
        ]

    def get_total_materials(self, obj):
        return obj.matiere_retours.count()


class FournisseurMaterialsSerializer(serializers.ModelSerializer):
    available_materials = serializers.SerializerMethodField()

    class Meta:
        model = Fournisseur
        fields = ["id", "nom", "numero_fiscal", "available_materials"]

    def get_available_materials(self, obj):
        # Ici tu dois récupérer les matières saisies, par exemple via un filtre personnalisé
        # Si tu n'as pas de relation directe, adapte cette partie
        # Ex: récupère toutes les MatiereRetourFournisseur des bons du fournisseur avec quantité > 0
        bons = BonRetourFournisseur.objects.filter(fournisseur=obj, is_deleted=False)
        matieres = MatiereRetourFournisseur.objects.filter(bon_retour__in=bons, is_deleted=False)
        # On retourne un format simplifié, par exemple nom_matiere et quantite max dispo (ou autre logique)
        # Ici on peut juste retourner toutes les matières retournées (sans déduplication)
        data = []
        for m in matieres:
            data.append({
                "nom_matiere": m.nom_matiere,
                "quantite_retournee": m.quantite_retournee,
            })
        return data



from rest_framework import serializers
from .models import PlanTraiteFournisseur, TraiteFournisseur, FactureAchatMatiere, Fournisseur


class TraiteFournisseurSerializer(serializers.ModelSerializer):
    numero_facture = serializers.CharField(source='plan_traite.numero_facture', read_only=True)
    fournisseur_nom = serializers.CharField(source='plan_traite.nom_raison_sociale', read_only=True)

    class Meta:
        model = TraiteFournisseur
        fields = '__all__'
        extra_fields = ('numero_facture', 'fournisseur_nom')

    def get_fields(self):
        fields = super().get_fields()
        for field_name in getattr(self.Meta, 'extra_fields', []):
            fields[field_name] = serializers.ReadOnlyField()
        return fields


class PlanTraiteFournisseurSerializer(serializers.ModelSerializer):
    fournisseur = FournisseurSerializer(read_only=True)
    traites = TraiteFournisseurSerializer(many=True, read_only=True)
    facture_numero = serializers.CharField(source='numero_facture', read_only=True)
    fournisseur_nom = serializers.CharField(source='nom_raison_sociale', read_only=True)
    bank_name = serializers.CharField(read_only=True)
    bank_address = serializers.CharField(read_only=True)

    class Meta:
        model = PlanTraiteFournisseur
        fields = '__all__'


class CreatePlanTraiteFournisseurSerializer(serializers.Serializer):
    numero_facture = serializers.CharField(required=True)
    nombre_traite = serializers.IntegerField(min_value=1, max_value=24, required=True)
    date_premier_echeance = serializers.DateField(required=True)
    periode = serializers.IntegerField(min_value=1, required=False, default=30)
    montant_total = serializers.FloatField(required=False, allow_null=True)
    rip = serializers.CharField(required=False, allow_blank=True)
    acceptance = serializers.CharField(required=False, allow_blank=True)
    notice = serializers.CharField(required=False, allow_blank=True)
    bank_name = serializers.CharField(required=False, allow_blank=True)
    bank_address = serializers.CharField(required=False, allow_blank=True)

    def validate_numero_facture(self, value):
        if not FactureAchatMatiere.objects.filter(numero=value).exists():
            raise serializers.ValidationError("La facture spécifiée n'existe pas.")
        return value

    def create(self, validated_data):
        facture = FactureAchatMatiere.objects.get(numero=validated_data["numero_facture"])
        fournisseur = facture.fournisseur


        plan = PlanTraiteFournisseur.objects.create(
            facture=facture,
            fournisseur=fournisseur,
            numero_facture=facture.numero,
            nom_raison_sociale=facture.fournisseur,
            matricule_fiscal=getattr(fournisseur, "matricule_fiscal", "") if fournisseur else "",
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


class UpdateTraiteFournisseurStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['PAYEE', 'NON_PAYEE'])

    def validate_status(self, value):
        return value.upper()


class UpdatePlanFournisseurStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['PAYEE', 'NON_PAYEE', 'PARTIELLEMENT_PAYEE'])

    def validate_status(self, value):
        return value.upper()


class SoftDeletePlanTraiteFournisseurSerializer(serializers.Serializer):
    is_deleted = serializers.BooleanField(default=True)

    def validate_is_deleted(self, value):
        if not isinstance(value, bool):
            raise serializers.ValidationError("Ce champ doit être un booléen.")
        return value
