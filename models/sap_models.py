"""
SAP-style data models for MM/IM functionality
Plant, Storage Location, Material Document, Movement Types, etc.
"""
from datetime import datetime, date
from models import db

class SAPPlant(db.Model):
    """Plant (SAP-style organizational unit)"""
    __tablename__ = 'sap_plants'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(4), unique=True, nullable=False)  # e.g., "1000"
    name = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100))
    country = db.Column(db.String(50))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    storage_locations = db.relationship('SAPStorageLocation', back_populates='plant', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<SAPPlant {self.code}: {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'city': self.city,
            'country': self.country,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SAPStorageLocation(db.Model):
    """Storage Location within a Plant"""
    __tablename__ = 'sap_storage_locations'
    
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('sap_plants.id'), nullable=False)
    code = db.Column(db.String(4), nullable=False)  # e.g., "0001"
    name = db.Column(db.String(200), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    plant = db.relationship('SAPPlant', back_populates='storage_locations')
    
    __table_args__ = (
        db.UniqueConstraint('plant_id', 'code', name='unique_plant_sloc'),
    )
    
    def __repr__(self):
        return f'<SAPStorageLocation {self.plant.code if self.plant else "?"}-{self.code}: {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'plant_id': self.plant_id,
            'plant_code': self.plant.code if self.plant else None,
            'code': self.code,
            'name': self.name,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SAPBatch(db.Model):
    """Batch/Lot tracking for materials"""
    __tablename__ = 'sap_batches'
    
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)  # Using existing Product as Material
    batch_number = db.Column(db.String(50), nullable=False)
    expiry_date = db.Column(db.Date)
    production_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    material = db.relationship('Product')
    
    __table_args__ = (
        db.UniqueConstraint('material_id', 'batch_number', name='unique_material_batch'),
    )
    
    def __repr__(self):
        return f'<SAPBatch {self.material.sku if self.material else "?"}-{self.batch_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'material_id': self.material_id,
            'material_sku': self.material.sku if self.material else None,
            'batch_number': self.batch_number,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'production_date': self.production_date.isoformat() if self.production_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SAPStockOnHand(db.Model):
    """Stock on hand by Material, Plant, Storage Location, Batch"""
    __tablename__ = 'sap_stock_on_hand'
    
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    plant_id = db.Column(db.Integer, db.ForeignKey('sap_plants.id'), nullable=False)
    sloc_id = db.Column(db.Integer, db.ForeignKey('sap_storage_locations.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('sap_batches.id'))
    quantity = db.Column(db.Numeric(15, 3), default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    material = db.relationship('Product')
    plant = db.relationship('SAPPlant')
    sloc = db.relationship('SAPStorageLocation')
    batch = db.relationship('SAPBatch')
    
    __table_args__ = (
        db.UniqueConstraint('material_id', 'plant_id', 'sloc_id', 'batch_id', name='unique_stock_location'),
    )
    
    def __repr__(self):
        return f'<SAPStockOnHand {self.material.sku if self.material else "?"} @ {self.plant.code if self.plant else "?"}/{self.sloc.code if self.sloc else "?"}: {self.quantity}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'material_id': self.material_id,
            'material_sku': self.material.sku if self.material else None,
            'material_name': self.material.name if self.material else None,
            'plant_id': self.plant_id,
            'plant_code': self.plant.code if self.plant else None,
            'sloc_id': self.sloc_id,
            'sloc_code': self.sloc.code if self.sloc else None,
            'batch_id': self.batch_id,
            'batch_number': self.batch.batch_number if self.batch else None,
            'quantity': float(self.quantity) if self.quantity else 0.0,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class SAPMovementType(db.Model):
    """Movement type definitions (101, 102, 261, etc.)"""
    __tablename__ = 'sap_movement_types'
    
    code = db.Column(db.String(3), primary_key=True)  # "101"
    name = db.Column(db.String(100), nullable=False)  # "Goods Receipt"
    description = db.Column(db.Text)
    category = db.Column(db.String(20))  # GR, GI, TR, SCRAP, REV
    reversal_code = db.Column(db.String(3))  # "102" for reversing "101"
    required_fields = db.Column(db.Text)  # JSON string
    ui_fields = db.Column(db.Text)  # JSON string
    allow_batch = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SAPMovementType {self.code}: {self.name}>'
    
    def to_dict(self):
        import json
        return {
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'reversal_code': self.reversal_code,
            'required_fields': json.loads(self.required_fields) if self.required_fields else [],
            'ui_fields': json.loads(self.ui_fields) if self.ui_fields else [],
            'allow_batch': self.allow_batch
        }


class SAPMaterialDocument(db.Model):
    """Material Document (header)"""
    __tablename__ = 'sap_material_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    doc_number = db.Column(db.String(10), unique=True, nullable=False)  # "4900000123"
    doc_date = db.Column(db.Date, nullable=False)
    posting_date = db.Column(db.Date, nullable=False)
    created_by = db.Column(db.String(100), nullable=False)
    header_text = db.Column(db.Text)
    reference_text = db.Column(db.String(200))
    reversal_of_doc_id = db.Column(db.Integer, db.ForeignKey('sap_material_documents.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('SAPMaterialDocumentItem', back_populates='document', cascade='all, delete-orphan', foreign_keys='SAPMaterialDocumentItem.matdoc_id')
    reversal_of = db.relationship('SAPMaterialDocument', remote_side=[id], backref='reversed_by')
    
    def __repr__(self):
        return f'<SAPMaterialDocument {self.doc_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'doc_number': self.doc_number,
            'doc_date': self.doc_date.isoformat() if self.doc_date else None,
            'posting_date': self.posting_date.isoformat() if self.posting_date else None,
            'created_by': self.created_by,
            'header_text': self.header_text,
            'reference_text': self.reference_text,
            'reversal_of_doc_id': self.reversal_of_doc_id,
            'reversal_of_doc_number': self.reversal_of.doc_number if self.reversal_of else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'items': [item.to_dict() for item in self.items]
        }


class SAPMaterialDocumentItem(db.Model):
    """Material Document item (line item)"""
    __tablename__ = 'sap_material_document_items'
    
    id = db.Column(db.Integer, primary_key=True)
    matdoc_id = db.Column(db.Integer, db.ForeignKey('sap_material_documents.id'), nullable=False)
    line_no = db.Column(db.Integer, nullable=False)  # 10, 20, 30...
    movement_type = db.Column(db.String(3), db.ForeignKey('sap_movement_types.code'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    plant_id = db.Column(db.Integer, db.ForeignKey('sap_plants.id'), nullable=False)
    sloc_from_id = db.Column(db.Integer, db.ForeignKey('sap_storage_locations.id'))
    sloc_to_id = db.Column(db.Integer, db.ForeignKey('sap_storage_locations.id'))
    batch_id = db.Column(db.Integer, db.ForeignKey('sap_batches.id'))
    quantity = db.Column(db.Numeric(15, 3), nullable=False)
    uom = db.Column(db.String(3), nullable=False)
    item_text = db.Column(db.Text)
    reversal_of_item_id = db.Column(db.Integer, db.ForeignKey('sap_material_document_items.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    document = db.relationship('SAPMaterialDocument', back_populates='items', foreign_keys=[matdoc_id])
    movement_type_ref = db.relationship('SAPMovementType')
    material = db.relationship('Product')
    plant = db.relationship('SAPPlant')
    sloc_from = db.relationship('SAPStorageLocation', foreign_keys=[sloc_from_id])
    sloc_to = db.relationship('SAPStorageLocation', foreign_keys=[sloc_to_id])
    batch = db.relationship('SAPBatch')
    reversal_of_item = db.relationship('SAPMaterialDocumentItem', remote_side=[id], backref='reversed_by_item')
    
    __table_args__ = (
        db.UniqueConstraint('matdoc_id', 'line_no', name='unique_matdoc_line'),
    )
    
    def __repr__(self):
        return f'<SAPMaterialDocumentItem {self.matdoc_id}-{self.line_no}: {self.movement_type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'matdoc_id': self.matdoc_id,
            'line_no': self.line_no,
            'movement_type': self.movement_type,
            'movement_type_name': self.movement_type_ref.name if self.movement_type_ref else None,
            'material_id': self.material_id,
            'material_sku': self.material.sku if self.material else None,
            'material_name': self.material.name if self.material else None,
            'plant_id': self.plant_id,
            'plant_code': self.plant.code if self.plant else None,
            'sloc_from_id': self.sloc_from_id,
            'sloc_from_code': self.sloc_from.code if self.sloc_from else None,
            'sloc_to_id': self.sloc_to_id,
            'sloc_to_code': self.sloc_to.code if self.sloc_to else None,
            'batch_id': self.batch_id,
            'batch_number': self.batch.batch_number if self.batch else None,
            'quantity': float(self.quantity) if self.quantity else 0.0,
            'uom': self.uom,
            'item_text': self.item_text,
            'reversal_of_item_id': self.reversal_of_item_id
        }


class SAPDocSequence(db.Model):
    """Document numbering sequence"""
    __tablename__ = 'sap_doc_sequences'
    
    key = db.Column(db.String(20), primary_key=True)  # "MATDOC"
    next_number = db.Column(db.Integer, default=1)
    
    def __repr__(self):
        return f'<SAPDocSequence {self.key}: {self.next_number}>'


class SAPAuditLog(db.Model):
    """Audit trail for all SAP transactions"""
    __tablename__ = 'sap_audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # POST_MATDOC, REVERSE_MATDOC, etc.
    entity_type = db.Column(db.String(50))  # MaterialDocument, Material, StockOnHand
    entity_id = db.Column(db.String(50))
    message = db.Column(db.Text)
    before_json = db.Column(db.Text)
    after_json = db.Column(db.Text)
    
    def __repr__(self):
        return f'<SAPAuditLog {self.timestamp} {self.action} by {self.username}>'
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'username': self.username,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'message': self.message,
            'before': json.loads(self.before_json) if self.before_json else None,
            'after': json.loads(self.after_json) if self.after_json else None
        }


class SAPConfig(db.Model):
    """System configuration"""
    __tablename__ = 'sap_config'
    
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(500))
    description = db.Column(db.Text)
    
    def __repr__(self):
        return f'<SAPConfig {self.key}={self.value}>'
