from rest_framework import viewsets, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from .models import CommandeProduit, LineCommande, Facture, PaymentComptant
from .facture_serialzers import (
    CommandeSerializer, LineCommandeSerializer,
    FactureSerializer, PaymentComptantSerializer
)


class CommandeProduitViewSet(viewsets.ModelViewSet):
    queryset = CommandeProduit.objects.all().select_related('client').prefetch_related('lignes')
    serializer_class = CommandeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @transaction.atomic
    def perform_create(self, serializer):
        commande = serializer.save()
        # Ici vous pourriez ajouter la logique pour créer les lignes de commande
        # si vous les recevez dans la requête

@action(detail=True, methods=['post'])
def create_facture(self, request, pk=None):
    commande = self.get_object()
    if hasattr(commande, 'facture'):
        return Response(
            {"error": "Une facture existe déjà pour cette commande"},
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer = FactureSerializer(data={'commande': commande.id})
    if serializer.is_valid():
        facture = serializer.save()
        return Response(FactureSerializer(facture).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LineCommandeViewSet(viewsets.ModelViewSet):
    queryset = LineCommande.objects.all().select_related('commande', 'produit')
    serializer_class = LineCommandeSerializer

class FactureViewSet(viewsets.ModelViewSet):
    queryset = Facture.objects.all().select_related('commande', 'commande__client')
    serializer_class = FactureSerializer

    @action(detail=True, methods=['post'])
    def payer_comptant(self, request, pk=None):
        facture = self.get_object()
        payment, created = PaymentComptant.objects.get_or_create(
            facture=facture,
            defaults={
                'montant': facture.montant_total,
                'status': 'PAID'
            }
        )
        if not created:
            payment.status = 'PAID'
            payment.save()
        return Response(PaymentComptantSerializer(payment).data)

    @action(detail=False, methods=['get'])
    def by_client(self, request):
        client_id = request.query_params.get("client_id")
        if not client_id:
            return Response({"error": "Le paramètre client_id est requis"}, status=400)
        factures = self.queryset.filter(commande__client_id=client_id)
        serializer = self.get_serializer(factures, many=True)
        return Response(serializer.data)

class PaymentComptantViewSet(viewsets.ModelViewSet):
    queryset = PaymentComptant.objects.all().select_related('facture')
    serializer_class = PaymentComptantSerializer