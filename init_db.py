"""
Database initialization script
"""
from app import create_app
from models import db
from models.product import Product
from models.warehouse import Warehouse
from models.supplier import Supplier
from services.inventory_service import InventoryService

def init_db():
    """Initialize database with sample data"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        
        # Check if data already exists
        if Product.query.first():
            print("Database already contains data. Skipping initialization.")
            return
        
        print("Populating sample data...")
        
        # Create sample warehouses
        warehouses = [
            Warehouse(
                code='WH001',
                name='Main Warehouse',
                location='New York, NY',
                capacity=10000,
                manager='John Smith',
                phone='555-0101',
                email='john.smith@example.com',
                status='ACTIVE'
            ),
            Warehouse(
                code='WH002',
                name='West Coast Distribution Center',
                location='Los Angeles, CA',
                capacity=15000,
                manager='Jane Doe',
                phone='555-0102',
                email='jane.doe@example.com',
                status='ACTIVE'
            ),
            Warehouse(
                code='WH003',
                name='Regional Warehouse',
                location='Chicago, IL',
                capacity=8000,
                manager='Bob Johnson',
                phone='555-0103',
                email='bob.johnson@example.com',
                status='ACTIVE'
            )
        ]
        
        for wh in warehouses:
            db.session.add(wh)
        
        # Create sample products
        products = [
            Product(
                sku='PROD001',
                name='Industrial Widget A',
                description='High-quality industrial widget for manufacturing',
                category='Components',
                unit_of_measure='EA',
                unit_price=25.50,
                reorder_point=100,
                reorder_quantity=500,
                status='ACTIVE'
            ),
            Product(
                sku='PROD002',
                name='Premium Gadget B',
                description='Advanced gadget with multiple features',
                category='Electronics',
                unit_of_measure='EA',
                unit_price=149.99,
                reorder_point=50,
                reorder_quantity=200,
                status='ACTIVE'
            ),
            Product(
                sku='PROD003',
                name='Standard Tool Set',
                description='Complete tool set for general use',
                category='Tools',
                unit_of_measure='SET',
                unit_price=89.99,
                reorder_point=25,
                reorder_quantity=100,
                status='ACTIVE'
            ),
            Product(
                sku='PROD004',
                name='Office Supply Kit',
                description='Essential office supplies bundle',
                category='Office',
                unit_of_measure='KIT',
                unit_price=39.99,
                reorder_point=150,
                reorder_quantity=300,
                status='ACTIVE'
            ),
            Product(
                sku='PROD005',
                name='Safety Equipment Package',
                description='Complete safety equipment for workplace',
                category='Safety',
                unit_of_measure='PKG',
                unit_price=199.99,
                reorder_point=30,
                reorder_quantity=150,
                status='ACTIVE'
            )
        ]
        
        for product in products:
            db.session.add(product)
        
        # Create sample suppliers
        suppliers = [
            Supplier(
                code='SUP001',
                name='Global Manufacturing Inc.',
                contact_person='Alice Williams',
                email='alice@globalmanuf.com',
                phone='555-1001',
                address='123 Industrial Ave, Detroit, MI 48201',
                payment_terms='NET30',
                status='ACTIVE',
                rating=5
            ),
            Supplier(
                code='SUP002',
                name='Tech Components Ltd.',
                contact_person='David Chen',
                email='david@techcomp.com',
                phone='555-1002',
                address='456 Silicon Way, San Jose, CA 95110',
                payment_terms='NET45',
                status='ACTIVE',
                rating=4
            ),
            Supplier(
                code='SUP003',
                name='Office Solutions Corp.',
                contact_person='Emma Brown',
                email='emma@officesolutions.com',
                phone='555-1003',
                address='789 Business Blvd, Atlanta, GA 30303',
                payment_terms='NET30',
                status='ACTIVE',
                rating=4
            )
        ]
        
        for supplier in suppliers:
            db.session.add(supplier)
        
        db.session.commit()
        
        # Add initial stock
        print("Adding initial stock levels...")
        
        stock_data = [
            ('PROD001', 'WH001', 500, 20.00),
            ('PROD001', 'WH002', 300, 20.00),
            ('PROD002', 'WH001', 150, 120.00),
            ('PROD002', 'WH003', 100, 120.00),
            ('PROD003', 'WH001', 75, 70.00),
            ('PROD003', 'WH002', 50, 70.00),
            ('PROD004', 'WH001', 200, 32.00),
            ('PROD004', 'WH002', 150, 32.00),
            ('PROD004', 'WH003', 100, 32.00),
            ('PROD005', 'WH001', 80, 160.00),
            ('PROD005', 'WH002', 60, 160.00),
        ]
        
        for sku, wh_code, qty, cost in stock_data:
            InventoryService.receive_stock(
                product_sku=sku,
                warehouse_code=wh_code,
                quantity=qty,
                unit_cost=cost,
                reference='INIT',
                notes='Initial stock load'
            )
        
        print("Database initialization complete!")
        print("\nSample data created:")
        print(f"  - {len(warehouses)} warehouses")
        print(f"  - {len(products)} products")
        print(f"  - {len(suppliers)} suppliers")
        print(f"  - {len(stock_data)} stock records")
        print("\nYou can now run the application with: python app.py")

if __name__ == '__main__':
    init_db()
