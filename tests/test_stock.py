"""
Tests for stock management
"""
import pytest
from app import create_app
from models import db
from models.product import Product
from models.warehouse import Warehouse
from models.stock import Stock
from services.inventory_service import InventoryService

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create test data
        product = Product(
            sku='TEST001',
            name='Test Product',
            unit_price=50.00,
            reorder_point=10,
            reorder_quantity=100
        )
        db.session.add(product)
        
        warehouse = Warehouse(
            code='WH001',
            name='Test Warehouse',
            location='Test Location'
        )
        db.session.add(warehouse)
        
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

def test_receive_stock(app, client):
    """Test receiving stock"""
    with app.app_context():
        result = InventoryService.receive_stock(
            product_sku='TEST001',
            warehouse_code='WH001',
            quantity=100,
            unit_cost=45.00,
            reference='PO-001'
        )
        
        assert result['stock']['quantity_on_hand'] == 100
        assert result['stock']['quantity_available'] == 100
        assert result['transaction']['transaction_type'] == 'RECEIPT'

def test_issue_stock(app, client):
    """Test issuing stock"""
    with app.app_context():
        # Receive stock first
        InventoryService.receive_stock(
            product_sku='TEST001',
            warehouse_code='WH001',
            quantity=100,
            unit_cost=45.00
        )
        
        # Issue stock
        result = InventoryService.issue_stock(
            product_sku='TEST001',
            warehouse_code='WH001',
            quantity=30,
            reference='SO-001'
        )
        
        assert result['stock']['quantity_on_hand'] == 70
        assert result['stock']['quantity_available'] == 70

def test_insufficient_stock(app, client):
    """Test issuing more stock than available"""
    with app.app_context():
        # Receive stock first
        InventoryService.receive_stock(
            product_sku='TEST001',
            warehouse_code='WH001',
            quantity=50,
            unit_cost=45.00
        )
        
        # Try to issue more than available
        with pytest.raises(ValueError, match='Insufficient stock'):
            InventoryService.issue_stock(
                product_sku='TEST001',
                warehouse_code='WH001',
                quantity=100
            )

def test_stock_transfer(app, client):
    """Test transferring stock between warehouses"""
    with app.app_context():
        # Create second warehouse
        warehouse2 = Warehouse(
            code='WH002',
            name='Second Warehouse',
            location='Another Location'
        )
        db.session.add(warehouse2)
        db.session.commit()
        
        # Receive stock at first warehouse
        InventoryService.receive_stock(
            product_sku='TEST001',
            warehouse_code='WH001',
            quantity=100,
            unit_cost=45.00
        )
        
        # Transfer stock
        result = InventoryService.transfer_stock(
            product_sku='TEST001',
            from_warehouse='WH001',
            to_warehouse='WH002',
            quantity=30
        )
        
        assert result['source_stock']['quantity_on_hand'] == 70
        assert result['destination_stock']['quantity_on_hand'] == 30

def test_stock_adjustment(app, client):
    """Test stock adjustment"""
    with app.app_context():
        # Create initial stock
        InventoryService.receive_stock(
            product_sku='TEST001',
            warehouse_code='WH001',
            quantity=100,
            unit_cost=45.00
        )
        
        # Adjust stock
        result = InventoryService.adjust_stock(
            product_sku='TEST001',
            warehouse_code='WH001',
            new_quantity=85,
            reason='Physical count adjustment'
        )
        
        assert result['stock']['quantity_on_hand'] == 85
        assert result['transaction']['transaction_type'] == 'ADJUSTMENT'

def test_get_stock_levels(app, client):
    """Test getting stock levels"""
    with app.app_context():
        # Receive stock
        InventoryService.receive_stock(
            product_sku='TEST001',
            warehouse_code='WH001',
            quantity=100,
            unit_cost=45.00
        )
        
        # Get stock level
        stock_info = InventoryService.get_stock_level('TEST001')
        
        assert stock_info['product_sku'] == 'TEST001'
        assert stock_info['total_quantity_on_hand'] == 100
        assert stock_info['total_quantity_available'] == 100

def test_low_stock_items(app, client):
    """Test getting low stock items"""
    with app.app_context():
        # Receive stock below reorder point
        InventoryService.receive_stock(
            product_sku='TEST001',
            warehouse_code='WH001',
            quantity=5,  # Reorder point is 10
            unit_cost=45.00
        )
        
        # Get low stock items
        low_stock = InventoryService.get_low_stock_items()
        
        assert len(low_stock) > 0
        assert low_stock[0]['product_sku'] == 'TEST001'
        assert low_stock[0]['needs_immediate_reorder'] is True
