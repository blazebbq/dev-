# Stock Management System

A comprehensive stock management software similar to SAP ERP, designed for inventory tracking, warehouse management, and supply chain operations.

## Features

### Core Modules
- **Inventory Management**: Track products, stock levels, and locations
- **Warehouse Management**: Multiple warehouse support with location tracking
- **Purchase Orders**: Create and manage purchase orders with suppliers
- **Stock Movements**: Track all stock transactions (receipts, issues, transfers)
- **Reporting**: Real-time inventory reports and analytics
- **Supplier Management**: Maintain supplier information and relationships

### Key Capabilities
- Real-time stock level monitoring
- Multi-warehouse support
- Automatic reorder point alerts
- Stock valuation (FIFO, LIFO, Average Cost)
- Batch and serial number tracking
- Transaction history and audit trail
- RESTful API for integration

## Technology Stack

- **Backend**: Python 3.8+
- **Framework**: Flask (REST API)
- **Database**: SQLite (development), PostgreSQL (production ready)
- **ORM**: SQLAlchemy
- **API Documentation**: OpenAPI/Swagger

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/blazebbq/dev-.git
cd dev-
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python init_db.py
```

5. Run the application:
```bash
python app.py
```

The application will start on `http://localhost:5000`

## API Documentation

Once the application is running, visit:
- API Documentation: `http://localhost:5000/api/docs`
- Swagger UI: `http://localhost:5000/swagger`

## Quick Start Guide

### Creating a Product
```bash
curl -X POST http://localhost:5000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "PROD001",
    "name": "Widget A",
    "description": "High-quality widget",
    "unit_price": 25.50,
    "reorder_point": 100,
    "reorder_quantity": 500
  }'
```

### Creating a Warehouse
```bash
curl -X POST http://localhost:5000/api/warehouses \
  -H "Content-Type: application/json" \
  -d '{
    "code": "WH001",
    "name": "Main Warehouse",
    "location": "New York, NY"
  }'
```

### Recording Stock Receipt
```bash
curl -X POST http://localhost:5000/api/stock/receipt \
  -H "Content-Type: application/json" \
  -d '{
    "product_sku": "PROD001",
    "warehouse_code": "WH001",
    "quantity": 1000,
    "unit_cost": 20.00,
    "reference": "PO-2024-001"
  }'
```

### Checking Stock Levels
```bash
curl http://localhost:5000/api/stock/levels
```

## Project Structure

```
.
├── app.py                  # Main application entry point
├── config.py              # Configuration settings
├── init_db.py            # Database initialization script
├── requirements.txt       # Python dependencies
├── models/               # Data models
│   ├── product.py
│   ├── warehouse.py
│   ├── stock.py
│   ├── supplier.py
│   └── purchase_order.py
├── controllers/          # API controllers
│   ├── product_controller.py
│   ├── warehouse_controller.py
│   ├── stock_controller.py
│   ├── supplier_controller.py
│   └── purchase_order_controller.py
├── services/            # Business logic layer
│   ├── inventory_service.py
│   ├── stock_movement_service.py
│   └── reporting_service.py
├── static/              # Static files (CSS, JS)
│   ├── css/
│   └── js/
├── templates/           # HTML templates
│   ├── index.html
│   ├── products.html
│   ├── warehouses.html
│   └── reports.html
└── tests/              # Test suite
    ├── test_products.py
    ├── test_stock.py
    └── test_reports.py
```

## Database Schema

### Products
- SKU (Primary Key)
- Name
- Description
- Unit Price
- Reorder Point
- Reorder Quantity
- Status (Active/Inactive)

### Warehouses
- Code (Primary Key)
- Name
- Location
- Capacity

### Stock
- Product SKU (Foreign Key)
- Warehouse Code (Foreign Key)
- Quantity on Hand
- Reserved Quantity
- Available Quantity

### Stock Transactions
- Transaction ID (Primary Key)
- Product SKU
- Warehouse Code
- Transaction Type (Receipt, Issue, Transfer, Adjustment)
- Quantity
- Unit Cost
- Reference Number
- Timestamp

### Suppliers
- Supplier ID (Primary Key)
- Name
- Contact Person
- Email
- Phone
- Address

### Purchase Orders
- PO Number (Primary Key)
- Supplier ID
- Order Date
- Expected Delivery Date
- Status (Draft, Approved, Received, Closed)
- Total Amount

## Testing

Run the test suite:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=. tests/
```

## Configuration

Edit `config.py` to customize:
- Database connection
- Server port and host
- Debug mode
- API rate limiting
- Authentication settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Support

For issues and questions:
- GitHub Issues: https://github.com/blazebbq/dev-/issues
- Email: tomcthermo@gmail.com

## Roadmap

- [ ] User authentication and authorization
- [ ] Role-based access control (RBAC)
- [ ] Barcode scanning integration
- [ ] Mobile application
- [ ] Advanced analytics and forecasting
- [ ] Integration with accounting systems
- [ ] Multi-currency support
- [ ] Automated email notifications
- [ ] Export to Excel/PDF
- [ ] Dashboard with real-time charts
