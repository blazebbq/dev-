"""
Purchase Order model for stock management
"""
from datetime import datetime
from models import db

class PurchaseOrder(db.Model):
    """Purchase Order entity"""
    __tablename__ = 'purchase_orders'
    
    po_number = db.Column(db.String(50), primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_delivery_date = db.Column(db.DateTime)
    warehouse_code = db.Column(db.String(20), db.ForeignKey('warehouses.code'))
    status = db.Column(db.String(20), default='DRAFT')  # DRAFT, APPROVED, SENT, RECEIVED, CLOSED, CANCELLED
    total_amount = db.Column(db.Numeric(12, 2), default=0.00)
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    supplier = db.relationship('Supplier', back_populates='purchase_orders')
    warehouse = db.relationship('Warehouse')
    line_items = db.relationship('PurchaseOrderLine', back_populates='purchase_order', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<PurchaseOrder {self.po_number}: {self.status}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'po_number': self.po_number,
            'supplier_id': self.supplier_id,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'expected_delivery_date': self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            'warehouse_code': self.warehouse_code,
            'status': self.status,
            'total_amount': float(self.total_amount) if self.total_amount else 0.0,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'line_items': [item.to_dict() for item in self.line_items]
        }

class PurchaseOrderLine(db.Model):
    """Purchase Order Line Item"""
    __tablename__ = 'purchase_order_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), db.ForeignKey('purchase_orders.po_number'), nullable=False)
    line_number = db.Column(db.Integer, nullable=False)
    product_sku = db.Column(db.String(50), db.ForeignKey('products.sku'), nullable=False)
    quantity_ordered = db.Column(db.Integer, nullable=False)
    quantity_received = db.Column(db.Integer, default=0)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    line_total = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Relationships
    purchase_order = db.relationship('PurchaseOrder', back_populates='line_items')
    product = db.relationship('Product')
    
    __table_args__ = (
        db.UniqueConstraint('po_number', 'line_number', name='unique_po_line'),
    )
    
    def __repr__(self):
        return f'<PurchaseOrderLine {self.po_number}-{self.line_number}: {self.product_sku}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'po_number': self.po_number,
            'line_number': self.line_number,
            'product_sku': self.product_sku,
            'quantity_ordered': self.quantity_ordered,
            'quantity_received': self.quantity_received,
            'unit_price': float(self.unit_price) if self.unit_price else 0.0,
            'line_total': float(self.line_total) if self.line_total else 0.0
        }
