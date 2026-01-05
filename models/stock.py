"""
Stock model for inventory tracking
"""
from datetime import datetime
from models import db

class Stock(db.Model):
    """Stock entity representing inventory levels"""
    __tablename__ = 'stock'
    
    id = db.Column(db.Integer, primary_key=True)
    product_sku = db.Column(db.String(50), db.ForeignKey('products.sku'), nullable=False)
    warehouse_code = db.Column(db.String(20), db.ForeignKey('warehouses.code'), nullable=False)
    quantity_on_hand = db.Column(db.Integer, default=0)
    quantity_reserved = db.Column(db.Integer, default=0)
    quantity_available = db.Column(db.Integer, default=0)
    last_stock_take = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', back_populates='stock_records')
    warehouse = db.relationship('Warehouse', back_populates='stock_records')
    
    # Unique constraint: one stock record per product per warehouse
    __table_args__ = (
        db.UniqueConstraint('product_sku', 'warehouse_code', name='unique_stock_location'),
    )
    
    def __repr__(self):
        return f'<Stock {self.product_sku} @ {self.warehouse_code}: {self.quantity_on_hand}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'product_sku': self.product_sku,
            'warehouse_code': self.warehouse_code,
            'quantity_on_hand': self.quantity_on_hand,
            'quantity_reserved': self.quantity_reserved,
            'quantity_available': self.quantity_available,
            'last_stock_take': self.last_stock_take.isoformat() if self.last_stock_take else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class StockTransaction(db.Model):
    """Stock transaction entity for audit trail"""
    __tablename__ = 'stock_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(20), nullable=False)  # RECEIPT, ISSUE, TRANSFER, ADJUSTMENT
    product_sku = db.Column(db.String(50), db.ForeignKey('products.sku'), nullable=False)
    warehouse_code = db.Column(db.String(20), db.ForeignKey('warehouses.code'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2))
    reference = db.Column(db.String(100))  # PO number, transfer number, etc.
    notes = db.Column(db.Text)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100))
    
    # For transfers
    to_warehouse_code = db.Column(db.String(20), db.ForeignKey('warehouses.code'))
    
    # Relationships
    product = db.relationship('Product', back_populates='transactions')
    warehouse = db.relationship('Warehouse', foreign_keys=[warehouse_code], back_populates='transactions')
    to_warehouse = db.relationship('Warehouse', foreign_keys=[to_warehouse_code])
    
    def __repr__(self):
        return f'<StockTransaction {self.id}: {self.transaction_type} {self.quantity} {self.product_sku}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'transaction_type': self.transaction_type,
            'product_sku': self.product_sku,
            'warehouse_code': self.warehouse_code,
            'quantity': self.quantity,
            'unit_cost': float(self.unit_cost) if self.unit_cost else None,
            'reference': self.reference,
            'notes': self.notes,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'created_by': self.created_by,
            'to_warehouse_code': self.to_warehouse_code
        }
