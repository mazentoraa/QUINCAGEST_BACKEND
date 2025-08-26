import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from api.models import Client, FactureProduits, PlanTraite, Traite, Bank
from django.utils import timezone
from datetime import timedelta

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def client():
    return Client.objects.create(
        nom_client="Test Client",
        numero_fiscal="123456789",
        adresse="123 Test St",
        nom_raison_sociale="Test Company"
    )

@pytest.fixture
def facture(client):
    facture = FactureProduits.objects.create(
        numero_facture="FAC-001",
        client=client,
        date_emission=timezone.now().date(),
        statut="draft",
        montant_ht=1000,
        montant_tva=200,
        montant_ttc=1200
    )
    return facture

@pytest.fixture
def bank():
    return Bank.objects.create(
        name="Test Bank",
        address="Bank Address 123",
        rib="RIB123456789"
    )

@pytest.fixture
def plan_traite(facture):
    return PlanTraite.objects.create(
        facture=facture,
        nombre_traite=3,
        date_premier_echeance=timezone.now().date() + timedelta(days=30),
        periode=30,
        montant_total=1200,
        nom_raison_sociale=facture.client.nom_raison_sociale,
        matricule_fiscal=facture.client.numero_fiscal,
        mode_paiement="traite"
    )

@pytest.mark.django_db
def test_create_traite(api_client, plan_traite, bank):
    url = reverse('traite-list')
    data = {
        "plan_traite": plan_traite.id,
        "date_echeance": (timezone.now().date() + timedelta(days=30)).isoformat(),
        "status": "NON_PAYEE",
        "montant": 400,
        "aval": "Aval info",
        "acceptation": "Acceptation info",
        "bank_id": bank.id
    }
    response = api_client.post(url, data, format='json')
    assert response.status_code == 201
    assert response.data['aval'] == "Aval info"
    assert response.data['acceptation'] == "Acceptation info"
    assert response.data['bank']['name'] == "Test Bank"

@pytest.mark.django_db
def test_list_traites(api_client, plan_traite, bank):
    # Create some traites
    Traite.objects.create(
        plan_traite=plan_traite,
        date_echeance=timezone.now().date() + timedelta(days=30),
        status="NON_PAYEE",
        montant=400,
        aval="Aval 1",
        acceptation="Accept 1",
        bank=bank
    )
    Traite.objects.create(
        plan_traite=plan_traite,
        date_echeance=timezone.now().date() + timedelta(days=60),
        status="NON_PAYEE",
        montant=400,
        aval="Aval 2",
        acceptation="Accept 2",
        bank=bank
    )
    url = reverse('traite-list')
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.data) >= 2

@pytest.mark.django_db
def test_update_traite_status(api_client, plan_traite, bank):
    traite = Traite.objects.create(
        plan_traite=plan_traite,
        date_echeance=timezone.now().date() + timedelta(days=30),
        status="NON_PAYEE",
        montant=400,
        aval="Aval info",
        acceptation="Acceptation info",
        bank=bank
    )
    url = reverse('traite-update-status', args=[traite.id])
    data = {"status": "PAYEE"}
    response = api_client.patch(url, data, format='json')
    assert response.status_code == 200
    assert response.data['status'] == "PAYEE"
