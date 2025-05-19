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
    epaisser = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Thickness of the material in mm",
        null=True,
        blank=True,
    )
    longueur = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Length of the material in mm",
        null=True,
        blank=True,
    )
    surface = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Surface area of the material in m²",
        null=True,
        blank=True,
    )
    prix_unitaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
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
    prix = models.DecimalField(
        max_digits=10,
        decimal_places=2,
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
    epaisseur = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Thickness of the product in mm",
        null=True,
        blank=True,
    )
    longueur = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Length of the product in mm",
        null=True,
        blank=True,
    )
    surface = models.DecimalField(
        max_digits=10,
        decimal_places=2,
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
