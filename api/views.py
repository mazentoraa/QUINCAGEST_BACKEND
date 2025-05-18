from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Client
from .serializers import ClientSerializer
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token



class ClientViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing clients
    """
    permission_classes = [IsAdminUser]
    queryset = Client.objects.all().order_by('nom_client')
    serializer_class = ClientSerializer

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search clients by name or fiscal number
        """
        query = request.query_params.get('query', None)
        if not query:
            return Response({
                'message': 'Le paramètre de recherche est obligatoire'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        clients = self.queryset.filter(
            Q(nom_client__icontains=query) | 
            Q(numero_fiscal__icontains=query)
        )
        
        serializer = self.get_serializer(clients, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Create a new client with validation
        """
        if not request.data.get('nom_client') or not request.data.get('numero_fiscal'):
            return Response({
                'message': 'Le nom du client et le numéro fiscal sont obligatoires'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        return super().create(request, *args, **kwargs)
        
    def update(self, request, *args, **kwargs):
        """
        Update an existing client with validation
        """
        if not request.data.get('nom_client') or not request.data.get('numero_fiscal'):
            return Response({
                'message': 'Le nom du client et le numéro fiscal sont obligatoires'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        return super().update(request, *args, **kwargs)




class AdminLoginView(APIView):
    permission_classes = []
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user and user.is_staff:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'username': user.username,
                'is_admin': user.is_staff
            })
        return Response({'error': 'Invalid credentials or not an admin'}, 
                        status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        request.user.auth_token.delete()
        return Response({"message": "Successfully logged out."}, 
                        status=status.HTTP_200_OK)

class CheckAuthView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            'authenticated': True,
            'user_id': request.user.id,
            'username': request.user.username,
            'is_admin': request.user.is_staff
        })