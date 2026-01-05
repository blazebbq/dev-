# Stock Management System - API Documentation

## Overview

The Stock Management System provides a comprehensive RESTful API for managing inventory, warehouses, suppliers, and purchase orders. All endpoints return JSON responses.

**Base URL**: `http://localhost:5000/api`

## Authentication

Currently, the API does not require authentication. For production deployment, consider implementing JWT or OAuth2 authentication.

## Common Response Codes

- `200 OK`: Successful GET/PUT request
- `201 Created`: Successful POST request
- `204 No Content`: Successful DELETE request
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Endpoints

### Health Check

#### Check API Health
```
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Stock Management System",
  "version": "1.0.0"
}
```

---

## Products

### List All Products
```
GET /api/products
```

**Response:**
```json
[
  {
    "sku": "PROD001",
    "name": "Industrial Widget A",
    "description": "High-quality industrial widget",
    "category": "Components",
    "unit_of_measure": "EA",
    "unit_price": 25.50,
    "reorder_point": 100,
    "reorder_quantity": 500,
    "status": "ACTIVE",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

### Create Product
```
POST /api/products
Content-Type: application/json
```

**Request Body:**
```json
{
  "sku": "PROD001",
  "name": "Widget A",
  "description": "High-quality widget",
  "category": "Components",
  "unit_of_measure": "EA",
  "unit_price": 25.50,
  "reorder_point": 100,
  "reorder_quantity": 500,
  "status": "ACTIVE"
}
```

**Response:** `201 Created` with product data

### Get Product
```
GET /api/products/{sku}
```

**Response:** Product object or `404 Not Found`

### Update Product
```
PUT /api/products/{sku}
Content-Type: application/json
```

**Request Body:** Partial or full product object

**Response:** Updated product object

### Delete Product
```
DELETE /api/products/{sku}
```

**Response:** `204 No Content`

---

## Warehouses

### List All Warehouses
```
GET /api/warehouses
```

**Response:**
```json
[
  {
    "code": "WH001",
    "name": "Main Warehouse",
    "location": "New York, NY",
    "capacity": 10000,
    "manager": "John Smith",
    "phone": "555-0101",
    "email": "john@example.com",
    "status": "ACTIVE",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

### Create Warehouse
```
POST /api/warehouses
Content-Type: application/json
```

**Request Body:**
```json
{
  "code": "WH001",
  "name": "Main Warehouse",
  "location": "New York, NY",
  "capacity": 10000,
  "manager": "John Smith",
  "phone": "555-0101",
  "email": "john@example.com",
  "status": "ACTIVE"
}
```

### Get Warehouse
```
GET /api/warehouses/{code}
```

### Update Warehouse
```
PUT /api/warehouses/{code}
```

### Delete Warehouse
```
DELETE /api/warehouses/{code}
```

---

## Stock Management

### Get All Stock Levels
```
GET /api/stock/levels
```

**Response:**
```json
[
  {
    "product_sku": "PROD001",
    "product_name": "Industrial Widget A",
    "total_on_hand": 800,
    "total_available": 800,
    "total_reserved": 0,
    "reorder_point": 100,
    "needs_reorder": false
  }
]
```

### Get Product Stock Level
```
GET /api/stock/levels/{sku}?warehouse={warehouse_code}
```

**Query Parameters:**
- `warehouse` (optional): Filter by warehouse code

**Response:**
```json
{
  "product_sku": "PROD001",
  "total_quantity_on_hand": 800,
  "total_quantity_available": 800,
  "total_quantity_reserved": 0,
  "warehouses": [
    {
      "id": 1,
      "product_sku": "PROD001",
      "warehouse_code": "WH001",
      "quantity_on_hand": 500,
      "quantity_reserved": 0,
      "quantity_available": 500
    }
  ]
}
```

### Record Stock Receipt
```
POST /api/stock/receipt
Content-Type: application/json
```

**Request Body:**
```json
{
  "product_sku": "PROD001",
  "warehouse_code": "WH001",
  "quantity": 1000,
  "unit_cost": 20.00,
  "reference": "PO-2024-001",
  "notes": "Received from supplier"
}
```

**Response:** `201 Created` with stock and transaction data

### Record Stock Issue
```
POST /api/stock/issue
Content-Type: application/json
```

**Request Body:**
```json
{
  "product_sku": "PROD001",
  "warehouse_code": "WH001",
  "quantity": 100,
  "reference": "SO-2024-001",
  "notes": "Issued for sales order"
}
```

### Transfer Stock
```
POST /api/stock/transfer
Content-Type: application/json
```

**Request Body:**
```json
{
  "product_sku": "PROD001",
  "from_warehouse": "WH001",
  "to_warehouse": "WH002",
  "quantity": 50,
  "reference": "TRANSFER-001",
  "notes": "Rebalancing stock"
}
```

### Adjust Stock
```
POST /api/stock/adjust
Content-Type: application/json
```

**Request Body:**
```json
{
  "product_sku": "PROD001",
  "warehouse_code": "WH001",
  "new_quantity": 485,
  "reason": "Physical count adjustment"
}
```

### Get Low Stock Items
```
GET /api/stock/low-stock?threshold=20
```

**Query Parameters:**
- `threshold` (optional): Percentage below reorder point (default: 20)

### Get Stock Transactions
```
GET /api/stock/transactions?product_sku={sku}&warehouse_code={code}
```

**Query Parameters:**
- `product_sku` (optional): Filter by product
- `warehouse_code` (optional): Filter by warehouse

---

## Suppliers

### List All Suppliers
```
GET /api/suppliers
```

### Create Supplier
```
POST /api/suppliers
Content-Type: application/json
```

**Request Body:**
```json
{
  "code": "SUP001",
  "name": "Global Manufacturing Inc.",
  "contact_person": "Alice Williams",
  "email": "alice@globalmanuf.com",
  "phone": "555-1001",
  "address": "123 Industrial Ave, Detroit, MI 48201",
  "payment_terms": "NET30",
  "status": "ACTIVE",
  "rating": 5
}
```

### Get Supplier
```
GET /api/suppliers/{id}
```

### Update Supplier
```
PUT /api/suppliers/{id}
```

### Delete Supplier
```
DELETE /api/suppliers/{id}
```

---

## Purchase Orders

### List Purchase Orders
```
GET /api/purchase-orders?status={status}
```

**Query Parameters:**
- `status` (optional): Filter by status (DRAFT, APPROVED, SENT, RECEIVED, CLOSED, CANCELLED)

### Create Purchase Order
```
POST /api/purchase-orders
Content-Type: application/json
```

**Request Body:**
```json
{
  "po_number": "PO-2024-001",
  "supplier_id": 1,
  "order_date": "2024-01-01T00:00:00",
  "expected_delivery_date": "2024-01-15T00:00:00",
  "warehouse_code": "WH001",
  "status": "DRAFT",
  "notes": "Quarterly restock",
  "created_by": "john.smith",
  "line_items": [
    {
      "product_sku": "PROD001",
      "quantity_ordered": 500,
      "unit_price": 20.00
    }
  ]
}
```

### Get Purchase Order
```
GET /api/purchase-orders/{po_number}
```

### Update Purchase Order
```
PUT /api/purchase-orders/{po_number}
```

### Delete Purchase Order
```
DELETE /api/purchase-orders/{po_number}
```

---

## Reports

### Inventory Valuation Report
```
GET /api/reports/inventory-valuation
```

**Response:**
```json
{
  "total_inventory_value": 115140.35,
  "report_date": "2024-01-01T00:00:00",
  "items": [
    {
      "product_sku": "PROD001",
      "product_name": "Industrial Widget A",
      "quantity": 800,
      "unit_price": 25.50,
      "total_value": 20400.00
    }
  ]
}
```

### Stock Movement Report
```
GET /api/reports/stock-movement?start_date={date}&end_date={date}&product_sku={sku}
```

**Query Parameters:**
- `start_date` (optional): Start date for report
- `end_date` (optional): End date for report
- `product_sku` (optional): Filter by product

### Warehouse Utilization Report
```
GET /api/reports/warehouse-utilization
```

**Response:**
```json
[
  {
    "warehouse_code": "WH001",
    "warehouse_name": "Main Warehouse",
    "product_count": 5,
    "total_items": 1765,
    "capacity": 10000,
    "utilization_percent": 17.65
  }
]
```

### ABC Analysis Report
```
GET /api/reports/abc-analysis
```

**Response:**
```json
{
  "total_value": 115140.35,
  "items": [
    {
      "product_sku": "PROD002",
      "product_name": "Premium Gadget B",
      "quantity": 250,
      "unit_price": 149.99,
      "total_value": 37497.50,
      "category": "A",
      "cumulative_percent": 32.60
    }
  ]
}
```

### Purchase Order Summary
```
GET /api/reports/purchase-orders?status={status}
```

---

## Error Handling

All errors return a JSON object with an error message:

```json
{
  "error": "Error message description"
}
```

## Best Practices

1. **Idempotency**: Use unique references for transactions to avoid duplicates
2. **Validation**: Always validate stock availability before issuing
3. **Transactions**: Use the transaction history for audit trail
4. **Pagination**: For large datasets, implement pagination (future feature)
5. **Rate Limiting**: Consider implementing rate limiting for production

## Code Examples

### Python Example
```python
import requests

# Create a product
response = requests.post('http://localhost:5000/api/products', json={
    'sku': 'PROD100',
    'name': 'New Product',
    'unit_price': 99.99,
    'reorder_point': 50,
    'reorder_quantity': 200
})

product = response.json()
print(f"Created product: {product['sku']}")

# Receive stock
response = requests.post('http://localhost:5000/api/stock/receipt', json={
    'product_sku': 'PROD100',
    'warehouse_code': 'WH001',
    'quantity': 1000,
    'unit_cost': 85.00,
    'reference': 'PO-001'
})

result = response.json()
print(f"Stock on hand: {result['stock']['quantity_on_hand']}")
```

### cURL Example
```bash
# Get all products
curl http://localhost:5000/api/products

# Create a product
curl -X POST http://localhost:5000/api/products \
  -H "Content-Type: application/json" \
  -d '{"sku":"PROD100","name":"New Product","unit_price":99.99}'

# Get stock levels
curl http://localhost:5000/api/stock/levels

# Issue stock
curl -X POST http://localhost:5000/api/stock/issue \
  -H "Content-Type: application/json" \
  -d '{"product_sku":"PROD001","warehouse_code":"WH001","quantity":50}'
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/blazebbq/dev-/issues
- Email: tomcthermo@gmail.com
