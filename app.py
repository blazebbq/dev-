"""
Stock Management System - Main Application with Authentication and SAP UI
"""
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import config
from models import db
from models.product import Product
from models.warehouse import Warehouse
from models.stock import Stock, StockTransaction
from models.supplier import Supplier
from models.purchase_order import PurchaseOrder, PurchaseOrderLine
from models.user import User, UnitOfMeasure, Bin, BinStock, WorkOrder, WorkOrderLine
from models.sap_models import SAPPlant, SAPStorageLocation, SAPMovementType, SAPConfig
from services.inventory_service import InventoryService
from services.reporting_service import ReportingService
from controllers.sap_ui import register_sap_routes
from datetime import datetime
import os

def create_app(config_name='default'):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create tables and initialize data
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@example.com',
                full_name='Administrator',
                role='ADMIN'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create default units
            default_units = [
                UnitOfMeasure(code='EA', name='Each', unit_type='COUNT', description='Single unit'),
                UnitOfMeasure(code='KG', name='Kilogram', unit_type='WEIGHT', description='Metric weight unit'),
                UnitOfMeasure(code='G', name='Gram', unit_type='WEIGHT', description='Metric weight unit', base_unit='G', conversion_factor=1),
                UnitOfMeasure(code='LB', name='Pound', unit_type='WEIGHT', description='Imperial weight unit'),
                UnitOfMeasure(code='L', name='Liter', unit_type='VOLUME', description='Metric volume unit'),
                UnitOfMeasure(code='ML', name='Milliliter', unit_type='VOLUME', description='Metric volume unit'),
            ]
            for unit in default_units:
                if not UnitOfMeasure.query.filter_by(code=unit.code).first():
                    db.session.add(unit)
            
            db.session.commit()
        
        # Initialize SAP data if not exists
        if SAPPlant.query.count() == 0:
            from init_sap_data import init_sap_data
            init_sap_data()
    
    # Register SAP routes first (includes /)
    register_sap_routes(app)
    
    # Register API routes
    register_routes(app)
    
    return app

def register_routes(app):
    """Register all API routes"""
    
    # Authentication routes (login page and API endpoints only)
    @app.route('/login')
    def login():
        """Login page"""
        if current_user.is_authenticated:
            return redirect('/')
        return render_template('login.html')
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Old dashboard - redirect to legacy"""
        return redirect('/legacy')
    
    @app.route('/api/auth/login', methods=['POST'])
    def api_login():
        """API login endpoint"""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            return jsonify({
                'success': True,
                'user': user.to_dict()
            })
        
        return jsonify({'error': 'Invalid credentials'}), 401
    
    @app.route('/api/auth/logout', methods=['POST'])
    @login_required
    def api_logout():
        """API logout endpoint"""
        logout_user()
        return jsonify({'success': True})
    
    @app.route('/api/auth/current-user')
    @login_required
    def current_user_info():
        """Get current user info"""
        return jsonify(current_user.to_dict())
    
    @app.route('/api/health')
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'Stock Management System',
            'version': '1.0.0'
        })
    
    # Product endpoints
    @app.route('/api/products', methods=['GET', 'POST'])
    @login_required
    def products():
        """Get all products or create a new product"""
        if request.method == 'GET':
            products = Product.query.all()
            return jsonify([p.to_dict() for p in products])
        
        elif request.method == 'POST':
            data = request.get_json()
            
            # Check if product already exists
            if Product.query.get(data.get('sku')):
                return jsonify({'error': 'Product with this SKU already exists'}), 400
            
            product = Product(
                sku=data.get('sku'),
                name=data.get('name'),
                description=data.get('description'),
                category=data.get('category'),
                unit_of_measure=data.get('unit_of_measure', 'EA'),
                unit_of_measure_id=data.get('unit_of_measure_id'),
                unit_price=data.get('unit_price', 0),
                reorder_point=data.get('reorder_point', 0),
                reorder_quantity=data.get('reorder_quantity', 0),
                status=data.get('status', 'ACTIVE'),
                image_url=data.get('image_url'),
                barcode=data.get('barcode'),
                serial_number_required=data.get('serial_number_required', False),
                batch_tracking_required=data.get('batch_tracking_required', False)
            )
            
            db.session.add(product)
            db.session.commit()
            
            return jsonify(product.to_dict()), 201
    
    @app.route('/api/products/<sku>', methods=['GET', 'PUT', 'DELETE'])
    @login_required
    def product_detail(sku):
        """Get, update, or delete a specific product"""
        product = Product.query.get(sku)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        if request.method == 'GET':
            return jsonify(product.to_dict())
        
        elif request.method == 'PUT':
            data = request.get_json()
            product.name = data.get('name', product.name)
            product.description = data.get('description', product.description)
            product.category = data.get('category', product.category)
            product.unit_of_measure = data.get('unit_of_measure', product.unit_of_measure)
            if 'unit_of_measure_id' in data:
                product.unit_of_measure_id = data.get('unit_of_measure_id')
            product.unit_price = data.get('unit_price', product.unit_price)
            product.reorder_point = data.get('reorder_point', product.reorder_point)
            product.reorder_quantity = data.get('reorder_quantity', product.reorder_quantity)
            product.status = data.get('status', product.status)
            product.image_url = data.get('image_url', product.image_url)
            product.barcode = data.get('barcode', product.barcode)
            
            db.session.commit()
            return jsonify(product.to_dict())
        
        elif request.method == 'DELETE':
            db.session.delete(product)
            db.session.commit()
            return '', 204
    
    # Warehouse endpoints
    @app.route('/api/warehouses', methods=['GET', 'POST'])
    @login_required
    def warehouses():
        """Get all warehouses or create a new warehouse"""
        if request.method == 'GET':
            warehouses = Warehouse.query.all()
            return jsonify([w.to_dict() for w in warehouses])
        
        elif request.method == 'POST':
            data = request.get_json()
            
            if Warehouse.query.get(data.get('code')):
                return jsonify({'error': 'Warehouse with this code already exists'}), 400
            
            warehouse = Warehouse(
                code=data.get('code'),
                name=data.get('name'),
                location=data.get('location'),
                capacity=data.get('capacity'),
                manager=data.get('manager'),
                phone=data.get('phone'),
                email=data.get('email'),
                status=data.get('status', 'ACTIVE')
            )
            
            db.session.add(warehouse)
            db.session.commit()
            
            return jsonify(warehouse.to_dict()), 201
    
    @app.route('/api/warehouses/<code>', methods=['GET', 'PUT', 'DELETE'])
    @login_required
    def warehouse_detail(code):
        """Get, update, or delete a specific warehouse"""
        warehouse = Warehouse.query.get(code)
        if not warehouse:
            return jsonify({'error': 'Warehouse not found'}), 404
        
        if request.method == 'GET':
            return jsonify(warehouse.to_dict())
        
        elif request.method == 'PUT':
            data = request.get_json()
            warehouse.name = data.get('name', warehouse.name)
            warehouse.location = data.get('location', warehouse.location)
            warehouse.capacity = data.get('capacity', warehouse.capacity)
            warehouse.manager = data.get('manager', warehouse.manager)
            warehouse.phone = data.get('phone', warehouse.phone)
            warehouse.email = data.get('email', warehouse.email)
            warehouse.status = data.get('status', warehouse.status)
            
            db.session.commit()
            return jsonify(warehouse.to_dict())
        
        elif request.method == 'DELETE':
            db.session.delete(warehouse)
            db.session.commit()
            return '', 204
    
    # Stock endpoints
    @app.route('/api/stock/levels', methods=['GET'])
    @login_required
    def stock_levels():
        """Get current stock levels for all products"""
        return jsonify(InventoryService.get_all_stock_levels())
    
    @app.route('/api/stock/levels/<sku>', methods=['GET'])
    @login_required
    def product_stock_level(sku):
        """Get stock level for a specific product"""
        warehouse_code = request.args.get('warehouse')
        stock_info = InventoryService.get_stock_level(sku, warehouse_code)
        
        if not stock_info:
            return jsonify({'error': 'Stock not found'}), 404
        
        return jsonify(stock_info)
    
    @app.route('/api/stock/receipt', methods=['POST'])
    @login_required
    def stock_receipt():
        """Record stock receipt"""
        data = request.get_json()
        
        try:
            result = InventoryService.receive_stock(
                product_sku=data.get('product_sku'),
                warehouse_code=data.get('warehouse_code'),
                quantity=data.get('quantity'),
                unit_cost=data.get('unit_cost'),
                reference=data.get('reference'),
                notes=data.get('notes')
            )
            return jsonify(result), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/stock/issue', methods=['POST'])
    @login_required
    def stock_issue():
        """Record stock issue"""
        data = request.get_json()
        
        try:
            result = InventoryService.issue_stock(
                product_sku=data.get('product_sku'),
                warehouse_code=data.get('warehouse_code'),
                quantity=data.get('quantity'),
                reference=data.get('reference'),
                notes=data.get('notes')
            )
            return jsonify(result), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/stock/transfer', methods=['POST'])
    @login_required
    def stock_transfer():
        """Transfer stock between warehouses"""
        data = request.get_json()
        
        try:
            result = InventoryService.transfer_stock(
                product_sku=data.get('product_sku'),
                from_warehouse=data.get('from_warehouse'),
                to_warehouse=data.get('to_warehouse'),
                quantity=data.get('quantity'),
                reference=data.get('reference'),
                notes=data.get('notes')
            )
            return jsonify(result), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/stock/adjust', methods=['POST'])
    @login_required
    def stock_adjust():
        """Adjust stock quantity"""
        data = request.get_json()
        
        try:
            result = InventoryService.adjust_stock(
                product_sku=data.get('product_sku'),
                warehouse_code=data.get('warehouse_code'),
                new_quantity=data.get('new_quantity'),
                reason=data.get('reason')
            )
            return jsonify(result), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/stock/low-stock', methods=['GET'])
    @login_required
    def low_stock():
        """Get products with low stock levels"""
        threshold = request.args.get('threshold', 20, type=int)
        return jsonify(InventoryService.get_low_stock_items(threshold))
    
    @app.route('/api/stock/transactions', methods=['GET'])
    @login_required
    def stock_transactions():
        """Get stock transaction history"""
        product_sku = request.args.get('product_sku')
        warehouse_code = request.args.get('warehouse_code')
        
        query = StockTransaction.query
        
        if product_sku:
            query = query.filter_by(product_sku=product_sku)
        if warehouse_code:
            query = query.filter_by(warehouse_code=warehouse_code)
        
        transactions = query.order_by(StockTransaction.transaction_date.desc()).limit(100).all()
        return jsonify([t.to_dict() for t in transactions])
    
    # Supplier endpoints
    @app.route('/api/suppliers', methods=['GET', 'POST'])
    @login_required
    def suppliers():
        """Get all suppliers or create a new supplier"""
        if request.method == 'GET':
            suppliers = Supplier.query.all()
            return jsonify([s.to_dict() for s in suppliers])
        
        elif request.method == 'POST':
            data = request.get_json()
            
            # Check if code already exists
            if Supplier.query.filter_by(code=data.get('code')).first():
                return jsonify({'error': 'Supplier with this code already exists'}), 400
            
            supplier = Supplier(
                code=data.get('code'),
                name=data.get('name'),
                contact_person=data.get('contact_person'),
                email=data.get('email'),
                phone=data.get('phone'),
                address=data.get('address'),
                payment_terms=data.get('payment_terms'),
                status=data.get('status', 'ACTIVE'),
                rating=data.get('rating')
            )
            
            db.session.add(supplier)
            db.session.commit()
            
            return jsonify(supplier.to_dict()), 201
    
    @app.route('/api/suppliers/<int:supplier_id>', methods=['GET', 'PUT', 'DELETE'])
    @login_required
    def supplier_detail(supplier_id):
        """Get, update, or delete a specific supplier"""
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return jsonify({'error': 'Supplier not found'}), 404
        
        if request.method == 'GET':
            return jsonify(supplier.to_dict())
        
        elif request.method == 'PUT':
            data = request.get_json()
            supplier.name = data.get('name', supplier.name)
            supplier.contact_person = data.get('contact_person', supplier.contact_person)
            supplier.email = data.get('email', supplier.email)
            supplier.phone = data.get('phone', supplier.phone)
            supplier.address = data.get('address', supplier.address)
            supplier.payment_terms = data.get('payment_terms', supplier.payment_terms)
            supplier.status = data.get('status', supplier.status)
            supplier.rating = data.get('rating', supplier.rating)
            
            db.session.commit()
            return jsonify(supplier.to_dict())
        
        elif request.method == 'DELETE':
            db.session.delete(supplier)
            db.session.commit()
            return '', 204
    
    # Purchase Order endpoints
    @app.route('/api/purchase-orders', methods=['GET', 'POST'])
    @login_required
    def purchase_orders():
        """Get all purchase orders or create a new one"""
        if request.method == 'GET':
            status = request.args.get('status')
            query = PurchaseOrder.query
            
            if status:
                query = query.filter_by(status=status)
            
            orders = query.all()
            return jsonify([po.to_dict() for po in orders])
        
        elif request.method == 'POST':
            data = request.get_json()
            
            if PurchaseOrder.query.get(data.get('po_number')):
                return jsonify({'error': 'Purchase order with this number already exists'}), 400
            
            po = PurchaseOrder(
                po_number=data.get('po_number'),
                supplier_id=data.get('supplier_id'),
                order_date=data.get('order_date'),
                expected_delivery_date=data.get('expected_delivery_date'),
                warehouse_code=data.get('warehouse_code'),
                status=data.get('status', 'DRAFT'),
                notes=data.get('notes'),
                created_by=data.get('created_by')
            )
            
            # Add line items
            total_amount = 0
            for idx, line_data in enumerate(data.get('line_items', []), 1):
                line_total = line_data['quantity_ordered'] * line_data['unit_price']
                total_amount += line_total
                
                line = PurchaseOrderLine(
                    line_number=idx,
                    product_sku=line_data['product_sku'],
                    quantity_ordered=line_data['quantity_ordered'],
                    unit_price=line_data['unit_price'],
                    line_total=line_total
                )
                po.line_items.append(line)
            
            po.total_amount = total_amount
            
            db.session.add(po)
            db.session.commit()
            
            return jsonify(po.to_dict()), 201
    
    @app.route('/api/purchase-orders/<po_number>', methods=['GET', 'PUT', 'DELETE'])
    @login_required
    def purchase_order_detail(po_number):
        """Get, update, or delete a specific purchase order"""
        po = PurchaseOrder.query.get(po_number)
        if not po:
            return jsonify({'error': 'Purchase order not found'}), 404
        
        if request.method == 'GET':
            return jsonify(po.to_dict())
        
        elif request.method == 'PUT':
            data = request.get_json()
            po.status = data.get('status', po.status)
            po.expected_delivery_date = data.get('expected_delivery_date', po.expected_delivery_date)
            po.notes = data.get('notes', po.notes)
            
            db.session.commit()
            return jsonify(po.to_dict())
        
        elif request.method == 'DELETE':
            db.session.delete(po)
            db.session.commit()
            return '', 204
    
    # Reporting endpoints
    @app.route('/api/reports/inventory-valuation', methods=['GET'])
    @login_required
    def inventory_valuation():
        """Get inventory valuation report"""
        return jsonify(ReportingService.get_inventory_valuation())
    
    @app.route('/api/reports/stock-movement', methods=['GET'])
    @login_required
    def stock_movement_report():
        """Get stock movement report"""
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        product_sku = request.args.get('product_sku')
        
        return jsonify(ReportingService.get_stock_movement_report(start_date, end_date, product_sku))
    
    @app.route('/api/reports/warehouse-utilization', methods=['GET'])
    @login_required
    def warehouse_utilization():
        """Get warehouse utilization report"""
        return jsonify(ReportingService.get_warehouse_utilization())
    
    @app.route('/api/reports/abc-analysis', methods=['GET'])
    @login_required
    def abc_analysis():
        """Get ABC analysis report"""
        return jsonify(ReportingService.get_abc_analysis())
    
    @app.route('/api/reports/purchase-orders', methods=['GET'])
    @login_required
    def purchase_order_summary():
        """Get purchase order summary"""
        status = request.args.get('status')
        return jsonify(ReportingService.get_purchase_order_summary(status))
    
    # Units of Measure endpoints
    @app.route('/api/units', methods=['GET', 'POST'])
    @login_required
    def units():
        """Get all units or create a new unit"""
        if request.method == 'GET':
            units = UnitOfMeasure.query.all()
            return jsonify([u.to_dict() for u in units])
        
        elif request.method == 'POST':
            data = request.get_json()
            
            if UnitOfMeasure.query.filter_by(code=data.get('code')).first():
                return jsonify({'error': 'Unit with this code already exists'}), 400
            
            unit = UnitOfMeasure(
                code=data.get('code'),
                name=data.get('name'),
                description=data.get('description'),
                unit_type=data.get('unit_type'),
                base_unit=data.get('base_unit'),
                conversion_factor=data.get('conversion_factor'),
                is_active=True
            )
            
            db.session.add(unit)
            db.session.commit()
            
            return jsonify(unit.to_dict()), 201
    
    @app.route('/api/units/<int:unit_id>', methods=['GET', 'PUT', 'DELETE'])
    @login_required
    def unit_detail(unit_id):
        """Get, update, or delete a specific unit"""
        unit = UnitOfMeasure.query.get(unit_id)
        if not unit:
            return jsonify({'error': 'Unit not found'}), 404
        
        if request.method == 'GET':
            return jsonify(unit.to_dict())
        
        elif request.method == 'PUT':
            data = request.get_json()
            unit.name = data.get('name', unit.name)
            unit.description = data.get('description', unit.description)
            unit.unit_type = data.get('unit_type', unit.unit_type)
            unit.base_unit = data.get('base_unit', unit.base_unit)
            unit.conversion_factor = data.get('conversion_factor', unit.conversion_factor)
            unit.is_active = data.get('is_active', unit.is_active)
            
            db.session.commit()
            return jsonify(unit.to_dict())
        
        elif request.method == 'DELETE':
            db.session.delete(unit)
            db.session.commit()
            return '', 204
    
    # Bin endpoints
    @app.route('/api/bins', methods=['GET', 'POST'])
    @login_required
    def bins():
        """Get all bins or create a new bin"""
        if request.method == 'GET':
            warehouse_code = request.args.get('warehouse')
            query = Bin.query
            
            if warehouse_code:
                query = query.filter_by(warehouse_code=warehouse_code)
            
            bins = query.all()
            return jsonify([b.to_dict() for b in bins])
        
        elif request.method == 'POST':
            data = request.get_json()
            
            if Bin.query.filter_by(code=data.get('code')).first():
                return jsonify({'error': 'Bin with this code already exists'}), 400
            
            bin_obj = Bin(
                code=data.get('code'),
                warehouse_code=data.get('warehouse_code'),
                aisle=data.get('aisle'),
                rack=data.get('rack'),
                level=data.get('level'),
                position=data.get('position'),
                bin_type=data.get('bin_type', 'STORAGE'),
                capacity=data.get('capacity'),
                is_active=True
            )
            
            db.session.add(bin_obj)
            db.session.commit()
            
            return jsonify(bin_obj.to_dict()), 201
    
    @app.route('/api/bins/<int:bin_id>', methods=['GET', 'PUT', 'DELETE'])
    @login_required
    def bin_detail(bin_id):
        """Get, update, or delete a specific bin"""
        bin_obj = Bin.query.get(bin_id)
        if not bin_obj:
            return jsonify({'error': 'Bin not found'}), 404
        
        if request.method == 'GET':
            return jsonify(bin_obj.to_dict())
        
        elif request.method == 'PUT':
            data = request.get_json()
            bin_obj.aisle = data.get('aisle', bin_obj.aisle)
            bin_obj.rack = data.get('rack', bin_obj.rack)
            bin_obj.level = data.get('level', bin_obj.level)
            bin_obj.position = data.get('position', bin_obj.position)
            bin_obj.bin_type = data.get('bin_type', bin_obj.bin_type)
            bin_obj.capacity = data.get('capacity', bin_obj.capacity)
            bin_obj.is_active = data.get('is_active', bin_obj.is_active)
            
            db.session.commit()
            return jsonify(bin_obj.to_dict())
        
        elif request.method == 'DELETE':
            db.session.delete(bin_obj)
            db.session.commit()
            return '', 204
    
    # Bin Stock endpoints
    @app.route('/api/bin-stock', methods=['GET'])
    @login_required
    def get_bin_stock():
        """Get stock at bin level"""
        bin_id = request.args.get('bin_id')
        product_sku = request.args.get('product_sku')
        
        query = BinStock.query
        
        if bin_id:
            query = query.filter_by(bin_id=bin_id)
        if product_sku:
            query = query.filter_by(product_sku=product_sku)
        
        stock_items = query.all()
        return jsonify([s.to_dict() for s in stock_items])
    
    @app.route('/api/bin-stock/move', methods=['POST'])
    @login_required
    def move_bin_stock():
        """Move stock between bins"""
        data = request.get_json()
        
        from_bin_id = data.get('from_bin_id')
        to_bin_id = data.get('to_bin_id')
        product_sku = data.get('product_sku')
        quantity = data.get('quantity')
        
        # Get source bin stock
        source_stock = BinStock.query.filter_by(
            bin_id=from_bin_id,
            product_sku=product_sku
        ).first()
        
        if not source_stock or source_stock.quantity < quantity:
            return jsonify({'error': 'Insufficient stock in source bin'}), 400
        
        # Update source
        source_stock.quantity -= quantity
        source_stock.updated_at = datetime.utcnow()
        
        # Get or create destination bin stock
        dest_stock = BinStock.query.filter_by(
            bin_id=to_bin_id,
            product_sku=product_sku
        ).first()
        
        if not dest_stock:
            dest_stock = BinStock(
                bin_id=to_bin_id,
                product_sku=product_sku,
                quantity=0
            )
            db.session.add(dest_stock)
        
        dest_stock.quantity += quantity
        dest_stock.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'source': source_stock.to_dict(),
            'destination': dest_stock.to_dict()
        }), 201
    
    # Work Order endpoints
    @app.route('/api/work-orders', methods=['GET', 'POST'])
    @login_required
    def work_orders():
        """Get all work orders or create a new one"""
        if request.method == 'GET':
            status = request.args.get('status')
            query = WorkOrder.query
            
            if status:
                query = query.filter_by(status=status)
            
            orders = query.all()
            return jsonify([wo.to_dict() for wo in orders])
        
        elif request.method == 'POST':
            data = request.get_json()
            
            if WorkOrder.query.filter_by(order_number=data.get('order_number')).first():
                return jsonify({'error': 'Work order with this number already exists'}), 400
            
            wo = WorkOrder(
                order_number=data.get('order_number'),
                order_type=data.get('order_type', 'PICK'),
                warehouse_code=data.get('warehouse_code'),
                status='OPEN',
                priority=data.get('priority', 'NORMAL'),
                assigned_to=data.get('assigned_to'),
                created_by=current_user.id,
                notes=data.get('notes')
            )
            
            # Add line items
            for idx, line_data in enumerate(data.get('line_items', []), 1):
                line = WorkOrderLine(
                    line_number=idx,
                    product_sku=line_data['product_sku'],
                    from_bin_id=line_data.get('from_bin_id'),
                    quantity_required=line_data['quantity_required'],
                    status='PENDING'
                )
                wo.line_items.append(line)
            
            db.session.add(wo)
            db.session.commit()
            
            return jsonify(wo.to_dict()), 201
    
    @app.route('/api/work-orders/<order_number>', methods=['GET', 'PUT', 'DELETE'])
    @login_required
    def work_order_detail(order_number):
        """Get, update, or delete a specific work order"""
        wo = WorkOrder.query.filter_by(order_number=order_number).first()
        if not wo:
            return jsonify({'error': 'Work order not found'}), 404
        
        if request.method == 'GET':
            return jsonify(wo.to_dict())
        
        elif request.method == 'PUT':
            data = request.get_json()
            wo.status = data.get('status', wo.status)
            wo.priority = data.get('priority', wo.priority)
            wo.assigned_to = data.get('assigned_to', wo.assigned_to)
            wo.notes = data.get('notes', wo.notes)
            
            if data.get('status') == 'IN_PROGRESS' and not wo.started_at:
                wo.started_at = datetime.utcnow()
            elif data.get('status') == 'COMPLETED' and not wo.completed_at:
                wo.completed_at = datetime.utcnow()
            
            db.session.commit()
            return jsonify(wo.to_dict())
        
        elif request.method == 'DELETE':
            db.session.delete(wo)
            db.session.commit()
            return '', 204
    
    @app.route('/api/work-orders/<order_number>/pick-list', methods=['GET'])
    @login_required
    def print_pick_list(order_number):
        """Generate printable pick list"""
        wo = WorkOrder.query.filter_by(order_number=order_number).first()
        if not wo:
            return jsonify({'error': 'Work order not found'}), 404
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pick List - {order_number}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ border-bottom: 3px solid #333; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background: #f0f0f0; }}
                .header-info {{ display: flex; justify-content: space-between; margin-bottom: 20px; }}
                @media print {{ button {{ display: none; }} }}
            </style>
        </head>
        <body>
            <button onclick="window.print()">Print</button>
            <h1>Pick List</h1>
            <div class="header-info">
                <div>
                    <p><strong>Order #:</strong> {wo.order_number}</p>
                    <p><strong>Type:</strong> {wo.order_type}</p>
                    <p><strong>Warehouse:</strong> {wo.warehouse_code or 'N/A'}</p>
                </div>
                <div>
                    <p><strong>Status:</strong> {wo.status}</p>
                    <p><strong>Priority:</strong> {wo.priority}</p>
                    <p><strong>Created:</strong> {wo.created_at.strftime('%Y-%m-%d %H:%M') if wo.created_at else 'N/A'}</p>
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Product SKU</th>
                        <th>Product Name</th>
                        <th>From Bin</th>
                        <th>Quantity Required</th>
                        <th>Quantity Picked</th>
                        <th>Signature</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f'''
                    <tr>
                        <td>{line.line_number}</td>
                        <td>{line.product_sku}</td>
                        <td>{line.product.name if line.product else 'N/A'}</td>
                        <td>{line.from_bin.code if line.from_bin else 'N/A'}</td>
                        <td>{line.quantity_required}</td>
                        <td>{line.quantity_picked}</td>
                        <td style="min-width: 100px;"></td>
                    </tr>
                    ''' for line in wo.line_items])}
                </tbody>
            </table>
            
            <div style="margin-top: 40px;">
                <p><strong>Notes:</strong> {wo.notes or 'None'}</p>
            </div>
            
            <div style="margin-top: 60px; border-top: 1px solid #333; padding-top: 20px;">
                <p><strong>Picker Signature:</strong> __________________ <strong>Date:</strong> __________</p>
            </div>
        </body>
        </html>
        """
        
        return html

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
