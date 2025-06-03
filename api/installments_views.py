from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import PlanTraite, Traite, Client, Cd
from .installments_serializers import (
    PlanTraiteSerializer,
    TraiteSerializer,
    CreatePlanTraiteSerializer,
    UpdateTraiteStatusSerializer
)


class PlanTraiteViewSet(viewsets.ModelViewSet):
    queryset = PlanTraite.objects.all().select_related('client')
    serializer_class = PlanTraiteSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePlanTraiteSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        numero_commande = validated_data.get('numero_commande')
        nombre_traite = validated_data.get('nombre_traite')
        date_premier_echeance = validated_data.get('date_premier_echeance')
        periode = validated_data.get('periode', 30)

        try:
            commande = Cd.objects.select_related('client').get(numero_commande=numero_commande)
            client = commande.client
        except Cd.DoesNotExist:
            return Response(
                {"numero_commande": ["Commande introuvable."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        montant_total = validated_data.get('montant_total') or commande.montant_ttc
        nom_raison_sociale = client.nom_client
        matricule_fiscal = client.numero_fiscal

        plan = PlanTraite.objects.create(
            client=client,
            numero_facture=numero_commande,
            nombre_traite=nombre_traite,
            date_premier_echeance=date_premier_echeance,
            periode=periode,
            montant_total=montant_total,
            nom_raison_sociale=nom_raison_sociale,
            matricule_fiscal=matricule_fiscal,
        )

        plan._create_traites()  # 🔁 Appel direct et sûr
        plan.save()

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

        traite.status = serializer.validated_data['status']
        traite.save()

        plan = traite.plan_traite
        # ✅ Vérifie si toutes les traites du plan sont payées
        if not plan.traites.filter(status="NON_PAYEE").exists():
            plan.status = "PAYEE"
            plan.save()

        return Response(TraiteSerializer(traite).data)





