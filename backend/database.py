from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class MarketplaceItem(db.Model):
    __tablename__ = 'marketplace_item'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    marketplace = db.Column(db.String(64), nullable=False)
    identifier = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PriceRecord(db.Model):
    __tablename__ = 'price_record'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('marketplace_item.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    old_price = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    promotion = db.Column(db.Boolean, default=False)

def init_db():
    db.create_all()

def add_item_to_db(data):
    item = MarketplaceItem(
        name=data.get('name'),
        marketplace=data.get('marketplace'),
        identifier=data.get('identifier')
    )
    db.session.add(item)
    db.session.commit()
    return {
        'id': item.id,
        'name': item.name,
        'marketplace': item.marketplace,
        'identifier': item.identifier
    }

def get_all_items():
    items = MarketplaceItem.query.all()
    return [{'id': item.id, 'name': item.name, 'marketplace': item.marketplace, 'identifier': item.identifier} for item in items]
