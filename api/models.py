from datetime import timedelta
from django.db import models
import re


def validate_email(value):
    from django.core.exceptions import ValidationError

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, value):
        raise ValidationError("Format d'email invalide")


def validate_phone(value):
    from django.core.exceptions import ValidationError

    if not value.isdigit():
        raise ValidationError("Le numéro doit contenir uniquement des chiffres")


class Client(models.Model):
    nom_client = models.CharField(max_length=255, help_text="Client name")
    numero_fiscal = models.CharField(
        max_length=255, unique=True, help_text="Fiscal registration number"
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

    class Meta:
        ordering = ["nom_client"]
        indexes = [
            models.Index(fields=["nom_client"]),
            models.Index(fields=["numero_fiscal"]),
        ]

    def __str__(self):
        return self.nom_client


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
    description = models.TextField(
        blank=True, null=True, help_text="Material description"
    )
    reception_date = models.DateField(
        help_text="Date of material reception",
        null=True,
        blank=True,
    )
    thickness = models.IntegerField(
        help_text="Thickness of the material in mm",
        null=True,
        blank=True,
    )
    length = models.IntegerField(
        help_text="Length of the material in mm",
        null=True,
        blank=True,
    )
    width = models.IntegerField(
        help_text="Width of the material in mm",
        null=True,
        blank=True,
    )
    surface = models.IntegerField(
        help_text="Surface area of the material in m²",
        null=True,
        blank=True,
    )
    prix_unitaire = models.FloatField(
        help_text="Unit price of the material",
        null=True,
        blank=True,
    )
    quantite = models.PositiveIntegerField(
        default=0, help_text="Quantity in stock"
    )  # starting quantity
    remaining_quantity = models.PositiveIntegerField(
        default=0, help_text="Remaining quantity after work"
    )
    date_creation = models.DateTimeField(
        auto_now_add=True, help_text="Date when the material was created"
    )
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, help_text="Date when the material was last updated"
    )

    def __str__(self):
        return f"{self.type_matiere} - {self.client.nom_client}"

    def save(self, *args, **kwargs):
        # If this is a new instance or remaining_quantity wasn't explicitly set
        if not self.pk or self.remaining_quantity == 0:
            self.remaining_quantity = self.quantite
        super().save(*args, **kwargs)

    def update_quantity_after_usage(self, amount_used):
        """Update quantity after usage in a work"""
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
    epaisseur = models.IntegerField(
        help_text="Thickness of the product in mm",
        null=True,
        blank=True,
    )
    longueur = models.IntegerField(
        help_text="Length of the product in mm",
        null=True,
        blank=True,
    )
    largeur = models.IntegerField(  # Added field
        help_text="Width of the product in mm",
        null=True,
        blank=True,
    )
    surface = models.IntegerField(
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

    class Meta:
        ordering = ["nom_produit"]
        indexes = [
            models.Index(fields=["nom_produit"]),
            models.Index(fields=["prix"]),
        ]

    def __str__(self):
        return self.nom_produit


class MatiereUsage(models.Model):
    travaux = models.ForeignKey(
        "Traveaux",
        on_delete=models.CASCADE,
        related_name="matiere_usages",
        help_text="Work",
    )
    matiere = models.ForeignKey(
        Matiere, on_delete=models.CASCADE, related_name="usages", help_text="Material"
    )
    quantite_utilisee = models.PositiveIntegerField(
        default=1, help_text="Quantity used in the work"
    )

    class Meta:
        unique_together = ("travaux", "matiere")

    def __str__(self):
        return f"{self.matiere} - {self.quantite_utilisee} units for {self.travaux}"

    def save(self, *args, **kwargs):
        # Check if this is a new instance being created
        if not self.pk:
            # Update material quantity
            success = self.matiere.update_quantity_after_usage(self.quantite_utilisee)
            if not success:
                from django.core.exceptions import ValidationError

                raise ValidationError(
                    f"Insufficient quantity available for {self.matiere}. "
                    f"Available: {self.matiere.remaining_quantity}, Requested: {self.quantite_utilisee}"
                )
        super().save(*args, **kwargs)


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
    description = models.TextField(blank=True, null=True, help_text="Work description")

    date_creation = models.DateTimeField(
        auto_now_add=True, help_text="Date when the work was created"
    )
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, help_text="Date when the work was last updated"
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
        """Calculate invoice totals"""
        if not self.pk:
            # Instance not saved yet, or no travaux linked.
            self.montant_ht = 0
            self.montant_tva = 0
            self.montant_ttc = 0
            return 0

        total_ht = 0
        # Use select_related to ensure we get fresh product data
        for travail in self.travaux.select_related("produit").all():
            # Add product costs
            if travail.produit and travail.produit.prix is not None:
                total_ht += float(travail.produit.prix) * travail.quantite

            # Add material costs if they exist
            for usage in travail.matiere_usages.select_related("matiere").all():
                if usage.matiere and usage.matiere.prix_unitaire is not None:
                    total_ht += (
                        float(usage.matiere.prix_unitaire) * usage.quantite_utilisee
                    )

        self.montant_ht = total_ht
        # Ensure tax_rate is a float for calculation
        tax_rate_float = float(self.tax_rate if self.tax_rate is not None else 0)
        self.montant_tva = total_ht * (tax_rate_float / 100)
        self.montant_ttc = self.montant_ht + self.montant_tva
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
    matieres = models.ManyToManyField(
        Matiere,
        through="MatiereRetour",
        related_name="bons_retour",
        help_text="Returned materials",
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
        Matiere, on_delete=models.CASCADE, related_name="retours"
    )
    quantite_retournee = models.PositiveIntegerField(
        default=1, help_text="Quantity of material returned"
    )

    class Meta:
        unique_together = ("bon_retour", "matiere")

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
        """Calculate quote totals"""
        if not self.pk:
            # Instance not saved yet
            self.montant_ht = 0
            self.montant_tva = 0
            self.montant_ttc = 0
            return 0

        # Total without tax
        total_ht = sum(
            item.prix_total
            for item in self.produit_devis.all()
            if item.prix_total is not None
        )

        self.montant_ht = total_ht
        # Calculate tax
        tax_rate_float = float(self.tax_rate if self.tax_rate is not None else 0)
        self.montant_tva = total_ht * (tax_rate_float / 100)
        self.montant_ttc = self.montant_ht + self.montant_tva
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
            notes=self.notes,
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

    class Meta:
        unique_together = ("commande", "produit")

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
        self.commande.save()


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
        max_length=50, unique=True, help_text="Order number"
    )
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="commandes", help_text="Client"
    )
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

    facture = models.OneToOneField(
        FactureTravaux,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commande_associee",
        help_text="Associated invoice",
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

    def generate_invoice(self):
        """Generate an invoice for this order if it's completed"""
        if self.statut != "completed" or self.facture is not None:
            return None

        # Create invoice
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


class PlanTraite(models.Model):
    STATUT_CHOICES = [
        ("EN_COURS", "En cours"),
        ("PAYEE", "payée"),
    ]

    facture = models.OneToOneField(
        Facture, on_delete=models.CASCADE, help_text="Invoice"
    )
    nombre_traite = models.PositiveIntegerField(help_text="Number of traitements")
    date_emission = models.DateField(
        auto_now_add=True, help_text="Invoice generation date"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="EN_COURS",
        help_text="Traite status",
    )

    date_premier_echeance = models.DateField(
        null=True, blank=True, help_text="Date of the first installment"
    )

    periode = models.PositiveIntegerField(
        null=True, blank=True, help_text="Period between each milking"
    )

    montant_total = models.FloatField(
        null=True,
        blank=True,
        help_text="Total amount",
    )
    nom_raison_sociale = models.CharField(
        max_length=255, blank=True, null=True, help_text="Nom de la raison sociale"
    )
    matricule_fiscal = models.CharField(
        max_length=255, blank=True, null=True, help_text="Matricule fiscal"
    )
    mode_paiement = models.CharField(
        max_length=20,
        choices=[
            ("traite", "Traite"),
            ("cash", "Comptant"),
            ("mixte", "Mixte"),
            ("virement", "Virement"),
        ],
        default="traite",
        help_text="Payment method for the installment plan",
    )

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
            self.montant_total = self.facture.montant_ttc

        if not hasattr(self, "_traites_created") and self.pk:
            self._create_traites()

        super().save(*args, **kwargs)

    def _create_traites(self):
        if self.nombre_traite > 0 and self.date_premier_echeance and self.montant_total:
            montant_par_traite = self.montant_total / self.nombre_traite

            for i in range(self.nombre_traite):
                if i == 0:
                    date_echeance = self.date_premier_echeance
                else:
                    date_echeance = self.date_premier_echeance + timedelta(
                        days=i * (self.periode or 30)
                    )
                Traite.objects.create(
                    plan_traite=self,
                    date_echeance=self.date_echeance,
                    montant=montant_par_traite,
                    status="NON_PAYEE",
                )

            self._traites_created = True


class Traite(models.Model):
    STATUT_CHOICES = [("NON_PAYEE", "Non payée"), ("PAYEE", "Payée")]

    plan_traite = models.ForeignKey(
        PlanTraite, on_delete=models.CASCADE, related_name="traites", help_text="Traite"
    )
    date_echeance = models.DateField(
        auto_now_add=True, help_text="Invoice generation date"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="NON_PAYEE",
        help_text="Traite status",
    )

    montant = models.FloatField(
        null=True,
        blank=True,
        help_text="Total amount",
    )

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

    numero_commande = models.CharField(
        max_length=50, unique=True, help_text="Order number"
    )
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="cd", help_text="Client"
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
            ("mixte", "Mixte"),
            ("virement", "Virement"),
        ],
        default="cash",
        help_text="Payment method",
    )
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

    facture = models.OneToOneField(
        FactureTravaux,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cd_associee",
        help_text="Associated invoice",
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

    def generate_invoice(self):
        """Generate an invoice for this order if it's completed"""
        if self.statut != "completed" or self.facture is not None:
            return None

        # Create invoice
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

    class Meta:
        unique_together = ("cd", "produit")

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