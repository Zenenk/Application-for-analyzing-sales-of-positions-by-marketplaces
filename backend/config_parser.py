import yaml

def read_config(file_path):
    with open(file_path, encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config
