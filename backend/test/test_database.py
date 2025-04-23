from database import db, init_db, add_item_to_db, get_all_items
import os
import tempfile
from flask import Flask

def test_database():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        init_db()
        data = {
            'name': 'Test Item',
            'marketplace': 'Ozon',
            'identifier': 'http://ozon.ru/test'
        }
        item = add_item_to_db(data)
        items = get_all_items()
        assert len(items) == 1
