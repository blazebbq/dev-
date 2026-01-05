"""
SAP-style UI controllers
T-code routing, MIGO, MB51, MMBE, etc.
"""
from flask import render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import date, datetime
from models import db
from models.product import Product
from models.sap_models import (
    SAPPlant, SAPStorageLocation, SAPMovementType, SAPMaterialDocument,
    SAPStockOnHand, SAPConfig
)
from services.movements_service import MovementsService


# T-code registry
TCODE_REGISTRY = {
    'MIGO': '/tcode/migo',
    'MB51': '/tcode/mb51',
    'MMBE': '/tcode/mmbe',
    'MM03': '/tcode/mm03',
    'MM02': '/tcode/mm02',
    'ZMM01': '/tcode/zmm01',
    'ZMD01': '/tcode/zmd01',
    'ZMVT': '/tcode/zmvt',
    'ZREP01': '/tcode/zrep01',
    'ZREP02': '/tcode/zrep02',
    'ZCONFIG': '/tcode/zconfig',
}


def register_sap_routes(app):
    """Register all SAP-style UI routes"""
    
    @app.route('/')
    @login_required
    def sap_home():
        """SAP dashboard (default)"""
        return redirect('/tcode/migo')
    
    @app.route('/legacy')
    @login_required
    def legacy_ui():
        """Old dashboard UI"""
        return render_template('dashboard.html')
    
    @app.route('/tcode', methods=['POST'])
    @login_required
    def tcode_handler():
        """T-code command field handler"""
        tcode = request.form.get('tcode', '').strip().upper()
        
        # Strip /n or /o prefix
        tcode = tcode.replace('/N', '').replace('/O', '')
        
        if tcode in TCODE_REGISTRY:
            return redirect(TCODE_REGISTRY[tcode])
        else:
            return render_template('sap_base.html',
                                 active_tcode='',
                                 status_message=f'Transaction {tcode} does not exist',
                                 status_type='error')
    
    @app.route('/tcode/migo', methods=['GET'])
    @login_required
    def migo():
        """MIGO - Goods Movement screen"""
        movement_types = SAPMovementType.query.all()
        current_plant = request.args.get('plant', '1000')
        current_sloc = request.args.get('sloc', '0001')
        
        return render_template('sap_migo.html',
                             active_tcode='MIGO',
                             movement_types=movement_types,
                             current_plant=current_plant,
                             current_sloc=current_sloc,
                             today=date.today().isoformat())
    
    @app.route('/tcode/migo/check', methods=['POST'])
    @login_required
    def migo_check():
        """MIGO - Validate document (Enter key)"""
        payload = {
            'movement_type': request.form.get('movement_type'),
            'material_sku': request.form.get('material_sku'),
            'plant_code': request.form.get('plant_code'),
            'sloc_from_code': request.form.get('sloc_from_code'),
            'sloc_to_code': request.form.get('sloc_to_code'),
            'batch_number': request.form.get('batch_number'),
            'quantity': request.form.get('quantity'),
            'uom': request.form.get('uom', 'EA'),
            'doc_date': request.form.get('doc_date'),
            'posting_date': request.form.get('posting_date'),
            'reference_text': request.form.get('reference_text'),
            'header_text': request.form.get('header_text'),
            'item_text': request.form.get('item_text'),
        }
        
        ok, errors, warnings = MovementsService.validate_migo_payload(payload)
        
        return jsonify({
            'ok': ok,
            'errors': errors,
            'warnings': warnings
        })
    
    @app.route('/tcode/migo/post', methods=['POST'])
    @login_required
    def migo_post():
        """MIGO - Post document (Post button)"""
        payload = {
            'movement_type': request.form.get('movement_type'),
            'material_sku': request.form.get('material_sku'),
            'plant_code': request.form.get('plant_code'),
            'sloc_from_code': request.form.get('sloc_from_code'),
            'sloc_to_code': request.form.get('sloc_to_code'),
            'batch_number': request.form.get('batch_number'),
            'quantity': request.form.get('quantity'),
            'uom': request.form.get('uom', 'EA'),
            'doc_date': request.form.get('doc_date'),
            'posting_date': request.form.get('posting_date'),
            'reference_text': request.form.get('reference_text'),
            'header_text': request.form.get('header_text'),
            'item_text': request.form.get('item_text'),
        }
        
        try:
            # Validate first
            ok, errors, warnings = MovementsService.validate_migo_payload(payload)
            if not ok:
                movement_types = SAPMovementType.query.all()
                return render_template('sap_migo.html',
                                     active_tcode='MIGO',
                                     movement_types=movement_types,
                                     current_plant=payload.get('plant_code', '1000'),
                                     current_sloc=payload.get('sloc_to_code', '0001'),
                                     today=date.today().isoformat(),
                                     form_data=payload,
                                     validation_errors=errors,
                                     validation_warnings=warnings)
            
            # Post the document
            doc_number = MovementsService.post_goods_movement(payload, current_user.username)
            
            # Show success
            movement_types = SAPMovementType.query.all()
            return render_template('sap_migo.html',
                                 active_tcode='MIGO',
                                 movement_types=movement_types,
                                 current_plant=payload.get('plant_code', '1000'),
                                 current_sloc=payload.get('sloc_to_code', '0001'),
                                 today=date.today().isoformat(),
                                 message=f'Material document {doc_number} posted successfully',
                                 message_type='success',
                                 doc_number=doc_number)
        
        except Exception as e:
            movement_types = SAPMovementType.query.all()
            return render_template('sap_migo.html',
                                 active_tcode='MIGO',
                                 movement_types=movement_types,
                                 current_plant=payload.get('plant_code', '1000'),
                                 current_sloc=payload.get('sloc_to_code', '0001'),
                                 today=date.today().isoformat(),
                                 form_data=payload,
                                 message=f'Error posting document: {str(e)}',
                                 message_type='error')
    
    @app.route('/tcode/mb51', methods=['GET'])
    @login_required
    def mb51():
        """MB51 - Material Document List"""
        # Get filter parameters
        filters = {
            'doc_number': request.args.get('doc_number'),
            'created_by': request.args.get('created_by'),
            'from_date': request.args.get('from_date'),
            'to_date': request.args.get('to_date'),
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v}
        
        # Get documents
        page = request.args.get('page', 1, type=int)
        pagination = {'page': page, 'per_page': 50}
        
        result = MovementsService.get_material_documents(filters, pagination)
        
        return render_template('sap_mb51.html',
                             active_tcode='MB51',
                             documents=result.get('items', []),
                             total=result.get('total', 0),
                             page=page,
                             pages=result.get('pages', 1),
                             filters=filters)
    
    @app.route('/tcode/mb51/doc/<doc_number>', methods=['GET'])
    @login_required
    def mb51_display(doc_number):
        """MB51 - Display Material Document"""
        doc = MovementsService.get_material_doc_display(doc_number)
        
        if not doc:
            return render_template('sap_base.html',
                                 active_tcode='MB51',
                                 status_message=f'Document {doc_number} not found',
                                 status_type='error')
        
        return render_template('sap_mb51_display.html',
                             active_tcode='MB51',
                             document=doc,
                             doc_number=doc_number)
    
    @app.route('/tcode/mb51/reverse/<doc_number>', methods=['POST'])
    @login_required
    def mb51_reverse(doc_number):
        """MB51 - Reverse Material Document"""
        try:
            new_doc_number = MovementsService.reverse_material_document(
                doc_number, 
                current_user.username
            )
            
            return redirect(url_for('mb51_display', doc_number=new_doc_number) + 
                          '?message=Document reversed successfully&message_type=success')
        
        except Exception as e:
            return redirect(url_for('mb51_display', doc_number=doc_number) +
                          f'?message=Error reversing document: {str(e)}&message_type=error')
    
    @app.route('/tcode/mmbe', methods=['GET'])
    @login_required
    def mmbe():
        """MMBE - Stock Overview"""
        # Get filter parameters
        filters = {
            'plant_code': request.args.get('plant_code'),
            'material_sku': request.args.get('material_sku'),
            'sloc_code': request.args.get('sloc_code'),
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v}
        
        # Get stock data
        stock_data = MovementsService.get_stock_overview(filters)
        
        return render_template('sap_mmbe.html',
                             active_tcode='MMBE',
                             stock_data=stock_data,
                             filters=filters)
    
    @app.route('/tcode/mm03', methods=['GET'])
    @login_required
    def mm03():
        """MM03 - Display Material"""
        material_sku = request.args.get('material')
        material = None
        
        if material_sku:
            material = Product.query.filter_by(sku=material_sku).first()
        
        return render_template('sap_mm03.html',
                             active_tcode='MM03',
                             material=material,
                             material_sku=material_sku)
    
    @app.route('/tcode/mm02', methods=['GET', 'POST'])
    @login_required
    def mm02():
        """MM02 - Change Material"""
        if request.method == 'GET':
            material_sku = request.args.get('material')
            material = None
            
            if material_sku:
                material = Product.query.filter_by(sku=material_sku).first()
            
            return render_template('sap_mm02.html',
                                 active_tcode='MM02',
                                 material=material,
                                 material_sku=material_sku)
        
        # POST - Update material
        material_sku = request.form.get('sku')
        material = Product.query.filter_by(sku=material_sku).first()
        
        if not material:
            return render_template('sap_mm02.html',
                                 active_tcode='MM02',
                                 message='Material not found',
                                 message_type='error')
        
        # Update fields
        material.name = request.form.get('name', material.name)
        material.description = request.form.get('description', material.description)
        material.unit_price = request.form.get('unit_price', material.unit_price)
        material.reorder_point = request.form.get('reorder_point', material.reorder_point)
        material.reorder_quantity = request.form.get('reorder_quantity', material.reorder_quantity)
        
        db.session.commit()
        
        return render_template('sap_mm02.html',
                             active_tcode='MM02',
                             material=material,
                             material_sku=material_sku,
                             message=f'Material {material_sku} updated successfully',
                             message_type='success')
    
    @app.route('/tcode/zmm01', methods=['GET', 'POST'])
    @login_required
    def zmm01():
        """ZMM01 - Create Material"""
        if request.method == 'GET':
            return render_template('sap_zmm01.html',
                                 active_tcode='ZMM01')
        
        # POST - Create material
        try:
            material = Product(
                sku=request.form.get('sku'),
                name=request.form.get('name'),
                description=request.form.get('description'),
                unit_of_measure=request.form.get('unit_of_measure', 'EA'),
                unit_price=request.form.get('unit_price', 0),
                reorder_point=request.form.get('reorder_point', 0),
                reorder_quantity=request.form.get('reorder_quantity', 0),
                status='ACTIVE'
            )
            
            db.session.add(material)
            db.session.commit()
            
            return render_template('sap_zmm01.html',
                                 active_tcode='ZMM01',
                                 message=f'Material {material.sku} created successfully',
                                 message_type='success')
        
        except Exception as e:
            return render_template('sap_zmm01.html',
                                 active_tcode='ZMM01',
                                 message=f'Error creating material: {str(e)}',
                                 message_type='error',
                                 form_data=request.form)
    
    @app.route('/tcode/zmd01', methods=['GET'])
    @login_required
    def zmd01():
        """ZMD01 - Plants and Storage Locations"""
        plants = SAPPlant.query.all()
        return render_template('sap_zmd01.html',
                             active_tcode='ZMD01',
                             plants=plants)
    
    @app.route('/tcode/zmvt', methods=['GET'])
    @login_required
    def zmvt():
        """ZMVT - Movement Types Reference"""
        movement_types = SAPMovementType.query.all()
        return render_template('sap_zmvt.html',
                             active_tcode='ZMVT',
                             movement_types=movement_types)
    
    @app.route('/tcode/zconfig', methods=['GET', 'POST'])
    @login_required
    def zconfig():
        """ZCONFIG - System Configuration"""
        if request.method == 'POST':
            # Update config
            key = request.form.get('key')
            value = request.form.get('value')
            
            if key:
                MovementsService.set_config(key, value)
                message = f'Configuration {key} updated'
                message_type = 'success'
            else:
                message = 'Invalid configuration'
                message_type = 'error'
        else:
            message = None
            message_type = None
        
        # Get all config
        configs = SAPConfig.query.all()
        
        return render_template('sap_zconfig.html',
                             active_tcode='ZCONFIG',
                             configs=configs,
                             message=message,
                             message_type=message_type)
