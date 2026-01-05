"""
User model for authentication and authorization
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from models import db

class User(UserMixin, db.Model):
    """User entity for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200))
    role = db.Column(db.String(50), default='USER')  # ADMIN, MANAGER, USER, VIEWER
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        permissions = {
            'ADMIN': ['view', 'create', 'edit', 'delete', 'manage_users', 'reports'],
            'MANAGER': ['view', 'create', 'edit', 'reports'],
            'USER': ['view', 'create', 'edit'],
            'VIEWER': ['view']
        }
        return permission in permissions.get(self.role, [])
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class UnitOfMeasure(db.Model):
    """Custom unit of measure definitions"""
    __tablename__ = 'units_of_measure'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    unit_type = db.Column(db.String(50))  # WEIGHT, VOLUME, LENGTH, COUNT, etc.
    base_unit = db.Column(db.String(20))  # For conversions
    conversion_factor = db.Column(db.Numeric(15, 6))  # Conversion to base unit
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UnitOfMeasure {self.code}: {self.name}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'unit_type': self.unit_type,
            'base_unit': self.base_unit,
            'conversion_factor': float(self.conversion_factor) if self.conversion_factor else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Bin(db.Model):
    """Bin/Location within a warehouse"""
    __tablename__ = 'bins'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    warehouse_code = db.Column(db.String(20), db.ForeignKey('warehouses.code'), nullable=False)
    aisle = db.Column(db.String(20))
    rack = db.Column(db.String(20))
    level = db.Column(db.String(20))
    position = db.Column(db.String(20))
    bin_type = db.Column(db.String(50))  # STORAGE, PICKING, RECEIVING, SHIPPING
    capacity = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    warehouse = db.relationship('Warehouse')
    stock_items = db.relationship('BinStock', back_populates='bin', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Bin {self.code} @ {self.warehouse_code}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'code': self.code,
            'warehouse_code': self.warehouse_code,
            'aisle': self.aisle,
            'rack': self.rack,
            'level': self.level,
            'position': self.position,
            'bin_type': self.bin_type,
            'capacity': self.capacity,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class BinStock(db.Model):
    """Stock at bin level"""
    __tablename__ = 'bin_stock'
    
    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.Integer, db.ForeignKey('bins.id'), nullable=False)
    product_sku = db.Column(db.String(50), db.ForeignKey('products.sku'), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bin = db.relationship('Bin', back_populates='stock_items')
    product = db.relationship('Product')
    
    __table_args__ = (
        db.UniqueConstraint('bin_id', 'product_sku', name='unique_bin_product'),
    )
    
    def __repr__(self):
        return f'<BinStock {self.product_sku} @ Bin {self.bin_id}: {self.quantity}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'bin_id': self.bin_id,
            'bin_code': self.bin.code if self.bin else None,
            'product_sku': self.product_sku,
            'product_name': self.product.name if self.product else None,
            'quantity': self.quantity,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class WorkOrder(db.Model):
    """Work orders for picking and fulfillment"""
    __tablename__ = 'work_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    order_type = db.Column(db.String(50))  # PICK, PACK, SHIP, RECEIVE, COUNT
    warehouse_code = db.Column(db.String(20), db.ForeignKey('warehouses.code'))
    status = db.Column(db.String(50), default='OPEN')  # OPEN, IN_PROGRESS, COMPLETED, CANCELLED
    priority = db.Column(db.String(20), default='NORMAL')  # LOW, NORMAL, HIGH, URGENT
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    warehouse = db.relationship('Warehouse')
    assigned_user = db.relationship('User', foreign_keys=[assigned_to])
    creator = db.relationship('User', foreign_keys=[created_by])
    line_items = db.relationship('WorkOrderLine', back_populates='work_order', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<WorkOrder {self.order_number}: {self.status}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'order_number': self.order_number,
            'order_type': self.order_type,
            'warehouse_code': self.warehouse_code,
            'status': self.status,
            'priority': self.priority,
            'assigned_to': self.assigned_to,
            'assigned_user_name': self.assigned_user.full_name if self.assigned_user else None,
            'created_by': self.created_by,
            'creator_name': self.creator.full_name if self.creator else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'line_items': [item.to_dict() for item in self.line_items]
        }

class WorkOrderLine(db.Model):
    """Work order line items"""
    __tablename__ = 'work_order_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=False)
    line_number = db.Column(db.Integer, nullable=False)
    product_sku = db.Column(db.String(50), db.ForeignKey('products.sku'), nullable=False)
    from_bin_id = db.Column(db.Integer, db.ForeignKey('bins.id'))
    quantity_required = db.Column(db.Integer, nullable=False)
    quantity_picked = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='PENDING')  # PENDING, PICKED, SHORT
    
    # Relationships
    work_order = db.relationship('WorkOrder', back_populates='line_items')
    product = db.relationship('Product')
    from_bin = db.relationship('Bin')
    
    __table_args__ = (
        db.UniqueConstraint('work_order_id', 'line_number', name='unique_wo_line'),
    )
    
    def __repr__(self):
        return f'<WorkOrderLine {self.work_order_id}-{self.line_number}: {self.product_sku}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'work_order_id': self.work_order_id,
            'line_number': self.line_number,
            'product_sku': self.product_sku,
            'product_name': self.product.name if self.product else None,
            'from_bin_id': self.from_bin_id,
            'from_bin_code': self.from_bin.code if self.from_bin else None,
            'quantity_required': self.quantity_required,
            'quantity_picked': self.quantity_picked,
            'status': self.status
        }
