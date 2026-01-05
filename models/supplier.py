"""
Supplier model for stock management
"""
from datetime import datetime
from models import db

class Supplier(db.Model):
    """Supplier entity representing vendors"""
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    payment_terms = db.Column(db.String(50))  # NET30, NET60, etc.
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, INACTIVE
    rating = db.Column(db.Integer)  # 1-5 rating
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    purchase_orders = db.relationship('PurchaseOrder', back_populates='supplier')
    
    def __repr__(self):
        return f'<Supplier {self.code}: {self.name}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'contact_person': self.contact_person,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'payment_terms': self.payment_terms,
            'status': self.status,
            'rating': self.rating,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
