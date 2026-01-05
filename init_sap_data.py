"""
Initialize SAP-style data: movement types, default plant/slocs, config
"""
from models import db
from models.sap_models import SAPPlant, SAPStorageLocation, SAPMovementType, SAPConfig
import json


def init_sap_data():
    """Initialize SAP master data"""
    
    # Create default plant if doesn't exist
    plant_1000 = SAPPlant.query.filter_by(code='1000').first()
    if not plant_1000:
        plant_1000 = SAPPlant(
            code='1000',
            name='Main Plant',
            city='New York',
            country='US',
            active=True
        )
        db.session.add(plant_1000)
        db.session.flush()
        print(f"Created plant: {plant_1000.code} - {plant_1000.name}")
    
    # Create default storage locations
    slocs = [
        ('0001', 'Main Storage'),
        ('0002', 'Receiving Area'),
        ('0003', 'Shipping Area'),
        ('0004', 'Quality Hold'),
    ]
    
    for sloc_code, sloc_name in slocs:
        sloc = SAPStorageLocation.query.filter_by(plant_id=plant_1000.id, code=sloc_code).first()
        if not sloc:
            sloc = SAPStorageLocation(
                plant_id=plant_1000.id,
                code=sloc_code,
                name=sloc_name,
                active=True
            )
            db.session.add(sloc)
            print(f"Created storage location: {plant_1000.code}-{sloc_code} - {sloc_name}")
    
    # Create movement types
    movement_types = [
        {
            'code': '101',
            'name': 'GR Goods Receipt',
            'description': 'Goods Receipt for Purchase Order',
            'category': 'GR',
            'reversal_code': '102',
            'required_fields': ['material', 'plant', 'sloc_to', 'quantity'],
            'ui_fields': ['material', 'plant', 'sloc_to', 'quantity', 'uom', 'reference_text', 'batch'],
            'allow_batch': True
        },
        {
            'code': '102',
            'name': 'GR Reversal',
            'description': 'Reversal of Goods Receipt',
            'category': 'REV',
            'reversal_code': None,
            'required_fields': ['material', 'plant', 'sloc_from', 'quantity'],
            'ui_fields': ['material', 'plant', 'sloc_from', 'quantity', 'uom', 'reference_text'],
            'allow_batch': True
        },
        {
            'code': '261',
            'name': 'GI to Production',
            'description': 'Goods Issue to Production Order',
            'category': 'GI',
            'reversal_code': '262',
            'required_fields': ['material', 'plant', 'sloc_from', 'quantity', 'reference_text'],
            'ui_fields': ['material', 'plant', 'sloc_from', 'quantity', 'uom', 'reference_text', 'batch'],
            'allow_batch': True
        },
        {
            'code': '262',
            'name': 'GI Reversal',
            'description': 'Reversal of Goods Issue',
            'category': 'REV',
            'reversal_code': None,
            'required_fields': ['material', 'plant', 'sloc_to', 'quantity'],
            'ui_fields': ['material', 'plant', 'sloc_to', 'quantity', 'uom', 'reference_text'],
            'allow_batch': True
        },
        {
            'code': '311',
            'name': 'Transfer Posting',
            'description': 'Transfer between Storage Locations',
            'category': 'TR',
            'reversal_code': '311',  # 311 reverses itself
            'required_fields': ['material', 'plant', 'sloc_from', 'sloc_to', 'quantity'],
            'ui_fields': ['material', 'plant', 'sloc_from', 'sloc_to', 'quantity', 'uom', 'reference_text', 'batch'],
            'allow_batch': True
        },
        {
            'code': '551',
            'name': 'Scrapping',
            'description': 'Scrapping without Cost Collector',
            'category': 'SCRAP',
            'reversal_code': '552',
            'required_fields': ['material', 'plant', 'sloc_from', 'quantity', 'item_text'],
            'ui_fields': ['material', 'plant', 'sloc_from', 'quantity', 'uom', 'item_text'],
            'allow_batch': True
        },
        {
            'code': '552',
            'name': 'Scrap Reversal',
            'description': 'Reversal of Scrapping',
            'category': 'REV',
            'reversal_code': None,
            'required_fields': ['material', 'plant', 'sloc_to', 'quantity'],
            'ui_fields': ['material', 'plant', 'sloc_to', 'quantity', 'uom'],
            'allow_batch': True
        }
    ]
    
    for mvt_data in movement_types:
        mvt = SAPMovementType.query.get(mvt_data['code'])
        if not mvt:
            mvt = SAPMovementType(
                code=mvt_data['code'],
                name=mvt_data['name'],
                description=mvt_data['description'],
                category=mvt_data['category'],
                reversal_code=mvt_data['reversal_code'],
                required_fields=json.dumps(mvt_data['required_fields']),
                ui_fields=json.dumps(mvt_data['ui_fields']),
                allow_batch=mvt_data['allow_batch']
            )
            db.session.add(mvt)
            print(f"Created movement type: {mvt.code} - {mvt.name}")
    
    # Create default config
    configs = [
        ('allow_negative_stock', 'false', 'Allow negative stock in postings'),
        ('default_plant', '1000', 'Default plant code'),
        ('default_sloc', '0001', 'Default storage location code'),
    ]
    
    for key, value, description in configs:
        config = SAPConfig.query.get(key)
        if not config:
            config = SAPConfig(key=key, value=value, description=description)
            db.session.add(config)
            print(f"Created config: {key} = {value}")
    
    db.session.commit()
    print("\nSAP data initialization complete!")


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        init_sap_data()
