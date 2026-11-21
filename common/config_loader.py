import os
from pathlib import Path
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = ROOT_DIR / "config" / "settings.yaml"
    if not config_path.exists():
        config_path = ROOT_DIR / "config" / "settings.example.yaml"

    with open(config_path, mode="r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # 支持通过环境变量覆盖敏感配置（用于 GitHub Actions CI/CD 注入 Secrets）
    server_ip = os.getenv("MALL_SERVER_IP")
    if server_ip:
        cfg["env"]["api_base_url"] = f"http://{server_ip}:28019/api/v1"
        cfg["env"]["web_base_url"] = f"http://{server_ip}"
        cfg["mysql"]["host"] = server_ip

    if os.getenv("MALL_MYSQL_PWD"):
        cfg["mysql"]["password"] = os.getenv("MALL_MYSQL_PWD")
    if os.getenv("MALL_LOGIN_NAME"):
        cfg["account"]["login_name"] = os.getenv("MALL_LOGIN_NAME")
    if os.getenv("MALL_LOGIN_PWD"):
        cfg["account"]["password"] = os.getenv("MALL_LOGIN_PWD")

    return cfg


CFG = load_config()