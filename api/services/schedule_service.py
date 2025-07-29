from datetime import date
from django.utils.timezone import now
from api.models import Cd, TraiteFournisseur, FichePaie, Traite


def get_schedule():
    today = date.today()
    upcoming_events = []

    # 1. Upcoming client invoices
    invoices = Cd.objects.filter(
        statut='pending',
        date_commande__gte=today
    )
    for inv in invoices:
        upcoming_events.append({
            'date': inv.date_commande.isoformat(),
            'description': f"Encaissement {inv.client.nom_client}",
            'amount': inv.montant_ttc,
            'type': 'positive'
        })

    # 2. Upcoming supplier traites
    traites = TraiteFournisseur.objects.filter(
        status='NON_PAYEE',
        date_echeance__gte=today
    )
    for t in traites:
        upcoming_events.append({
            'date': t.date_echeance.isoformat(),
            'description': f"Traite Fournisseur {t.plan_traite.fournisseur.nom}",
            'amount': -t.montant,
            'type': 'supplier'
        })
    
    # 2. Upcoming client traites
    traites = Traite.objects.filter(
        status='NON_PAYEE',
        date_echeance__gte=today
    )
    for t in traites:
        upcoming_events.append({
            'date': t.date_echeance.isoformat(),
            'description': f"Traite Client {t.plan_traite.client.nom_client}",
            'amount': t.montant,
            'type': 'positive'
        })

    # Salaries
    salaries = FichePaie.objects.filter(date_creation__gte=today)
    for s in salaries:
        upcoming_events.append({
            'date': s.date_creation.strftime("%Y-%m-%d"),
            'description': f"Salaire employé {s.employe.nom}",
            'amount': -s.net_a_payer,
            'type': 'negative'
        })

    # 4. Sort by date
    upcoming_events.sort(key=lambda x: x['date'])

    return upcoming_events
