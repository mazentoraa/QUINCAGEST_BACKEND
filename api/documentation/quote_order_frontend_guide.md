# Quote and Order Frontend Implementation Guide

This document provides guidance for implementing the frontend components for the Quote (Devis) and Order (Commande) features in our laser cutting business application.

## Table of Contents

1. [Component Architecture](#component-architecture)
2. [Quote Management](#quote-management)
   - [Quote List View](#quote-list-view)
   - [Quote Detail View](#quote-detail-view)
   - [Quote Form](#quote-form)
   - [Quote Status Management](#quote-status-management)
3. [Order Management](#order-management)
   - [Order List View](#order-list-view)
   - [Order Detail View](#order-detail-view)
   - [Order Form](#order-form)
   - [Order Status Management](#order-status-management)
4. [Product Management in Quotes and Orders](#product-management)
5. [Quote to Order Conversion](#quote-to-order-conversion)
6. [Invoice Generation](#invoice-generation)
7. [Best Practices and Tips](#best-practices-and-tips)

## Component Architecture

We recommend organizing your frontend components as follows:

```
src/
├── components/
│   ├── quotes/
│   │   ├── QuoteList.jsx
│   │   ├── QuoteDetail.jsx
│   │   ├── QuoteForm.jsx
│   │   ├── QuoteProductTable.jsx
│   │   └── QuoteStatusBadge.jsx
│   ├── orders/
│   │   ├── OrderList.jsx
│   │   ├── OrderDetail.jsx
│   │   ├── OrderForm.jsx
│   │   ├── OrderProductTable.jsx
│   │   └── OrderStatusBadge.jsx
│   └── shared/
│       ├── ProductSelector.jsx
│       ├── ClientSelector.jsx
│       └── PriceCalculator.jsx
├── pages/
│   ├── QuotesPage.jsx
│   ├── QuoteDetailPage.jsx
│   ├── NewQuotePage.jsx
│   ├── OrdersPage.jsx
│   ├── OrderDetailPage.jsx
│   └── NewOrderPage.jsx
├── services/
│   ├── quoteService.js
│   ├── orderService.js
│   └── productService.js
└── utils/
    ├── statusUtils.js
    └── calculationUtils.js
```

## Quote Management

### Quote List View

The Quote List should display a table or card view of all quotes with the following:

- Quote number
- Client name
- Issue date
- Status (using color-coded badges)
- Total amount
- Action buttons (View, Edit, Delete)

**Filtering and Sorting:**

- Status filter (All, Draft, Sent, Accepted, Rejected, Expired, Converted)
- Date range filter
- Client filter
- Sort by date (newest/oldest) or amount

**Implementation Tips:**

```jsx
function QuoteList() {
  const [quotes, setQuotes] = useState([]);
  const [filters, setFilters] = useState({
    status: "all",
    client: null,
    dateRange: null,
  });

  useEffect(() => {
    // Fetch quotes with optional filters
    fetchQuotes(filters)
      .then((data) => setQuotes(data))
      .catch((error) => handleError(error));
  }, [filters]);

  return (
    <div>
      <QuoteFilterBar filters={filters} onChange={setFilters} />
      <Table>
        <TableHeader>
          <TableRow>
            <TableCell>Numéro</TableCell>
            <TableCell>Client</TableCell>
            <TableCell>Date d'émission</TableCell>
            <TableCell>Statut</TableCell>
            <TableCell>Montant TTC</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHeader>
        <TableBody>
          {quotes.map((quote) => (
            <TableRow key={quote.id}>
              <TableCell>{quote.numero_devis}</TableCell>
              <TableCell>{quote.nom_client}</TableCell>
              <TableCell>{formatDate(quote.date_emission)}</TableCell>
              <TableCell>
                <QuoteStatusBadge status={quote.statut} />
              </TableCell>
              <TableCell>{formatCurrency(quote.montant_ttc)}</TableCell>
              <TableCell>
                <ActionButtons
                  quote={quote}
                  onView={handleView}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <Pagination /> {/* Add pagination if needed */}
    </div>
  );
}
```

### Quote Detail View

The Quote Detail view should display comprehensive information about a quote:

- Header section with quote number, dates, client info, and status
- Products table showing all items in the quote with quantities, prices, and discounts
- Financial summary section (subtotal, tax, total)
- Notes and payment terms section
- Action buttons based on quote status (e.g., "Mark as Sent", "Convert to Order")

**Implementation Tips:**

```jsx
function QuoteDetail({ quoteId }) {
  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchQuoteDetails(quoteId)
      .then((data) => {
        setQuote(data);
        setLoading(false);
      })
      .catch((error) => {
        handleError(error);
        setLoading(false);
      });
  }, [quoteId]);

  if (loading) return <LoadingSpinner />;
  if (!quote) return <NotFoundError />;

  return (
    <div className="quote-detail">
      <header className="quote-header">
        <h1>Devis {quote.numero_devis}</h1>
        <QuoteStatusBadge status={quote.statut} />

        <div className="quote-meta">
          <div>
            <strong>Date d'émission:</strong> {formatDate(quote.date_emission)}
          </div>
          <div>
            <strong>Date de validité:</strong> {formatDate(quote.date_validite)}
          </div>
          <div>
            <strong>Client:</strong> {quote.nom_client}
          </div>
        </div>

        <div className="quote-actions">
          <StatusActionButtons
            quote={quote}
            onStatusChange={handleStatusChange}
            onConvertToOrder={handleConversion}
          />
        </div>
      </header>

      <section className="quote-products">
        <h2>Produits</h2>
        <QuoteProductTable
          products={quote.produit_devis}
          onAddProduct={handleAddProduct}
          onRemoveProduct={handleRemoveProduct}
          editable={quote.statut === "draft"}
        />
      </section>

      <section className="quote-financials">
        <div className="financial-summary">
          <div>Montant HT: {formatCurrency(quote.montant_ht)}</div>
          <div>
            TVA ({quote.tax_rate}%): {formatCurrency(quote.montant_tva)}
          </div>
          <div className="total">
            Total TTC: {formatCurrency(quote.montant_ttc)}
          </div>
        </div>
      </section>

      <section className="quote-details">
        <h3>Remarques</h3>
        <div className="quote-remarks">{quote.remarques}</div>

        <h3>Notes</h3>
        <div className="quote-notes">{quote.notes || "Aucune note"}</div>

        <h3>Conditions de paiement</h3>
        <div className="payment-terms">
          {quote.conditions_paiement || "Non spécifié"}
        </div>
      </section>
    </div>
  );
}
```

### Quote Form

The Quote Form should handle both creation and editing:

- Client selection dropdown (with search)
- Date inputs (emission date automatically sets validity date to +15 days)
- Product selection section with ability to add multiple products
- For each product: quantity, unit price, and discount fields
- Real-time calculation of totals
- Notes and payment terms fields

**Implementation Tips:**

```jsx
function QuoteForm({ quoteId = null }) {
  const [formData, setFormData] = useState({
    numero_devis: "",
    client: "",
    date_emission: formatDateForInput(new Date()),
    date_validite: formatDateForInput(addDays(new Date(), 15)),
    statut: "draft",
    tax_rate: 20,
    remarques:
      "Remarques :\n_ Validité du devis : 15 jours.\n_ Ce devis doit être accepté et signé pour valider la commande",
    notes: "",
    conditions_paiement: "",
    produits: [],
  });

  // Load quote data if editing existing quote
  useEffect(() => {
    if (quoteId) {
      fetchQuoteDetails(quoteId)
        .then((data) => {
          setFormData({
            ...data,
            produits: data.produit_devis.map((p) => ({
              produit: p.produit,
              quantite: p.quantite,
              prix_unitaire: p.prix_unitaire,
              remise_pourcentage: p.remise_pourcentage,
            })),
          });
        })
        .catch((error) => handleError(error));
    }
  }, [quoteId]);

  // Handle emission date change (auto-update validity date)
  const handleEmissionDateChange = (date) => {
    setFormData({
      ...formData,
      date_emission: date,
      date_validite: formatDateForInput(addDays(new Date(date), 15)),
    });
  };

  // Handle product changes
  const handleAddProduct = (product) => {
    setFormData({
      ...formData,
      produits: [
        ...formData.produits,
        {
          produit: product.id,
          quantite: 1,
          prix_unitaire: product.prix,
          remise_pourcentage: 0,
        },
      ],
    });
  };

  const handleProductChange = (index, field, value) => {
    const updatedProducts = [...formData.produits];
    updatedProducts[index][field] = value;
    setFormData({
      ...formData,
      produits: updatedProducts,
    });
  };

  const handleRemoveProduct = (index) => {
    const updatedProducts = formData.produits.filter((_, i) => i !== index);
    setFormData({
      ...formData,
      produits: updatedProducts,
    });
  };

  // Form submission
  const handleSubmit = (e) => {
    e.preventDefault();

    const saveFunction = quoteId
      ? updateQuote(quoteId, formData)
      : createQuote(formData);

    saveFunction
      .then((response) => {
        showSuccessNotification();
        navigateToQuoteDetail(response.id);
      })
      .catch((error) => handleError(error));
  };

  return <form onSubmit={handleSubmit}>{/* Form fields go here */}</form>;
}
```

### Quote Status Management

Implement proper status transitions with appropriate UI controls:

- Draft → Sent: "Send Quote" button (changes status to 'sent')
- Sent → Accepted/Rejected: "Mark as Accepted" and "Mark as Rejected" buttons
- Accepted → Converted: "Convert to Order" button
- Show warning for expired quotes
- Disable editing for non-draft quotes

## Order Management

### Order List View

Similar to Quote List, with appropriate order-specific fields:

- Order number
- Client name
- Order date and delivery dates
- Status (with color-coded badges)
- Total amount
- Associated quote number (if applicable)
- Action buttons

### Order Detail View

Similar to Quote Detail, with these differences:

- Display both delivery dates (expected and actual)
- Show quote reference if created from a quote
- Show invoice reference if an invoice has been generated
- Add buttons for order-specific actions (update status, generate invoice)

### Order Form

Similar to Quote Form, with order-specific fields:

- Expected delivery date field
- Option to create from scratch or select an existing quote to convert

### Order Status Management

Implement proper status transitions with appropriate UI controls:

- Pending → Processing: "Start Processing" button
- Processing → Completed: "Mark as Completed" button
- Completed → Invoiced: "Generate Invoice" button
- Allow cancellation from any state except 'invoiced'

## Product Management

For both quotes and orders, implement a robust product selection and management interface:

```jsx
function ProductSelectorTable({
  products,
  onAdd,
  onUpdate,
  onRemove,
  disabled = false,
}) {
  const [availableProducts, setAvailableProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);

  useEffect(() => {
    fetchProducts()
      .then((data) => setAvailableProducts(data))
      .catch((error) => handleError(error));
  }, []);

  const handleProductSelect = (productId) => {
    const product = availableProducts.find((p) => p.id === productId);
    setSelectedProduct(product);
  };

  const handleAddProduct = () => {
    if (selectedProduct) {
      onAdd({
        produit: selectedProduct.id,
        quantite: 1,
        prix_unitaire: selectedProduct.prix,
        remise_pourcentage: 0,
      });
      setSelectedProduct(null);
    }
  };

  return (
    <div className="product-management">
      {!disabled && (
        <div className="product-selector">
          <select onChange={(e) => handleProductSelect(Number(e.target.value))}>
            <option value="">Sélectionner un produit</option>
            {availableProducts.map((product) => (
              <option key={product.id} value={product.id}>
                {product.nom_produit} - {formatCurrency(product.prix)}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={handleAddProduct}
            disabled={!selectedProduct}
          >
            Ajouter
          </button>
        </div>
      )}

      <table className="product-table">
        <thead>
          <tr>
            <th>Produit</th>
            <th>Quantité</th>
            <th>Prix unitaire</th>
            <th>Remise (%)</th>
            <th>Total HT</th>
            {!disabled && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {products.map((product, index) => (
            <ProductTableRow
              key={index}
              product={product}
              onUpdate={(field, value) => onUpdate(index, field, value)}
              onRemove={() => onRemove(index)}
              disabled={disabled}
            />
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td colSpan={4} className="text-right">
              <strong>Total HT:</strong>
            </td>
            <td>{formatCurrency(calculateSubtotal(products))}</td>
            {!disabled && <td></td>}
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
```

## Quote to Order Conversion

Implement a dedicated UI for converting quotes to orders:

```jsx
function QuoteConversionDialog({ quote, onConfirm, onCancel }) {
  const [confirmationChecked, setConfirmationChecked] = useState(false);

  const handleSubmit = () => {
    convertQuoteToOrder(quote.id, { confirmation: confirmationChecked })
      .then((response) => {
        showSuccessNotification("Quote successfully converted to order");
        onConfirm(response);
      })
      .catch((error) => {
        showErrorNotification(error.message);
      });
  };

  return (
    <Dialog open={true} onClose={onCancel}>
      <DialogTitle>Convert Quote to Order</DialogTitle>
      <DialogContent>
        <p>
          You are about to convert quote <strong>{quote.numero_devis}</strong>{" "}
          to an order.
        </p>
        <p>This will:</p>
        <ul>
          <li>Create a new order with all the information from this quote</li>
          <li>Change the quote status to "converted"</li>
          <li>Transfer all products with their quantities and prices</li>
        </ul>

        <FormControlLabel
          control={
            <Checkbox
              checked={confirmationChecked}
              onChange={(e) => setConfirmationChecked(e.target.checked)}
            />
          }
          label="I confirm that I want to convert this quote to an order"
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          disabled={!confirmationChecked}
          color="primary"
        >
          Convert to Order
        </Button>
      </DialogActions>
    </Dialog>
  );
}
```

## Invoice Generation

Implement a similar confirmation dialog for invoice generation:

```jsx
function InvoiceGenerationDialog({ order, onConfirm, onCancel }) {
  const [confirmationChecked, setConfirmationChecked] = useState(false);

  const handleSubmit = () => {
    generateInvoice(order.id, { confirmation: confirmationChecked })
      .then((response) => {
        showSuccessNotification("Invoice successfully generated");
        onConfirm(response);
      })
      .catch((error) => {
        showErrorNotification(error.message);
      });
  };

  return (
    <Dialog open={true} onClose={onCancel}>
      <DialogTitle>Generate Invoice</DialogTitle>
      <DialogContent>
        <p>
          You are about to generate an invoice for order{" "}
          <strong>{order.numero_commande}</strong>.
        </p>
        <p>This will:</p>
        <ul>
          <li>Create a new invoice with all the information from this order</li>
          <li>Change the order status to "invoiced"</li>
          <li>The invoice will be created with status "draft"</li>
        </ul>

        <FormControlLabel
          control={
            <Checkbox
              checked={confirmationChecked}
              onChange={(e) => setConfirmationChecked(e.target.checked)}
            />
          }
          label="I confirm that I want to generate an invoice for this order"
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          disabled={!confirmationChecked}
          color="primary"
        >
          Generate Invoice
        </Button>
      </DialogActions>
    </Dialog>
  );
}
```

## Best Practices and Tips

### Authentication Integration

All API requests must include authentication. Example using axios:

```javascript
// Create an axios instance with authentication
import axios from "axios";

const api = axios.create({
  baseURL: "/api",
});

// Add authentication token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("authToken");
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

// Use this configured instance for all API calls
export const fetchQuotes = async (filters) => {
  const response = await api.get("/devis/", { params: filters });
  return response.data;
};
```

### Error Handling

Implement consistent error handling:

```javascript
const handleAPIError = (error) => {
  // Get error message from API response if available
  const errorMessage =
    error.response?.data?.error ||
    error.response?.data?.detail ||
    "An unexpected error occurred";

  // Display appropriate notification
  showErrorNotification(errorMessage);

  // Log for debugging
  console.error("API Error:", error);

  // Return error message for component handling
  return errorMessage;
};
```

### Status Badge Component

Create a reusable component for status badges:

```jsx
function StatusBadge({ type, status }) {
  // Map of statuses to colors and labels
  const statusConfig = {
    quote: {
      draft: { color: "gray", label: "Brouillon" },
      sent: { color: "blue", label: "Envoyé" },
      accepted: { color: "green", label: "Accepté" },
      rejected: { color: "red", label: "Rejeté" },
      expired: { color: "orange", label: "Expiré" },
      converted: { color: "purple", label: "Converti" },
    },
    order: {
      pending: { color: "blue", label: "En attente" },
      processing: { color: "orange", label: "En traitement" },
      completed: { color: "green", label: "Terminée" },
      cancelled: { color: "red", label: "Annulée" },
      invoiced: { color: "purple", label: "Facturée" },
    },
  };

  const config = statusConfig[type]?.[status] || {
    color: "gray",
    label: status,
  };

  return (
    <span className={`status-badge status-${config.color}`}>
      {config.label}
    </span>
  );
}
```

### Financial Calculations

Create utility functions for financial calculations:

```javascript
// Calculate subtotal from products
export const calculateSubtotal = (products) => {
  return products.reduce((sum, product) => {
    const unitPrice = product.prix_unitaire || 0;
    const quantity = product.quantite || 0;
    const discount = product.remise_pourcentage || 0;
    const discountFactor = 1 - discount / 100;
    return sum + unitPrice * quantity * discountFactor;
  }, 0);
};

// Calculate tax amount
export const calculateTax = (subtotal, taxRate) => {
  return subtotal * (taxRate / 100);
};

// Calculate total with tax
export const calculateTotal = (subtotal, taxRate) => {
  return subtotal + calculateTax(subtotal, taxRate);
};

// Format currency for display
export const formatCurrency = (amount) => {
  if (amount === null || amount === undefined) return "-";
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
  }).format(amount);
};
```

### Responsive Design

Ensure your components work well on different screen sizes:

```css
/* Example CSS for responsive tables */
@media (max-width: 768px) {
  .responsive-table {
    display: block;
  }

  .responsive-table thead {
    display: none;
  }

  .responsive-table tbody tr {
    display: block;
    margin-bottom: 1rem;
    border: 1px solid #e0e0e0;
    padding: 0.5rem;
  }

  .responsive-table tbody td {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem;
    text-align: right;
    border-bottom: 1px solid #f0f0f0;
  }

  .responsive-table tbody td::before {
    content: attr(data-label);
    font-weight: bold;
    text-align: left;
  }
}
```
