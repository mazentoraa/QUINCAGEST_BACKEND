from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import FactureMatiere, Client
from .facture_matiere_serializers import (
    FactureMatiereSerializer,
    FactureMatiereDetailSerializer,
)


class FactureMatiereViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = FactureMatiere.objects.all().order_by("-date_reception")
    serializer_class = FactureMatiereSerializer

    def get_serializer_class(self):
        if self.action == "retrieve":
            return FactureMatiereDetailSerializer
        return FactureMatiereSerializer

    def get_queryset(self):
        queryset = self.queryset
        client_id = self.request.query_params.get("client_id")
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        return queryset.prefetch_related("matieres")

    @swagger_auto_schema(
        operation_description="Créer une facture matière",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["client", "matieres", "date_reception"],
            properties={
                "client": openapi.Schema(type=openapi.TYPE_INTEGER),
                "matieres": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                ),
                "numero_bon": openapi.Schema(type=openapi.TYPE_STRING),
                "date_reception": openapi.Schema(
                    type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE
                ),
                "notes": openapi.Schema(type=openapi.TYPE_STRING),
                "tax_rate": openapi.Schema(type=openapi.TYPE_NUMBER),
            },
        ),
        responses={
            201: FactureMatiereSerializer,
            400: "Données invalides",
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        facture = serializer.save()
        return Response(self.get_serializer(facture).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def search(self, request):
        query = request.query_params.get("query")
        if not query:
            return Response({"error": "Le paramètre query est requis."}, status=400)

        results = self.queryset.filter(
            Q(numero_bon__icontains=query) | Q(client__nom_client__icontains=query)
        )
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_client(self, request):
        client_id = request.query_params.get("client_id")
        if not client_id:
            return Response({"error": "client_id requis."}, status=400)

        results = self.queryset.filter(client_id=client_id)
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        total_bons = self.queryset.count()
        total_matieres = sum(f.matieres.count() for f in self.queryset.all())
        return Response({
            "total_bons": total_bons,
            "total_matieres": total_matieres,
        })
