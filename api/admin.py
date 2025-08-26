from django.contrib import admin
from .models import (
    Client,
    Produit,
    FactureProduits,
    Entreprise,
    PlanTraite,
    Traite,
    BonRetour,
    ProduitRetour,
    Devis,
    ProduitDevis,
    Commande,
    ProduitCommande,
    Employe,
)

# Register your models here.
admin.site.register(Client)
admin.site.register(Produit)
admin.site.register(FactureProduits)
admin.site.register(Entreprise)
admin.site.register(PlanTraite)
admin.site.register(Traite)
admin.site.register(BonRetour)
admin.site.register(ProduitRetour)
admin.site.register(Devis)
admin.site.register(ProduitDevis)
admin.site.register(Commande)
admin.site.register(ProduitCommande)
admin.site.register(Employe)

