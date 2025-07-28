from datetime import date, timedelta
from django.db.models import Sum
from api.models import Traite, TraiteFournisseur

def compute_trend(current, previous):
    if previous == 0:
        return 0
    return round(((current - previous) / previous) * 100, 1)

def get_week_range(weeks_ago=0):
    today = date.today()
    start = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks_ago * 7)
    end = start + timedelta(days=6)
    return start, end

def get_all_traites():
    today = date.today()
    start_curr, end_curr = get_week_range(0)
    start_prev, end_prev = get_week_range(1)

    # -------- 1. Clients traites
    total_clients = Traite.objects.filter(plan_traite__is_deleted = False).aggregate(total=Sum("montant"))["total"] or 0
    total_clients_prev = Traite.objects.filter(
        date_echeance__range=(start_prev, end_prev),
        plan_traite__is_deleted = False
    ).aggregate(total=Sum("montant"))["total"] or 0
    clients_trend = compute_trend(total_clients, total_clients_prev)

    total_clients_encaissees = Traite.objects.filter(status='PAYEE', plan_traite__is_deleted = False).aggregate(total=Sum("montant"))["total"] or 0
    total_clients_encaissees_prev = Traite.objects.filter(
        date_echeance__range=(start_prev, end_prev), status='PAYEE',
        plan_traite__is_deleted = False
    ).aggregate(total=Sum("montant"))["total"] or 0

    # -------- 2. Fournisseur traites
    total_fournisseurs = TraiteFournisseur.objects.filter(plan_traite__is_deleted = False).aggregate(total=Sum("montant"))["total"] or 0
    total_fournisseurs_prev = TraiteFournisseur.objects.filter(
        date_echeance__range=(start_prev, end_prev),
        plan_traite__is_deleted = False
    ).aggregate(total=Sum("montant"))["total"] or 0
    fournisseurs_trend = compute_trend(total_fournisseurs, total_fournisseurs_prev)

    total_fournisseurs_payees = TraiteFournisseur.objects.filter(status='PAYEE', plan_traite__is_deleted = False).aggregate(total=Sum("montant"))["total"] or 0
    total_fournisseurs_payees_prev = TraiteFournisseur.objects.filter(
        date_echeance__range=(start_prev, end_prev), status='PAYEE',
        plan_traite__is_deleted = False
    ).aggregate(total=Sum("montant"))["total"] or 0

    # -------- 3. Echues
    echues_clients = Traite.objects.filter(date_echeance__lt=today, status="NON_PAYEE", plan_traite__is_deleted = False).aggregate(
        total=Sum("montant"))["total"] or 0
    echues_fournisseurs = TraiteFournisseur.objects.filter(date_echeance__lt=today, status="NON_PAYEE", plan_traite__is_deleted = False).aggregate(
        total=Sum("montant"))["total"] or 0
    echues_total = echues_clients + echues_fournisseurs

    # Counts
    echues_clients_count = Traite.objects.filter(date_echeance__lt=today, status="NON_PAYEE", plan_traite__is_deleted = False).count()
    echues_fournisseurs_count = TraiteFournisseur.objects.filter(date_echeance__lt=today, status="NON_PAYEE", plan_traite__is_deleted = False).count()
    echues_count = echues_clients_count + echues_fournisseurs_count

    # Previous week echues
    echues_prev_clients = Traite.objects.filter(
        date_echeance__lt=start_curr,
        date_echeance__gte=start_prev,
        plan_traite__is_deleted = False,
        status="NON_PAYEE"
    ).aggregate(total=Sum("montant"))["total"] or 0
    echues_prev_fournisseurs = TraiteFournisseur.objects.filter(
        date_echeance__lt=start_curr,
        date_echeance__gte=start_prev,
        plan_traite__is_deleted = False,
        status="NON_PAYEE"
    ).aggregate(total=Sum("montant"))["total"] or 0
    echues_prev = echues_prev_clients + echues_prev_fournisseurs
    echues_trend = compute_trend(echues_total, echues_prev)

    # -------- 4. Net
    net = total_clients_encaissees - total_fournisseurs_payees
    net_prev = total_clients_encaissees_prev - total_fournisseurs_payees_prev
    net_trend = compute_trend(net, net_prev)


    # -------- 5. Build traites list

    def get_etat(t):
        if t.status == "PAYEE":
            return "paye"
        elif t.date_echeance < today:
            return "echu"
        else:
            return "en-cours"
        
    client_data = [
        {
            "id": t.id,
            "type": "client",
            "tier": t.plan_traite.client.nom_client if t.plan_traite.client else t.plan_traite.nom_raison_sociale,
            "ref": t.plan_traite.numero_facture,
            "echeance": t.date_echeance,
            "montant": t.montant,
            "statut": t.status,
            "etat": get_etat(t)
        }
        for t in Traite.objects.filter(plan_traite__is_deleted = False).select_related("plan_traite__client").all()
    ]

    fournisseur_data = [
        {
            "id": t.id,
            "type": "fournisseur",
            "tier": t.plan_traite.fournisseur.nom if t.plan_traite.fournisseur else t.plan_traite.nom_raison_sociale,
            "ref": t.plan_traite.numero_facture,
            "echeance": t.date_echeance,
            "montant": -t.montant,
            "statut": t.status,
            "etat": get_etat(t)
        }
        for t in TraiteFournisseur.objects.filter(plan_traite__is_deleted = False).select_related("plan_traite__fournisseur").all()
    ]

    all_traites = sorted(client_data + fournisseur_data, key=lambda x: x["echeance"])

    stats = {
        "clients": {
            "value": round(total_clients, 2),
            "count": Traite.objects.count(),
            "trend": clients_trend
        },
        "fournisseurs": {
            "value": -round(total_fournisseurs, 2),
            "count": TraiteFournisseur.objects.count(),
            "trend": -fournisseurs_trend  # negative to show it's an outgoing
        },
        "echues": {
            "value": round(echues_total, 2),
            "count": echues_count,
            "trend": echues_trend
        },
        "net": {
            "value": round(net, 2),
            "trend": net_trend
        }
    }
    return {
        "traites": all_traites,
        "stats": stats
    }
