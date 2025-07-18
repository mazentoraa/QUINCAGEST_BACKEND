from django.forms import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Client, Traveaux, Produit, Matiere, MatiereUsage,Entreprise
from .serializers import (
    ClientSerializer,
    TraveauxSerializer,
    ProduitSerializer,
    MatiereSerializer,
    MatiereUsageSerializer,
    EntrepriseSerializer,
    
)
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets, filters
from .models import MatierePremiereAchat
from .serializers import MatierePremiereAchatSerializer

class MatiereViewSet(viewsets.ModelViewSet):
    """
    API pour la gestion des matières premières.

    Liste toutes les matières, crée de nouvelles matières, et modifie ou supprime les matières existantes.
    """

    permission_classes = [IsAdminUser]
    queryset = Matiere.objects.all().order_by("-date_creation")
    serializer_class = MatiereSerializer

    @swagger_auto_schema(
        operation_description="Récupérer les matières filtrées par client",
        manual_parameters=[
            openapi.Parameter(
                "client_id",
                openapi.IN_QUERY,
                description="ID du client pour filtrer les matières",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: MatiereSerializer(many=True),
            400: "Paramètre client_id manquant",
        },
    )
    @action(detail=False, methods=["get"])
    def by_client(self, request):
        """
        Get materials filtered by client
        """
        client_id = request.query_params.get("client_id")
        if not client_id:
            return Response(
                {"message": "Le paramètre client_id est obligatoire"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        materials = self.queryset.filter(client_id=client_id)
        serializer = self.get_serializer(materials, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        client_id = self.request.data.get("client_id")
        if client_id:
            try:
                client = Client.objects.get(pk=client_id)
                serializer.save(client=client)
            except Client.DoesNotExist:
                raise ValidationError({"client_id": "Client not found"})
        else:
            serializer.save()


class TraveauxViewSet(viewsets.ModelViewSet):
    """
    API pour la gestion des travaux.

    Liste tous les travaux, crée de nouveaux travaux, et modifie ou supprime les travaux existants.
    Les travaux sont liés à des clients, des produits, et peuvent utiliser différentes matières.
    """

    permission_classes = [IsAdminUser]
    queryset = Traveaux.objects.all().order_by("-date_creation")
    serializer_class = TraveauxSerializer

    def get_queryset(self):
        """
        Override to include matiere usage data in response
        """
        return self.queryset.prefetch_related("matiere_usages__matiere")

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Restore materials before deleting
        for usage in instance.matiere_usages.all():
            if usage.source == "client" and usage.matiere:
                usage.matiere.remaining_quantity += usage.quantite_utilisee
                usage.matiere.save()
            elif usage.source == "stock" and usage.achat:
                usage.achat.remaining_quantity += usage.quantite_utilisee
                usage.achat.save()

        # Delete the work
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        print("📥 Request data:", self.request.data)
        client_id = self.request.data.get("client_id")
        produit_id = self.request.data.get("produit_id")
        if client_id and produit_id:
            try:
                client = Client.objects.get(pk=client_id)
                produit = Produit.objects.get(pk=produit_id)
                serializer.save(client=client, produit=produit)
            except (Client.DoesNotExist, Produit.DoesNotExist):
                raise ValidationError(
                    {"client_id": "Client not found", "produit_id": "Produit not found"}
                )
        else:
            serializer.save()

    @swagger_auto_schema(
        operation_description="Récupérer les travaux filtrés par client",
        manual_parameters=[
            openapi.Parameter(
                "client_id",
                openapi.IN_QUERY,
                description="ID du client pour filtrer les travaux",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: TraveauxSerializer(many=True),
            400: "Paramètre client_id manquant",
        },
    )
    @action(detail=False, methods=["get"])
    def by_client(self, request):
        """
        Get works filtered by client
        """
        client_id = request.query_params.get("client_id")
        if not client_id:
            return Response(
                {"message": "Le paramètre client_id est obligatoire"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        travaux = self.get_queryset().filter(client_id=client_id)
        serializer = self.get_serializer(travaux, many=True)
        return Response(serializer.data)


class ClientViewSet(viewsets.ModelViewSet):
    """
    API pour la gestion des clients.

    Liste tous les clients, crée de nouveaux clients, et modifie ou supprime les clients existants.
    """

    permission_classes = [IsAdminUser]
    queryset = Client.objects.all().order_by("nom_client")
    serializer_class = ClientSerializer

    @swagger_auto_schema(
        operation_description="Rechercher des clients par nom ou numéro fiscal",
        manual_parameters=[
            openapi.Parameter(
                "query",
                openapi.IN_QUERY,
                description="Texte à rechercher dans les noms de clients ou numéros fiscaux",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
        responses={
            200: ClientSerializer(many=True),
            400: "Paramètre de recherche manquant",
        },
    )
    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        Search clients by name or fiscal number
        """
        query = request.query_params.get("query", None)
        if not query:
            return Response(
                {"message": "Le paramètre de recherche est obligatoire"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        clients = self.queryset.filter(
            Q(nom_client__icontains=query) | Q(numero_fiscal__icontains=query)
        )

        serializer = self.get_serializer(clients, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Créer un nouveau client",
        request_body=ClientSerializer,
        responses={201: ClientSerializer, 400: "Données invalides ou incomplètes"},
    )
    def create(self, request, *args, **kwargs):
        """
        Create a new client with validation
        """
        if not request.data.get("nom_client") or not request.data.get("numero_fiscal"):
            return Response(
                {"message": "Le nom du client et le numéro fiscal sont obligatoires"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Mettre à jour un client existant",
        request_body=ClientSerializer,
        responses={200: ClientSerializer, 400: "Données invalides ou incomplètes"},
    )
    def update(self, request, *args, **kwargs):
        """
        Update an existing client with validation
        """
        if not request.data.get("nom_client") or not request.data.get("numero_fiscal"):
            return Response(
                {"message": "Le nom du client et le numéro fiscal sont obligatoires"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().update(request, *args, **kwargs)


class ProduitViewSet(viewsets.ModelViewSet):
    """
    API pour la gestion des produits.

    Liste tous les produits, crée de nouveaux produits, et modifie ou supprime les produits existants.
    """

    permission_classes = [IsAdminUser]
    queryset = Produit.objects.all().order_by("-id")
    serializer_class = ProduitSerializer

    @swagger_auto_schema(
        operation_description="Créer un nouveau produit",
        request_body=ProduitSerializer,
        responses={201: ProduitSerializer, 400: "Données invalides ou incomplètes"},
    )
    def create(self, request, *args, **kwargs):
        """
        Create a new product with validation
        """
        if not request.data.get("nom_produit"):
            return Response(
                {"message": "Le nom du produit est obligatoire"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Mettre à jour un produit existant",
        request_body=ProduitSerializer,
        responses={200: ProduitSerializer, 400: "Données invalides ou incomplètes"},
    )
    def update(self, request, *args, **kwargs):
        """
        Update an existing product with validation
        """
        if not request.data.get("nom_produit"):
            return Response(
                {"message": "Le nom du produit est obligatoire"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Récupérer les produits filtrés par type de matière",
        manual_parameters=[
            openapi.Parameter(
                "type_matiere",
                openapi.IN_QUERY,
                description="Type de matière pour filtrer les produits",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
        responses={
            200: ProduitSerializer(many=True),
            400: "Paramètre type_matiere manquant",
        },
    )
    @action(detail=False, methods=["get"])
    def by_material_type(self, request):
        """
        Get products filtered by material type
        """
        type_matiere = request.query_params.get("type_matiere")
        if not type_matiere:
            return Response(
                {"message": "Le paramètre type_matiere est obligatoire"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        products = self.queryset.filter(type_matiere=type_matiere)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)


class AdminLoginView(APIView):
    """
    API pour l'authentification des administrateurs.

    Permet aux administrateurs de se connecter et d'obtenir un token d'authentification.
    """

    permission_classes = []

    @swagger_auto_schema(
        operation_description="Connexion administrateur et génération de token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["username", "password"],
            properties={
                "username": openapi.Schema(type=openapi.TYPE_STRING),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD
                ),
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "token": openapi.Schema(type=openapi.TYPE_STRING),
                    "user_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "username": openapi.Schema(type=openapi.TYPE_STRING),
                    "is_admin": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                },
            ),
            401: "Identifiants invalides ou utilisateur non administrateur",
        },
    )
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)

        if user and user.is_staff:
            token, _ = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "token": token.key,
                    "user_id": user.pk,
                    "username": user.username,
                    "is_admin": user.is_staff,
                }
            )
        return Response(
            {"error": "Invalid credentials or not an admin"},
            status=status.HTTP_401_UNAUTHORIZED,
        )


class LogoutView(APIView):
    """
    API pour la déconnexion.

    Supprime le token d'authentification actuel.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Déconnexion et suppression du token",
        responses={200: "Déconnexion réussie"},
    )
    def post(self, request):
        request.user.auth_token.delete()
        return Response(
            {"message": "Successfully logged out."}, status=status.HTTP_200_OK
        )


class CheckAuthView(APIView):
    """
    API pour vérifier l'authentification.

    Vérifie si l'utilisateur est authentifié et renvoie ses informations.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Vérification de l'état d'authentification",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "authenticated": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    "user_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "username": openapi.Schema(type=openapi.TYPE_STRING),
                    "is_admin": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                },
            )
        },
    )
    def get(self, request):
        return Response(
            {
                "authenticated": True,
                "user_id": request.user.id,
                "username": request.user.username,
                "is_admin": request.user.is_staff,
            }
        )

class EntrepriseViewSet(viewsets.ModelViewSet):
    """
    API pour la gestion des entreprises.

    Liste toutes les entreprises, crée de nouvelles entreprises, et modifie ou supprime les entreprises existantes.
    """

    permission_classes = [IsAdminUser]
    queryset = Entreprise.objects.all().order_by("nom_entreprise")
    serializer_class = EntrepriseSerializer


    @swagger_auto_schema(
        operation_description="Créer un nouvelle entreprise",
        request_body=EntrepriseSerializer,
        responses={201: EntrepriseSerializer, 400: "Données invalides ou incomplètes"},
    )
    def create(self, request, *args, **kwargs):
        """
        Create a new client with validation
        """
        if not request.data.get("nom_entreprise") or not request.data.get("numero_fiscal"):
            return Response(
                {"message": "Le nom de l'entreprise et le numéro fiscal sont obligatoires"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Mettre à jour une entreprise existante",
        request_body=EntrepriseSerializer,
        responses={200: EntrepriseSerializer, 400: "Données invalides ou incomplètes"},
    )
    def update(self, request, *args, **kwargs):
        """
        Update an existing client with validation
        """
        if not request.data.get("nom_entreprise") or not request.data.get("numero_fiscal"):
            return Response(
                {"message": "Le nom de l'entreprise et le numéro fiscal sont obligatoires"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().update(request, *args, **kwargs) 
    


from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from .models import MatierePremiereAchat
from .serializers import MatierePremiereAchatSerializer

class MatierePremiereAchatViewSet(viewsets.ModelViewSet):
    queryset = MatierePremiereAchat.objects.all().order_by("-created_at")
    serializer_class = MatierePremiereAchatSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['ref', 'nom_matiere', 'fournisseur_principal']

    def get_queryset(self):
        queryset = super().get_queryset()
        categorie = self.request.query_params.get("categorie")
        if categorie and categorie != "all":
            queryset = queryset.filter(categorie=categorie)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("❌ Erreurs de validation (create):", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            print("❌ Erreurs de validation (update):", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Matière supprimée avec succès."}, status=status.HTTP_204_NO_CONTENT)




from rest_framework import viewsets
from .models import FactureAchatMatiere
from .serializers import FactureAchatMatiereSerializer

class FactureAchatMatiereViewSet(viewsets.ModelViewSet):
    queryset = FactureAchatMatiere.objects.all().order_by('-id')
    serializer_class = FactureAchatMatiereSerializer


from rest_framework import viewsets
from .models import BonLivraisonMatiere
from .serializers import BonLivraisonMatiereSerializer

class BonLivraisonMatiereViewSet(viewsets.ModelViewSet):
    queryset = BonLivraisonMatiere.objects.all().order_by('-id')
    serializer_class = BonLivraisonMatiereSerializer



from .models import Fournisseur
from .serializers import FournisseurSerializer

class FournisseurViewSet(viewsets.ModelViewSet):
    queryset = Fournisseur.objects.all()
    serializer_class = FournisseurSerializer
    



from .models import Consommable
from .serializers import ConsommableSerializer

class ConsommableViewSet(viewsets.ModelViewSet):
    queryset = Consommable.objects.all().order_by('-date_achat')
    serializer_class = ConsommableSerializer

from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404

from .models import BonRetourFournisseur, Fournisseur, MatiereRetourFournisseur, Matiere
from .serializers import (
    BonRetourFournisseurSerializer,
    BonRetourFournisseurListSerializer,
    MatiereForRetourFournisseurSerializer,
)


class BonRetourFournisseurViewSet(ModelViewSet):
    queryset = BonRetourFournisseur.objects.select_related("fournisseur").prefetch_related(
        "matiere_retours__matiere"
    )
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["numero_bon", "fournisseur__nom", "notes"]
    ordering_fields = ["date_retour", "date_reception", "numero_bon"]
    ordering = ["-date_retour"]

    def get_serializer_class(self):
        if self.action == "list":
            return BonRetourFournisseurListSerializer
        return BonRetourFournisseurSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get("status", None)
        fournisseur_filter = self.request.query_params.get("fournisseur", None)
        date_retour_filter = self.request.query_params.get("date_retour", None)
        date_reception_filter = self.request.query_params.get("date_reception", None)

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if fournisseur_filter:
            queryset = queryset.filter(fournisseur_id=fournisseur_filter)
        if date_retour_filter:
            queryset = queryset.filter(date_retour=date_retour_filter)
        if date_reception_filter:
            queryset = queryset.filter(date_reception=date_reception_filter)

        return queryset


@api_view(["GET"])
def fournisseur_available_materials(request, fournisseur_id):
    try:
        fournisseur = get_object_or_404(Fournisseur, id=fournisseur_id)

        bons = BonRetourFournisseur.objects.filter(fournisseur=fournisseur, is_deleted=False)
        matieres = MatiereRetourFournisseur.objects.filter(bon_retour__in=bons, is_deleted=False)

        response_data = {
            "fournisseur": {
                "id": fournisseur.id,
                "nom": fournisseur.nom,
                "numero_fiscal": fournisseur.numero_fiscal,
            },
            "available_materials": [
                {
                    "nom_matiere": m.nom_matiere,
                    "quantite_retournee": m.quantite_retournee,
                }
                for m in matieres
            ],
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Fournisseur.DoesNotExist:
        return Response({"error": "Fournisseur not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
def validate_return_quantities_fournisseur(request):
    materials_data = request.data.get("materials", [])

    if not materials_data:
        return Response(
            {"error": "No materials provided for validation"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    validation_results = []
    has_errors = False

    for material_data in materials_data:
        matiere_id = material_data.get("matiere_id")
        quantite_retournee = material_data.get("quantite_retournee", 0)

        try:
            matiere = Matiere.objects.get(id=matiere_id)

            result = {
                "matiere_id": matiere_id,
                "matiere_name": f"{matiere.type_matiere} - {matiere.nom_matiere}",
                "requested_quantity": quantite_retournee,
                "available_quantity": matiere.remaining_quantity,
                "is_valid": quantite_retournee <= matiere.remaining_quantity,
            }

            if not result["is_valid"]:
                result["error"] = (
                    f"Cannot return {quantite_retournee} units. Only {matiere.remaining_quantity} available."
                )
                has_errors = True

            validation_results.append(result)

        except Matiere.DoesNotExist:
            validation_results.append(
                {
                    "matiere_id": matiere_id,
                    "error": "Material not found",
                    "is_valid": False,
                }
            )
            has_errors = True

    return Response(
        {"is_valid": not has_errors, "validation_results": validation_results},
        status=status.HTTP_200_OK,
    )


class BonRetourFournisseurByFournisseurView(generics.ListAPIView):
    serializer_class = BonRetourFournisseurListSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["date_retour", "date_reception", "numero_bon"]
    ordering = ["-date_retour"]

    def get_queryset(self):
        fournisseur_id = self.kwargs["fournisseur_id"]
        return BonRetourFournisseur.objects.filter(fournisseur_id=fournisseur_id).select_related("fournisseur")


class BonRetourFournisseurStatsView(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        total_bons = BonRetourFournisseur.objects.count()
        draft_bons = BonRetourFournisseur.objects.filter(status="draft").count()
        sent_bons = BonRetourFournisseur.objects.filter(status="sent").count()
        completed_bons = BonRetourFournisseur.objects.filter(status="completed").count()
        cancelled_bons = BonRetourFournisseur.objects.filter(status="cancelled").count()

        return Response(
            {
                "total_bons_retour": total_bons,
                "status_breakdown": {
                    "draft": draft_bons,
                    "sent": sent_bons,
                    "completed": completed_bons,
                    "cancelled": cancelled_bons,
                },
            },
            status=status.HTTP_200_OK,
        )


from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import PlanTraiteFournisseur, TraiteFournisseur, FactureAchatMatiere, Fournisseur
from .serializers import (  # <- adapte si autre nom
    PlanTraiteFournisseurSerializer,
    TraiteFournisseurSerializer,
    CreatePlanTraiteFournisseurSerializer,
    UpdateTraiteFournisseurStatusSerializer,
    UpdatePlanFournisseurStatusSerializer,
    SoftDeletePlanTraiteFournisseurSerializer
)


class PlanTraiteFournisseurViewSet(viewsets.ModelViewSet):
    queryset = PlanTraiteFournisseur.objects.filter(is_deleted=False).select_related('fournisseur')
    serializer_class = PlanTraiteFournisseurSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePlanTraiteFournisseurSerializer
        elif self.action == 'soft_delete':
            return SoftDeletePlanTraiteFournisseurSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        numero_facture = validated_data.get('numero_facture')
        try:
            facture = FactureAchatMatiere.objects.get(numero=numero_facture)
        except FactureAchatMatiere.DoesNotExist:
            return Response(
                {"numero_facture": ["Facture introuvable."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        fournisseur = Fournisseur.objects.filter(nom=facture.fournisseur).first()

        plan = PlanTraiteFournisseur.objects.create(
            facture=facture,
            fournisseur=fournisseur,
            numero_facture=facture.numero,
            nom_raison_sociale=facture.fournisseur,
            matricule_fiscal=getattr(fournisseur, 'matricule_fiscal', '') if fournisseur else '',
            nombre_traite=validated_data.get('nombre_traite'),
            date_premier_echeance=validated_data.get('date_premier_echeance'),
            periode=validated_data.get('periode', 30),
            montant_total=validated_data.get('montant_total') or facture.prix_total,
            rip=validated_data.get('rip', ''),
            acceptance=validated_data.get('acceptance', ''),
            notice=validated_data.get('notice', ''),
            bank_name=validated_data.get('bank_name', ''),
            bank_address=validated_data.get('bank_address', '')
        )

        plan._create_traites()
        plan.save()

        return Response(PlanTraiteFournisseurSerializer(plan).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def traites(self, request, pk=None):
        plan = self.get_object()
        traites = plan.traites.all()
        serializer = TraiteFournisseurSerializer(traites, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['put'], url_path='update-status')
    def update_status(self, request, pk=None):
        plan = self.get_object()
        serializer = UpdatePlanFournisseurStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan.status = serializer.validated_data['status']
        plan.save()

        return Response({
            "message": "Statut du plan mis à jour avec succès",
            "plan_id": plan.id,
            "new_status": plan.status
        }, status=200)

    @action(detail=True, methods=['patch'], url_path='soft-delete')
    def soft_delete(self, request, pk=None):
        plan = self.get_object()
        serializer = SoftDeletePlanTraiteFournisseurSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan.is_deleted = serializer.validated_data['is_deleted']
        plan.save()

        return Response({
            "message": "Le plan a été marqué comme supprimé.",
            "plan_id": plan.id
        }, status=200)


class TraiteFournisseurViewSet(viewsets.ModelViewSet):
    queryset = TraiteFournisseur.objects.all().select_related('plan_traite')
    serializer_class = TraiteFournisseurSerializer

    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        traite = self.get_object()
        serializer = UpdateTraiteFournisseurStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        traite.status = serializer.validated_data['status']
        traite.save()

        # Mise à jour automatique du statut du plan associé
        plan = traite.plan_traite
        all_status = [t.status for t in plan.traites.all()]

        if all(s == 'PAYEE' for s in all_status):
            plan.status = 'PAYEE'
        elif any(s == 'PAYEE' for s in all_status):
            plan.status = 'PARTIELLEMENT_PAYEE'
        else:
            plan.status = 'NON_PAYEE'

        plan.save()

        return Response(TraiteFournisseurSerializer(traite).data, status=200)



from rest_framework import viewsets
from .models import Employe
from .serializers import EmployeSerializer

class EmployeViewSet(viewsets.ModelViewSet):
    queryset = Employe.objects.all().order_by('-created_at')
    serializer_class = EmployeSerializer


# views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum, Count
from .models import Avance, Remboursement
from .serializers import AvanceSerializer, RemboursementSerializer

class AvanceViewSet(viewsets.ModelViewSet):
    queryset = Avance.objects.all().order_by('-date_demande')
    serializer_class = AvanceSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        statut = self.request.query_params.get('statut')

        if search:
            queryset = queryset.filter(employee__nom__icontains=search)
        if statut:
            queryset = queryset.filter(statut=statut)

        return queryset

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        avance = self.get_object()
        new_statut = request.data.get('statut')
        if new_statut not in dict(Avance.STATUT_CHOICES):
            return Response({'error': 'Statut invalide'}, status=400)
        avance.statut = new_statut
        avance.save()
        return Response(self.get_serializer(avance).data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        data = {
            "avances_actives": Avance.objects.filter(statut='Acceptée').count(),
            "avances_pending": Avance.objects.filter(statut='En attente').count(),
            "total_avances": Avance.objects.count(),
            "total_montant": Avance.objects.aggregate(total=Sum('montant'))['total'] or 0,
            "total_rembourse": Remboursement.objects.aggregate(total=Sum('montant'))['total'] or 0,
        }
        data['total_reste'] = round(data['total_montant'] - data['total_rembourse'], 2)
        return Response(data)


from rest_framework import viewsets
from .models import Employe, FichePaie
from .serializers import EmployeSerializer, FichePaieSerializer
from .paie_utils import appliquer_remboursement_avance 
class FichePaieViewSet(viewsets.ModelViewSet):
    queryset = FichePaie.objects.all()
    serializer_class = FichePaieSerializer

def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fiche = serializer.save()  # création normale de la fiche

        appliquer_remboursement_avance(fiche)  # ← applique automatiquement l’avance

        # recharger la fiche mise à jour (net_a_payer, avance_deduite...)
        serializer = self.get_serializer(fiche)
        return Response(serializer.data, status=status.HTTP_201_CREATED)