"""
Stock Management System - Main Application
"""
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from config import config
from models import db
from models.product import Product
from models.warehouse import Warehouse
from models.stock import Stock, StockTransaction
from models.supplier import Supplier
from models.purchase_order import PurchaseOrder, PurchaseOrderLine
from services.inventory_service import InventoryService
from services.reporting_service import ReportingService
import os

def create_app(config_name='default'):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Register routes
    register_routes(app)
    
    return app

def register_routes(app):
    """Register all API routes"""
    
    @app.route('/')
    def index():
        """Home page"""
        return render_template('index.html')
    
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
                unit_price=data.get('unit_price', 0),
                reorder_point=data.get('reorder_point', 0),
                reorder_quantity=data.get('reorder_quantity', 0),
                status=data.get('status', 'ACTIVE')
            )
            
            db.session.add(product)
            db.session.commit()
            
            return jsonify(product.to_dict()), 201
    
    @app.route('/api/products/<sku>', methods=['GET', 'PUT', 'DELETE'])
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
            product.unit_price = data.get('unit_price', product.unit_price)
            product.reorder_point = data.get('reorder_point', product.reorder_point)
            product.reorder_quantity = data.get('reorder_quantity', product.reorder_quantity)
            product.status = data.get('status', product.status)
            
            db.session.commit()
            return jsonify(product.to_dict())
        
        elif request.method == 'DELETE':
            db.session.delete(product)
            db.session.commit()
            return '', 204
    
    # Warehouse endpoints
    @app.route('/api/warehouses', methods=['GET', 'POST'])
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
    def stock_levels():
        """Get current stock levels for all products"""
        return jsonify(InventoryService.get_all_stock_levels())
    
    @app.route('/api/stock/levels/<sku>', methods=['GET'])
    def product_stock_level(sku):
        """Get stock level for a specific product"""
        warehouse_code = request.args.get('warehouse')
        stock_info = InventoryService.get_stock_level(sku, warehouse_code)
        
        if not stock_info:
            return jsonify({'error': 'Stock not found'}), 404
        
        return jsonify(stock_info)
    
    @app.route('/api/stock/receipt', methods=['POST'])
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
    def low_stock():
        """Get products with low stock levels"""
        threshold = request.args.get('threshold', 20, type=int)
        return jsonify(InventoryService.get_low_stock_items(threshold))
    
    @app.route('/api/stock/transactions', methods=['GET'])
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
    def inventory_valuation():
        """Get inventory valuation report"""
        return jsonify(ReportingService.get_inventory_valuation())
    
    @app.route('/api/reports/stock-movement', methods=['GET'])
    def stock_movement_report():
        """Get stock movement report"""
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        product_sku = request.args.get('product_sku')
        
        return jsonify(ReportingService.get_stock_movement_report(start_date, end_date, product_sku))
    
    @app.route('/api/reports/warehouse-utilization', methods=['GET'])
    def warehouse_utilization():
        """Get warehouse utilization report"""
        return jsonify(ReportingService.get_warehouse_utilization())
    
    @app.route('/api/reports/abc-analysis', methods=['GET'])
    def abc_analysis():
        """Get ABC analysis report"""
        return jsonify(ReportingService.get_abc_analysis())
    
    @app.route('/api/reports/purchase-orders', methods=['GET'])
    def purchase_order_summary():
        """Get purchase order summary"""
        status = request.args.get('status')
        return jsonify(ReportingService.get_purchase_order_summary(status))

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
