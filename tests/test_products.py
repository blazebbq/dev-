"""
Tests for product management
"""
import pytest
from app import create_app
from models import db
from models.product import Product

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

def test_create_product(client):
    """Test creating a new product"""
    response = client.post('/api/products', json={
        'sku': 'TEST001',
        'name': 'Test Product',
        'description': 'Test description',
        'unit_price': 99.99,
        'reorder_point': 10,
        'reorder_quantity': 50
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['sku'] == 'TEST001'
    assert data['name'] == 'Test Product'

def test_get_products(client):
    """Test getting all products"""
    # Create a product first
    client.post('/api/products', json={
        'sku': 'TEST001',
        'name': 'Test Product',
        'unit_price': 99.99
    })
    
    response = client.get('/api/products')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['sku'] == 'TEST001'

def test_get_product_detail(client):
    """Test getting a specific product"""
    # Create a product first
    client.post('/api/products', json={
        'sku': 'TEST001',
        'name': 'Test Product',
        'unit_price': 99.99
    })
    
    response = client.get('/api/products/TEST001')
    assert response.status_code == 200
    data = response.get_json()
    assert data['sku'] == 'TEST001'

def test_update_product(client):
    """Test updating a product"""
    # Create a product first
    client.post('/api/products', json={
        'sku': 'TEST001',
        'name': 'Test Product',
        'unit_price': 99.99
    })
    
    # Update the product
    response = client.put('/api/products/TEST001', json={
        'name': 'Updated Product',
        'unit_price': 149.99
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Updated Product'
    assert data['unit_price'] == 149.99

def test_delete_product(client):
    """Test deleting a product"""
    # Create a product first
    client.post('/api/products', json={
        'sku': 'TEST001',
        'name': 'Test Product',
        'unit_price': 99.99
    })
    
    # Delete the product
    response = client.delete('/api/products/TEST001')
    assert response.status_code == 204
    
    # Verify it's deleted
    response = client.get('/api/products/TEST001')
    assert response.status_code == 404

def test_duplicate_product(client):
    """Test creating a product with duplicate SKU"""
    client.post('/api/products', json={
        'sku': 'TEST001',
        'name': 'Test Product',
        'unit_price': 99.99
    })
    
    # Try to create another product with same SKU
    response = client.post('/api/products', json={
        'sku': 'TEST001',
        'name': 'Another Product',
        'unit_price': 79.99
    })
    
    assert response.status_code == 400
    assert 'error' in response.get_json()
