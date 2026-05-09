import humps
from pydantic import BaseModel, ConfigDict


def to_camel(string: str) -> str:
    return humps.camelize(string)


class BaseSchemaModel(BaseModel):
    """API レスポンス / 既存リクエスト共通の base.

    互換性のため `extra` は default のまま（=`ignore`）にしておき、
    新規 / 既存リクエストモデルでオーバーポストを禁止したい場合は
    `BaseRequestSchemaModel` を継承する。
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class BaseRequestSchemaModel(BaseModel):
    """CR-4 補強: リクエストモデル用の strict ベース.

    `extra='forbid'` で予期しないフィールドを 422 で弾く。
    クライアントが `sender_type=system` 等の意図しないキーを送り込めない構造を強制する。

    既存スキーマは段階的に移行する想定（今は新規 / 重要 schema から適用）。
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )
