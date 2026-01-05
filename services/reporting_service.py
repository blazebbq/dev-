"""
Reporting Service - Generate reports and analytics
"""
from models import db
from models.product import Product
from models.stock import Stock, StockTransaction
from models.purchase_order import PurchaseOrder
from sqlalchemy import func
from datetime import datetime, timedelta

class ReportingService:
    """Service class for reporting and analytics"""
    
    @staticmethod
    def get_inventory_valuation():
        """Calculate total inventory value"""
        query = db.session.query(
            Stock.product_sku,
            func.sum(Stock.quantity_on_hand).label('total_quantity')
        ).group_by(Stock.product_sku).all()
        
        total_value = 0
        items = []
        
        for row in query:
            product = Product.query.get(row.product_sku)
            if product and row.total_quantity:
                item_value = float(product.unit_price) * row.total_quantity
                total_value += item_value
                items.append({
                    'product_sku': row.product_sku,
                    'product_name': product.name,
                    'quantity': row.total_quantity,
                    'unit_price': float(product.unit_price),
                    'total_value': item_value
                })
        
        return {
            'total_inventory_value': total_value,
            'items': items,
            'report_date': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def get_stock_movement_report(start_date=None, end_date=None, product_sku=None):
        """Get stock movement history"""
        query = StockTransaction.query
        
        if start_date:
            query = query.filter(StockTransaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(StockTransaction.transaction_date <= end_date)
        if product_sku:
            query = query.filter(StockTransaction.product_sku == product_sku)
        
        transactions = query.order_by(StockTransaction.transaction_date.desc()).all()
        
        return {
            'transactions': [t.to_dict() for t in transactions],
            'count': len(transactions)
        }
    
    @staticmethod
    def get_warehouse_utilization():
        """Calculate warehouse capacity utilization"""
        warehouses = db.session.query(
            Stock.warehouse_code,
            func.count(Stock.product_sku).label('product_count'),
            func.sum(Stock.quantity_on_hand).label('total_items')
        ).group_by(Stock.warehouse_code).all()
        
        results = []
        for wh in warehouses:
            from models.warehouse import Warehouse
            warehouse = Warehouse.query.get(wh.warehouse_code)
            utilization = None
            if warehouse and warehouse.capacity:
                utilization = (wh.total_items / warehouse.capacity) * 100
            
            results.append({
                'warehouse_code': wh.warehouse_code,
                'warehouse_name': warehouse.name if warehouse else 'Unknown',
                'product_count': wh.product_count,
                'total_items': wh.total_items,
                'capacity': warehouse.capacity if warehouse else None,
                'utilization_percent': round(utilization, 2) if utilization else None
            })
        
        return results
    
    @staticmethod
    def get_purchase_order_summary(status=None):
        """Get purchase order statistics"""
        query = PurchaseOrder.query
        
        if status:
            query = query.filter(PurchaseOrder.status == status)
        
        orders = query.all()
        
        total_value = sum(float(po.total_amount) for po in orders)
        
        return {
            'order_count': len(orders),
            'total_value': total_value,
            'orders': [po.to_dict() for po in orders]
        }
    
    @staticmethod
    def get_abc_analysis():
        """Perform ABC analysis on inventory (based on value)"""
        query = db.session.query(
            Stock.product_sku,
            func.sum(Stock.quantity_on_hand).label('total_quantity')
        ).group_by(Stock.product_sku).all()
        
        items = []
        total_value = 0
        
        for row in query:
            product = Product.query.get(row.product_sku)
            if product and row.total_quantity:
                item_value = float(product.unit_price) * row.total_quantity
                items.append({
                    'product_sku': row.product_sku,
                    'product_name': product.name,
                    'quantity': row.total_quantity,
                    'unit_price': float(product.unit_price),
                    'total_value': item_value
                })
                total_value += item_value
        
        # Sort by value descending
        items.sort(key=lambda x: x['total_value'], reverse=True)
        
        # Calculate cumulative percentage
        cumulative_value = 0
        for item in items:
            cumulative_value += item['total_value']
            cumulative_percent = (cumulative_value / total_value * 100) if total_value > 0 else 0
            
            # Classify as A, B, or C
            if cumulative_percent <= 80:
                item['category'] = 'A'
            elif cumulative_percent <= 95:
                item['category'] = 'B'
            else:
                item['category'] = 'C'
            
            item['cumulative_percent'] = round(cumulative_percent, 2)
        
        return {
            'items': items,
            'total_value': total_value
        }
