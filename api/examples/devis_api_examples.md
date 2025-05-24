# Devis API - Example Requests

This document provides examples of JSON requests and responses for the Devis (Quote) API endpoints.

## Create a new Devis

**Endpoint:** `POST /api/devis/`

**Request Body:**

```json
{
  "client": 1,
  "date_emission": "2023-11-15",
  "date_validite": "2023-12-15",
  "statut": "draft",
  "tax_rate": 20.0,
  "remarques": "Devis pour projet d'aménagement bureau",
  "notes": "Client prioritaire",
  "conditions_paiement": "Paiement sous 30 jours",
  "produits": [
    {
      "produit": 1,
      "quantite": 5,
      "prix_unitaire": 125.5,
      "remise_pourcentage": 10
    },
    {
      "produit": 2,
      "quantite": 2,
      "prix_unitaire": 75.0
    }
  ]
}
```

**Response:**

```json
{
  "id": 42,
  "numero_devis": "DEV-2023-042",
  "client": 1,
  "nom_client": "Entreprise ABC",
  "produits": [],
  "produit_devis": [
    {
      "id": 67,
      "produit": 1,
      "nom_produit": "Plaque Acrylique 5mm",
      "quantite": 5,
      "prix_unitaire": 125.5,
      "remise_pourcentage": 10,
      "prix_total": 564.75
    },
    {
      "id": 68,
      "produit": 2,
      "nom_produit": "Support Métal",
      "quantite": 2,
      "prix_unitaire": 75.0,
      "remise_pourcentage": 0,
      "prix_total": 150.0
    }
  ],
  "date_emission": "2023-11-15",
  "date_validite": "2023-12-15",
  "statut": "draft",
  "tax_rate": 20.0,
  "montant_ht": 714.75,
  "montant_tva": 142.95,
  "montant_ttc": 857.7,
  "remarques": "Devis pour projet d'aménagement bureau",
  "notes": "Client prioritaire",
  "conditions_paiement": "Paiement sous 30 jours",
  "date_creation": "2023-11-15T10:30:45.123456Z",
  "derniere_mise_a_jour": "2023-11-15T10:30:45.123456Z"
}
```

## Update an existing Devis

**Endpoint:** `PUT /api/devis/{id}/`

**Request Body:**

```json
{
  "client": 1,
  "date_emission": "2023-11-15",
  "date_validite": "2023-12-31",
  "statut": "pending",
  "tax_rate": 20.0,
  "remarques": "Devis mis à jour pour projet d'aménagement bureau",
  "notes": "Client prioritaire - Offre spéciale fin d'année",
  "conditions_paiement": "Paiement sous 45 jours"
}
```

## Add a product to Devis

**Endpoint:** `POST /api/devis/{id}/add_product/`

**Request Body:**

```json
{
  "produit": 3,
  "quantite": 10,
  "prix_unitaire": 45.75,
  "remise_pourcentage": 5
}
```

**Response:**

```json
{
  "id": 69,
  "produit": 3,
  "nom_produit": "Gravure Personnalisée",
  "quantite": 10,
  "prix_unitaire": 45.75,
  "remise_pourcentage": 5,
  "prix_total": 434.63
}
```

## Remove a product from Devis

**Endpoint:** `DELETE /api/devis/{id}/remove_product/`

**Request Body:**

```json
{
  "produit": 2
}
```

**Response:** 204 No Content

## Convert Devis to Commande

**Endpoint:** `POST /api/devis/{id}/convert_to_commande/`

**Request Body:**

```json
{
  "confirmation": true
}
```

**Response:**

```json
{
  "id": 36,
  "numero_commande": "CMD-2023-036",
  "devis": 42,
  "client": 1,
  "nom_client": "Entreprise ABC",
  "statut": "in_progress",
  "date_commande": "2023-11-15",
  "produit_commande": [
    {
      "id": 87,
      "produit": 1,
      "nom_produit": "Plaque Acrylique 5mm",
      "quantite": 5,
      "prix_unitaire": 125.5,
      "remise_pourcentage": 10,
      "prix_total": 564.75
    },
    {
      "id": 88,
      "produit": 3,
      "nom_produit": "Gravure Personnalisée",
      "quantite": 10,
      "prix_unitaire": 45.75,
      "remise_pourcentage": 5,
      "prix_total": 434.63
    }
  ],
  "montant_ht": 999.38,
  "montant_tva": 199.88,
  "montant_ttc": 1199.26,
  "date_livraison_prevue": null,
  "adresse_livraison": "",
  "instructions_speciales": "",
  "date_creation": "2023-11-15T14:25:30.123456Z",
  "derniere_mise_a_jour": "2023-11-15T14:25:30.123456Z"
}
```

## Get Devis by Client

**Endpoint:** `GET /api/devis/by_client/?client_id=1`

**Response:**

```json
[
  {
    "id": 42,
    "numero_devis": "DEV-2023-042",
    "client": 1,
    "nom_client": "Entreprise ABC",
    "date_emission": "2023-11-15",
    "date_validite": "2023-12-15",
    "statut": "accepted",
    "montant_ht": 999.38,
    "montant_tva": 199.88,
    "montant_ttc": 1199.26
  },
  {
    "id": 41,
    "numero_devis": "DEV-2023-041",
    "client": 1,
    "nom_client": "Entreprise ABC",
    "date_emission": "2023-10-20",
    "date_validite": "2023-11-20",
    "statut": "completed",
    "montant_ht": 1250.0,
    "montant_tva": 250.0,
    "montant_ttc": 1500.0
  }
]
```

## Get a single Devis details

**Endpoint:** `GET /api/devis/{id}/`

**Response:**

```json
{
  "id": 42,
  "numero_devis": "DEV-2023-042",
  "client": 1,
  "nom_client": "Entreprise ABC",
  "produits": [],
  "produit_devis": [
    {
      "id": 67,
      "produit": 1,
      "nom_produit": "Plaque Acrylique 5mm",
      "quantite": 5,
      "prix_unitaire": 125.5,
      "remise_pourcentage": 10,
      "prix_total": 564.75
    },
    {
      "id": 69,
      "produit": 3,
      "nom_produit": "Gravure Personnalisée",
      "quantite": 10,
      "prix_unitaire": 45.75,
      "remise_pourcentage": 5,
      "prix_total": 434.63
    }
  ],
  "produits_details": [
    {
      "id": 1,
      "nom_produit": "Plaque Acrylique 5mm",
      "prix": 125.5,
      "type_matiere": "acrylique"
    },
    {
      "id": 2,
      "nom_produit": "Support Métal",
      "prix": 75.0,
      "type_matiere": "metal"
    },
    {
      "id": 3,
      "nom_produit": "Gravure Personnalisée",
      "prix": 45.75,
      "type_matiere": "service"
    }
  ],
  "date_emission": "2023-11-15",
  "date_validite": "2023-12-15",
  "statut": "accepted",
  "tax_rate": 20.0,
  "montant_ht": 999.38,
  "montant_tva": 199.88,
  "montant_ttc": 1199.26,
  "remarques": "Devis pour projet d'aménagement bureau",
  "notes": "Client prioritaire",
  "conditions_paiement": "Paiement sous 30 jours",
  "date_creation": "2023-11-15T10:30:45.123456Z",
  "derniere_mise_a_jour": "2023-11-15T14:15:22.123456Z"
}
```

## List all Devis

**Endpoint:** `GET /api/devis/`

**Response:**

```json
[
  {
    "id": 42,
    "numero_devis": "DEV-2023-042",
    "client": 1,
    "nom_client": "Entreprise ABC",
    "date_emission": "2023-11-15",
    "date_validite": "2023-12-15",
    "statut": "accepted",
    "montant_ht": 999.38,
    "montant_tva": 199.88,
    "montant_ttc": 1199.26
  },
  {
    "id": 43,
    "numero_devis": "DEV-2023-043",
    "client": 2,
    "nom_client": "Studio Design XYZ",
    "date_emission": "2023-11-18",
    "date_validite": "2023-12-18",
    "statut": "pending",
    "montant_ht": 1750.0,
    "montant_tva": 350.0,
    "montant_ttc": 2100.0
  },
  {
    "id": 41,
    "numero_devis": "DEV-2023-041",
    "client": 1,
    "nom_client": "Entreprise ABC",
    "date_emission": "2023-10-20",
    "date_validite": "2023-11-20",
    "statut": "completed",
    "montant_ht": 1250.0,
    "montant_tva": 250.0,
    "montant_ttc": 1500.0
  }
]
```

**Query Parameters:**

| Parameter | Type    | Description                                                             |
| --------- | ------- | ----------------------------------------------------------------------- |
| client    | integer | Filter quotes by client ID                                              |
| statut    | string  | Filter quotes by status (draft, pending, accepted, rejected, completed) |
| date_from | date    | Filter quotes with emission date greater than or equal to this date     |
| date_to   | date    | Filter quotes with emission date less than or equal to this date        |

**Example with filters:** `GET /api/devis/?client=1&statut=pending&date_from=2023-10-01`
