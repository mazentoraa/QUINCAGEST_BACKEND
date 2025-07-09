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
