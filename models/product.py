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
    unit_of_measure_id = db.Column(db.Integer, db.ForeignKey('units_of_measure.id'))
    unit_of_measure = db.Column(db.String(20), default='EA')  # Keep for backward compatibility
    unit_price = db.Column(db.Numeric(10, 2), default=0.00)
    reorder_point = db.Column(db.Integer, default=0)
    reorder_quantity = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, INACTIVE, DISCONTINUED
    image_url = db.Column(db.String(500))
    barcode = db.Column(db.String(100))
    serial_number_required = db.Column(db.Boolean, default=False)
    batch_tracking_required = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stock_records = db.relationship('Stock', back_populates='product', cascade='all, delete-orphan')
    transactions = db.relationship('StockTransaction', back_populates='product')
    custom_unit = db.relationship('UnitOfMeasure', foreign_keys=[unit_of_measure_id])
    
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
            'unit_of_measure_id': self.unit_of_measure_id,
            'custom_unit_name': self.custom_unit.name if self.custom_unit else None,
            'unit_price': float(self.unit_price) if self.unit_price else 0.0,
            'reorder_point': self.reorder_point,
            'reorder_quantity': self.reorder_quantity,
            'status': self.status,
            'image_url': self.image_url,
            'barcode': self.barcode,
            'serial_number_required': self.serial_number_required,
            'batch_tracking_required': self.batch_tracking_required,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
