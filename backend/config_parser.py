"""
Модуль для чтения конфигурационного файла .conf.
"""
import configparser

def read_config(config_file):
    """
    Читает конфигурационный файл (INI формат) и возвращает настройки в виде словаря.
    
    Аргументы:
      - config_file: путь к .conf файлу.
    
    Ожидаемый формат конфигурационного файла:
        [MARKETPLACES]
        marketplaces = Ozon, Wildberries

        [SEARCH]
        categories = хлебцы, хлебцы гречневые
        urls = https://... , https://...
        time_range = 7

        [EXPORT]
        format = CSV
        save_to_db = True

    Возвращает:
      - settings: словарь, где ключи - названия секций, 
                  а значения - словари параметров из этой секции.
    """
    config = configparser.ConfigParser(interpolation=None)
    config.read(config_file, encoding='utf-8')
    settings = {}
    for section in config.sections():
        settings[section] = dict(config.items(section))
    return settings

if __name__ == "__main__":
    cfg = read_config("config/config.conf")
    print(cfg)
