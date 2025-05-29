# i want to create a serializer for the facture and the paymentcomptant and the command and the linecommand
from rest_framework import serializers
from .models import  PlanTraite, Traite,Facture,CommandeProduit,LineCommande , PaymentComptant
from .serializers import ClientSerializer
from django.db import transaction
from django.utils import timezone



class LineCommandeSerializer(serializers.ModelSerializer):
    produit_nom = serializers.CharField(source='produit.nom_produit', read_only=True)
    prix_unitaire = serializers.IntegerField(source='prix', read_only=True)
    commande_id = serializers.PrimaryKeyRelatedField(
        queryset=CommandeProduit.objects.all(),
        source='commande',
        write_only=True,
        required=True
    )

    class Meta:
        model = LineCommande
        fields = [
            'id', 'produit', 'produit_nom', 'prix', 'prix_unitaire', 
            'quantite', 'prix_total', 'date_creation', 'derniere_mise_a_jour','commande_id'
        ]
        read_only_fields = ['prix_total', 'date_creation', 'derniere_mise_a_jour']

class CommandeSerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source='client.nom_client', read_only=True)
    lignes = LineCommandeSerializer(many=True, read_only=True)
    montant_total = serializers.SerializerMethodField()
    montant_ht = serializers.DecimalField(max_digits=10, decimal_places=2, required=False,coerce_to_string=False)
    taux_tva = serializers.DecimalField(max_digits=4, decimal_places=2, required=False,coerce_to_string=False)
    montant_tva = serializers.DecimalField(max_digits=10, decimal_places=2, required=False,coerce_to_string=False,read_only=True )
    montant_ttc = serializers.DecimalField(max_digits=10, decimal_places=2, required=False,coerce_to_string=False,read_only=True )

    class Meta:
        model = CommandeProduit
        fields = [
             'id', 'client', 'client_nom', 'date_creation', 'derniere_mise_a_jour',
            'lignes', 'montant_total', 'montant_ht', 'taux_tva', 'montant_tva', 'montant_ttc'
        ]
        read_only_fields = ['date_creation', 'derniere_mise_a_jour']
        extra_kwargs = {
            'client': {'required': True}
        }

    def get_montant_total(self, obj):
        return sum(ligne.prix_total for ligne in obj.lignes.all())
    def create(self, validated_data):
        # Calcul automatique des montants si non fournis
        if 'montant_ht' not in validated_data:
            validated_data['montant_ht'] = 0
        if 'taux_tva' not in validated_data:
            validated_data['taux_tva'] = 19  # Valeur par défaut
            
        validated_data['montant_tva'] = (validated_data['montant_ht'] * validated_data['taux_tva']) / 100
        validated_data['montant_ttc'] = validated_data['montant_ht'] + validated_data['montant_tva']
        
        return super().create(validated_data)

class FactureSerializer(serializers.ModelSerializer):
    commande_details = CommandeSerializer(source='commande', read_only=True)
    client_nom = serializers.CharField(source='commande.client.nom_client', read_only=True)
    commande = serializers.PrimaryKeyRelatedField(
        queryset=CommandeProduit.objects.all(),
        write_only=True,  # Ce champ est seulement pour l'écriture
        required=True
    )
    montant_total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,      # <<== important !
        read_only=True,      # <<== double sécurité pour empêcher l'utilisateur de l'envoyer
        coerce_to_string=False,
    )

    class Meta:
        model = Facture
        fields = [
            'id', 'commande', 'commande_details', 'client_nom',
            'montant_total', 'date_creation', 'derniere_mise_a_jour'
        ]
        read_only_fields = ['montant_total', 'date_creation', 'derniere_mise_a_jour']

    def create(self, validated_data):
        commande = validated_data['commande']
        facture = Facture.objects.create(
            commande=commande,
            montant_total=commande.montant_ttc
        )
        return facture

class PaymentComptantSerializer(serializers.ModelSerializer):
    facture_details = FactureSerializer(source='facture', read_only=True)

    class Meta:
        model = PaymentComptant
        fields = [
            'id', 'facture', 'facture_details', 'status',
            'montant', 'date_creation'
        ]
        read_only_fields = ['date_creation']


