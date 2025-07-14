from django.contrib import admin
from .models import (
    Client,
    Matiere,
    Produit,
    MatiereUsage,
    Traveaux,
    FactureTravaux,
    Entreprise,
    FactureMatiere,
    PlanTraite,
    Traite,
    BonRetour,
    MatiereRetour,
    Devis,
    ProduitDevis,
    Commande,
    ProduitCommande,
    Employe,
)

# Register your models here.
admin.site.register(Client)
admin.site.register(Matiere)
admin.site.register(Produit)
admin.site.register(MatiereUsage)
admin.site.register(Traveaux)
admin.site.register(FactureTravaux)
admin.site.register(Entreprise)
admin.site.register(FactureMatiere)
admin.site.register(PlanTraite)
admin.site.register(Traite)
admin.site.register(BonRetour)
admin.site.register(MatiereRetour)
admin.site.register(Devis)
admin.site.register(ProduitDevis)
admin.site.register(Commande)
admin.site.register(ProduitCommande)
admin.site.register(Employe)

