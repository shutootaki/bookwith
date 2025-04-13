from dropbox import Dropbox
from src.config.app_config import AppConfig


def get_dropbox_client() -> Dropbox:
    """Dropboxクライアントのインスタンスを取得します"""
    config = AppConfig.get_config()
    return Dropbox(
        app_key=config.dropbox_client_id,
        app_secret=config.dropbox_client_secret,
    )


# トークンのマッピング
TOKEN_MAPPING = {"dropbox": "dropbox_refresh_token"}
