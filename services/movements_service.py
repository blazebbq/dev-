"""
SAP-style movements service
Handles material document posting, reversals, stock updates, and validation
"""
from datetime import datetime, date
from decimal import Decimal
from models import db
from models.product import Product
from models.sap_models import (
    SAPPlant, SAPStorageLocation, SAPBatch, SAPStockOnHand,
    SAPMovementType, SAPMaterialDocument, SAPMaterialDocumentItem,
    SAPDocSequence, SAPAuditLog, SAPConfig
)
import json


class MovementsService:
    """Service for SAP MM/IM goods movements"""
    
    @staticmethod
    def validate_migo_payload(payload):
        """
        Validate a goods movement payload before posting
        Returns: (ok: bool, errors: list, warnings: list)
        """
        errors = []
        warnings = []
        
        # Extract data
        movement_type = payload.get('movement_type')
        material_sku = payload.get('material_sku')
        plant_code = payload.get('plant_code')
        quantity = payload.get('quantity')
        uom = payload.get('uom')
        
        # Validate movement type
        if not movement_type:
            errors.append("Movement type is required")
        else:
            mvt = SAPMovementType.query.get(movement_type)
            if not mvt:
                errors.append(f"Movement type {movement_type} does not exist")
        
        # Validate material
        if not material_sku:
            errors.append("Material is required")
        else:
            material = Product.query.filter_by(sku=material_sku).first()
            if not material:
                errors.append(f"Material {material_sku} does not exist")
            elif material.status != 'ACTIVE':
                errors.append(f"Material {material_sku} is not active")
        
        # Validate plant
        if not plant_code:
            errors.append("Plant is required")
        else:
            plant = SAPPlant.query.filter_by(code=plant_code).first()
            if not plant:
                errors.append(f"Plant {plant_code} does not exist")
        
        # Validate quantity
        if not quantity or Decimal(str(quantity)) <= 0:
            errors.append("Quantity must be greater than 0")
        
        # Validate storage locations based on movement type
        if movement_type:
            mvt = SAPMovementType.query.get(movement_type)
            if mvt:
                if mvt.category == 'GR':  # Goods Receipt
                    sloc_to_code = payload.get('sloc_to_code')
                    if not sloc_to_code:
                        errors.append("Destination storage location is required for goods receipt")
                    elif plant_code:
                        plant = SAPPlant.query.filter_by(code=plant_code).first()
                        if plant:
                            sloc_to = SAPStorageLocation.query.filter_by(plant_id=plant.id, code=sloc_to_code).first()
                            if not sloc_to:
                                errors.append(f"Storage location {sloc_to_code} does not exist in plant {plant_code}")
                
                elif mvt.category == 'GI':  # Goods Issue
                    sloc_from_code = payload.get('sloc_from_code')
                    if not sloc_from_code:
                        errors.append("Source storage location is required for goods issue")
                    elif plant_code and material_sku:
                        # Check if enough stock available
                        plant = SAPPlant.query.filter_by(code=plant_code).first()
                        material = Product.query.filter_by(sku=material_sku).first()
                        if plant and material:
                            sloc_from = SAPStorageLocation.query.filter_by(plant_id=plant.id, code=sloc_from_code).first()
                            if sloc_from:
                                stock = SAPStockOnHand.query.filter_by(
                                    material_id=material.id,
                                    plant_id=plant.id,
                                    sloc_id=sloc_from.id,
                                    batch_id=payload.get('batch_id')
                                ).first()
                                
                                available_qty = stock.quantity if stock else Decimal('0')
                                allow_negative = MovementsService.get_config('allow_negative_stock', 'false') == 'true'
                                
                                if available_qty < Decimal(str(quantity)):
                                    if not allow_negative:
                                        errors.append(f"Insufficient stock. Available: {available_qty}, Required: {quantity}")
                                    else:
                                        warnings.append(f"Stock will become negative. Available: {available_qty}, Required: {quantity}")
                
                elif mvt.category == 'TR':  # Transfer
                    sloc_from_code = payload.get('sloc_from_code')
                    sloc_to_code = payload.get('sloc_to_code')
                    if not sloc_from_code:
                        errors.append("Source storage location is required for transfer")
                    if not sloc_to_code:
                        errors.append("Destination storage location is required for transfer")
                    if sloc_from_code == sloc_to_code:
                        errors.append("Source and destination storage locations must be different")
        
        ok = len(errors) == 0
        return ok, errors, warnings
    
    @staticmethod
    def post_goods_movement(payload, username):
        """
        Post a goods movement and create material document
        Returns: doc_number
        """
        # Validate first
        ok, errors, warnings = MovementsService.validate_migo_payload(payload)
        if not ok:
            raise ValueError(f"Validation failed: {'; '.join(errors)}")
        
        # Extract data
        movement_type = payload.get('movement_type')
        material_sku = payload.get('material_sku')
        plant_code = payload.get('plant_code')
        sloc_from_code = payload.get('sloc_from_code')
        sloc_to_code = payload.get('sloc_to_code')
        batch_number = payload.get('batch_number')
        quantity = Decimal(str(payload.get('quantity')))
        uom = payload.get('uom', 'EA')
        header_text = payload.get('header_text', '')
        reference_text = payload.get('reference_text', '')
        item_text = payload.get('item_text', '')
        doc_date = payload.get('doc_date', date.today())
        posting_date = payload.get('posting_date', date.today())
        
        # Convert string dates if needed
        if isinstance(doc_date, str):
            doc_date = datetime.strptime(doc_date, '%Y-%m-%d').date()
        if isinstance(posting_date, str):
            posting_date = datetime.strptime(posting_date, '%Y-%m-%d').date()
        
        # Get entities
        material = Product.query.filter_by(sku=material_sku).first()
        plant = SAPPlant.query.filter_by(code=plant_code).first()
        mvt = SAPMovementType.query.get(movement_type)
        
        sloc_from = None
        sloc_to = None
        batch = None
        
        if sloc_from_code:
            sloc_from = SAPStorageLocation.query.filter_by(plant_id=plant.id, code=sloc_from_code).first()
        if sloc_to_code:
            sloc_to = SAPStorageLocation.query.filter_by(plant_id=plant.id, code=sloc_to_code).first()
        if batch_number:
            batch = SAPBatch.query.filter_by(material_id=material.id, batch_number=batch_number).first()
            if not batch:
                # Create batch if doesn't exist
                batch = SAPBatch(material_id=material.id, batch_number=batch_number)
                db.session.add(batch)
                db.session.flush()
        
        # Generate document number
        doc_number = MovementsService._generate_doc_number()
        
        # Create material document
        matdoc = SAPMaterialDocument(
            doc_number=doc_number,
            doc_date=doc_date,
            posting_date=posting_date,
            created_by=username,
            header_text=header_text,
            reference_text=reference_text
        )
        db.session.add(matdoc)
        db.session.flush()
        
        # Create document item
        item = SAPMaterialDocumentItem(
            matdoc_id=matdoc.id,
            line_no=10,
            movement_type=movement_type,
            material_id=material.id,
            plant_id=plant.id,
            sloc_from_id=sloc_from.id if sloc_from else None,
            sloc_to_id=sloc_to.id if sloc_to else None,
            batch_id=batch.id if batch else None,
            quantity=quantity,
            uom=uom,
            item_text=item_text
        )
        db.session.add(item)
        
        # Update stock based on movement type
        if mvt.category == 'GR':  # Goods Receipt
            MovementsService._update_stock(
                material.id, plant.id, sloc_to.id, batch.id if batch else None,
                quantity, increase=True
            )
        elif mvt.category == 'GI' or mvt.category == 'SCRAP':  # Goods Issue or Scrap
            MovementsService._update_stock(
                material.id, plant.id, sloc_from.id, batch.id if batch else None,
                quantity, increase=False
            )
        elif mvt.category == 'TR':  # Transfer
            MovementsService._update_stock(
                material.id, plant.id, sloc_from.id, batch.id if batch else None,
                quantity, increase=False
            )
            MovementsService._update_stock(
                material.id, plant.id, sloc_to.id, batch.id if batch else None,
                quantity, increase=True
            )
        
        # Write audit log
        MovementsService._write_audit_log(
            username=username,
            action='POST_MATDOC',
            entity_type='MaterialDocument',
            entity_id=doc_number,
            message=f"Posted material document {doc_number} with movement type {movement_type}",
            after_json=json.dumps(matdoc.to_dict())
        )
        
        db.session.commit()
        
        return doc_number
    
    @staticmethod
    def reverse_material_document(original_doc_number, username, partial_items=None):
        """
        Reverse a material document
        Returns: new_doc_number
        """
        # Get original document
        original_doc = SAPMaterialDocument.query.filter_by(doc_number=original_doc_number).first()
        if not original_doc:
            raise ValueError(f"Document {original_doc_number} not found")
        
        # Check if already reversed
        if original_doc.reversed_by:
            raise ValueError(f"Document {original_doc_number} has already been reversed by {original_doc.reversed_by[0].doc_number}")
        
        # Generate new document number
        new_doc_number = MovementsService._generate_doc_number()
        
        # Create reversal document
        reversal_doc = SAPMaterialDocument(
            doc_number=new_doc_number,
            doc_date=date.today(),
            posting_date=date.today(),
            created_by=username,
            header_text=f"Reversal of {original_doc_number}",
            reference_text=original_doc.reference_text,
            reversal_of_doc_id=original_doc.id
        )
        db.session.add(reversal_doc)
        db.session.flush()
        
        # Reverse items
        line_no = 10
        for original_item in original_doc.items:
            # Get reversal movement type
            mvt = SAPMovementType.query.get(original_item.movement_type)
            if not mvt or not mvt.reversal_code:
                raise ValueError(f"Movement type {original_item.movement_type} cannot be reversed")
            
            reversal_mvt = SAPMovementType.query.get(mvt.reversal_code)
            
            # Create reversal item
            reversal_item = SAPMaterialDocumentItem(
                matdoc_id=reversal_doc.id,
                line_no=line_no,
                movement_type=reversal_mvt.code,
                material_id=original_item.material_id,
                plant_id=original_item.plant_id,
                sloc_from_id=original_item.sloc_to_id,  # Swap from/to
                sloc_to_id=original_item.sloc_from_id,
                batch_id=original_item.batch_id,
                quantity=original_item.quantity,
                uom=original_item.uom,
                item_text=f"Reversal of item {original_item.line_no}",
                reversal_of_item_id=original_item.id
            )
            db.session.add(reversal_item)
            
            # Update stock (reverse the effect)
            original_mvt_cat = mvt.category
            if original_mvt_cat == 'GR':  # Was GR, now reverse (decrease)
                MovementsService._update_stock(
                    original_item.material_id, original_item.plant_id, original_item.sloc_to_id,
                    original_item.batch_id, original_item.quantity, increase=False
                )
            elif original_mvt_cat == 'GI' or original_mvt_cat == 'SCRAP':  # Was GI, now reverse (increase)
                MovementsService._update_stock(
                    original_item.material_id, original_item.plant_id, original_item.sloc_from_id,
                    original_item.batch_id, original_item.quantity, increase=True
                )
            elif original_mvt_cat == 'TR':  # Was transfer, reverse it
                MovementsService._update_stock(
                    original_item.material_id, original_item.plant_id, original_item.sloc_from_id,
                    original_item.batch_id, original_item.quantity, increase=True
                )
                MovementsService._update_stock(
                    original_item.material_id, original_item.plant_id, original_item.sloc_to_id,
                    original_item.batch_id, original_item.quantity, increase=False
                )
            
            line_no += 10
        
        # Write audit log
        MovementsService._write_audit_log(
            username=username,
            action='REVERSE_MATDOC',
            entity_type='MaterialDocument',
            entity_id=new_doc_number,
            message=f"Reversed material document {original_doc_number}",
            after_json=json.dumps(reversal_doc.to_dict())
        )
        
        db.session.commit()
        
        return new_doc_number
    
    @staticmethod
    def get_stock_overview(filters=None):
        """
        Get stock overview with optional filters
        Returns hierarchical structure by plant/sloc/material
        """
        query = SAPStockOnHand.query
        
        if filters:
            if filters.get('plant_code'):
                plant = SAPPlant.query.filter_by(code=filters['plant_code']).first()
                if plant:
                    query = query.filter_by(plant_id=plant.id)
            
            if filters.get('material_sku'):
                material = Product.query.filter_by(sku=filters['material_sku']).first()
                if material:
                    query = query.filter_by(material_id=material.id)
            
            if filters.get('sloc_code') and filters.get('plant_code'):
                plant = SAPPlant.query.filter_by(code=filters['plant_code']).first()
                if plant:
                    sloc = SAPStorageLocation.query.filter_by(plant_id=plant.id, code=filters['sloc_code']).first()
                    if sloc:
                        query = query.filter_by(sloc_id=sloc.id)
        
        # Only show non-zero stock
        query = query.filter(SAPStockOnHand.quantity != 0)
        
        stocks = query.all()
        return [stock.to_dict() for stock in stocks]
    
    @staticmethod
    def get_material_documents(filters=None, pagination=None):
        """
        Get list of material documents with filters and pagination
        """
        query = SAPMaterialDocument.query.order_by(SAPMaterialDocument.created_at.desc())
        
        if filters:
            if filters.get('doc_number'):
                query = query.filter(SAPMaterialDocument.doc_number.contains(filters['doc_number']))
            
            if filters.get('created_by'):
                query = query.filter(SAPMaterialDocument.created_by == filters['created_by'])
            
            if filters.get('from_date'):
                query = query.filter(SAPMaterialDocument.posting_date >= filters['from_date'])
            
            if filters.get('to_date'):
                query = query.filter(SAPMaterialDocument.posting_date <= filters['to_date'])
        
        if pagination:
            page = pagination.get('page', 1)
            per_page = pagination.get('per_page', 50)
            paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            return {
                'items': [doc.to_dict() for doc in paginated.items],
                'total': paginated.total,
                'page': page,
                'per_page': per_page,
                'pages': paginated.pages
            }
        
        docs = query.limit(100).all()
        return [doc.to_dict() for doc in docs]
    
    @staticmethod
    def get_material_doc_display(doc_number):
        """
        Get complete material document for display
        """
        doc = SAPMaterialDocument.query.filter_by(doc_number=doc_number).first()
        if not doc:
            return None
        return doc.to_dict()
    
    @staticmethod
    def _update_stock(material_id, plant_id, sloc_id, batch_id, quantity, increase=True):
        """
        Update stock on hand (internal method)
        """
        # Get or create stock record
        stock = SAPStockOnHand.query.filter_by(
            material_id=material_id,
            plant_id=plant_id,
            sloc_id=sloc_id,
            batch_id=batch_id
        ).first()
        
        if not stock:
            stock = SAPStockOnHand(
                material_id=material_id,
                plant_id=plant_id,
                sloc_id=sloc_id,
                batch_id=batch_id,
                quantity=Decimal('0')
            )
            db.session.add(stock)
        
        # Update quantity
        if increase:
            stock.quantity += quantity
        else:
            stock.quantity -= quantity
        
        stock.last_updated = datetime.utcnow()
    
    @staticmethod
    def _generate_doc_number():
        """
        Generate next material document number (SAP-style)
        Format: 49XXXXXXXX (10 digits)
        """
        # Get or create sequence
        seq = SAPDocSequence.query.get('MATDOC')
        if not seq:
            seq = SAPDocSequence(key='MATDOC', next_number=1)
            db.session.add(seq)
            db.session.flush()
        
        # Generate number
        doc_number = f"49{seq.next_number:08d}"
        
        # Increment sequence
        seq.next_number += 1
        
        return doc_number
    
    @staticmethod
    def _write_audit_log(username, action, entity_type, entity_id, message, before_json=None, after_json=None):
        """
        Write audit log entry
        """
        log = SAPAuditLog(
            username=username,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            message=message,
            before_json=before_json,
            after_json=after_json
        )
        db.session.add(log)
    
    @staticmethod
    def get_config(key, default=None):
        """
        Get configuration value
        """
        config = SAPConfig.query.get(key)
        return config.value if config else default
    
    @staticmethod
    def set_config(key, value, description=None):
        """
        Set configuration value
        """
        config = SAPConfig.query.get(key)
        if not config:
            config = SAPConfig(key=key, value=value, description=description)
            db.session.add(config)
        else:
            config.value = value
            if description:
                config.description = description
        db.session.commit()
