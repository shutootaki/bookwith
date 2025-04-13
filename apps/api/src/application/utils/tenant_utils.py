"""テナント管理のためのユーティリティ関数"""

from typing import Optional


def extract_user_id_from_tenant(tenant_id: str) -> Optional[str]:
    """テナントIDからユーザーIDを抽出する"""
    parts = tenant_id.split("_", 1)
    if len(parts) > 0:
        return parts[0]
    return None


def extract_file_info_from_tenant(tenant_id: str) -> Optional[str]:
    """テナントIDからファイル情報を抽出する"""
    parts = tenant_id.split("_", 1)
    if len(parts) > 1:
        return parts[1]
    return None
