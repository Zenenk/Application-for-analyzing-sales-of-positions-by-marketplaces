import configparser

def read_config(config_file):
    """
    Чтение конфигурационного файла и возвращение настроек.
    
    Ожидаемый формат файла (.conf):
    
    [MARKETPLACES]
    marketplaces = Ozon, Wildberries

    [SEARCH]
    categories = хлебцы, хлебцы гречневые
    urls = https://www.ozon.ru/category/produkty, https://www.wildberries.ru/catalog/produkty
    time_range = 7  # дней

    [EXPORT]
    format = CSV
    save_to_db = True
    """
    config = configparser.ConfigParser()
    config.read(config_file, encoding='utf-8')
    settings = {}
    for section in config.sections():
        settings[section] = dict(config.items(section))
    return settings

if __name__ == "__main__":
    config = read_config("config/config.conf")
    print(config)
