from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from .models import Client, Produit, Entreprise, Categorie, SousCategorie
from drf_extra_fields.fields import Base64ImageField
from django.db import transaction
from decimal import Decimal

# A supprimer
# class ProduitSerializer(serializers.ModelSerializer):
#     client_id = serializers.PrimaryKeyRelatedField(
#         queryset=Client.objects.all(), source="client"
#     )
#     client_name = serializers.CharField(source="client.nom_client", read_only=True)
#     prix_unitaire = serializers.FloatField(required=False)

#     class Meta:
#         model = Produit
#         fields = (
#             "id",
#             "numero_bon",
#             "nom_produit",
#             "reception_date",
#             "client_name",
#             "client_id",
#             "description",
#             "prix_unitaire",
#             "date_creation",
#             "quantite",
#             "remaining_quantity",  
#             "derniere_mise_a_jour",
#             "width",
#             "length",
#             "thickness",
#             "surface",
#         )
#         extra_kwargs = {
#             "type_produit": {"required": True},
#             "description": {"required": False},
#             "prix_unitaire": {"required": False},
#             "client_id": {"required": True},
#             "numero_bon": {"required": False, "allow_null": True, "allow_blank": True},
#             "quantite": {"required": True},
#             "remaining_quantity": {"required": False},  # ✅ autorisé en écriture
#         }
#         read_only_fields = (
#             "date_creation",
#             "derniere_mise_a_jour",
          
#         )

class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ["id", "nom"]


class SousCategorieSerializer(serializers.ModelSerializer):
    categorie = CategorieSerializer(read_only=True)
    categorie_id = serializers.PrimaryKeyRelatedField(
        queryset=Categorie.objects.all(), source="categorie", write_only=True
    )

    class Meta:
        model = SousCategorie
        fields = ["id", "nom", "categorie", "categorie_id"]


class ProduitSerializer(serializers.ModelSerializer):

    image = Base64ImageField(required=False, allow_null=True)
    categorie = CategorieSerializer(read_only=True)
    sous_categorie = SousCategorieSerializer(read_only=True)

    categorie_id = serializers.PrimaryKeyRelatedField(
        queryset=Categorie.objects.all(), source="categorie", write_only=True
    )
    sous_categorie_id = serializers.PrimaryKeyRelatedField(
        queryset=SousCategorie.objects.all(), source="sous_categorie", write_only=True
    )

    class Meta:
        model = Produit
        fields = [
            "id",
            "nom_produit",
            "ref_produit",
            "categorie",
            "sous_categorie",
            "categorie_id", 
            "sous_categorie_id",
            "materiau",
            "fournisseur",
            "stock",
            "seuil_alerte",
            "unite_mesure",
            "statut",
            "code_barres",
            "emplacement",
            "prix_achat",
            "prix_unitaire",
            "description",
            "image",
            "date_creation",
            "derniere_mise_a_jour",
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

# # A supprimer
# class ProduitUsageSerializer(serializers.ModelSerializer):
#     produit_id = serializers.IntegerField(write_only=True) # To acccept
#     material_id = serializers.SerializerMethodField(read_only=True) # to return

#     class Meta:
#         model = ProduitUsage
#         fields = ("produit_id", "material_id", "quantite_utilisee", "source")

#     def get_material_id(self, obj):
#         if obj.source == "client" and obj.produit:
#             return obj.produit.id
#         elif obj.source == "stock" and obj.achat:
#             return obj.achat.id
#         return None


# class TraveauxSerializer(serializers.ModelSerializer):
#     client_id = serializers.IntegerField()
#     produit_id = serializers.IntegerField()
#     client_name = serializers.CharField(source="client.nom_client", read_only=True)
#     produit_name = serializers.CharField(source="produit.nom_produit", read_only=True)
#     produit_usages = ProduitUsageSerializer(many=True, required=False)
#     remise = serializers.FloatField(required=False, default=0)

#     class Meta:
#         model = Traveaux
#         fields = (
#             "id",
#             "client_id",
#             "produit_id",
#             "client_name",
#             "produit_name",
#             "duree",
#             "quantite",
#             "description",
#             "date_creation",
#             "produit_usages",
#             "derniere_mise_a_jour",
#             "remise",
#         )
#         read_only_fields = (
#             "date_creation",
#             "derniere_mise_a_jour",
#             "client_name",
#             "produit_name",
#         )
#         extra_kwargs = {"duree": {"required": True}, "quantite": {"required": True},"remise": {"required": False, "default": 0},}

#     @transaction.atomic
#     def create(self, validated_data):
#         print("🔥 Validated Data:", validated_data)
#         client_id = validated_data.pop("client_id")
#         produit_id = validated_data.pop("produit_id")
#         produit_usages_data = validated_data.pop("produit_usages", [])

#         try:
#             client = Client.objects.get(pk=client_id)
#             produit = Produit.objects.get(pk=produit_id)
#             validated_data["client"] = client
#             validated_data["produit"] = produit
#         except (Client.DoesNotExist, Produit.DoesNotExist):
#             raise serializers.ValidationError("Client or Product not found")

#         travaux = Traveaux.objects.create(**validated_data)

#         # Process material usage
#         for produit_usage_data in produit_usages_data:
#             produit_id = produit_usage_data.get("produit_id")
#             quantite_utilisee = Decimal(produit_usage_data.get("quantite_utilisee"))
#             source = produit_usage_data.get("source", "stock")  # Default to main stock

#             if source == "client":
#                 try:
#                     produit = Produit.objects.get(pk=produit_id)

#                     # Check if we have enough quantity
#                     if produit.remaining_quantity < quantite_utilisee:
#                         raise serializers.ValidationError(
#                             f"Not enough material available. Only {produit.remaining_quantity} units of {produit.type_produit} remaining."
#                         )

#                     # Create the usage record
#                     ProduitUsage.objects.create(
#                         travaux=travaux,
#                         produit=produit,
#                         quantite_utilisee=quantite_utilisee,
#                         source=source
#                     )

#                     # Update the remaining quantity
#                     produit.remaining_quantity -= quantite_utilisee
#                     produit.save()

#                 except Produit.DoesNotExist:
#                     raise serializers.ValidationError(
#                         f"Product with ID {produit_id} not found"
#                     )
#             elif source == "stock":
#                 try:
#                     achat = ProduitPremiereAchat.objects.get(pk=produit_id)
#                     if achat.remaining_quantity < quantite_utilisee:
#                         raise serializers.ValidationError(
#                             f"Not enough stock: {achat.remaining_quantity} remaining for {achat.nom_produit}"
#                         )
#                     achat.remaining_quantity -= quantite_utilisee
#                     achat.save()

#                     ProduitUsage.objects.create(
#                         travaux=travaux,
#                         quantite_utilisee=quantite_utilisee,
#                         source=source,
#                         achat_id=achat.id 
#                     )

#                 except ProduitPremiereAchat.DoesNotExist:
#                     raise serializers.ValidationError(f"Stock material with ID {produit_id} not found")

#         return travaux
    
#     def update(self, instance, validated_data):
#         if "produit_usages" in validated_data:
#             produit_usages_data = validated_data.pop("produit_usages")

#             # Reset quantities for existing usages first
#             for usage in instance.produit_usages.all():
#                 if usage.source == "client" and usage.produit:
#                     usage.produit.remaining_quantity += usage.quantite_utilisee
#                     usage.produit.save()
#                 elif usage.source == "stock" and usage.achat:
#                     usage.achat.remaining_quantity += usage.quantite_utilisee
#                     usage.achat.save()
#                 usage.delete()

#             # Re-add new usages
#             for usage_data in produit_usages_data:
#                 source = usage_data.get("source", "stock")
#                 produit_id = usage_data.get("produit_id")
#                 quantite_utilisee = usage_data.get("quantite_utilisee")

#                 if source == "client":
#                     try:
#                         produit = Produit.objects.get(pk=produit_id)
#                         if produit.remaining_quantity < quantite_utilisee:
#                             raise serializers.ValidationError(
#                                 f"Not enough client material. Only {produit.remaining_quantity} units left of {produit.type_produit}."
#                             )

#                         ProduitUsage.objects.create(
#                             travaux=instance,
#                             produit=produit,
#                             quantite_utilisee=quantite_utilisee,
#                             source=source,
#                         )

#                         produit.remaining_quantity -= quantite_utilisee
#                         produit.save()
#                     except Produit.DoesNotExist:
#                         raise serializers.ValidationError(
#                             f"Client material with ID {produit_id} not found."
#                         )

#                 elif source == "stock":
#                     try:
#                         achat = ProduitPremiereAchat.objects.get(pk=produit_id)
#                         if achat.remaining_quantity < quantite_utilisee:
#                             raise serializers.ValidationError(
#                                 f"Not enough stock material. Only {achat.remaining_quantity} units left of {achat.nom_produit}."
#                             )

#                         ProduitUsage.objects.create(
#                             travaux=instance,
#                             achat=achat,
#                             quantite_utilisee=quantite_utilisee,
#                             source=source,
#                         )

#                         achat.remaining_quantity -= quantite_utilisee
#                         achat.save()
#                     except ProduitPremiereAchat.DoesNotExist:
#                         raise serializers.ValidationError(
#                             f"Stock material with ID {produit_id} not found."
#                         )

#         return super().update(instance, validated_data)


class EntrepriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entreprise
        fields = "__all__"

# A supprimer
# class ProduitAchatSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ProduitAchat
#         fields = '__all__'

from rest_framework import serializers
from .models import FactureAchatProduit, Achat


class AchatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achat
        fields = ['id', 'nom', 'prix', 'quantite']


class FactureAchatProduitSerializer(serializers.ModelSerializer):
    achats = AchatSerializer(many=True)

    class Meta:
        model = FactureAchatProduit
        fields = ['id', 'numero', 'fournisseur','mode_paiement', 'mixte_comptant', 'prix_total', 'date_facture', 'achats']

    def create(self, validated_data):
        achats_data = validated_data.pop('achats', [])
        facture = FactureAchatProduit.objects.create(**validated_data)
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



from .models import BonLivraisonProduit, Livraison


class LivraisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Livraison
        fields = ['id', 'nom', 'prix', 'quantite']


class BonLivraisonProduitSerializer(serializers.ModelSerializer):
    livraisons = LivraisonSerializer(many=True)

    class Meta:
        model = BonLivraisonProduit
        fields = ['id', 'numero', 'fournisseur', 'prix_total', 'date_livraison', 'livraisons']

    def create(self, validated_data):
        livraisons_data = validated_data.pop('livraisons', [])
        bon = BonLivraisonProduit.objects.create(**validated_data)
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
from .models import BonRetourFournisseur, ProduitRetourFournisseur, Produit, Fournisseur


class ProduitForRetourFournisseurSerializer(serializers.ModelSerializer):
    """Serializer for materials available for return to fournisseur"""

    nom_produit = serializers.CharField()
    quantite_retournee = serializers.IntegerField(min_value=1)

    class Meta:
        model = Produit
        fields = [
            "nom_produit",
            "quantite_retournee",
        ]
        read_only_fields = [
            "id",
            # "type_produit",
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


class ProduitRetourFournisseurFreeSerializer(serializers.Serializer):
    nom_produit = serializers.CharField()
    quantite_retournee = serializers.IntegerField(min_value=1)

    class Meta:
        model = ProduitRetourFournisseur
        fields = ["id", "produit_id", "produit_details", "quantite_retournee"]

    def validate_produit_id(self, value):
        try:
            produit = Produit.objects.get(id=value)
            return value
        except Produit.DoesNotExist:
            raise serializers.ValidationError("Product not found.")

    def validate(self, attrs):
        produit_id = attrs.get("produit_id")
        quantite_retournee = attrs.get("quantite_retournee", 1)

        if produit_id:
            try:
                produit = Produit.objects.get(id=produit_id)
                if quantite_retournee > produit.remaining_quantity:
                    raise serializers.ValidationError({
                        "quantite_retournee": f"Cannot return {quantite_retournee} units. Only {produit.remaining_quantity} remaining."
                    })
            except Produit.DoesNotExist:
                raise serializers.ValidationError({"produit_id": "Product not found."})
        return attrs


class FournisseurBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fournisseur
        fields = ["id", "nom", "adresse"]


class BonRetourFournisseurSerializer(serializers.ModelSerializer):
    fournisseur_details = FournisseurBasicSerializer(source="fournisseur", read_only=True)
    produit_retours = ProduitRetourFournisseurFreeSerializer(many=True)
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
            "produit_retours",
        ]
        read_only_fields = [
            "id",
            "date_creation",
            "derniere_mise_a_jour",
            "date_emission",
        ]

    def create(self, validated_data):
        produits_data = validated_data.pop("produit_retours", [])
        bon_retour = BonRetourFournisseur.objects.create(**validated_data)

        for mat_data in produits_data:
            ProduitRetourFournisseur.objects.create(
                bon_retour=bon_retour,
                nom_produit=mat_data["nom_produit"],
                quantite_retournee=mat_data["quantite_retournee"],
            )
        return bon_retour

    def update(self, instance, validated_data):
        produit_retours_data = validated_data.pop("produit_retours", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if produit_retours_data is not None:
            instance.produit_retours.all().delete()
            for mat_data in produit_retours_data:
                ProduitRetourFournisseur.objects.create(bon_retour=instance, **mat_data)

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

    def get_total_products(self, obj):
        return obj.produit_retours.count()


class FournisseurProductsSerializer(serializers.ModelSerializer):
    available_materials = serializers.SerializerMethodField()

    class Meta:
        model = Fournisseur
        fields = ["id", "nom", "numero_fiscal", "available_materials"]

    def get_available_materials(self, obj):
        # Ici tu dois récupérer les matières saisies, par exemple via un filtre personnalisé
        # Si tu n'as pas de relation directe, adapte cette partie
        # Ex: récupère toutes les ProduitRetourFournisseur des bons du fournisseur avec quantité > 0
        bons = BonRetourFournisseur.objects.filter(fournisseur=obj, is_deleted=False)
        produits = ProduitRetourFournisseur.objects.filter(bon_retour__in=bons, is_deleted=False)
        # On retourne un format simplifié, par exemple nom_produit et quantite max dispo (ou autre logique)
        # Ici on peut juste retourner toutes les matières retournées (sans déduplication)
        data = []
        for m in produits:
            data.append({
                "nom_produit": m.nom_produit,
                "quantite_retournee": m.quantite_retournee,
            })
        return data



from rest_framework import serializers
from .models import PlanTraiteFournisseur, TraiteFournisseur, FactureAchatProduit, Fournisseur


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
        if not FactureAchatProduit.objects.filter(numero=value).exists():
            raise serializers.ValidationError("La facture spécifiée n'existe pas.")
        return value

    def create(self, validated_data):
        facture = FactureAchatProduit.objects.get(numero=validated_data["numero_facture"])
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
from .models import Avance
# serializers.py

from rest_framework import serializers
from .models import Avance, Remboursement, Employe

class AvanceSerializer(serializers.ModelSerializer):
    mensualite = serializers.SerializerMethodField()
    progression = serializers.SerializerMethodField()
    reste = serializers.SerializerMethodField()

    class Meta:
        model = Avance
        fields = '__all__'

    def get_mensualite(self, obj):
        return obj.mensualite()

    def get_progression(self, obj):
        return obj.progression()

    def get_reste(self, obj):
        return obj.reste()


class RemboursementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Remboursement
        fields = '__all__'




from rest_framework import serializers
from .models import Employe, Avance, Remboursement, FichePaie


class FichePaieSerializer(serializers.ModelSerializer):
    class Meta:
        model = FichePaie
        fields = '__all__'

class EmployeSerializer(serializers.ModelSerializer):
    fiches_paie = FichePaieSerializer(many=True, read_only=True)
    avances = AvanceSerializer(many=True, read_only=True)
    class Meta:
        model = Employe
        fields = '__all__'


from .models import Employe, FichePaie
class FichePaieDetailSerializer(serializers.ModelSerializer):
    employe = EmployeSerializer(read_only=True)

    class Meta:
        model = FichePaie
        fields = '__all__'

from rest_framework import serializers
from .models import Avoir, AvoirArticle

class AvoirArticleSerializer(serializers.ModelSerializer):
    total = serializers.ReadOnlyField()
    
    class Meta:
        model = AvoirArticle
        fields = ['id', 'nom', 'prix', 'quantite', 'total']
        
    def validate_prix(self, value):
        if value < 0:
            raise serializers.ValidationError("Le prix ne peut pas être négatif.")
        return value
    
    def validate_quantite(self, value):
        if value < 1:
            raise serializers.ValidationError("La quantité doit être au moins 1.")
        return value


class AvoirSerializer(serializers.ModelSerializer):
    articles = AvoirArticleSerializer(many=True, required=False)
    
    class Meta:
        model = Avoir
        fields = [
            'id', 'numero', 'fournisseur', 'type_avoir', 'mode_paiement',
            'montant_total', 'date_avoir', 'articles', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_montant_total(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Le montant total ne peut pas être négatif.")
        return value
    
    def create(self, validated_data):
        articles_data = validated_data.pop('articles', [])
        avoir = Avoir.objects.create(**validated_data)
        
        for article_data in articles_data:
            AvoirArticle.objects.create(avoir=avoir, **article_data)
        
        return avoir
    
    def update(self, instance, validated_data):
        articles_data = validated_data.pop('articles', [])
        
        # Mettre à jour les champs de l'avoir
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Supprimer les anciens articles et créer les nouveaux
        instance.articles.all().delete()
        for article_data in articles_data:
            AvoirArticle.objects.create(avoir=instance, **article_data)
        
        return instance

