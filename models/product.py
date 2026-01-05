"""
Product model for stock management
"""
from datetime import datetime
from models import db

class Product(db.Model):
    """Product entity representing items in inventory"""
    __tablename__ = 'products'
    
    sku = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    unit_of_measure = db.Column(db.String(20), default='EA')
    unit_price = db.Column(db.Numeric(10, 2), default=0.00)
    reorder_point = db.Column(db.Integer, default=0)
    reorder_quantity = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, INACTIVE, DISCONTINUED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stock_records = db.relationship('Stock', back_populates='product', cascade='all, delete-orphan')
    transactions = db.relationship('StockTransaction', back_populates='product')
    
    def __repr__(self):
        return f'<Product {self.sku}: {self.name}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'sku': self.sku,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'unit_of_measure': self.unit_of_measure,
            'unit_price': float(self.unit_price) if self.unit_price else 0.0,
            'reorder_point': self.reorder_point,
            'reorder_quantity': self.reorder_quantity,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
