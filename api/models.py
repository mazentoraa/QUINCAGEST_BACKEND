from datetime import timedelta
from django.db import models
import re
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP

MATIERE_PREFIXES = {
    "acier": "AC",
    "acier_inoxydable": "AI",
    "aluminium": "AL",
    "laiton": "LA",
    "cuivre": "CU",
    "acier_galvanise": "AG",
    "autre": "OT",
}
def validate_email(value):

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, value):
        raise ValidationError("Format d'email invalide")

def validate_matricule_fiscal(value):
    pattern = r'^\d{3}\s\d{4}[A-Z]/[A-Z]/[A-Z]/\d{3}$'
    if not re.match(pattern, value):
        raise ValidationError("Le matricule fiscal doit être au format : 000 0000X/X/X/000")


def validate_phone(value):
    from django.core.exceptions import ValidationError

    if not value.isdigit():
        raise ValidationError("Le numéro doit contenir uniquement des chiffres")


class Client(models.Model):
    nom_client = models.CharField(max_length=255, help_text="Client name")
    numero_fiscal = models.CharField(
        max_length=255, unique=True,validators=[validate_matricule_fiscal], help_text="Fiscal registration number"
    )
    adresse = models.CharField(
        max_length=255, blank=True, null=True, help_text="Client address"
    )
    telephone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[validate_phone],
        help_text="Client phone number",
    )
    nom_responsable = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Manager or responsible person's name",
    )
    email = models.EmailField(
        blank=True, null=True, validators=[validate_email], help_text="Client's email"
    )
    email_responsable = models.EmailField(
        blank=True,
        null=True,
        validators=[validate_email],
        help_text="Manager or responsible person's email",
    )
    telephone_responsable = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[validate_phone],
        help_text="Manager or responsible person's phone number",
    )
    autre_numero = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[validate_phone],
        help_text="Other optional number",
    )
    informations_complementaires = models.TextField(
        blank=True, null=True, help_text="Additional information about the client"
    )
    date_creation = models.DateTimeField(
        auto_now_add=True, help_text="Date when the client was created"
    )
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, help_text="Date when the client was last updated"
    )
    nom_raison_sociale = models.CharField(
        max_length=255, blank=True, null=True, help_text="Nom de la raison sociale"
    )
    code_client = models.CharField(max_length=5, unique=True, blank=True)
    is_deleted = models.BooleanField(default=False, help_text="Client deleted")
    deleted_at = models.DateTimeField(
        null=True, blank=True, help_text="Date when the client was deleted"
    )

    class Meta:
        ordering = ["nom_client"]
        indexes = [
            models.Index(fields=["nom_client"]),
            models.Index(fields=["numero_fiscal"]),
        ]

    def __str__(self):
        return self.nom_client

    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)
            self.code_client = f"{self.id:05d}"
            kwargs['force_insert'] = False
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)


class Matiere(models.Model):
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="matieres", help_text="Client"
    )
    numero_bon = models.CharField(
        max_length=50,
        unique=True,
        help_text="Material reception number",
        null=True,
        blank=True,
    )
    type_matiere = models.CharField(
        max_length=50,
        choices=[
            ("acier", "Acier"),
            ("acier_inoxydable", "Acier inoxydable"),
            ("aluminium", "Aluminium"),
            ("laiton", "Laiton"),
            ("cuivre", "Cuivre"),
            ("acier_galvanise", "Acier galvanisé"),
            ("autre", "Autre"),
        ],
        default="autre",
        help_text="Material type",
    )
    description = models.TextField(blank=True, null=True, help_text="Material description")
    reception_date = models.DateField(help_text="Date of material reception", null=True, blank=True)
    thickness = models.IntegerField(help_text="Thickness in mm", null=True, blank=True)
    length = models.IntegerField(help_text="Length in mm", null=True, blank=True)
    width = models.IntegerField(help_text="Width in mm", null=True, blank=True)
    surface = models.IntegerField(help_text="Surface area (m²)", null=True, blank=True)
    prix_unitaire = models.FloatField(help_text="Unit price", null=True, blank=True)
    quantite = models.PositiveIntegerField(default=0, help_text="Quantity in stock")
    remaining_quantity = models.PositiveIntegerField(default=0, help_text="Remaining quantity")
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.type_matiere} - {self.client.nom_client}"

    def save(self, *args, **kwargs):
        # Initialiser la quantité restante à la création
        if not self.pk or self.remaining_quantity == 0:
            self.remaining_quantity = self.quantite

        # Générer un numero_bon unique s'il est vide
        if not self.numero_bon:
            year = timezone.now().year
            prefix = f"BL-{year}-"
            last_num = (
                Matiere.objects
                .filter(numero_bon__startswith=prefix)
                .order_by("-numero_bon")
                .values_list("numero_bon", flat=True)
                .first()
            )

            if last_num:
                try:
                    last_number = int(last_num.split("-")[-1])
                except ValueError:
                    last_number = 0
            else:
                last_number = 0

            self.numero_bon = f"{prefix}{str(last_number + 1).zfill(5)}"

        super().save(*args, **kwargs)

    def update_quantity_after_usage(self, amount_used):
        if self.remaining_quantity >= amount_used:
            self.remaining_quantity -= amount_used
            self.save()
            return True
        return False


class Produit(models.Model):
    nom_produit = models.CharField(max_length=255, help_text="Product name")
    description = models.TextField(
        blank=True, null=True, help_text="Product description"
    )
    type_matiere = models.CharField(
        max_length=50,
        choices=[
            ("acier", "Acier"),
            ("acier_inoxydable", "Acier inoxydable"),
            ("aluminium", "Aluminium"),
            ("laiton", "Laiton"),
            ("cuivre", "Cuivre"),
            ("acier_galvanise", "Acier galvanisé"),
            ("autre", "Autre"),
        ],
        default="autre",
        help_text="Material type",
    )
    prix = models.FloatField(
        help_text="Product price",
        null=True,
        blank=True,
    )
    image = models.ImageField(
        upload_to="produits/",
        blank=True,
        null=True,
        help_text="Product image",
    )
    epaisseur = models.FloatField(
        help_text="Thickness of the product in mm",
        null=True,
        blank=True,
    )
    longueur = models.FloatField(
        help_text="Length of the product in mm",
        null=True,
        blank=True,
    )
    largeur = models.FloatField(  # Added field
        help_text="Width of the product in mm",
        null=True,
        blank=True,
    )
    surface = models.FloatField(
        help_text="Surface area of the product in m²",
        null=True,
        blank=True,
    )
    date_creation = models.DateTimeField(
        auto_now_add=True, help_text="Date when the product was created"
    )
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, help_text="Date when the product was last updated"
    )
    is_deleted = models.BooleanField(default=False, help_text="Product deleted")
    deleted_at = models.DateTimeField(
        null=True, blank=True, help_text="Date when the product was deleted"
    )
    code_produit = models.CharField(
    max_length=20,
    blank=True,
)

    class Meta:
        ordering = ["nom_produit"]
        indexes = [
            models.Index(fields=["nom_produit"]),
            models.Index(fields=["prix"]),
        ]
    
    def save(self, *args, **kwargs):
        if not self.code_produit:
            prefix = MATIERE_PREFIXES.get(self.type_matiere, "OT")

           
            existing_codes = Produit.objects.filter(code_produit__startswith=prefix + "-") \
                                            .values_list("code_produit", flat=True)

            max_number = 0
            for code in existing_codes:
                try:
                    number = int(code.split("-")[-1])
                    max_number = max(max_number, number)
                except (ValueError, IndexError):
                    continue

            self.code_produit = f"{prefix}-{max_number + 1:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom_produit


class MatierePremiereAchat(models.Model):
    ref = models.CharField(max_length=100, unique=True)
    nom_matiere = models.CharField(max_length=200)

    categorie = models.CharField(
        max_length=100,
        choices=[
            ("acier", "Acier"),
            ("acier_inoxydable", "Acier inoxydable"),
            ("aluminium", "Aluminium"),
            ("laiton", "Laiton"),
            ("cuivre", "Cuivre"),
            ("acier_galvanise", "Acier galvanisé"),
            ("metaux","Metaux"),
            ("autre", "Autre"),
        ],
        default="autre",
    )

    description = models.TextField(blank=True, null=True)
    unite_mesure = models.CharField(
        max_length=10,
        choices=[
            ("kg", "Kilogramme"),
            ("pcs", "Pièce"),
            ("m2", "Mètre carré"),
            ("m3", "Mètre cube"),
        ],
        default="kg"
    )

    longueur = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, help_text="Longueur en mètres"
    )
    largeur = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, help_text="Largeur en mètres"
    )
    epaisseur = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, help_text="Épaisseur en mm"
    )
    surface = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, help_text="Surface en m²"
    )

    remaining_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_minimum = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    emplacement = models.CharField(max_length=200, blank=True, null=True)

    fournisseur_principal = models.CharField(max_length=200)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=3)
    date_reception = models.DateField()
    ref_fournisseur = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ref} - {self.nom_matiere}"

class MatiereUsage(models.Model):
    SOURCE_CHOICES = [
        ("stock", "Main Stock"),
        ("client", "Client Provided"),
    ]

    achat = models.ForeignKey(MatierePremiereAchat, null=True, blank=True, on_delete=models.SET_NULL)
    
    travaux = models.ForeignKey(
        "Traveaux",
        on_delete=models.CASCADE,
        related_name="matiere_usages",
        help_text="Work",
    )
    matiere = models.ForeignKey(
        Matiere, on_delete=models.CASCADE, related_name="usages", help_text="Material", null=True, blank=True
    )
    quantite_utilisee = models.PositiveIntegerField(
        default=1, help_text="Quantity used in the work"
    )
    source = models.CharField(null=True, choices=SOURCE_CHOICES, help_text="Material usage source, stock or client")
    is_deleted = models.BooleanField(default=False, help_text="Material usage deleted")
    deleted_at = models.DateTimeField(
        null=True, blank=True, help_text="Date when the material usage was deleted"
    )

    # class Meta:
        # unique_together = ("travaux", "matiere")

    def __str__(self):
        name = self.matiere or self.achat
        return f"{name} - {self.quantite_utilisee} units for {self.travaux}"

    # def save(self, *args, **kwargs):
    #     # Check if this is a new instance being created
    #     if not self.pk:
    #         # Update material quantity
    #         if self.source == "client" and self.matiere:
    #             success = self.matiere.update_quantity_after_usage(self.quantite_utilisee)
    #         elif self.source == "stock" and self.achat:
    #             success = self.achat.update_quantity_after_usage(self.quantite_utilisee)
    #         if not success:
    #             from django.core.exceptions import ValidationError

    #             raise ValidationError(
    #                 f"Insufficient quantity available for {self.matiere}. "
    #                 f"Available: {self.matiere.remaining_quantity}, Requested: {self.quantite_utilisee}"
    #             )
    #     super().save(*args, **kwargs)


class Traveaux(models.Model):
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="travaux", help_text="Client"
    )
    produit = models.ForeignKey(
        Produit, on_delete=models.CASCADE, related_name="travaux", help_text="Product"
    )
    matieres = models.ManyToManyField(
        Matiere,
        through=MatiereUsage,
        related_name="travaux",
        help_text="Materials used",
    )
    duree = models.PositiveIntegerField(
        help_text="Duration of the work in hours",
    )
    quantite = models.FloatField(
        default=1, help_text="Quantity of the product used for the work"
    )
    remise_produit = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Discount value applied on this product"
    )
    remise_percent_produit = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Percentage discount on this product"
    )
    description = models.TextField(blank=True, null=True, help_text="Work description")

    date_creation = models.DateTimeField(
        auto_now_add=True, help_text="Date when the work was created"
    )
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, help_text="Date when the work was last updated"
    )
    is_deleted = models.BooleanField(default=False, help_text="Work deleted")
    deleted_at = models.DateTimeField(
        null=True, blank=True, help_text="Date when the work was deleted"
    )
    remise = models.FloatField(
        default=0,
        help_text="Remise appliquée sur le travail (en DT)"
    )
    class Meta:
        indexes = [
            models.Index(fields=["client"]),
            models.Index(fields=["produit"]),
            models.Index(fields=["duree"]),
        ]

    def __str__(self):
        return f"Travail pour {self.client.nom_client} - {self.produit.nom_produit}"


class FactureTravaux(models.Model):
    STATUT_CHOICES = [
        ("draft", "Brouillon"),
        ("sent", "Envoyée"),
        ("paid", "Payée"),
        ("cancelled", "Annulée"),
    ]
    FACTURE_TYPES = (
        ('facture', 'Facture'),
        ('avoir', 'Avoir'),
    )
    
    nature = models.CharField(max_length=10, choices=FACTURE_TYPES, default='facture')

    numero_facture = models.CharField(
        max_length=50, unique=True, help_text="Invoice number"
    )
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="factures", help_text="Client"
    )
    travaux = models.ManyToManyField(
        "Traveaux", related_name="factures", help_text="Work items included in invoice"
    )

    date_emission = models.DateField(help_text="Invoice generation date")
    date_echeance = models.DateField(null=True, blank=True, help_text="Due date")
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="draft",
        help_text="Invoice status",
    )

    tax_rate = models.IntegerField(default=20, help_text="Tax rate percentage")
    timbre_fiscal = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    montant_ht = models.FloatField(
        null=True,
        blank=True,
        help_text="Total amount excluding tax",
    )
    montant_tva = models.FloatField(null=True, blank=True, help_text="Tax amount")
    montant_ttc = models.FloatField(
        null=True,
        blank=True,
        help_text="Total amount including tax",
    )

    date_generated = models.DateTimeField(
        auto_now_add=True, help_text="Date when the invoice was generated"
    )
    notes = models.TextField(
        blank=True, null=True, help_text="Additional notes on the invoice"
    )
    conditions_paiement = models.TextField(
        blank=True, null=True, help_text="Payment terms and conditions"
    )

    date_creation = models.DateTimeField(auto_now_add=True, help_text="Creation date")
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, help_text="Last update date"
    )
    is_deleted = models.BooleanField(default=False, help_text="Invoice deleted")
    deleted_at = models.DateTimeField(
        null=True, blank=True, help_text="Date when the invoice was deleted"
    )

    class Meta:
        ordering = ["-date_emission", "-numero_facture"]
        indexes = [
            models.Index(fields=["numero_facture"]),
            models.Index(fields=["client"]),
            models.Index(fields=["date_emission"]),
            models.Index(fields=["statut"]),
        ]

    def __str__(self):
        return f"Facture {self.numero_facture}"


    def calculate_totals(self):

        if not self.pk:
            self.montant_ht = 0
            self.montant_tva = 0
            self.montant_ttc = 0
            return 0

        total_brut = Decimal("0.0")
        total_remise = Decimal("0.0")
        total_ht = Decimal("0.0")

        for travail in self.travaux.select_related("produit").prefetch_related("matiere_usages__matiere"):

            if travail.produit and travail.produit.prix is not None:
                prix_unitaire = Decimal(travail.produit.prix)
                quantite = Decimal(travail.quantite)
                remise_percent = Decimal(travail.remise_percent_produit or 0)

                line_total_brut = prix_unitaire * quantite
                remise_value = (line_total_brut * remise_percent / Decimal("100")).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                line_total_ht = line_total_brut - remise_value

                total_brut += line_total_brut
                total_remise += remise_value
                total_ht += line_total_ht

            for usage in travail.matiere_usages.all():
                if usage.matiere and usage.matiere.prix_unitaire is not None:
                    pu = Decimal(usage.matiere.prix_unitaire)
                    qte = Decimal(usage.quantite_utilisee)
                    total_ht += pu * qte
        tax_rate = Decimal(self.tax_rate or 0)

        # Facture ou avoir
        if self.nature == 'facture':
            fodec = (total_ht * Decimal('0.01')).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
            timbre = Decimal(getattr(self, 'timbre_fiscal', 0))
        else:
            fodec = 0
            timbre = 0

        self.montant_ht = total_ht
        self.montant_tva = (total_ht + fodec) * (tax_rate / 100)
        self.montant_ttc = total_ht + fodec + self.montant_tva + timbre

        return self.montant_ttc



    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and (self.montant_ht is None):  # Only set to 0 if not provided
            self.montant_ht = 0
            self.montant_tva = 0
            self.montant_ttc = 0

        super().save(*args, **kwargs)  # Save first (generates PK if new)

        if (is_new and self.travaux.exists()) or (
            not is_new and self.montant_ht is None
        ):  # Recalculate if new and travaux exist, or if totals are None
            self.calculate_totals()

            if (
                self.montant_ht is not None
            ):  # Check if calculate_totals actually set something
                super().save(
                    update_fields=[
                        "montant_ht",
                        "montant_tva",
                        "montant_ttc",
                        "derniere_mise_a_jour",
                    ]
                )


class Entreprise(models.Model):
    nom_entreprise = models.CharField(max_length=255, help_text="Nom de l'entreprise")
    numero_fiscal = models.CharField(
        max_length=255, unique=True, help_text="Fiscal registration number"
    )
    adresse = models.CharField(
        max_length=255, blank=True, null=True, help_text="Entreprise address"
    )
    telephone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[validate_phone],
        help_text="Entreprise phone number",
    )
    email = models.EmailField(
        blank=True,
        null=True,
        validators=[validate_email],
        help_text="Entreprise's email",
    )
    site_web = models.URLField(
        blank=True, null=True, help_text="Site web de l'entreprise"
    )
    logo = models.ImageField(
        upload_to="entreprises/",
        blank=True,
        null=True,
        help_text="Logo de l'entreprise",
    )


class FactureMatiere(models.Model):
    """Model for material reception BON DE RECEPTION"""

    numero_bon = models.CharField(max_length=50, unique=True, help_text="Bon number")
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="bons_reception",
        help_text="Client",
    )
    matieres = models.ManyToManyField(
        Matiere, related_name="bons_reception", help_text="Received materials"
    )
    date_reception = models.DateField(help_text="Reception date")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes")

    tax_rate = models.IntegerField(default=20, help_text="Tax rate percentage")
    montant_ht = models.FloatField(
        null=True, blank=True, help_text="Total amount excluding tax"
    )
    montant_tva = models.FloatField(null=True, blank=True, help_text="Tax amount")
    montant_ttc = models.FloatField(
        null=True, blank=True, help_text="Total amount including tax"
    )

    date_creation = models.DateTimeField(auto_now_add=True, help_text="Creation date")
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, help_text="Last update date"
    )
    is_deleted = models.BooleanField(default=False, help_text="BON deleted")
    deleted_at = models.DateTimeField(
        null=True, blank=True, help_text="Date when the BON was deleted"
    )

    class Meta:
        ordering = ["-date_reception"]
        indexes = [
            models.Index(fields=["numero_bon"]),
            models.Index(fields=["client"]),
            models.Index(fields=["date_reception"]),
        ]

    def __str__(self):
        return f"Bon de Livraison {self.numero_bon} - {self.client.nom_client}"

    def calculate_totals(self):
        """Calcul des montants HT, TVA et TTC"""
        if not self.pk:
            return 0

        total_ht = 0
        for matiere in self.matieres.all():
            if matiere.prix_unitaire and matiere.quantite:
                total_ht += float(matiere.prix_unitaire) * matiere.quantite

        self.montant_ht = total_ht
        self.montant_tva = total_ht * (float(self.tax_rate) / 100)
        self.montant_ttc = self.montant_ht + self.montant_tva
        return self.montant_ttc

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new or not self.montant_ht:
            self.calculate_totals()
            if self.montant_ht:
                super().save(*args, **kwargs)


class BonRetour(models.Model):
    """Model for material return BON DE RETOUR"""

    numero_bon = models.CharField(max_length=50, unique=True, help_text="Bon number")
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="bons_retour",
        help_text="Client",
    )
    # matieres = models.ManyToManyField(
    #     Matiere,
    #     through="MatiereRetour",
    #     related_name="bons_retour",
    #     help_text="Returned materials",
    # )

    status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "Brouillon"),
            ("sent", "Envoyée"),
            ("completed", "Complété"),
            ("cancelled", "Annulée"),
        ],
        default="draft",
        help_text="Bon status",
    )

    date_reception = models.DateField(help_text="Reception date")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes")

    date_creation = models.DateTimeField(auto_now_add=True, help_text="Creation date")
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, help_text="Last update date"
    )
    date_retour = models.DateField(help_text="Return date")
    date_emission = models.DateField(auto_now_add=True, help_text="Emission date")
    is_deleted = models.BooleanField(default=False, help_text="BON returned deleted")
    deleted_at = models.DateTimeField(
        null=True, blank=True, help_text="Date when the BON returned was deleted"
    )

    class Meta:
        ordering = ["-date_retour", "-numero_bon"]
        indexes = [
            models.Index(fields=["numero_bon"]),
            models.Index(fields=["client"]),
            models.Index(fields=["date_retour"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Bon Retour {self.numero_bon} - {self.client.nom_client}"

    def save(self, *args, **kwargs):
        # No financial calculations needed on save
        super().save(*args, **kwargs)


class MatiereRetour(models.Model):
    bon_retour = models.ForeignKey(
        "BonRetour", on_delete=models.CASCADE, related_name="matiere_retours"
    )
    matiere = models.ForeignKey( 
        Matiere, on_delete=models.CASCADE, related_name="retours" , null=True , blank=True
    )
    nom_matiere = models.CharField(max_length=255, null=True, blank=True)
    quantite_retournee = models.PositiveIntegerField(
        default=1, help_text="Quantity of material returned"
    )
    is_deleted = models.BooleanField(default=False, help_text="Material returned deleted")
    deleted_at = models.DateTimeField(
        null=True, blank=True, help_text="Date when the material returned was deleted"
    )

    class Meta:
        pass

    def __str__(self):
        return f"{self.quantite_retournee} of {self.matiere.type_matiere} for Bon Retour {self.bon_retour.numero_bon}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class ProduitDevis(models.Model):
    """Through model to connect products with quotes (Devis) with additional information"""

    devis = models.ForeignKey(
        "Devis",
        on_delete=models.CASCADE,
        related_name="produit_devis",
        help_text="Quote",
    )
    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        related_name="devis_produits",
        help_text="Product",
    )
    quantite = models.PositiveIntegerField(default=1, help_text="Product quantity")
    prix_unitaire = models.FloatField(
        help_text="Unit price for this product",
        null=True,
        blank=True,
    )
    remise_pourcentage = models.FloatField(default=0, help_text="Discount percentage")
    prix_total = models.FloatField(
        null=True, blank=True, help_text="Total price for this product entry"
    )
    is_deleted = models.BooleanField(default=False, help_text="Product entry deleted")
    deleted_at = models.DateTimeField(
        null=True, blank=True, help_text="Date when the product entry was deleted"
    )

    class Meta:
        unique_together = ("devis", "produit")

    def __str__(self):
        return f"{self.produit.nom_produit} - {self.quantite} units for {self.devis}"

    def save(self, *args, **kwargs):
        # Auto-calculate price if not specified
        if self.prix_unitaire is None and self.produit.prix is not None:
            self.prix_unitaire = self.produit.prix

        # Calculate total price with discount
        if self.prix_unitaire is not None:
            discount_factor = 1 - (self.remise_pourcentage / 100)
            self.prix_total = self.quantite * self.prix_unitaire * discount_factor

        super().save(*args, **kwargs)

        # Update the devis totals
        self.devis.calculate_totals()
        self.devis.save()


class Devis(models.Model):
    """Model for client quotes (Devis)"""

    STATUT_CHOICES = [
        ("draft", "Brouillon"),
        ("sent", "Envoyé"),
        ("accepted", "Accepté"),
        ("rejected", "Rejeté"),
        ("expired", "Expiré"),
        ("converted", "Converti en commande"),
    ]

    numero_devis = models.CharField(
        max_length=50, unique=True, help_text="Quote number"
    )
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="devis", help_text="Client"
    )
    produits = models.ManyToManyField(
        Produit,
        through=ProduitDevis,
        related_name="devis",
        help_text="Products included in quote",
    )

    date_emission = models.DateField(help_text="Quote issue date")
    date_validite = models.DateField(
        help_text="Quote validity date (15 days after issue)"
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="draft",
        help_text="Quote status",
    )

    tax_rate = models.IntegerField(default=20, help_text="Tax rate percentage")
    montant_ht = models.FloatField(
        null=True,
        blank=True,
        help_text="Total amount excluding tax",
    )
    montant_tva = models.FloatField(null=True, blank=True, help_text="Tax amount")
    montant_ttc = models.FloatField(
        null=True,
        blank=True,
        help_text="Total amount including tax",
    )

    remarques = models.TextField(
        default="Remarques :\n_ Validité du devis : 15 jours.\n_ Ce devis doit être accepté et signé pour valider la commande",
        help_text="Standard remarks on the quote",
    )

    notes = models.TextField(
        blank=True, null=True, help_text="Additional notes on the quote"
    )
    conditions_paiement = models.TextField(
        blank=True, null=True, help_text="Payment terms and conditions"
    )

    date_creation = models.DateTimeField(auto_now_add=True, help_text="Creation date")
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, help_text="Last update date"
    )
    is_deleted = models.BooleanField(default=False, help_text="Quote deleted")
    deleted_at = models.DateTimeField(
        null=True, blank=True, help_text="Date when the quote was deleted"
    )
        # autres champs existants...
    timbre_fiscal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.000,  # valeur par défaut du timbre fiscal en MAD ou autre
        verbose_name="Timbre fiscal"
    )

    class Meta:
        ordering = ["-date_emission", "-numero_devis"]
        indexes = [
            models.Index(fields=["numero_devis"]),
            models.Index(fields=["client"]),
            models.Index(fields=["date_emission"]),
            models.Index(fields=["statut"]),
        ]

    def __str__(self):
        return f"Devis {self.numero_devis} - {self.client.nom_client}"


    def calculate_totals(self):
        print("Calculating totals for Devis ID:", self.pk)
        print("Tax rate:", self.tax_rate)

        if not self.pk:
            self.montant_ht = Decimal("0.0")
            self.montant_tva = Decimal("0.0")
            self.montant_ttc = Decimal("0.0")
            return Decimal("0.0")

        total_ht = Decimal("0.0")

        for item in self.produit_devis.all():
            if item.prix_total is not None:
                total_ht += Decimal(item.prix_total)

        print("Total HT:", total_ht)

        tax_rate = Decimal(self.tax_rate or 0)
        fodec = (total_ht * Decimal("0.01")).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        timbre = Decimal(getattr(self, 'timbre_fiscal', 0))

        montant_tva = ((total_ht + fodec) * tax_rate / Decimal("100")).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        montant_ttc = total_ht + fodec + montant_tva + timbre

        self.montant_ht = total_ht
        self.montant_tva = montant_tva
        self.montant_ttc = montant_ttc
        print(f"FODEC: {fodec}, TVA: {montant_tva}, Timbre: {timbre}, TTC: {montant_ttc}")

        return self.montant_ttc



    def save(self, *args, **kwargs):
        # Set validity date if not set (15 days from emission)
        from datetime import timedelta

        if self.date_emission and not self.date_validite:
            self.date_validite = self.date_emission + timedelta(days=15)

        is_new = self.pk is None
        if is_new and (self.montant_ht is None):
            self.montant_ht = 0
            self.montant_tva = 0
            self.montant_ttc = 0

        super().save(*args, **kwargs)

        # Calculate totals if needed
        if (is_new and self.produits.exists()) or (
            not is_new and self.montant_ht is None
        ):
            self.calculate_totals()
            if self.montant_ht is not None:
                super().save(
                    update_fields=[
                        "montant_ht",
                        "montant_tva",
                        "montant_ttc",
                        "derniere_mise_a_jour",
                    ]
                )

    def convert_to_cd(self):
        if self.statut != "accepted":
            return None

        commande = Cd.objects.create(
            numero_commande=f"FACT-{self.numero_devis}",
            client=self.client,
            devis=self,
            date_commande=self.derniere_mise_a_jour.date(),
            statut="pending",
            tax_rate=self.tax_rate,
            montant_ht=self.montant_ht,
            montant_tva=self.montant_tva,
            montant_ttc=self.montant_ttc,
            notes=self.notes,
            conditions_paiement=self.conditions_paiement,
        )

        # Copy products from devis to commande
        for produit_devis in self.produit_devis.all():
            PdC.objects.create(
                cd=commande,  # Fixed: was 'commande', should be 'cd'
                produit=produit_devis.produit,
                quantite=produit_devis.quantite,
                prix_unitaire=produit_devis.prix_unitaire,
                remise_pourcentage=produit_devis.remise_pourcentage,
                prix_total=produit_devis.prix_total,
            )

        # Update the devis status
        self.statut = "converted"
        self.save(update_fields=["statut", "derniere_mise_a_jour"])

        return commande

    def convert_to_commande(self):
        """Convert this quote to an order if it's accepted"""
        if self.statut != "accepted":
            return None

        commande = Commande.objects.create(
            numero_commande=f"CMD-{self.numero_devis}",
            client=self.client,
            devis=self,
            date_commande=self.derniere_mise_a_jour.date(),
            statut="pending",
            tax_rate=self.tax_rate,
            montant_ht=self.montant_ht,
            montant_tva=self.montant_tva,
            montant_ttc=self.montant_ttc,
            timbre_fiscal=self.timbre_fiscal, 
            notes=self.notes,
            remarques=self.remarques,  
            conditions_paiement=self.conditions_paiement,
        )

        # Copy products from devis to commande
        for produit_devis in self.produit_devis.all():
            ProduitCommande.objects.create(
                commande=commande,
                produit=produit_devis.produit,
                quantite=produit_devis.quantite,
                prix_unitaire=produit_devis.prix_unitaire,
                remise_pourcentage=produit_devis.remise_pourcentage,
                prix_total=produit_devis.prix_total,
            )

        # Update the devis status
        self.statut = "converted"
        self.save(update_fields=["statut", "derniere_mise_a_jour"])

        return commande


class ProduitCommande(models.Model):
    """Through model to connect products with orders (Commande) with additional information"""

    commande = models.ForeignKey(
        "Commande",
        on_delete=models.CASCADE,
        related_name="produit_commande",
        help_text="Order",
    )
    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        related_name="commande_produits",
        help_text="Product",
    )
    quantite = models.PositiveIntegerField(default=1, help_text="Product quantity")
    prix_unitaire = models.FloatField(
        help_text="Unit price for this product",
        null=True,
        blank=True,
    )
    remise_pourcentage = models.FloatField(default=0, help_text="Discount percentage")
    prix_total = models.FloatField(
        null=True, blank=True, help_text="Total price for this product entry"
    )
    is_deleted = models.BooleanField(default=False, help_text="Product entry deleted")
    deleted_at = models.DateTimeField(
        null=True, blank=True, help_text="Date when the product entry was deleted"
    )

    # class Meta:
        # unique_together = ("commande", "produit")

    def __str__(self):
        return f"{self.produit.nom_produit} - {self.quantite} units for {self.commande}"

    def save(self, *args, **kwargs):
        # Auto-calculate price if not specified
        if self.prix_unitaire is None and self.produit.prix is not None:
            self.prix_unitaire = self.produit.prix

        # Calculate total price with discount
        if self.prix_unitaire is not None:
            discount_factor = 1 - (self.remise_pourcentage / 100)
            self.prix_total = self.quantite * self.prix_unitaire * discount_factor

        super().save(*args, **kwargs)

        # Update the commande totals
        self.commande.calculate_totals()
        self.commande.save(update_fields=["montant_ht", "montant_tva", "montant_ttc"])



class Commande(models.Model):
    """Model for client orders (Commandes)"""

    STATUT_CHOICES = [
        ("pending", "En attente"),
        ("processing", "En cours de traitement"),
        ("completed", "Terminée"),
        ("cancelled", "Annulée"),
        ("invoiced", "Facturée"),
    ]

    numero_commande = models.CharField(
        max_length=50, unique=True, help_text="Order number", blank=True
    )
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="commandes", help_text="Client"
    )
    code_client = models.CharField(max_length=20, null=True, blank=True)
    devis = models.OneToOneField(
        Devis,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commande",
        help_text="Associated quote",
    )
    produits = models.ManyToManyField(
        Produit,
        through=ProduitCommande,
        related_name="commandes",
        help_text="Products included in order",
    )

    date_commande = models.DateField(help_text="Order date")
    date_livraison_prevue = models.DateField(
        null=True, blank=True, help_text="Expected delivery date"
    )
    date_livraison_reelle = models.DateField(
        null=True, blank=True, help_text="Actual delivery date"
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="pending",
        help_text="Order status",
    )
    mode_paiement = models.CharField(
        max_length=20,
        choices=[
            ("traite", "Traite"),
            ("cash", "Comptant"),
            ("cheque", "Cheque"),
            ("virement", "Virement"),
            ("carte", "Carte"),
        ],
        default="cash",
        help_text="Payment method",
    )
    type_facture = models.CharField(default="", help_text="Product or Bon invoice")
    tax_rate = models.IntegerField(default=20, help_text="Tax rate percentage")
    montant_ht = models.FloatField(
        null=True,
        blank=True,
        help_text="Total amount excluding tax",
    )
    timbre_fiscal = models.FloatField(null=True, blank=True, help_text="Fiscal stamp")
    montant_tva = models.FloatField(null=True, blank=True, help_text="Tax amount")
    montant_ttc = models.FloatField(
        null=True,
        blank=True,
        help_text="Total amount including tax",
    )

    # facture = models.OneToOneField(
    #     FactureTravaux,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name="commande_associee",
    #     help_text="Associated invoice",
    # )

    notes = models.TextField(
        blank=True, null=True, help_text="Additional notes on the order"
    )
    remarques = models.TextField(
    blank=True,
    null=True,
    help_text="Remarques standard sur la commande"
)

    conditions_paiement = models.TextField(
        blank=True, null=True, help_text="Payment terms and conditions"
    )

    date_creation = models.DateTimeField(auto_now_add=True, help_text="Creation date")
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, help_text="Last update date"
    )
    is_deleted = models.BooleanField(default=False, help_text="Order deleted")
    deleted_at = models.DateTimeField(
        null=True, blank=True, help_text="Date when the order was deleted"
    )

    class Meta:
        ordering = ["-date_commande", "-numero_commande"]
        indexes = [
            models.Index(fields=["numero_commande"]),
            models.Index(fields=["client"]),
            models.Index(fields=["date_commande"]),
            models.Index(fields=["statut"]),
        ]

    def __str__(self):
        return f"Commande {self.numero_commande} - {self.client.nom_client}"

    def calculate_totals(self):
        print("Calculating totals for Commande ID:", self.pk)
        print("Tax rate:", self.tax_rate)

        if not self.pk:
            self.montant_ht = 0
            self.montant_tva = 0
            self.montant_ttc = 0
            return 0

        total_brut = Decimal("0.0")
        total_remise = Decimal("0.0")
        total_ht = Decimal("0.0")

        for item in self.produit_commande.select_related("produit").all():
            prix_unitaire = Decimal(item.prix_unitaire or 0)
            quantite = Decimal(item.quantite or 0)
            remise_percent = Decimal(item.remise_pourcentage or 0)

            line_total_brut = prix_unitaire * quantite
            remise_value = (line_total_brut * remise_percent / Decimal("100")).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
            line_total_ht = line_total_brut - remise_value

            total_brut += line_total_brut
            total_remise += remise_value
            total_ht += line_total_ht

            print(f" - ProduitCommande id {item.id}: PU={prix_unitaire}, QTE={quantite}, Remise%={remise_percent}")
            print(f"   => Brut={line_total_brut}, Remise={remise_value}, HT={line_total_ht}")

        print(f"Total brut: {total_brut}, Total remise: {total_remise}, Total HT: {total_ht}")

        tax_rate = Decimal(self.tax_rate or 0)
        self.montant_ht = total_ht
        self.montant_tva = (total_ht * tax_rate / Decimal("100")).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        self.montant_ttc = (total_ht + self.montant_tva).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

        return self.montant_ttc


    def save(self, *args, **kwargs):
        # Auto-generate numero_commande if not provided
        if not self.numero_commande:
            self.numero_commande = self._generate_numero_commande(self.type_facture, self.nature)

        # Don't calculate or reset totals here — that logic should live outside save()
        super().save(*args, **kwargs)

    def _generate_numero_commande(self, type_facture, nature):
        """Generate next sequential order number, filling gaps if any exist"""
        from datetime import datetime
        current_year = datetime.now().year
        if nature == "facture":
            prefix_type = "FAC-BL" if type_facture == "bon" else "FAC"
        else:
            prefix_type = "AV-BL" if type_facture == "bon" else "AV"
        prefix = f"{prefix_type}-{current_year}-"
        # Find the highest existing number for current year
        existing_commandes = Cd.objects.filter(
            numero_commande__startswith=prefix
        ).order_by("-numero_commande")

        if existing_commandes.exists():
            last_numero = existing_commandes.first().numero_commande
            # Extract the sequential number part
            try:
                last_number = int(last_numero.split("-")[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1

        # Format with 5-digit zero padding
        return f"{prefix}{next_number:05d}"

    def generate_invoice(self):
        """Generate an invoice for this order if it's completed"""
        if self.statut != "completed" or self.facture is not None:
            return None

        facture = FactureTravaux.objects.create(
            numero_facture=f"FAC-{self.numero_commande}",
            client=self.client,
            date_emission=self.derniere_mise_a_jour.date(),
            statut="draft",
            tax_rate=self.tax_rate,
            montant_ht=self.montant_ht,
            montant_tva=self.montant_tva,
            montant_ttc=self.montant_ttc,
            notes=self.notes,
            conditions_paiement=self.conditions_paiement,
        )

        self.facture = facture
        self.statut = "invoiced"
        self.save(update_fields=["facture", "statut", "derniere_mise_a_jour"])

        return facture



# pour les produits
class CommandeProduit(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="commandes_produits",
        help_text="Client",
        null=True,
        blank=True,
    )

    date_creation = models.DateTimeField(
        auto_now_add=True, help_text="Date when the command was created"
    )
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, help_text="Date when the command was last updated"
    )
    montant_ht = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text="Montant hors taxes"
    )

    taux_tva = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=19,  # 20% par défaut
        help_text="Taux de TVA en pourcentage",
    )

    montant_tva = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text="Montant de la TVA"
    )

    montant_ttc = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Montant toutes taxes comprises",
    )
    is_deleted = models.BooleanField(default=False, help_text="Tax deleted")
    deleted_at = models.DateTimeField(
        null=True, blank=True, help_text="Date when the tax was deleted"
    )

    def save(self, *args, **kwargs):
        if not self.montant_ht:
            self.montant_ht = 0

        self.montant_tva = (self.montant_ht * self.taux_tva) / 100
        self.montant_ttc = self.montant_ht + self.montant_tva

        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-date_creation"]
        indexes = [
            models.Index(fields=["client"]),
            models.Index(fields=["date_creation"]),
        ]

    def __str__(self):
        return f"Commande pour {self.client.nom_client}"


class Facture(models.Model):
    commande = models.OneToOneField(
        CommandeProduit,
        on_delete=models.CASCADE,
        related_name="facture",
        help_text="Commande",
    )

    montant_total = models.IntegerField(
        null=True,
        blank=True,
        help_text="Total amount",
    )
    date_creation = models.DateTimeField(
        auto_now_add=True, help_text="Date when the invoice was created"
    )
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, help_text="Date when the invoice was last updated"
    )
    is_deleted = models.BooleanField(default=False, help_text="Invoice deleted")
    deleted_at = models.DateTimeField(
        null=True, blank=True, help_text="Date when the invoice was deleted"
    )


class PlanTraite(models.Model):
    STATUT_CHOICES = [
        ("NON_PAYEE", "Non payée"),
        ("PAYEE", "Payée"),
    ]


    facture = models.OneToOneField(
        'FactureTravaux', on_delete=models.CASCADE, null=True, blank=True
    )
    client = models.ForeignKey(
        "Client", on_delete=models.SET_NULL, null=True, blank=True
    )
    numero_facture = models.CharField(max_length=50, blank=True, null=True)
    nombre_traite = models.PositiveIntegerField()
    date_emission = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUT_CHOICES, default="NON_PAYEE")
    date_premier_echeance = models.DateField(null=True, blank=True)
    periode = models.PositiveIntegerField(null=True, blank=True)
    montant_total = models.FloatField(null=True, blank=True)
    nom_raison_sociale = models.CharField(max_length=255, blank=True, null=True)
    matricule_fiscal = models.CharField(max_length=255, blank=True, null=True)
    mode_paiement = models.CharField(
        max_length=20,
        choices=[
            ("traite", "Traite"),
            ("cash", "Comptant"),
            ("mixte", "Mixte"),
            ("virement", "Virement"),
        ],
        default="traite"
    )
    rip = models.CharField(max_length=40, null=True, blank=True)
    acceptance = models.TextField(null=True, blank=True)
    notice = models.TextField(null=True, blank=True)
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    bank_address = models.TextField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_emission"]
        indexes = [
            models.Index(fields=["facture"]),
            models.Index(fields=["date_emission"]),
            models.Index(fields=["date_premier_echeance"]),
            models.Index(fields=["status"]),
        ]

    def save(self, *args, **kwargs):
        # Calcul automatique du montant si lié à une facture
        if not self.montant_total and self.facture_id:
            self.montant_total = self.facture.montant_ttc

        creating = self.pk is None  # Nouveau plan ?
        super().save(*args, **kwargs)

        if creating:
            self._create_traites()

    def _create_traites(self):
        # Vérifier s'il y a déjà des traites pour ce plan
        if self.traites.exists():
            return  # Ne rien faire si des traites existent déjà
        if self.nombre_traite > 0 and self.date_premier_echeance and self.montant_total:
            montant_par_traite = self.montant_total / self.nombre_traite
            for i in range(self.nombre_traite):
                date_echeance = (
                    self.date_premier_echeance if i == 0 else
                    self.date_premier_echeance + timedelta(days=i * (self.periode or 30))
                )
                Traite.objects.create(
                    plan_traite=self,
                    date_echeance=date_echeance,
                    montant=round(montant_par_traite, 3),
                    status="NON_PAYEE"
                )
    

class Traite(models.Model):
    STATUT_CHOICES = [
        ("NON_PAYEE", "Non payée"),
        ("PAYEE", "Payée"),
    ]

    plan_traite = models.ForeignKey(
        PlanTraite,
        on_delete=models.CASCADE,
        related_name="traites"
    )
    date_echeance = models.DateField(help_text="Date d'échéance")
    status = models.CharField(
        max_length=255,
        choices=STATUT_CHOICES, 
        default="NON_PAYEE"       
    )
    montant = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["-date_echeance"]
        indexes = [
            models.Index(fields=["plan_traite"]),
            models.Index(fields=["date_echeance"]),
            models.Index(fields=["status"]),
        ]


class LineCommande(models.Model):
    commande = models.ForeignKey(
        CommandeProduit,
        on_delete=models.CASCADE,
        related_name="lignes",
        help_text="Commande",
    )
    produit = models.OneToOneField(
        Produit, on_delete=models.CASCADE, related_name="ligne", help_text="Produit"
    )
    prix = models.IntegerField(
        help_text="Product price",
        null=True,
        blank=True,
    )
    quantite = models.PositiveIntegerField(
        default=1, help_text="Quantité"
    )  # starting quantity
    prix_total = models.IntegerField(
        help_text="Total price",
        null=True,
        blank=True,
    )
    date_creation = models.DateTimeField(
        auto_now_add=True, help_text="Date when the command was created"
    )
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, help_text="Date when the command was last updated"
    )

    class Meta:
        ordering = ["-date_creation"]
        indexes = [
            models.Index(fields=["commande"]),
            models.Index(fields=["produit"]),
            models.Index(fields=["prix"]),
            models.Index(fields=["quantite"]),
            models.Index(fields=["prix_total"]),
            models.Index(fields=["date_creation"]),
        ]

    def __str__(self):
        return f"Commande pour {self.client.nom_client} - {self.produit.nom_produit}"

    def save(self, *args, **kwargs):
        self.prix_total = self.prix * self.quantite
        super().save(*args, **kwargs)


class PaymentComptant(models.Model):
    FACTURE_CHOICES = [
        ("NOT_PAID", "Non payée"),
        ("PAID", "Payée"),
    ]
    facture = models.OneToOneField(
        Facture, on_delete=models.CASCADE, help_text="Invoice"
    )
    status = models.CharField(
        max_length=20,
        choices=FACTURE_CHOICES,
        default="NOT_PAID",
        help_text="Payment status",
    )
    date_creation = models.DateTimeField(
        auto_now_add=True, help_text="Date when the payment was created"
    )
    montant = models.IntegerField(
        null=True,
        blank=True,
        help_text="Total amount",
    )

    class Meta:
        ordering = ["-date_creation"]
        indexes = [
            models.Index(fields=["facture"]),
            models.Index(fields=["date_creation"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Paiement pour {self.facture.client.nom_client}"


## make a copy of Models Commande here


class Cd(models.Model):
    """Model for client orders (Commandes)"""

    STATUT_CHOICES = [
        ("pending", "En attente"),
        ("processing", "En cours de traitement"),
        ("completed", "Terminée"),
        ("cancelled", "Annulée"),
        ("invoiced", "Facturée"),
    ]

    FACTURE_TYPES = (
        ('facture', 'Facture'),
        ('avoir', 'Avoir'),
    )
    
    nature = models.CharField(max_length=10, choices=FACTURE_TYPES, default='facture')

    numero_commande = models.CharField(
        max_length=50, unique=True, help_text="Order number"
    )
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="cd", help_text="Client"
    )
    facture = models.OneToOneField(
        FactureTravaux,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commande_associee",
        help_text="Associated invoice",
    )
    devis = models.OneToOneField(
        Devis,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cd",
        help_text="Associated quote",
    )
    produits = models.ManyToManyField(
        Produit,
        through="PdC",
        related_name="cd",
        help_text="Products included in order",
    )

    date_commande = models.DateField(help_text="Order date")
    date_livraison_prevue = models.DateField(
        null=True, blank=True, help_text="Expected delivery date"
    )
    date_livraison_reelle = models.DateField(
        null=True, blank=True, help_text="Actual delivery date"
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="pending",
        help_text="Order status",
    )
    mode_paiement = models.CharField(
        max_length=20,
        choices=[
            ("traite", "Traite"),
            ("cash", "Comptant"),
            ("cheque", "Cheque"),
            ("virement", "Virement"),
            ("carte", "Carte"),
        ],
        default="cash",
        help_text="Payment method",
    )
    type_facture = models.CharField(default="", help_text="Product or Bon invoice")
    tax_rate = models.IntegerField(default=20, help_text="Tax rate percentage")
    montant_ht = models.FloatField(
        null=True,
        blank=True,
        help_text="Total amount excluding tax",
    )
    timbre_fiscal = models.FloatField(null=True, blank=True, help_text="Fiscal stamp")
    montant_tva = models.FloatField(null=True, blank=True, help_text="Tax amount")
    montant_ttc = models.FloatField(
        null=True,
        blank=True,
        help_text="Total amount including tax",
    )
    bons = models.ManyToManyField(
        FactureTravaux,
        blank=True,
        related_name="commandes_associees",
        help_text="Liste des bons liés à cette commande"
    )

    notes = models.TextField(
        blank=True, null=True, help_text="Additional notes on the order"
    )
    conditions_paiement = models.TextField(
        blank=True, null=True, help_text="Payment terms and conditions"
    )

    date_creation = models.DateTimeField(auto_now_add=True, help_text="Creation date")
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, help_text="Last update date"
    )

    class Meta:
        ordering = ["-date_commande", "-numero_commande"]
        indexes = [
            models.Index(fields=["numero_commande"]),
            models.Index(fields=["client"]),
            models.Index(fields=["date_commande"]),
            models.Index(fields=["statut"]),
        ]

    def __str__(self):
        return f"Commande {self.numero_commande} - {self.client.nom_client}"

    def calculate_totals(self):
        """Calculate order totals"""
        if not self.pk:
            # Instance not saved yet
            self.montant_ht = 0
            self.montant_tva = 0
            self.montant_ttc = 0
            return 0

        # Total without tax
        total_ht = sum(
            item.prix_total
            for item in self.produit_commande.all()
            if item.prix_total is not None
        )

        self.montant_ht = total_ht
        # Calculate tax
        tax_rate_float = float(self.tax_rate if self.tax_rate is not None else 0)
        self.montant_tva = total_ht * (tax_rate_float / 100)
        self.montant_ttc = self.montant_ht + self.montant_tva
        return self.montant_ttc

    def save(self, *args, **kwargs):
        # Auto-generate numero_commande if not provided
        if not self.numero_commande:
            self.numero_commande = self._generate_numero_commande(self.type_facture, self.nature)

        is_new = self.pk is None
        if is_new and (self.montant_ht is None):
            self.montant_ht = 0
            self.montant_tva = 0
            self.montant_ttc = 0

        super().save(*args, **kwargs)

        # Calculate totals if needed
        if (is_new and self.produits.exists()) or (
            not is_new and self.montant_ht is None
        ):
            self.calculate_totals()
            if self.montant_ht is not None:
                super().save(
                    update_fields=[
                        "montant_ht",
                        "montant_tva",
                        "montant_ttc",
                        "derniere_mise_a_jour",
                    ]
                )

    def _generate_numero_commande(self, type_facture, nature):
        """Generate next sequential order number for current year (never reuses numbers)"""
        from datetime import datetime
        current_year = datetime.now().year
        if nature == "facture":
            prefix_type = "FAC-BL" if type_facture == "bon" else "FAC"
        else:
            prefix_type = "AV-BL" if type_facture == "bon" else "AV"
        prefix = f"{prefix_type}-{current_year}-"
        # Find the highest existing number for current year
        existing_commandes = Cd.objects.filter(
            numero_commande__startswith=prefix
        ).order_by("-numero_commande")

        if existing_commandes.exists():
            last_numero = existing_commandes.first().numero_commande
            # Extract the sequential number part
            try:
                last_number = int(last_numero.split("-")[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1

        # Format with 5-digit zero padding
        return f"{prefix}{next_number:05d}"

    def generate_invoice(self):
        """Generate an invoice for this order if it's completed"""
        if self.statut != "completed" or self.facture is not None:
            return None

        # Create invoice.
        facture = FactureTravaux.objects.create(
            numero_facture=f"FAC-{self.numero_commande}",
            client=self.client,
            date_emission=self.derniere_mise_a_jour.date(),
            statut="draft",
            tax_rate=self.tax_rate,
            montant_ht=self.montant_ht,
            montant_tva=self.montant_tva,
            montant_ttc=self.montant_ttc,
            notes=self.notes,
            conditions_paiement=self.conditions_paiement,
        )

        # Link the invoice to the order
        self.facture = facture
        self.statut = "invoiced"
        self.save(update_fields=["facture", "statut", "derniere_mise_a_jour"])

        return facture


class PdC(models.Model):
    """Through model to connect products with orders (Commande) with additional information"""

    cd = models.ForeignKey(
        "Cd",
        on_delete=models.CASCADE,
        related_name="produit_commande",
        help_text="Order",
    )
    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        related_name="cd_produits",
        help_text="Product",
    )
    bon_id = models.ForeignKey(FactureTravaux, null=True, blank=True, on_delete=models.SET_NULL, related_name="produits_utilises")
    bon_numero = models.CharField(max_length=100, null=True, blank=True)
    quantite = models.PositiveIntegerField(default=1, help_text="Product quantity")
    prix_unitaire = models.FloatField(
        help_text="Unit price for this product",
        null=True,
        blank=True,
    )
    timbre_fiscal = models.FloatField(
        null=True, blank=True, help_text="Fiscal stamp for this product entry"
    )
    remise_pourcentage = models.FloatField(default=0, help_text="Discount percentage")
    prix_total = models.FloatField(
        null=True, blank=True, help_text="Total price for this product entry"
    )

    # class Meta:
    #     unique_together = ("cd", "produit")

    def __str__(self):
        return f"{self.produit.nom_produit} - {self.quantite} units for {self.cd}"

    def save(self, *args, **kwargs):
        # Auto-calculate price if not specified
        if self.prix_unitaire is None and self.produit.prix is not None:
            self.prix_unitaire = self.produit.prix

        # Calculate total price with discount
        if self.prix_unitaire is not None:
            discount_factor = 1 - (self.remise_pourcentage / 100)
            self.prix_total = self.quantite * self.prix_unitaire * discount_factor

        super().save(*args, **kwargs)

        # Update the cd totals
        self.cd.calculate_totals()
        self.cd.save()


class MatierePurchase(models.Model):
    nom = models.CharField(
        max_length=100,
        blank=True,

    )
    description = models.TextField(
        blank=True, null=True, help_text="Material description"
    )
    prix_unitaire = models.FloatField(
        help_text="Unit price of the material",
        null=True,
        blank=True,
    )
    quantite = models.PositiveIntegerField(
        default=0, help_text="Quantity in stock"
    )  # starting quantity
    
    date_creation = models.DateTimeField(
        auto_now_add=True, help_text="Date when the material was created"
    )
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, help_text="Date when the material was last updated"
    )
    purshase_date = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False, help_text="Material deleted")
    deleted_at = models.DateTimeField(
        null=True, blank=True, help_text="Date when the material was deleted"
    )

    def __str__(self):
        return f"{self.type_matiere} - {self.client.nom_client}"

    # def save(self, *args, **kwargs):
    #     # If this is a new instance or remaining_quantity wasn't explicitly set
    #     if not self.pk or self.remaining_quantity == 0:
    #         self.remaining_quantity = self.quantite
    #     super().save(*args, **kwargs)

class FactureAchatMatiere(models.Model):
    numero = models.CharField(max_length=100, blank=True, null=True)
    fournisseur = models.CharField(max_length=255, blank=True, null=True)

    TYPE_ACHAT_CHOICES = [
        ('matière première', 'matière première'),
        ('consommable', 'consommable'),
        ('autres', 'autres'),
    ]
    mode_paiement = models.CharField(
        max_length=20,
        choices=[
            ("traite", "Traite"),
            ("cash", "Comptant"),
            ("cheque", "Cheque"),
            ("virement", "Virement"),
            ("carte", "Carte"),
        ],
        default="cash",
        help_text="Payment method",
    )
    type_achat = models.CharField(max_length=50, choices=TYPE_ACHAT_CHOICES, blank=True, null=True)

    prix_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    date_facture = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Facture {self.numero or self.id}"


class Achat(models.Model):
    facture = models.ForeignKey(FactureAchatMatiere, on_delete=models.CASCADE, related_name='achats')
    nom = models.CharField(max_length=255)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    quantite = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.nom} x {self.quantite} (Facture {self.facture.numero or self.facture.id})"

from django.db import models

class BonLivraisonMatiere(models.Model):
    numero = models.CharField(max_length=100, blank=True, null=True)
    fournisseur = models.CharField(max_length=255, blank=True, null=True)

    TYPE_ACHAT_CHOICES = [
        ('matière première', 'matière première'),
        ('consommable', 'consommable'),
        ('autres', 'autres'),
    ]
    type_achat = models.CharField(max_length=50, choices=TYPE_ACHAT_CHOICES, blank=True, null=True)

    prix_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    date_livraison = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Bon {self.numero or self.id}"


class Livraison(models.Model):
    bon = models.ForeignKey(BonLivraisonMatiere, on_delete=models.CASCADE, related_name='livraisons')
    nom = models.CharField(max_length=255)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    quantite = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.nom} x {self.quantite} (Bon {self.bon.numero or self.bon.id})"


class Fournisseur(models.Model):
    nom = models.CharField(max_length=255)
    num_reg_fiscal = models.CharField(max_length=100, unique=True)
    adresse = models.CharField(max_length=500)
    telephone = models.CharField(max_length=20)
    infos_complementaires = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nom




class Consommable(models.Model):
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    quantite = models.PositiveIntegerField()
    date_achat = models.DateField()

    def __str__(self):
        return self.nom

from django.db import models
from .models import Fournisseur, Matiere

class BonRetourFournisseur(models.Model):
    numero_bon = models.CharField(max_length=50, unique=True)
    fournisseur = models.ForeignKey(
        Fournisseur,
        on_delete=models.CASCADE,
        related_name="bons_retour_fournisseur",
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "Brouillon"),
            ("sent", "Envoyée"),
            ("completed", "Complété"),
            ("cancelled", "Annulée"),
        ],
        default="draft",
    )
    date_reception = models.DateField()
    date_retour = models.DateField()
    date_emission = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)


class MatiereRetourFournisseur(models.Model):
    bon_retour = models.ForeignKey(
        BonRetourFournisseur,
        on_delete=models.CASCADE,
        related_name="matiere_retours",
    )
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.CASCADE,
        related_name="retours_fournisseur",
        null=True,
        blank=True,
    )
    nom_matiere = models.CharField(max_length=255, null=True, blank=True)
    quantite_retournee = models.PositiveIntegerField(default=1)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)


from datetime import timedelta
from django.db import models


class PlanTraiteFournisseur(models.Model):
    STATUT_CHOICES = [
        ("NON_PAYEE", "Non payée"),
        ("PAYEE", "Payée"),
        ("PARTIELLEMENT_PAYEE", "Partiellement payée"),
    ]

    facture = models.OneToOneField(
        'FactureAchatMatiere', on_delete=models.CASCADE, null=True, blank=True
    )
    fournisseur = models.ForeignKey(
        "Fournisseur", on_delete=models.SET_NULL, null=True, blank=True
    )
    numero_facture = models.CharField(max_length=50, blank=True, null=True)
    nombre_traite = models.PositiveIntegerField()
    date_emission = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUT_CHOICES, default="NON_PAYEE")
    date_premier_echeance = models.DateField(null=True, blank=True)
    periode = models.PositiveIntegerField(null=True, blank=True)
    montant_total = models.FloatField(null=True, blank=True)
    nom_raison_sociale = models.CharField(max_length=255, blank=True, null=True)
    matricule_fiscal = models.CharField(max_length=255, blank=True, null=True)
    mode_paiement = models.CharField(
        max_length=20,
        choices=[
            ("traite", "Traite"),
            ("cash", "Comptant"),
            ("mixte", "Mixte"),
            ("virement", "Virement"),
        ],
        default="traite"
    )
    rip = models.CharField(max_length=40, null=True, blank=True)
    acceptance = models.TextField(null=True, blank=True)
    notice = models.TextField(null=True, blank=True)
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    bank_address = models.TextField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_emission", "date_premier_echeance"]
        indexes = [
            models.Index(fields=["facture"]),
            models.Index(fields=["date_emission"]),
            models.Index(fields=["date_premier_echeance"]),
            models.Index(fields=["status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.montant_total and self.facture_id:
            self.montant_total = float(self.facture.prix_total or 0)

        creating = self.pk is None
        super().save(*args, **kwargs)

        if creating:
            self._create_traites()

    def _create_traites(self):
        # Vérifier s'il y a déjà des traites pour ce plan
        if self.traites.exists():
            return  # Ne rien faire si des traites existent déjà
        if self.nombre_traite > 0 and self.date_premier_echeance and self.montant_total:
            montant_par_traite = self.montant_total / self.nombre_traite
            for i in range(self.nombre_traite):
                date_echeance = (
                    self.date_premier_echeance if i == 0 else
                    self.date_premier_echeance + timedelta(days=i * (self.periode or 30))
                )
                TraiteFournisseur.objects.create(
                    plan_traite=self,
                    date_echeance=date_echeance,
                    montant=round(montant_par_traite, 3),
                    status="NON_PAYEE"
                )


class TraiteFournisseur(models.Model):
    STATUT_CHOICES = [
        ("NON_PAYEE", "Non payée"),
        ("PAYEE", "Payée"),
        ("PARTIELLEMENT_PAYEE", "Partiellement payée"),
    ]

    plan_traite = models.ForeignKey(
        PlanTraiteFournisseur,
        on_delete=models.CASCADE,
        related_name="traites"
    )
    date_echeance = models.DateField(help_text="Date d'échéance")
    status = models.CharField(
        max_length=255,
        choices=STATUT_CHOICES,
        default="NON_PAYEE"
    )
    montant = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["-date_echeance"]
        indexes = [
            models.Index(fields=["plan_traite"]),
            models.Index(fields=["date_echeance"]),
            models.Index(fields=["status"]),
        ]


from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db import models

class Employe(models.Model):
    id_employe = models.CharField(max_length=100, unique=True)
    nom = models.CharField(max_length=255)
    cin = models.CharField(max_length=50, blank=True, null=True)
    telephone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    date_naissance = models.DateField(blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)

    # ✅ Nouveaux champs
    numero_cnss = models.CharField(max_length=50, blank=True, null=True)
    situation_familiale = models.CharField(max_length=50, blank=True, null=True)
    enfants_a_charge = models.IntegerField(blank=True, null=True)
    nombre_enfants = models.IntegerField(blank=True, null=True)
    categorie = models.CharField(max_length=50, blank=True, null=True)

    # Infos pro
    poste = models.CharField(max_length=100, blank=True, null=True)
    departement = models.CharField(max_length=100, blank=True, null=True)
    date_embauche = models.DateField(blank=True, null=True)
    statut = models.CharField(max_length=50, blank=True, null=True)
    code_contrat = models.CharField(max_length=50, blank=True, null=True)
    type_contrat = models.CharField(max_length=50, blank=True, null=True)
    responsable = models.CharField(max_length=255, blank=True, null=True)
    salaire = models.FloatField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom

class Avance(models.Model):
    STATUT_CHOICES = (
        ('En attente', 'En attente'),
        ('Acceptée', 'Acceptée'),
        ('Refusée', 'Refusée'),
    )

    employee = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='avances')
    montant = models.FloatField()
    date_demande = models.DateField(default=timezone.now)
    motif = models.TextField()
    nbr_mensualite = models.IntegerField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='En attente')

    def mensualite(self):
        if self.nbr_mensualite:
            return round(self.montant / self.nbr_mensualite, 2)
        return 0

    def progression(self):
        if self.statut != 'Acceptée':
            return 0
        rembourse = Remboursement.objects.filter(avance=self).aggregate(total=models.Sum('montant'))['total'] or 0
        return min(100, round((rembourse / self.montant) * 100, 1)) if self.montant else 0

    def reste(self):
        rembourse = Remboursement.objects.filter(avance=self).aggregate(total=models.Sum('montant'))['total'] or 0
        return round(self.montant - rembourse, 2)

    def __str__(self):
        return f"Avance - {self.employee} - {self.montant} DH"
        

class Remboursement(models.Model):
    avance = models.ForeignKey(Avance, on_delete=models.CASCADE, related_name='remboursements')
    date = models.DateField(default=timezone.now)
    montant = models.FloatField()


class FichePaie(models.Model):
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='fiches_paie')
    avance_deduite = models.FloatField(default=0)
    mois = models.IntegerField()
    annee = models.IntegerField()
    salaire_base = models.FloatField()
    prime_anciennete = models.FloatField(default=0)
    indemnite_presence = models.FloatField(default=0)
    indemnite_transport = models.FloatField(default=0)
    prime_langue = models.FloatField(default=0)
    jours_feries_payes = models.FloatField(default=0)
    absences_non_remunerees = models.FloatField(default=0)
    prime_ramadan = models.FloatField(default=0)
    prime_teletravail = models.FloatField(default=0)
    avantage_assurance = models.FloatField(default=0)
    conge_precedent = models.FloatField(default=0)
    conge_acquis = models.FloatField(default=0)
    conge_pris = models.FloatField(default=0)
    conge_restant = models.FloatField(default=0)
    conge_speciaux = models.FloatField(default=0)
    conge_maladie_m = models.FloatField(default=0)
    conge_maladie_a = models.FloatField(default=0)
    banque = models.CharField(max_length=100, null=True, blank=True)
    rib = models.CharField(max_length=100, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=50, default='Générée')

    # Calculs (déjà calculés en front, mais prévues ici pour cohérence)
    salaire_brut = models.FloatField(default=0)
    salaire_imposable = models.FloatField(default=0)
    cnss_salarie = models.FloatField(default=0)
    irpp = models.FloatField(default=0)
    css = models.FloatField(default=0)
    deduction_totale = models.FloatField(default=0)
    cnss_patronal = models.FloatField(default=0)
    accident_travail = models.FloatField(default=0)
    charges_patronales = models.FloatField(default=0)
    net_a_payer = models.FloatField(default=0)