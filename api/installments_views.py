from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import PlanTraite, Traite, FactureTravaux
from .installments_serializers import (
    PlanTraiteSerializer,
    TraiteSerializer,
    CreatePlanTraiteSerializer,
    UpdateTraiteStatusSerializer
)


class PlanTraiteViewSet(viewsets.ModelViewSet):
    queryset = PlanTraite.objects.all().select_related('facture')
    serializer_class = PlanTraiteSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePlanTraiteSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        # Afficher les données reçues pour le debug
        print("📥 Données reçues dans le backend :", request.data)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        facture_id = validated_data.get('facture_id')
        nombre_traite = validated_data.get('nombre_traite')
        date_premier_echeance = validated_data.get('date_premier_echeance')
        periode = validated_data.get('periode', 30)

        # Récupération de la facture
        try:
            facture = FactureTravaux.objects.get(pk=facture_id)
        except FactureTravaux.DoesNotExist:
            return Response({"facture_id": ["Facture introuvable."]}, status=status.HTTP_400_BAD_REQUEST)

        # Création du plan de traite
        plan = PlanTraite.objects.create(
            facture=facture,
            nombre_traite=nombre_traite,
            date_premier_echeance=date_premier_echeance,
            periode=periode,
            montant_total=facture.montant_ttc,
            nom_raison_sociale=facture.client.nom_raison_sociale,
            matricule_fiscal=facture.client.matricule_fiscal
        )

        # Retour du plan créé
        return Response(PlanTraiteSerializer(plan).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def traites(self, request, pk=None):
        plan = self.get_object()
        traites = plan.traites.all()
        serializer = TraiteSerializer(traites, many=True)
        return Response(serializer.data)


class TraiteViewSet(viewsets.ModelViewSet):
    queryset = Traite.objects.all().select_related('plan_traite')
    serializer_class = TraiteSerializer

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        traite = self.get_object()
        serializer = UpdateTraiteStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Mise à jour du statut
        traite.status = serializer.validated_data['status']
        traite.save()

        # Vérifie si toutes les traites sont payées
        plan = traite.plan_traite
        if plan.traites.filter(status='NON_PAYEE').count() == 0:
            plan.status = 'PAYEE'
            plan.save()

        return Response(TraiteSerializer(traite).data)
