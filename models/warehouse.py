"""
Warehouse model for stock management
"""
from datetime import datetime
from models import db

class Warehouse(db.Model):
    """Warehouse entity representing storage locations"""
    __tablename__ = 'warehouses'
    
    code = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(500))
    capacity = db.Column(db.Integer)
    manager = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, INACTIVE
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stock_records = db.relationship('Stock', back_populates='warehouse', cascade='all, delete-orphan')
    transactions = db.relationship('StockTransaction', back_populates='warehouse')
    
    def __repr__(self):
        return f'<Warehouse {self.code}: {self.name}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'code': self.code,
            'name': self.name,
            'location': self.location,
            'capacity': self.capacity,
            'manager': self.manager,
            'phone': self.phone,
            'email': self.email,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
