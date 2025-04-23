import os
import tempfile
from config_parser import read_config
import yaml

def test_read_config():
    sample_config = {'items': [{'marketplace': 'Ozon', 'identifier': 'https://www.ozon.ru/product/12345'}]}
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.yaml') as tf:
        yaml.safe_dump(sample_config, tf, allow_unicode=True)
        temp_name = tf.name
    config = read_config(temp_name)
    assert 'items' in config
    os.remove(temp_name)
