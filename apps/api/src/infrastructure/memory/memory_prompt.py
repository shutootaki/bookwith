from typing import Any

from src.config.app_config import AppConfig
from src.domain.message.entities.message import Message


def create_memory_prompt(
    buffer: list[Message],
    chat_memories: list[dict[str, Any]],
    user_profile_memories: list[dict[str, Any]],
    user_query: str,
    config: AppConfig | None = None,
) -> str:
    """記憶情報を含むプロンプトを構築する.

    Args:
        buffer: 最新のメッセージバッファ
        chat_memories: チャット関連の記憶検索結果
        user_profile_memories: ユーザープロファイル関連の記憶検索結果
        user_query: ユーザーの最新のクエリ
        config: アプリケーション設定

    Returns:
        構築されたプロンプト

    """
    if config is None:
        config = AppConfig.get_config()

    # システムプロンプト
    system_prompt = """あなたは役立つAIアシスタントです。ユーザーのプロファイル情報や過去の会話、最近のチャット履歴を考慮して、質問に丁寧に回答してください。
提供された情報を活用しながら、一貫性のあるパーソナライズされた応答を心がけてください。"""

    # ユーザープロファイル情報のフォーマット
    profile_context = "\n--- ユーザープロファイル情報 ---\n"
    if user_profile_memories:
        for mem in user_profile_memories:
            content = mem.get("content", "N/A")
            # _additionalはdict型で、その中にcertaintyがある場合に取得
            certainty = None
            if "_additional" in mem and isinstance(mem["_additional"], dict):
                certainty = mem["_additional"].get("certainty")

            profile_context += f"[ユーザープロファイル]: {content}"
            if certainty is not None:
                profile_context += f" (関連度: {certainty:.2f})"
            profile_context += "\n"
    else:
        profile_context += "関連するユーザープロファイル情報はありません。\n"

    # 関連する過去の会話スニペットのフォーマット
    memory_context = "\n--- 関連する過去の会話 ---\n"
    if chat_memories:
        for mem in chat_memories:
            content = mem.get("content", "N/A")
            sender = mem.get("sender", "不明")
            mem_type = mem.get("type", "message")
            # _additionalはdict型で、その中にcertaintyがある場合に取得
            certainty = None
            if "_additional" in mem and isinstance(mem["_additional"], dict):
                certainty = mem["_additional"].get("certainty")

            # 日本語に変換
            sender_ja = "ユーザー" if sender == "user" else "AI" if sender == "assistant" else "システム"
            mem_type_ja = "メッセージ" if mem_type == "message" else "要約"

            prefix = f"[過去の{mem_type_ja} by {sender_ja}]"
            memory_context += f"{prefix}: {content}"
            if certainty is not None:
                memory_context += f" (関連度: {certainty:.2f})"
            memory_context += "\n"
    else:
        memory_context += "現在のクエリに関連する過去の会話はありません。\n"

    # 最近のチャット履歴のフォーマット
    history_context = "\n--- 最近のチャット履歴 (古い順) ---\n"
    if buffer:
        # バッファは新しい順に並んでいるので、古い順に直す
        for msg in reversed(buffer):
            sender = "ユーザー" if msg.sender_type.value == "user" else "AI"
            history_context += f"{sender}: {msg.content.value}\n"
    else:
        history_context += "このセッションでのチャット履歴はまだありません。\n"

    # プロンプト結合
    # 順序: システム -> プロファイル -> 過去の会話 -> 最近の履歴 -> ユーザークエリ
    prompt_parts = [
        system_prompt,
        profile_context,
        memory_context,
        history_context,
        f"ユーザー: {user_query}",
        "AI:",  # AIの回答を開始する合図
    ]

    # 全てのパーツを結合
    full_prompt = "\n".join(prompt_parts)

    return full_prompt
