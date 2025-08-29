from django.forms import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import date, timedelta
from django.db.models import Q
from .models import Client, Produit, Entreprise, Categorie, SousCategorie
from .serializers import (
    ClientSerializer,
    ProduitSerializer,
    EntrepriseSerializer,
    CategorieSerializer,
    SousCategorieSerializer,
    CategorieNestedSerializer
)
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets, filters

# A supprimer
# class MatiereViewSet(viewsets.ModelViewSet):
#     """
#     API pour la gestion des matières premières.

#     Liste toutes les matières, crée de nouvelles matières, et modifie ou supprime les matières existantes.
#     """

#     permission_classes = [IsAdminUser]
#     queryset = Matiere.objects.all().order_by("-date_creation")
#     serializer_class = MatiereSerializer

#     @swagger_auto_schema(
#         operation_description="Récupérer les matières filtrées par client",
#         manual_parameters=[
#             openapi.Parameter(
#                 "client_id",
#                 openapi.IN_QUERY,
#                 description="ID du client pour filtrer les matières",
#                 type=openapi.TYPE_INTEGER,
#                 required=True,
#             )
#         ],
#         responses={
#             200: MatiereSerializer(many=True),
#             400: "Paramètre client_id manquant",
#         },
#     )
#     @action(detail=False, methods=["get"])
#     def by_client(self, request):
#         """
#         Get materials filtered by client
#         """
#         client_id = request.query_params.get("client_id")
#         if not client_id:
#             return Response(
#                 {"message": "Le paramètre client_id est obligatoire"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         materials = self.queryset.filter(client_id=client_id)
#         serializer = self.get_serializer(materials, many=True)
#         return Response(serializer.data)

#     def perform_create(self, serializer):
#         client_id = self.request.data.get("client_id")
#         if client_id:
#             try:
#                 client = Client.objects.get(pk=client_id)
#                 serializer.save(client=client)
#             except Client.DoesNotExist:
#                 raise ValidationError({"client_id": "Client not found"})
#         else:
#             serializer.save()


# class TraveauxViewSet(viewsets.ModelViewSet):
#     """
#     API pour la gestion des travaux.

#     Liste tous les travaux, crée de nouveaux travaux, et modifie ou supprime les travaux existants.
#     Les travaux sont liés à des clients, des produits, et peuvent utiliser différentes matières.
#     """

#     permission_classes = [IsAdminUser]
#     queryset = Traveaux.objects.all().order_by("-date_creation")
#     serializer_class = TraveauxSerializer

#     def get_queryset(self):
#         """
#         Override to include matiere usage data in response
#         """
#         return self.queryset.prefetch_related("matiere_usages__matiere")

#     @transaction.atomic
#     def destroy(self, request, *args, **kwargs):
#         instance = self.get_object()

#         # Restore materials before deleting
#         for usage in instance.matiere_usages.all():
#             if usage.source == "client" and usage.matiere:
#                 usage.matiere.remaining_quantity += usage.quantite_utilisee
#                 usage.matiere.save()
#             elif usage.source == "stock" and usage.achat:
#                 usage.achat.remaining_quantity += usage.quantite_utilisee
#                 usage.achat.save()

#         # Delete the work
#         instance.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)

#     def perform_create(self, serializer):
#         print("📥 Request data:", self.request.data)
#         client_id = self.request.data.get("client_id")
#         produit_id = self.request.data.get("produit_id")
#         if client_id and produit_id:
#             try:
#                 client = Client.objects.get(pk=client_id)
#                 produit = Produit.objects.get(pk=produit_id)
#                 serializer.save(client=client, produit=produit)
#             except (Client.DoesNotExist, Produit.DoesNotExist):
#                 raise ValidationError(
#                     {"client_id": "Client not found", "produit_id": "Produit not found"}
#                 )
#         else:
#             serializer.save()

#     @swagger_auto_schema(
#         operation_description="Récupérer les travaux filtrés par client",
#         manual_parameters=[
#             openapi.Parameter(
#                 "client_id",
#                 openapi.IN_QUERY,
#                 description="ID du client pour filtrer les travaux",
#                 type=openapi.TYPE_INTEGER,
#                 required=True,
#             )
#         ],
#         responses={
#             200: TraveauxSerializer(many=True),
#             400: "Paramètre client_id manquant",
#         },
#     )
#     @action(detail=False, methods=["get"])
#     def by_client(self, request):
#         """
#         Get works filtered by client
#         """
#         client_id = request.query_params.get("client_id")
#         if not client_id:
#             return Response(
#                 {"message": "Le paramètre client_id est obligatoire"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         travaux = self.get_queryset().filter(client_id=client_id)
#         serializer = self.get_serializer(travaux, many=True)
#         return Response(serializer.data)


from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Q
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Client
from .serializers import ClientSerializer


class ClientViewSet(viewsets.ModelViewSet):
    """
    API pour la gestion des clients avec support de la corbeille.
    """

    permission_classes = [IsAdminUser]
    serializer_class = ClientSerializer
    queryset = Client.objects.all()  # <-- Ajout obligatoire

    def get_queryset(self):
        """
        Retourne seulement les clients non supprimés par défaut
        """
        return Client.objects.filter(is_deleted=False).order_by("nom_client")

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
        responses={200: ClientSerializer(many=True), 400: "Paramètre manquant"},
    )
    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        Recherche de clients actifs (nom ou numéro fiscal)
        """
        query = request.query_params.get("query", None)
        if not query:
            return Response(
                {"message": "Le paramètre de recherche est obligatoire"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        clients = self.get_queryset().filter(
            Q(nom_client__icontains=query) | Q(numero_fiscal__icontains=query)
        )

        serializer = self.get_serializer(clients, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Récupérer les clients supprimés (corbeille)",
        responses={200: ClientSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def deleted(self, request):
        """
        Retourne les clients dans la corbeille
        """
        clients = Client.objects.filter(is_deleted=True).order_by("-deleted_at")
        serializer = self.get_serializer(clients, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Déplacer un client vers la corbeille",
        responses={200: "Client supprimé logiquement", 404: "Non trouvé"},
    )
    @action(detail=True, methods=["patch"])
    def soft_delete(self, request, pk=None):
        """
        Suppression logique (corbeille)
        """
        try:
            client = self.get_object()
            client.is_deleted = True
            client.deleted_at = timezone.now()
            client.save()
            return Response({"message": "Client déplacé dans la corbeille"}, status=status.HTTP_200_OK)
        except Client.DoesNotExist:
            return Response({"message": "Client non trouvé"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Restaurer un client depuis la corbeille",
        responses={200: ClientSerializer, 404: "Client non trouvé"},
    )
    @action(detail=True, methods=["patch"])
    def restore(self, request, pk=None):
        """
        Restaurer un client supprimé
        """
        try:
            client = Client.objects.get(pk=pk, is_deleted=True)
            client.is_deleted = False
            client.deleted_at = None
            client.save()
            serializer = self.get_serializer(client)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Client.DoesNotExist:
            return Response({"message": "Client non trouvé"}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, *args, **kwargs):
        """
        Suppression définitive
        """
        try:
            client = Client.objects.get(pk=kwargs['pk'])
            client.delete()
            return Response({"message": "Client supprimé définitivement"}, status=status.HTTP_200_OK)
        except Client.DoesNotExist:
            return Response({"message": "Client non trouvé"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Créer un client",
        request_body=ClientSerializer,
        responses={201: ClientSerializer, 400: "Données invalides"},
    )
    def create(self, request, *args, **kwargs):
        if not request.data.get("nom_client") or not request.data.get("numero_fiscal"):
            return Response(
                {"message": "Le nom et le numéro fiscal sont obligatoires"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Mettre à jour un client",
        request_body=ClientSerializer,
        responses={200: ClientSerializer, 400: "Données invalides"},
    )
    def update(self, request, *args, **kwargs):
        if not request.data.get("nom_client") or not request.data.get("numero_fiscal"):
            return Response(
                {"message": "Le nom et le numéro fiscal sont obligatoires"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().update(request, *args, **kwargs)

from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status


class CategorieViewSet(viewsets.ModelViewSet):
    queryset = Categorie.objects.prefetch_related("sous_categories__produits", "produits").all()
    
    # Use normal serializer by default
    def get_serializer_class(self):
        if self.action == "list_tree":  # custom action for frontend tree
            return CategorieNestedSerializer
        return CategorieSerializer

    # custom endpoint for tree
    @action(detail=False, methods=["get"])
    def list_tree(self, request):
        queryset = self.get_queryset()
        serializer = CategorieNestedSerializer(queryset, many=True)
        return Response(serializer.data)


class SousCategorieViewSet(viewsets.ModelViewSet):
    queryset = SousCategorie.objects.all()
    serializer_class = SousCategorieSerializer

class ProduitViewSet(viewsets.ModelViewSet):
    """
    API pour la gestion des produits.
    
    Liste tous les produits, crée de nouveaux produits, et modifie ou supprime les produits existants.
    """
    queryset = Produit.objects.all()
    permission_classes = [IsAdminUser]
    serializer_class = ProduitSerializer
    
    def get_queryset(self):
        """Override to exclude deleted products by default"""
        return Produit.objects.filter(is_deleted=False).order_by("-id")

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
        operation_description="Supprimer logiquement un produit (soft delete)",
        responses={204: "Produit supprimé avec succès"},
    )
    def destroy(self, request, *args, **kwargs):
        """
        Soft delete a product instead of hard delete
        """
        instance = self.get_object()
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_description="Récupérer les produits supprimés (corbeille)",
        responses={200: ProduitSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def trash(self, request):
        """
        Get all deleted products (trash/recycle bin)
        """
        deleted_products = Produit.objects.filter(is_deleted=True).order_by("-deleted_at")
        serializer = self.get_serializer(deleted_products, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Restaurer un produit supprimé",
        responses={200: ProduitSerializer, 404: "Produit non trouvé"},
    )
    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        """
        Restore a deleted product
        """
        try:
            # Get the product even if it's deleted
            product = Produit.objects.get(pk=pk, is_deleted=True)
            product.is_deleted = False
            product.deleted_at = None
            product.save()
            
            serializer = self.get_serializer(product)
            return Response({
                "message": "Produit restauré avec succès",
                "product": serializer.data
            })
        except Produit.DoesNotExist:
            return Response(
                {"message": "Produit supprimé non trouvé"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @swagger_auto_schema(
        operation_description="Supprimer définitivement un produit de la corbeille",
        responses={204: "Produit supprimé définitivement"},
    )
    @action(detail=True, methods=["delete"])
    def permanent_delete(self, request, pk=None):
        """
        Permanently delete a product from trash
        """
        try:
            product = Produit.objects.get(pk=pk, is_deleted=True)
            product.delete()  # Hard delete
            return Response(
                {"message": "Produit supprimé définitivement"},
                status=status.HTTP_204_NO_CONTENT
            )
        except Produit.DoesNotExist:
            return Response(
                {"message": "Produit supprimé non trouvé"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @swagger_auto_schema(
        operation_description="Vider complètement la corbeille",
        responses={200: "Corbeille vidée avec succès"},
    )
    @action(detail=False, methods=["delete"])
    def empty_trash(self, request):
        """
        Empty the entire trash (permanent delete all deleted products)
        """
        deleted_count = Produit.objects.filter(is_deleted=True).count()
        Produit.objects.filter(is_deleted=True).delete()
        
        return Response({
            "message": f"{deleted_count} produits supprimés définitivement de la corbeille"
        })

    # A supprimer
    # @swagger_auto_schema(
    #     operation_description="Récupérer les produits filtrés par type de matière",
    #     manual_parameters=[
    #         openapi.Parameter(
    #             "type_matiere",
    #             openapi.IN_QUERY,
    #             description="Type de matière pour filtrer les produits",
    #             type=openapi.TYPE_STRING,
    #             required=True,
    #         )
    #     ],
    #     responses={
    #         200: ProduitSerializer(many=True),
    #         400: "Paramètre type_matiere manquant",
    #     },
    # )
    # @action(detail=False, methods=["get"])
    # def by_material_type(self, request):
    #     """
    #     Get products filtered by material type
    #     """
    #     type_matiere = request.query_params.get("type_matiere")
    #     if not type_matiere:
    #         return Response(
    #             {"message": "Le paramètre type_matiere est obligatoire"},
    #             status=status.HTTP_400_BAD_REQUEST,
    #         )
        
    #     products = self.get_queryset().filter(type_matiere=type_matiere)
    #     serializer = self.get_serializer(products, many=True)
    #     return Response(serializer.data)

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
# from .serializers import MatierePremiereAchatSerializer

# A supprimer
# class ProduitAchatViewSet(viewsets.ModelViewSet):
#     queryset = MatierePremiereAchat.objects.all().order_by("-created_at")
#     serializer_class = MatierePremiereAchatSerializer
#     filter_backends = [filters.SearchFilter]
#     search_fields = ['ref', 'nom_produit', 'fournisseur_principal']

#     def get_queryset(self):
#         queryset = super().get_queryset()
#         categorie = self.request.query_params.get("categorie")
#         if categorie and categorie != "all":
#             queryset = queryset.filter(categorie=categorie)
#         return queryset

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         if not serializer.is_valid():
#             print("❌ Erreurs de validation (create):", serializer.errors)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#         self.perform_create(serializer)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)

#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         if not serializer.is_valid():
#             print("❌ Erreurs de validation (update):", serializer.errors)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#         self.perform_update(serializer)
#         return Response(serializer.data)

#     def destroy(self, request, *args, **kwargs):
#         instance = self.get_object()
#         self.perform_destroy(instance)
#         return Response({"message": "Produit supprimée avec succès."}, status=status.HTTP_204_NO_CONTENT)




from rest_framework import viewsets
from .models import FactureAchatProduit
from .serializers import FactureAchatProduitSerializer

class FactureAchatProduitViewSet(viewsets.ModelViewSet):
    queryset = FactureAchatProduit.objects.all().order_by('-id')
    serializer_class = FactureAchatProduitSerializer


from rest_framework import viewsets
from .models import BonLivraisonProduit
from .serializers import BonLivraisonProduitSerializer

class BonLivraisonMatiereViewSet(viewsets.ModelViewSet):
    queryset = BonLivraisonProduit.objects.all().order_by('-id')
    serializer_class = BonLivraisonProduitSerializer



from .models import Fournisseur
from .serializers import FournisseurSerializer

# views.py
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response

class FournisseurViewSet(viewsets.ModelViewSet):
    serializer_class = FournisseurSerializer
    
    def get_queryset(self):
        # Par défaut, ne montrer que les fournisseurs non supprimés
        return Fournisseur.objects.filter(is_deleted=False)
    
    def destroy(self, request, *args, **kwargs):
        # Suppression logique au lieu de suppression physique
        instance = self.get_object()
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()
        return Response(status=204)
    
    @action(detail=False, methods=['get'])
    def trash(self, request):
        # Récupérer les fournisseurs supprimés
        deleted_fournisseurs = Fournisseur.objects.filter(is_deleted=True)
        serializer = self.get_serializer(deleted_fournisseurs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        # Restaurer un fournisseur
        try:
            fournisseur = Fournisseur.objects.get(pk=pk, is_deleted=True)
            fournisseur.is_deleted = False
            fournisseur.deleted_at = None
            fournisseur.save()
            return Response({'message': 'Fournisseur restauré avec succès'})
        except Fournisseur.DoesNotExist:
            return Response({'error': 'Fournisseur non trouvé'}, status=404)
    
    @action(detail=True, methods=['delete'])
    def permanent_delete(self, request, pk=None):
        # Suppression définitive
        try:
            fournisseur = Fournisseur.objects.get(pk=pk, is_deleted=True)
            fournisseur.delete()
            return Response({'message': 'Fournisseur supprimé définitivement'})
        except Fournisseur.DoesNotExist:
            return Response({'error': 'Fournisseur non trouvé'}, status=404)

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

from .models import BonRetourFournisseur, Fournisseur, ProduitRetourFournisseur, Produit
from .serializers import (
    BonRetourFournisseurSerializer,
    BonRetourFournisseurListSerializer,
    ProduitForRetourFournisseurSerializer,
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
        produits = ProduitRetourFournisseur.objects.filter(bon_retour__in=bons, is_deleted=False)

        response_data = {
            "fournisseur": {
                "id": fournisseur.id,
                "nom": fournisseur.nom,
                "numero_fiscal": fournisseur.numero_fiscal,
            },
            "available_materials": [
                {
                    "nom_produit": m.nom_produit,
                    "quantite_retournee": m.quantite_retournee,
                }
                for m in produits
            ],
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Fournisseur.DoesNotExist:
        return Response({"error": "Fournisseur not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
def validate_return_quantities_fournisseur(request):
    products_data = request.data.get("products", [])

    if not products_data:
        return Response(
            {"error": "No products provided for validation"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    validation_results = []
    has_errors = False

    for products_data in products_data:
        produit_id = products_data.get("produit_id")
        quantite_retournee = products_data.get("quantite_retournee", 0)

        try:
            produit = Matiere.objects.get(id=produit_id)

            result = {
                "produit_id": produit_id,
                "produit_name": f"{produit.nom_produit}",
                "requested_quantity": quantite_retournee,
                "available_quantity": produit.remaining_quantity,
                "is_valid": quantite_retournee <= produit.remaining_quantity,
            }

            if not result["is_valid"]:
                result["error"] = (
                    f"Cannot return {quantite_retournee} units. Only {produit.remaining_quantity} available."
                )
                has_errors = True

            validation_results.append(result)

        except Produit.DoesNotExist:
            validation_results.append(
                {
                    "produit_id": produit_id,
                    "error": "Product not found",
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

from .models import PlanTraiteFournisseur, TraiteFournisseur, FactureAchatProduit, Fournisseur
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
            facture = FactureAchatProduit.objects.get(numero=numero_facture)
        except FactureAchatProduit.DoesNotExist:
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


# Tresorerie
from rest_framework.permissions import IsAuthenticated
from .services.kpi_service import compute_kpis
from .services.schedule_service import get_schedule
from .services.traite_service import get_all_traites
from .services.period_service import (compute_encaissement_trend, compute_decaissement_trend, compute_resultat_net_trend, compute_traites_fournisseurs_trend, compute_traites_clients_trend, compute_echues_total_and_count_with_trend)
from .services.chart_data import compute_chart_data
from .utils.dates import get_period_range
from .services.kpi_service import compute_kpis
from .services.traite_service import get_all_traites

class PeriodView(APIView):
    def get(self, request):
        period = request.query_params.get("period", "week")
        range_func, label = get_period_range(period)
        start_date, end_date = range_func()
        kpiData = compute_kpis(evolution_weeks=4, range_func=range_func)
        traites = get_all_traites(range_func=range_func, globally=False)

        period_labels = {
            "week": "Cette semaine",
            "month": "Ce mois",
            "quarter": "Ce trimestre",
            "year": "Cette année"
        }
        label = period_labels.get(period, "Cette période")

        income, income_trend = kpiData["income"]["value"], kpiData["income"]["trend"]
        expense, expense_trend =  kpiData["expense"]["value"],  kpiData["income"]["trend"]
        net, net_trend =  kpiData["balance"]["value"],  kpiData["balance"]["trend"]
        traites_fournisseurs, traites_trend = [t for t in traites["traites"] if t["type"] == "fournisseur"], traites["stats"]["fournisseurs"]["trend"]
        traites_clients, traites_clients_trend = [t for t in traites["traites"] if t["type"] == "client"], traites["stats"]["clients"]["trend"]
        echues_total, echues_count, echues_trend = [t for t in traites["traites"] if t["etat"] == "echu"], traites["stats"]["echues"]["trend"], traites["stats"]["echues"]["count"]
        chart_data = compute_chart_data(start_date, end_date, label, period)

        # income, income_trend = compute_encaissement_trend(start_date, end_date)
        # expense, expense_trend = compute_decaissement_trend(start_date, end_date)
        # net, net_trend = compute_resultat_net_trend(start_date, end_date)
        # traites_fournisseurs, traites_trend = compute_traites_fournisseurs_trend(start_date, end_date)
        # traites_clients, traites_clients_trend = compute_traites_clients_trend(start_date, end_date)
        # echues_total, echues_count, echues_trend = compute_echues_total_and_count_with_trend(start_date, end_date)
        # chart_data = compute_chart_data(start_date, end_date, label, period)

        return Response({
            "encaissements": {
                "value": income,
                "trend": income_trend,
                "positive": income_trend >= 0,
                "label": label
            },
            "decaissements": {
                "value": -expense,
                "trend": -expense_trend,
                "positive": False,
                "label": label
            },
            "resultatNet": {
                "value": net,
                "trend": net_trend,
                "positive": net_trend >= 0,
                "label": label
            },
            "traitesFournisseurs": {
                "value": traites_fournisseurs,
                "trend": -traites_trend,
                "positive": False,
                "label": label
            },
            "traitesClients": {
                "value": traites_clients,
                "trend": traites_clients_trend,
                "positive": traites_clients_trend >= 0,
                "label": label
            },
            "echues": {
                "value": echues_total,
                "trend": echues_trend,
                "count": echues_count,
                "positive": False,
                "label": label
            },
            "chart_data": chart_data
        })

class TraiteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = get_all_traites()
        print("Traites data:", data) 
        return Response(data)

class KPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        evolution_weeks = request.GET.get("evolution_weeks", "30d")
        data = compute_kpis(evolution_weeks)
        return Response(data)

class ScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        end_date = date.today() + timedelta(days=7)
        data = get_schedule(end_date=end_date)
        return Response(data)

def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fiche = serializer.save()  # création normale de la fiche

        appliquer_remboursement_avance(fiche)  # ← applique automatiquement l’avance

        # recharger la fiche mise à jour (net_a_payer, avance_deduite...)
        serializer = self.get_serializer(fiche)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum
from django.utils import timezone
from .models import Avoir, AvoirArticle
from .serializers import AvoirSerializer

class AvoirViewSet(viewsets.ModelViewSet):
    queryset = Avoir.objects.all().prefetch_related('articles')
    serializer_class = AvoirSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtres depuis les query parameters
        numero = self.request.query_params.get('numero')
        fournisseur = self.request.query_params.get('fournisseur')
        type_avoir = self.request.query_params.get('type_avoir')
        date_debut = self.request.query_params.get('date_debut')
        date_fin = self.request.query_params.get('date_fin')
        
        if numero:
            queryset = queryset.filter(numero__icontains=numero)
        
        if fournisseur:
            queryset = queryset.filter(fournisseur__icontains=fournisseur)
        
        if type_avoir:
            queryset = queryset.filter(type_avoir=type_avoir)
        
        if date_debut:
            queryset = queryset.filter(date_avoir__gte=date_debut)
        
        if date_fin:
            queryset = queryset.filter(date_avoir__lte=date_fin)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Retourne les statistiques des avoirs"""
        queryset = self.get_queryset()
        
        stats = {
            'total_avoirs': queryset.count(),
            'montant_total': queryset.aggregate(
                total=Sum('montant_total')
            )['total'] or 0,
            'par_type': {},
            'par_mode_paiement': {},
            'recent_avoirs': AvoirSerializer(
                queryset[:5], many=True, context={'request': request}
            ).data
        }
        
        # Statistiques par type
        for choice in Avoir.TYPE_AVOIR_CHOICES:
            type_code = choice[0]
            count = queryset.filter(type_avoir=type_code).count()
            if count > 0:
                stats['par_type'][choice[1]] = count
        
        # Statistiques par mode de paiement
        for choice in Avoir.MODE_PAIEMENT_CHOICES:
            mode_code = choice[0]
            count = queryset.filter(mode_paiement=mode_code).count()
            if count > 0:
                stats['par_mode_paiement'][choice[1]] = count
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def dupliquer(self, request, pk=None):
        """Duplique un avoir existant"""
        avoir_original = self.get_object()
        
        # Créer une copie
        avoir_copie = Avoir.objects.create(
            fournisseur=avoir_original.fournisseur,
            type_avoir=avoir_original.type_avoir,
            mode_paiement=avoir_original.mode_paiement,
            montant_total=avoir_original.montant_total,
            date_avoir=timezone.now().date()
        )
        
        # Copier les articles
        for article in avoir_original.articles.all():
            AvoirArticle.objects.create(
                avoir=avoir_copie,
                nom=article.nom,
                prix=article.prix,
                quantite=article.quantite
            )
        
        serializer = self.get_serializer(avoir_copie)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        """Suppression avec message de confirmation"""
        instance = self.get_object()
        numero = instance.numero or f"ID-{instance.id}"
        self.perform_destroy(instance)
        return Response({
            'message': f'Avoir {numero} supprimé avec succès'
        }, status=status.HTTP_200_OK)