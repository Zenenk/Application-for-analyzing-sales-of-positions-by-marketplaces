from backend.config_parser import read_config

cfg = read_config("config/config.conf")
print("Config:", cfg)
urls = cfg.get("SEARCH", {}).get("urls", "")
print("URLs raw:", urls)
for u in [u.strip() for u in urls.split(",")]:
    print(" -> URL:", u)
