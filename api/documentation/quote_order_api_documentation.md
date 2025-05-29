# Quote and Order API Documentation

This document provides comprehensive documentation for the Quote (Devis) and Order (Commande) API endpoints in our laser cutting business application.

## Table of Contents

1. [Introduction](#introduction)
2. [Quotes (Devis)](#quotes-devis)
   - [Quote Model Structure](#quote-model-structure)
   - [API Endpoints](#quote-api-endpoints)
   - [Usage Examples](#quote-usage-examples)
3. [Orders (Commandes)](#orders-commandes)
   - [Order Model Structure](#order-model-structure)
   - [API Endpoints](#order-api-endpoints)
   - [Usage Examples](#order-usage-examples)
4. [Workflow Integration](#workflow-integration)

## Introduction

Our API provides functionality to manage quotes (devis) and orders (commandes) for our laser cutting business. Both modules are tightly integrated:

- Quotes are created first and can be converted to orders when accepted
- Orders can generate invoices when completed
- Both quotes and orders have products associated with them
- The system automatically calculates totals, tax, and handles price modifications

## Quotes (Devis)

### Quote Model Structure

A quote (devis) represents a price proposal for a client and includes:

- Basic information (quote number, client, dates, status)
- Products with quantities, unit prices, and discounts
- Financial calculations (total excluding tax, tax amount, total including tax)
- Additional details (notes, payment terms)

**Quote Statuses:**

- `draft`: Initial state
- `sent`: Quote sent to client
- `accepted`: Client has accepted the quote
- `rejected`: Client has rejected the quote
- `expired`: Quote validity period has passed
- `converted`: Quote has been converted to an order

### Quote API Endpoints

#### List all quotes

```
GET /api/devis/
```

Returns a simplified representation of all quotes.

**Response:**

```json
[
  {
    "id": 1,
    "numero_devis": "DEV-2025-001",
    "client": 5,
    "nom_client": "Client Name",
    "date_emission": "2025-05-01",
    "date_validite": "2025-05-16",
    "statut": "draft",
    "montant_ht": 1250.0,
    "montant_tva": 250.0,
    "montant_ttc": 1500.0
  },
  ...
]
```

#### Get a specific quote

```
GET /api/devis/{id}/
```

Returns detailed information about a specific quote, including products.

**Response:**

```json
{
  "id": 1,
  "numero_devis": "DEV-2025-001",
  "client": 5,
  "nom_client": "Client Name",
  "produits": [1, 3],
  "produit_devis": [
    {
      "id": 1,
      "produit": 1,
      "nom_produit": "Product 1",
      "quantite": 5,
      "prix_unitaire": 200.0,
      "remise_pourcentage": 0,
      "prix_total": 1000.0
    },
    {
      "id": 2,
      "produit": 3,
      "nom_produit": "Product 3",
      "quantite": 2,
      "prix_unitaire": 125.0,
      "remise_pourcentage": 0,
      "prix_total": 250.0
    }
  ],
  "produits_details": [...],  // Available products for adding to quote
  "date_emission": "2025-05-01",
  "date_validite": "2025-05-16",
  "statut": "draft",
  "tax_rate": 20,
  "montant_ht": 1250.0,
  "montant_tva": 250.0,
  "montant_ttc": 1500.0,
  "remarques": "Remarques :\n_ Validité du devis : 15 jours.\n_ Ce devis doit être accepté et signé pour valider la commande",
  "notes": null,
  "conditions_paiement": "50% à la commande, 50% à la livraison",
  "date_creation": "2025-05-01T10:30:00Z",
  "derniere_mise_a_jour": "2025-05-01T10:30:00Z"
}
```

#### Create a new quote

```
POST /api/devis/
```

**Request Body:**

```json
{
  "numero_devis": "DEV-2025-002",
  "client": 5,
  "date_emission": "2025-05-15",
  "statut": "draft",
  "tax_rate": 20,
  "notes": "Special requirements for this quote",
  "conditions_paiement": "50% à la commande, 50% à la livraison",
  "produits": [
    {
      "produit": 1,
      "quantite": 5,
      "prix_unitaire": 200.0
    },
    {
      "produit": 3,
      "quantite": 2,
      "prix_unitaire": 125.0
    }
  ]
}
```

**Notes:**

- The `date_validite` (validity date) will automatically be set to 15 days after `date_emission` if not provided
- The system automatically calculates totals (HT, TVA, TTC) based on the products

#### Update a quote

```
PUT /api/devis/{id}/
PATCH /api/devis/{id}/
```

Same structure as the create endpoint. Use PUT for complete replacement, PATCH for partial updates.

#### Delete a quote

```
DELETE /api/devis/{id}/
```

#### Add a product to a quote

```
POST /api/devis/{id}/add_product/
```

**Request Body:**

```json
{
  "produit": 2,
  "quantite": 3,
  "prix_unitaire": 150.0,
  "remise_pourcentage": 10
}
```

**Response:** The newly added or updated product with its calculated total.

#### Remove a product from a quote

```
DELETE /api/devis/{id}/remove_product/
```

**Request Body:**

```json
{
  "produit": 2
}
```

#### Convert a quote to an order

```
POST /api/devis/{id}/convert_to_commande/
```

**Request Body:**

```json
{
  "confirmation": true
}
```

**Response:** The newly created order details.

**Notes:**

- This endpoint is only available for quotes with `accepted` status
- A new order will be created with all the quote's products, financial details, and notes
- The quote status will be changed to `converted`

#### Get quotes by client

```
GET /api/devis/by_client/?client_id={client_id}
```

**Response:** List of quotes for the specified client.

### Quote Usage Examples

#### Typical Workflow:

1. Create a quote (status: `draft`)
2. Update quote details and add products
3. Change status to `sent` when sent to the client
4. Update status to `accepted` when the client approves
5. Convert the quote to an order

#### Adding Products:

```javascript
// Example: Adding a product to an existing quote
const addProductToQuote = async (quoteId, productData) => {
  try {
    const response = await axios.post(
      `/api/devis/${quoteId}/add_product/`,
      productData,
      { headers: { Authorization: `Token ${authToken}` } }
    );
    return response.data;
  } catch (error) {
    console.error("Error adding product to quote:", error);
    throw error;
  }
};

// Usage
addProductToQuote(1, {
  produit: 5,
  quantite: 10,
  prix_unitaire: 75.0,
  remise_pourcentage: 5,
});
```

## Orders (Commandes)

### Order Model Structure

An order (commande) represents a confirmed job for our laser cutting business and includes:

- Basic information (order number, client, dates, status)
- Products with quantities, unit prices, and discounts
- Financial calculations (total excluding tax, tax amount, total including tax)
- Additional details (notes, payment terms)
- Link to the originating quote (if applicable)
- Link to the generated invoice (if applicable)

**Order Statuses:**

- `pending`: Initial state
- `processing`: Work has started
- `completed`: Order is complete and ready for invoicing
- `cancelled`: Order has been cancelled
- `invoiced`: Invoice has been generated for this order

### Order API Endpoints

#### List all orders

```
GET /api/commandes/
```

Returns a simplified representation of all orders.

**Response:**

```json
[
  {
    "id": 1,
    "numero_commande": "CMD-DEV-2025-001",
    "client": 5,
    "nom_client": "Client Name",
    "date_commande": "2025-05-03",
    "date_livraison_prevue": "2025-05-10",
    "date_livraison_reelle": null,
    "statut": "pending",
    "montant_ht": 1250.0,
    "montant_tva": 250.0,
    "montant_ttc": 1500.0
  },
  ...
]
```

#### Get a specific order

```
GET /api/commandes/{id}/
```

Returns detailed information about a specific order, including products.

**Response:**

```json
{
  "id": 1,
  "numero_commande": "CMD-DEV-2025-001",
  "client": 5,
  "nom_client": "Client Name",
  "devis": 1,
  "devis_numero": "DEV-2025-001",
  "produits": [1, 3],
  "produit_commande": [
    {
      "id": 1,
      "produit": 1,
      "nom_produit": "Product 1",
      "quantite": 5,
      "prix_unitaire": 200.0,
      "remise_pourcentage": 0,
      "prix_total": 1000.0
    },
    {
      "id": 2,
      "produit": 3,
      "nom_produit": "Product 3",
      "quantite": 2,
      "prix_unitaire": 125.0,
      "remise_pourcentage": 0,
      "prix_total": 250.0
    }
  ],
  "produits_details": [...],  // Available products for adding to order
  "date_commande": "2025-05-03",
  "date_livraison_prevue": "2025-05-10",
  "date_livraison_reelle": null,
  "statut": "pending",
  "tax_rate": 20,
  "montant_ht": 1250.0,
  "montant_tva": 250.0,
  "montant_ttc": 1500.0,
  "facture": null,
  "facture_numero": null,
  "notes": null,
  "conditions_paiement": "50% à la commande, 50% à la livraison",
  "date_creation": "2025-05-03T14:45:00Z",
  "derniere_mise_a_jour": "2025-05-03T14:45:00Z"
}
```

#### Create a new order

```
POST /api/commandes/
```

**Request Body:**

```json
{
  "numero_commande": "CMD-2025-001",
  "client": 5,
  "date_commande": "2025-05-15",
  "date_livraison_prevue": "2025-05-22",
  "statut": "pending",
  "tax_rate": 20,
  "notes": "Special requirements for this order",
  "conditions_paiement": "50% à la commande, 50% à la livraison",
  "produits": [
    {
      "produit": 1,
      "quantite": 5,
      "prix_unitaire": 200.0
    },
    {
      "produit": 3,
      "quantite": 2,
      "prix_unitaire": 125.0
    }
  ]
}
```

**Notes:**

- The system automatically calculates totals (HT, TVA, TTC) based on the products
- You can create an order directly or convert it from an accepted quote

#### Update an order

```
PUT /api/commandes/{id}/
PATCH /api/commandes/{id}/
```

Same structure as the create endpoint. Use PUT for complete replacement, PATCH for partial updates.

#### Delete an order

```
DELETE /api/commandes/{id}/
```

#### Add a product to an order

```
POST /api/commandes/{id}/add_product/
```

**Request Body:**

```json
{
  "produit": 2,
  "quantite": 3,
  "prix_unitaire": 150.0,
  "remise_pourcentage": 10
}
```

**Response:** The newly added or updated product with its calculated total.

#### Remove a product from an order

```
DELETE /api/commandes/{id}/remove_product/
```

**Request Body:**

```json
{
  "produit": 2
}
```

#### Update order status

```
POST /api/commandes/{id}/update_status/
```

**Request Body:**

```json
{
  "status": "processing"
}
```

**Notes:**

- Valid statuses: `pending`, `processing`, `completed`, `cancelled`, `invoiced`
- An order must have at least one product to be marked as `completed`

#### Generate an invoice from an order

```
POST /api/commandes/{id}/generate_invoice/
```

**Request Body:**

```json
{
  "confirmation": true
}
```

**Response:**

```json
{
  "success": "Invoice generated successfully",
  "invoice_id": 15
}
```

**Notes:**

- This endpoint is only available for orders with `completed` status
- The order status will be changed to `invoiced` after successful invoice generation
- The system prevents generating duplicate invoices for the same order

#### Get orders by client

```
GET /api/commandes/by_client/?client_id={client_id}
```

**Response:** List of orders for the specified client.

### Order Usage Examples

#### Typical Workflow:

1. Create an order (status: `pending`) directly or by converting an accepted quote
2. Update order status to `processing` when work begins
3. Update order status to `completed` when work is finished
4. Generate an invoice from the completed order

#### Updating Order Status:

```javascript
// Example: Updating an order status
const updateOrderStatus = async (orderId, newStatus) => {
  try {
    const response = await axios.post(
      `/api/commandes/${orderId}/update_status/`,
      { status: newStatus },
      { headers: { Authorization: `Token ${authToken}` } }
    );
    return response.data;
  } catch (error) {
    console.error("Error updating order status:", error);
    throw error;
  }
};

// Usage
updateOrderStatus(1, "processing");
```

#### Generating an Invoice:

```javascript
// Example: Generating an invoice from a completed order
const generateInvoice = async (orderId) => {
  try {
    const response = await axios.post(
      `/api/commandes/${orderId}/generate_invoice/`,
      { confirmation: true },
      { headers: { Authorization: `Token ${authToken}` } }
    );
    return response.data;
  } catch (error) {
    console.error("Error generating invoice:", error);
    throw error;
  }
};

// Usage
generateInvoice(1);
```

## Workflow Integration

### Complete Quote-to-Invoice Workflow

1. **Create a Quote**:

   - Create a new quote with client information and products
   - Set status to "draft" while preparing

2. **Send Quote to Client**:

   - Update quote status to "sent"
   - The quote is now valid for 15 days (configurable through the `date_validite` field)

3. **Client Response**:

   - Update quote status to either "accepted" or "rejected" based on client response
   - If "rejected", the workflow ends here
   - If "accepted", continue to convert to order

4. **Convert to Order**:

   - Use the convert endpoint to transform the quote into an order
   - This maintains all information including products and prices
   - Quote status changes to "converted"
   - New order status is "pending"

5. **Order Processing**:

   - Update order status to "processing" when work begins
   - Add, modify, or remove products as needed during this phase

6. **Order Completion**:

   - Update order status to "completed" when all work is finished
   - Set the actual delivery date (`date_livraison_reelle`)

7. **Generate Invoice**:
   - Use the generate invoice endpoint to create an invoice from the completed order
   - Order status changes to "invoiced"
   - The invoice can then be processed through the invoice management system

### Important Notes for Frontend Implementation

1. **Authentication**:

   - All endpoints require authentication (include your authentication token with each request)

2. **Error Handling**:

   - All endpoints return appropriate HTTP status codes and error messages
   - Handle 400-level errors for user input issues
   - Handle 500-level errors for server issues

3. **Automatic Calculations**:

   - The system automatically calculates all financial totals
   - When adding/removing products, totals are recalculated

4. **Status Transitions**:

   - Respect the logical flow of status transitions
   - Some endpoints (like invoice generation) are only available for specific statuses

5. **Product Management**:
   - Use the `produits_details` field in detail endpoints to show available products
   - When adding products, the unit price will default to the product's standard price if not specified
