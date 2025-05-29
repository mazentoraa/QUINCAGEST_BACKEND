# Quote and Order API Examples

This document provides practical code examples for working with the Quote (Devis) and Order (Commande) API endpoints in our laser cutting business application.

## Table of Contents

1. [Setup](#setup)
2. [Quote API Examples](#quote-api-examples)
   - [Fetching Quotes](#fetching-quotes)
   - [Creating a Quote](#creating-a-quote)
   - [Managing Products in a Quote](#managing-products-in-a-quote)
   - [Quote Status Workflow](#quote-status-workflow)
   - [Converting a Quote to an Order](#converting-a-quote-to-an-order)
3. [Order API Examples](#order-api-examples)
   - [Fetching Orders](#fetching-orders)
   - [Creating an Order](#creating-an-order)
   - [Managing Products in an Order](#managing-products-in-an-order)
   - [Order Status Workflow](#order-status-workflow)
   - [Generating an Invoice](#generating-an-invoice)
4. [Error Handling](#error-handling)
5. [Complete Integration Examples](#complete-integration-examples)

## Setup

### API Service Setup

```javascript
// api/apiService.js
import axios from "axios";

// Create an axios instance with default configuration
const api = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for authorization
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("authToken");

    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle authentication errors
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("authToken");
      window.location = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Quote and Order Service

```javascript
// api/quoteService.js
import api from "./apiService";

export const getQuotes = async (filters = {}) => {
  const response = await api.get("/devis/", { params: filters });
  return response.data;
};

export const getQuoteById = async (id) => {
  const response = await api.get(`/devis/${id}/`);
  return response.data;
};

export const createQuote = async (quoteData) => {
  const response = await api.post("/devis/", quoteData);
  return response.data;
};

export const updateQuote = async (id, quoteData) => {
  const response = await api.put(`/devis/${id}/`, quoteData);
  return response.data;
};

export const partialUpdateQuote = async (id, quoteData) => {
  const response = await api.patch(`/devis/${id}/`, quoteData);
  return response.data;
};

export const deleteQuote = async (id) => {
  const response = await api.delete(`/devis/${id}/`);
  return response.data;
};

export const addProductToQuote = async (quoteId, productData) => {
  const response = await api.post(
    `/devis/${quoteId}/add_product/`,
    productData
  );
  return response.data;
};

export const removeProductFromQuote = async (quoteId, productId) => {
  const response = await api.delete(`/devis/${quoteId}/remove_product/`, {
    data: { produit: productId },
  });
  return response.data;
};

export const convertQuoteToOrder = async (quoteId) => {
  const response = await api.post(`/devis/${quoteId}/convert_to_commande/`, {
    confirmation: true,
  });
  return response.data;
};

export const getQuotesByClient = async (clientId) => {
  const response = await api.get(`/devis/by_client/`, {
    params: { client_id: clientId },
  });
  return response.data;
};

// Order service functions (similar pattern)
// api/orderService.js
import api from "./apiService";

export const getOrders = async (filters = {}) => {
  const response = await api.get("/commandes/", { params: filters });
  return response.data;
};

export const getOrderById = async (id) => {
  const response = await api.get(`/commandes/${id}/`);
  return response.data;
};

export const createOrder = async (orderData) => {
  const response = await api.post("/commandes/", orderData);
  return response.data;
};

export const updateOrder = async (id, orderData) => {
  const response = await api.put(`/commandes/${id}/`, orderData);
  return response.data;
};

export const partialUpdateOrder = async (id, orderData) => {
  const response = await api.patch(`/commandes/${id}/`, orderData);
  return response.data;
};

export const deleteOrder = async (id) => {
  const response = await api.delete(`/commandes/${id}/`);
  return response.data;
};

export const addProductToOrder = async (orderId, productData) => {
  const response = await api.post(
    `/commandes/${orderId}/add_product/`,
    productData
  );
  return response.data;
};

export const removeProductFromOrder = async (orderId, productId) => {
  const response = await api.delete(`/commandes/${orderId}/remove_product/`, {
    data: { produit: productId },
  });
  return response.data;
};

export const updateOrderStatus = async (orderId, newStatus) => {
  const response = await api.post(`/commandes/${orderId}/update_status/`, {
    status: newStatus,
  });
  return response.data;
};

export const generateInvoice = async (orderId) => {
  const response = await api.post(`/commandes/${orderId}/generate_invoice/`, {
    confirmation: true,
  });
  return response.data;
};

export const getOrdersByClient = async (clientId) => {
  const response = await api.get(`/commandes/by_client/`, {
    params: { client_id: clientId },
  });
  return response.data;
};
```

## Quote API Examples

### Fetching Quotes

#### Get All Quotes

```javascript
import { getQuotes } from "../api/quoteService";
import { useState, useEffect } from "react";

function QuoteList() {
  const [quotes, setQuotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchQuotes = async () => {
      try {
        setLoading(true);
        const data = await getQuotes();
        setQuotes(data);
        setError(null);
      } catch (err) {
        setError("Failed to fetch quotes");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchQuotes();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="quote-list">
      <h1>Quotes</h1>
      <table>
        <thead>
          <tr>
            <th>Quote No.</th>
            <th>Client</th>
            <th>Date</th>
            <th>Status</th>
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          {quotes.map((quote) => (
            <tr key={quote.id}>
              <td>{quote.numero_devis}</td>
              <td>{quote.nom_client}</td>
              <td>{new Date(quote.date_emission).toLocaleDateString()}</td>
              <td>{translateStatus(quote.statut)}</td>
              <td>{formatCurrency(quote.montant_ttc)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function translateStatus(status) {
  const statusMap = {
    draft: "Brouillon",
    sent: "Envoyé",
    accepted: "Accepté",
    rejected: "Rejeté",
    expired: "Expiré",
    converted: "Converti",
  };
  return statusMap[status] || status;
}

function formatCurrency(amount) {
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
  }).format(amount || 0);
}
```

#### Get Quote Details

```javascript
import { getQuoteById } from "../api/quoteService";
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";

function QuoteDetails() {
  const { id } = useParams();
  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchQuote = async () => {
      try {
        setLoading(true);
        const data = await getQuoteById(id);
        setQuote(data);
        setError(null);
      } catch (err) {
        setError("Failed to fetch quote details");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchQuote();
  }, [id]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!quote) return <div>Quote not found</div>;

  return (
    <div className="quote-details">
      <h1>Quote {quote.numero_devis}</h1>
      <div className="info-section">
        <div>
          <strong>Client:</strong> {quote.nom_client}
        </div>
        <div>
          <strong>Issue Date:</strong>{" "}
          {new Date(quote.date_emission).toLocaleDateString()}
        </div>
        <div>
          <strong>Valid Until:</strong>{" "}
          {new Date(quote.date_validite).toLocaleDateString()}
        </div>
        <div>
          <strong>Status:</strong> {translateStatus(quote.statut)}
        </div>
      </div>

      <h2>Products</h2>
      <table className="product-table">
        <thead>
          <tr>
            <th>Product</th>
            <th>Quantity</th>
            <th>Unit Price</th>
            <th>Discount %</th>
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          {quote.produit_devis.map((product) => (
            <tr key={product.id}>
              <td>{product.nom_produit}</td>
              <td>{product.quantite}</td>
              <td>{formatCurrency(product.prix_unitaire)}</td>
              <td>{product.remise_pourcentage}%</td>
              <td>{formatCurrency(product.prix_total)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td colSpan="4" style={{ textAlign: "right" }}>
              <strong>Total HT:</strong>
            </td>
            <td>{formatCurrency(quote.montant_ht)}</td>
          </tr>
          <tr>
            <td colSpan="4" style={{ textAlign: "right" }}>
              <strong>TVA ({quote.tax_rate}%):</strong>
            </td>
            <td>{formatCurrency(quote.montant_tva)}</td>
          </tr>
          <tr>
            <td colSpan="4" style={{ textAlign: "right" }}>
              <strong>Total TTC:</strong>
            </td>
            <td>{formatCurrency(quote.montant_ttc)}</td>
          </tr>
        </tfoot>
      </table>

      {/* Other quote details */}
    </div>
  );
}
```

### Creating a Quote

```javascript
import { createQuote } from "../api/quoteService";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

function CreateQuote() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    numero_devis: `DEV-${new Date().getFullYear()}-`,
    client: "",
    date_emission: new Date().toISOString().split("T")[0],
    statut: "draft",
    tax_rate: 20,
    notes: "",
    conditions_paiement: "50% à la commande, 50% à la livraison",
    produits: [],
  });
  const [clients, setClients] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch clients and products for dropdowns (implementation not shown)

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleAddProduct = () => {
    setFormData((prev) => ({
      ...prev,
      produits: [
        ...prev.produits,
        {
          produit: "",
          quantite: 1,
          prix_unitaire: null,
          remise_pourcentage: 0,
        },
      ],
    }));
  };

  const handleProductChange = (index, field, value) => {
    const updatedProducts = [...formData.produits];
    updatedProducts[index] = {
      ...updatedProducts[index],
      [field]: value,
    };

    // If we're changing the product, set the default price
    if (field === "produit") {
      const selectedProduct = products.find((p) => p.id === Number(value));
      if (selectedProduct) {
        updatedProducts[index].prix_unitaire = selectedProduct.prix;
      }
    }

    setFormData((prev) => ({
      ...prev,
      produits: updatedProducts,
    }));
  };

  const handleRemoveProduct = (index) => {
    const updatedProducts = formData.produits.filter((_, i) => i !== index);
    setFormData((prev) => ({
      ...prev,
      produits: updatedProducts,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);
      setError(null);
      const result = await createQuote(formData);
      // Navigate to the new quote's detail page
      navigate(`/quotes/${result.id}`);
    } catch (err) {
      setError(
        "Failed to create quote. Please check your inputs and try again."
      );
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="create-quote">
      <h1>Create New Quote</h1>
      {error && <div className="error-message">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="numero_devis">Quote Number</label>
          <input
            type="text"
            id="numero_devis"
            name="numero_devis"
            value={formData.numero_devis}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="client">Client</label>
          <select
            id="client"
            name="client"
            value={formData.client}
            onChange={handleChange}
            required
          >
            <option value="">Select a client</option>
            {clients.map((client) => (
              <option key={client.id} value={client.id}>
                {client.nom_client}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="date_emission">Issue Date</label>
          <input
            type="date"
            id="date_emission"
            name="date_emission"
            value={formData.date_emission}
            onChange={handleChange}
            required
          />
        </div>

        {/* More form fields */}

        <h2>Products</h2>
        <button type="button" onClick={handleAddProduct}>
          Add Product
        </button>

        {formData.produits.map((product, index) => (
          <div key={index} className="product-form-row">
            <select
              value={product.produit}
              onChange={(e) =>
                handleProductChange(index, "produit", e.target.value)
              }
              required
            >
              <option value="">Select a product</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nom_produit} - {formatCurrency(p.prix)}
                </option>
              ))}
            </select>

            <input
              type="number"
              value={product.quantite}
              onChange={(e) =>
                handleProductChange(index, "quantite", Number(e.target.value))
              }
              min="1"
              required
              placeholder="Qty"
            />

            <input
              type="number"
              value={product.prix_unitaire || ""}
              onChange={(e) =>
                handleProductChange(
                  index,
                  "prix_unitaire",
                  Number(e.target.value)
                )
              }
              step="0.01"
              min="0"
              placeholder="Unit Price"
            />

            <input
              type="number"
              value={product.remise_pourcentage}
              onChange={(e) =>
                handleProductChange(
                  index,
                  "remise_pourcentage",
                  Number(e.target.value)
                )
              }
              step="0.1"
              min="0"
              max="100"
              placeholder="Discount %"
            />

            <button type="button" onClick={() => handleRemoveProduct(index)}>
              Remove
            </button>
          </div>
        ))}

        <button type="submit" disabled={loading}>
          {loading ? "Creating..." : "Create Quote"}
        </button>
      </form>
    </div>
  );
}
```

### Managing Products in a Quote

```javascript
import { addProductToQuote, removeProductFromQuote } from "../api/quoteService";

// Add product to an existing quote
async function handleAddProduct(quoteId, productData) {
  try {
    const response = await addProductToQuote(quoteId, {
      produit: productData.produit,
      quantite: productData.quantite,
      prix_unitaire: productData.prix_unitaire,
      remise_pourcentage: productData.remise_pourcentage || 0,
    });

    // Handle success - update UI or state
    return response;
  } catch (error) {
    // Handle error
    console.error("Error adding product:", error);
    throw error;
  }
}

// Remove product from an existing quote
async function handleRemoveProduct(quoteId, productId) {
  try {
    await removeProductFromQuote(quoteId, productId);

    // Handle success - update UI or state
    return true;
  } catch (error) {
    // Handle error
    console.error("Error removing product:", error);
    throw error;
  }
}
```

### Quote Status Workflow

```javascript
import { partialUpdateQuote } from "../api/quoteService";

// Update quote status
async function updateQuoteStatus(quoteId, newStatus) {
  try {
    const response = await partialUpdateQuote(quoteId, {
      statut: newStatus,
    });

    // Handle success - update UI or state
    return response;
  } catch (error) {
    // Handle error
    console.error("Error updating status:", error);
    throw error;
  }
}

// Example usage
function QuoteStatusButton({ quote, onStatusChanged }) {
  const [updating, setUpdating] = useState(false);

  // Determine available actions based on current status
  const getAvailableActions = (currentStatus) => {
    switch (currentStatus) {
      case "draft":
        return [{ label: "Mark as Sent", status: "sent" }];
      case "sent":
        return [
          { label: "Mark as Accepted", status: "accepted" },
          { label: "Mark as Rejected", status: "rejected" },
        ];
      case "accepted":
        return [{ label: "Convert to Order", status: "convert" }];
      default:
        return [];
    }
  };

  const actions = getAvailableActions(quote.statut);

  const handleStatusChange = async (newStatus) => {
    if (newStatus === "convert") {
      // Handle conversion separately
      return;
    }

    try {
      setUpdating(true);
      await updateQuoteStatus(quote.id, newStatus);
      onStatusChanged(newStatus);
    } catch (error) {
      alert(`Failed to update status: ${error.message}`);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="status-actions">
      {actions.map((action) => (
        <button
          key={action.status}
          onClick={() => handleStatusChange(action.status)}
          disabled={updating}
        >
          {action.label}
        </button>
      ))}
    </div>
  );
}
```

### Converting a Quote to an Order

```javascript
import { convertQuoteToOrder } from "../api/quoteService";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

function QuoteConversionButton({ quoteId }) {
  const navigate = useNavigate();
  const [converting, setConverting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleConvert = async () => {
    try {
      setConverting(true);
      const result = await convertQuoteToOrder(quoteId);
      // Navigate to the new order
      navigate(`/orders/${result.id}`);
    } catch (error) {
      alert(
        `Failed to convert quote: ${
          error.response?.data?.error || error.message
        }`
      );
    } finally {
      setConverting(false);
      setShowConfirm(false);
    }
  };

  return (
    <>
      <button onClick={() => setShowConfirm(true)} disabled={converting}>
        Convert to Order
      </button>

      {showConfirm && (
        <div className="confirmation-dialog">
          <h3>Confirm Conversion</h3>
          <p>Are you sure you want to convert this quote to an order?</p>
          <p>This action cannot be undone.</p>
          <div className="dialog-actions">
            <button onClick={() => setShowConfirm(false)}>Cancel</button>
            <button
              onClick={handleConvert}
              disabled={converting}
              className="primary"
            >
              {converting ? "Converting..." : "Convert"}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
```

## Order API Examples

### Fetching Orders

Similar to the Quote API examples, but using the Order service functions.

### Creating an Order

Similar to creating a quote, with order-specific fields like delivery dates.

### Managing Products in an Order

Similar to managing products in a quote, using the Order API endpoints.

### Order Status Workflow

```javascript
import { updateOrderStatus } from "../api/orderService";

// Update order status
async function handleStatusChange(orderId, newStatus) {
  try {
    const response = await updateOrderStatus(orderId, newStatus);
    // Handle success - update UI or state
    return response;
  } catch (error) {
    // Handle error
    console.error("Error updating status:", error);
    throw error;
  }
}

// Example component for order status buttons
function OrderStatusActions({ order, onStatusChanged }) {
  const [updating, setUpdating] = useState(false);

  // Determine available actions based on current status
  const getAvailableActions = (currentStatus) => {
    switch (currentStatus) {
      case "pending":
        return [
          { label: "Start Processing", status: "processing" },
          { label: "Cancel Order", status: "cancelled" },
        ];
      case "processing":
        return [
          { label: "Mark as Completed", status: "completed" },
          { label: "Cancel Order", status: "cancelled" },
        ];
      case "completed":
        return [{ label: "Generate Invoice", status: "invoice" }];
      default:
        return [];
    }
  };

  const actions = getAvailableActions(order.statut);

  const handleAction = async (action) => {
    if (action === "invoice") {
      // Handle invoice generation separately
      return;
    }

    try {
      setUpdating(true);
      await handleStatusChange(order.id, action);
      onStatusChanged(action);
    } catch (error) {
      alert(`Failed to update status: ${error.message}`);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="status-actions">
      {actions.map((action) => (
        <button
          key={action.status}
          onClick={() => handleAction(action.status)}
          disabled={updating}
          className={action.status === "cancelled" ? "danger" : ""}
        >
          {action.label}
        </button>
      ))}
    </div>
  );
}
```

### Generating an Invoice

```javascript
import { generateInvoice } from "../api/orderService";
import { useState } from "react";

function GenerateInvoiceButton({ order, onSuccess }) {
  const [processing, setProcessing] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleGenerateInvoice = async () => {
    try {
      setProcessing(true);
      const result = await generateInvoice(order.id);
      onSuccess(result);
      alert(`Invoice generated successfully. Invoice ID: ${result.invoice_id}`);
    } catch (error) {
      alert(
        `Failed to generate invoice: ${
          error.response?.data?.error || error.message
        }`
      );
    } finally {
      setProcessing(false);
      setShowConfirm(false);
    }
  };

  // Only show button if order is completed and no invoice exists
  if (order.statut !== "completed" || order.facture) {
    return null;
  }

  return (
    <>
      <button
        onClick={() => setShowConfirm(true)}
        disabled={processing}
        className="primary"
      >
        Generate Invoice
      </button>

      {showConfirm && (
        <div className="confirmation-dialog">
          <h3>Confirm Invoice Generation</h3>
          <p>Are you sure you want to generate an invoice for this order?</p>
          <p>This will mark the order as invoiced.</p>
          <div className="dialog-actions">
            <button onClick={() => setShowConfirm(false)}>Cancel</button>
            <button
              onClick={handleGenerateInvoice}
              disabled={processing}
              className="primary"
            >
              {processing ? "Processing..." : "Generate Invoice"}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
```

## Error Handling

```javascript
// Utility function for handling API errors
export const handleApiError = (error) => {
  if (error.response) {
    // The request was made and the server responded with a status code
    // that falls out of the range of 2xx
    const { status, data } = error.response;

    if (status === 400) {
      // Handle validation errors
      if (typeof data === "object") {
        const errorMessages = [];
        for (const field in data) {
          if (Array.isArray(data[field])) {
            errorMessages.push(`${field}: ${data[field].join(" ")}`);
          } else if (typeof data[field] === "string") {
            errorMessages.push(`${field}: ${data[field]}`);
          }
        }
        return {
          title: "Validation Error",
          message: errorMessages.join("\n"),
        };
      } else if (data.error) {
        return {
          title: "Error",
          message: data.error,
        };
      }
    } else if (status === 401) {
      return {
        title: "Authentication Error",
        message: "Your session has expired. Please log in again.",
      };
    } else if (status === 403) {
      return {
        title: "Permission Denied",
        message: "You do not have permission to perform this action.",
      };
    } else if (status === 404) {
      return {
        title: "Not Found",
        message: "The requested resource was not found.",
      };
    } else if (status >= 500) {
      return {
        title: "Server Error",
        message: "A server error occurred. Please try again later.",
      };
    }
  } else if (error.request) {
    // The request was made but no response was received
    return {
      title: "Network Error",
      message:
        "No response received from server. Please check your connection.",
    };
  } else {
    // Something happened in setting up the request that triggered an error
    return {
      title: "Request Error",
      message: error.message,
    };
  }

  // Default error message
  return {
    title: "Error",
    message: "An unexpected error occurred.",
  };
};

// Usage example
import { handleApiError } from "../utils/errorHandlers";

try {
  // API call
  const result = await createQuote(formData);
  // success handling
} catch (error) {
  const { title, message } = handleApiError(error);
  // Show error notification with title and message
  showNotification("error", title, message);
  console.error(error);
}
```

## Complete Integration Examples

### Quote Management Page

```jsx
import React, { useState, useEffect } from "react";
import { getQuotes, deleteQuote } from "../api/quoteService";
import { Link } from "react-router-dom";

function QuotesManagementPage() {
  const [quotes, setQuotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    status: "all",
    dateFrom: "",
    dateTo: "",
  });

  useEffect(() => {
    loadQuotes();
  }, [filters]);

  const loadQuotes = async () => {
    try {
      setLoading(true);
      const queryParams = {};

      if (filters.status !== "all") {
        queryParams.statut = filters.status;
      }

      if (filters.dateFrom) {
        queryParams.date_from = filters.dateFrom;
      }

      if (filters.dateTo) {
        queryParams.date_to = filters.dateTo;
      }

      const data = await getQuotes(queryParams);
      setQuotes(data);
      setError(null);
    } catch (err) {
      setError("Failed to load quotes");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteQuote = async (id) => {
    if (!window.confirm("Are you sure you want to delete this quote?")) {
      return;
    }

    try {
      await deleteQuote(id);
      setQuotes(quotes.filter((quote) => quote.id !== id));
    } catch (err) {
      alert("Failed to delete quote");
      console.error(err);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <div className="quotes-management">
      <div className="page-header">
        <h1>Quote Management</h1>
        <Link to="/quotes/new" className="btn btn-primary">
          Create New Quote
        </Link>
      </div>

      <div className="filters">
        <div className="filter-item">
          <label htmlFor="status">Status:</label>
          <select
            id="status"
            name="status"
            value={filters.status}
            onChange={handleFilterChange}
          >
            <option value="all">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="sent">Sent</option>
            <option value="accepted">Accepted</option>
            <option value="rejected">Rejected</option>
            <option value="expired">Expired</option>
            <option value="converted">Converted</option>
          </select>
        </div>

        <div className="filter-item">
          <label htmlFor="dateFrom">From:</label>
          <input
            type="date"
            id="dateFrom"
            name="dateFrom"
            value={filters.dateFrom}
            onChange={handleFilterChange}
          />
        </div>

        <div className="filter-item">
          <label htmlFor="dateTo">To:</label>
          <input
            type="date"
            id="dateTo"
            name="dateTo"
            value={filters.dateTo}
            onChange={handleFilterChange}
          />
        </div>
      </div>

      {loading ? (
        <p>Loading quotes...</p>
      ) : error ? (
        <div className="error-message">{error}</div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Quote #</th>
              <th>Client</th>
              <th>Issue Date</th>
              <th>Valid Until</th>
              <th>Status</th>
              <th>Amount</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {quotes.length === 0 ? (
              <tr>
                <td colSpan="7" className="no-data">
                  No quotes found
                </td>
              </tr>
            ) : (
              quotes.map((quote) => (
                <tr key={quote.id}>
                  <td>{quote.numero_devis}</td>
                  <td>{quote.nom_client}</td>
                  <td>{new Date(quote.date_emission).toLocaleDateString()}</td>
                  <td>{new Date(quote.date_validite).toLocaleDateString()}</td>
                  <td>
                    <span className={`status-badge status-${quote.statut}`}>
                      {translateStatus(quote.statut)}
                    </span>
                  </td>
                  <td className="text-right">
                    {formatCurrency(quote.montant_ttc)}
                  </td>
                  <td>
                    <div className="action-buttons">
                      <Link to={`/quotes/${quote.id}`} className="btn btn-sm">
                        View
                      </Link>
                      {quote.statut === "draft" && (
                        <Link
                          to={`/quotes/${quote.id}/edit`}
                          className="btn btn-sm"
                        >
                          Edit
                        </Link>
                      )}
                      {quote.statut !== "converted" && (
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={() => handleDeleteQuote(quote.id)}
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default QuotesManagementPage;
```
