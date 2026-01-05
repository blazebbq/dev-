"""
Inventory Service - Business logic for inventory management
"""
from models import db
from models.product import Product
from models.warehouse import Warehouse
from models.stock import Stock, StockTransaction
from datetime import datetime
from sqlalchemy import func

class InventoryService:
    """Service class for inventory operations"""
    
    @staticmethod
    def get_stock_level(product_sku, warehouse_code=None):
        """Get current stock level for a product"""
        if warehouse_code:
            stock = Stock.query.filter_by(
                product_sku=product_sku,
                warehouse_code=warehouse_code
            ).first()
            return stock.to_dict() if stock else None
        else:
            # Get total stock across all warehouses
            stocks = Stock.query.filter_by(product_sku=product_sku).all()
            total_on_hand = sum(s.quantity_on_hand for s in stocks)
            total_available = sum(s.quantity_available for s in stocks)
            total_reserved = sum(s.quantity_reserved for s in stocks)
            
            return {
                'product_sku': product_sku,
                'total_quantity_on_hand': total_on_hand,
                'total_quantity_available': total_available,
                'total_quantity_reserved': total_reserved,
                'warehouses': [s.to_dict() for s in stocks]
            }
    
    @staticmethod
    def get_all_stock_levels():
        """Get stock levels for all products"""
        query = db.session.query(
            Stock.product_sku,
            func.sum(Stock.quantity_on_hand).label('total_on_hand'),
            func.sum(Stock.quantity_available).label('total_available'),
            func.sum(Stock.quantity_reserved).label('total_reserved')
        ).group_by(Stock.product_sku).all()
        
        results = []
        for row in query:
            product = Product.query.get(row.product_sku)
            results.append({
                'product_sku': row.product_sku,
                'product_name': product.name if product else 'Unknown',
                'total_on_hand': int(row.total_on_hand or 0),
                'total_available': int(row.total_available or 0),
                'total_reserved': int(row.total_reserved or 0),
                'reorder_point': product.reorder_point if product else 0,
                'needs_reorder': (row.total_available or 0) <= (product.reorder_point if product else 0)
            })
        
        return results
    
    @staticmethod
    def receive_stock(product_sku, warehouse_code, quantity, unit_cost=None, reference=None, notes=None):
        """Process stock receipt"""
        # Validate product and warehouse
        product = Product.query.get(product_sku)
        if not product:
            raise ValueError(f"Product {product_sku} not found")
        
        warehouse = Warehouse.query.get(warehouse_code)
        if not warehouse:
            raise ValueError(f"Warehouse {warehouse_code} not found")
        
        # Get or create stock record
        stock = Stock.query.filter_by(
            product_sku=product_sku,
            warehouse_code=warehouse_code
        ).first()
        
        if not stock:
            stock = Stock(
                product_sku=product_sku,
                warehouse_code=warehouse_code,
                quantity_on_hand=0,
                quantity_reserved=0,
                quantity_available=0
            )
            db.session.add(stock)
        
        # Update stock levels
        stock.quantity_on_hand += quantity
        stock.quantity_available += quantity
        stock.updated_at = datetime.utcnow()
        
        # Create transaction record
        transaction = StockTransaction(
            transaction_type='RECEIPT',
            product_sku=product_sku,
            warehouse_code=warehouse_code,
            quantity=quantity,
            unit_cost=unit_cost,
            reference=reference,
            notes=notes,
            transaction_date=datetime.utcnow()
        )
        db.session.add(transaction)
        
        db.session.commit()
        
        return {
            'stock': stock.to_dict(),
            'transaction': transaction.to_dict()
        }
    
    @staticmethod
    def issue_stock(product_sku, warehouse_code, quantity, reference=None, notes=None):
        """Process stock issue (removal from inventory)"""
        stock = Stock.query.filter_by(
            product_sku=product_sku,
            warehouse_code=warehouse_code
        ).first()
        
        if not stock:
            raise ValueError(f"No stock found for {product_sku} at {warehouse_code}")
        
        if stock.quantity_available < quantity:
            raise ValueError(f"Insufficient stock. Available: {stock.quantity_available}, Requested: {quantity}")
        
        # Update stock levels
        stock.quantity_on_hand -= quantity
        stock.quantity_available -= quantity
        stock.updated_at = datetime.utcnow()
        
        # Create transaction record
        transaction = StockTransaction(
            transaction_type='ISSUE',
            product_sku=product_sku,
            warehouse_code=warehouse_code,
            quantity=-quantity,  # Negative for issue
            reference=reference,
            notes=notes,
            transaction_date=datetime.utcnow()
        )
        db.session.add(transaction)
        
        db.session.commit()
        
        return {
            'stock': stock.to_dict(),
            'transaction': transaction.to_dict()
        }
    
    @staticmethod
    def transfer_stock(product_sku, from_warehouse, to_warehouse, quantity, reference=None, notes=None):
        """Transfer stock between warehouses"""
        # Validate source stock
        source_stock = Stock.query.filter_by(
            product_sku=product_sku,
            warehouse_code=from_warehouse
        ).first()
        
        if not source_stock:
            raise ValueError(f"No stock found for {product_sku} at {from_warehouse}")
        
        if source_stock.quantity_available < quantity:
            raise ValueError(f"Insufficient stock. Available: {source_stock.quantity_available}, Requested: {quantity}")
        
        # Update source warehouse
        source_stock.quantity_on_hand -= quantity
        source_stock.quantity_available -= quantity
        source_stock.updated_at = datetime.utcnow()
        
        # Get or create destination stock
        dest_stock = Stock.query.filter_by(
            product_sku=product_sku,
            warehouse_code=to_warehouse
        ).first()
        
        if not dest_stock:
            dest_stock = Stock(
                product_sku=product_sku,
                warehouse_code=to_warehouse,
                quantity_on_hand=0,
                quantity_reserved=0,
                quantity_available=0
            )
            db.session.add(dest_stock)
        
        # Update destination warehouse
        dest_stock.quantity_on_hand += quantity
        dest_stock.quantity_available += quantity
        dest_stock.updated_at = datetime.utcnow()
        
        # Create transaction record
        transaction = StockTransaction(
            transaction_type='TRANSFER',
            product_sku=product_sku,
            warehouse_code=from_warehouse,
            to_warehouse_code=to_warehouse,
            quantity=quantity,
            reference=reference,
            notes=notes,
            transaction_date=datetime.utcnow()
        )
        db.session.add(transaction)
        
        db.session.commit()
        
        return {
            'source_stock': source_stock.to_dict(),
            'destination_stock': dest_stock.to_dict(),
            'transaction': transaction.to_dict()
        }
    
    @staticmethod
    def adjust_stock(product_sku, warehouse_code, new_quantity, reason=None):
        """Adjust stock to a specific quantity (for corrections)"""
        stock = Stock.query.filter_by(
            product_sku=product_sku,
            warehouse_code=warehouse_code
        ).first()
        
        if not stock:
            # Create new stock record
            stock = Stock(
                product_sku=product_sku,
                warehouse_code=warehouse_code,
                quantity_on_hand=new_quantity,
                quantity_reserved=0,
                quantity_available=new_quantity
            )
            db.session.add(stock)
            adjustment = new_quantity
        else:
            adjustment = new_quantity - stock.quantity_on_hand
            stock.quantity_on_hand = new_quantity
            stock.quantity_available = new_quantity - stock.quantity_reserved
            stock.updated_at = datetime.utcnow()
        
        # Create transaction record
        transaction = StockTransaction(
            transaction_type='ADJUSTMENT',
            product_sku=product_sku,
            warehouse_code=warehouse_code,
            quantity=adjustment,
            notes=reason,
            transaction_date=datetime.utcnow()
        )
        db.session.add(transaction)
        
        db.session.commit()
        
        return {
            'stock': stock.to_dict(),
            'transaction': transaction.to_dict()
        }
    
    @staticmethod
    def get_low_stock_items(threshold_percent=20):
        """Get products with low stock levels"""
        results = []
        products = Product.query.filter(Product.status == 'ACTIVE').all()
        
        for product in products:
            stock_info = InventoryService.get_stock_level(product.sku)
            if stock_info:
                total_available = stock_info.get('total_quantity_available', 0)
                threshold = product.reorder_point * (1 + threshold_percent / 100)
                
                if total_available <= threshold:
                    results.append({
                        'product_sku': product.sku,
                        'product_name': product.name,
                        'current_stock': total_available,
                        'reorder_point': product.reorder_point,
                        'reorder_quantity': product.reorder_quantity,
                        'needs_immediate_reorder': total_available <= product.reorder_point
                    })
        
        return results
