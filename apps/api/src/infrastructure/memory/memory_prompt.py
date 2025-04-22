import logging
from typing import Any

import tiktoken
from tiktoken.core import Encoding

from src.config.app_config import AppConfig
from src.domain.message.entities.message import Message

# ロガーの設定
logger = logging.getLogger(__name__)

# tiketokenエンコーダー（トークンカウント用）
TIKTOKEN_ENCODING: Encoding | None = None
try:
    TIKTOKEN_ENCODING = tiktoken.get_encoding("cl100k_base")  # GPT-4用のエンコーディング
except Exception as e:
    logger.warning(f"tiktokenの初期化に失敗しました: {str(e)}")


def estimate_tokens(text: str) -> int:
    """テキストのトークン数を推定."""
    if TIKTOKEN_ENCODING:
        return len(TIKTOKEN_ENCODING.encode(text))
    # フォールバック: 簡易的なトークン数推定
    return len(text) // 4


def format_memory_item(memory: dict[str, Any], prefix: str = "") -> str:
    """記憶アイテムをフォーマット."""
    content = memory.get("content", "N/A")

    # 関連度を取得
    certainty = None
    if "_additional" in memory and isinstance(memory["_additional"], dict):
        certainty = memory["_additional"].get("certainty")

    # 関連度がある場合は表示
    formatted = f"{prefix}{content}"
    if certainty is not None:
        formatted += f" (関連度: {certainty:.2f})"

    return formatted


def truncate_text_to_tokens(text: str, max_tokens: int) -> str:
    """トークン数制限に基づいてテキストを切り詰める."""
    if TIKTOKEN_ENCODING:
        tokens = TIKTOKEN_ENCODING.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return TIKTOKEN_ENCODING.decode(tokens[:max_tokens]) + "..."
    # フォールバック: 大まかな文字数で切り詰め
    char_per_token = 4  # 平均的な文字/トークン比
    max_chars = max_tokens * char_per_token
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def create_memory_prompt(  # noqa: C901
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
提供された情報を活用しながら、一貫性のあるパーソナライズされた応答を心がけてください。
以前の会話やユーザープロファイルから得られた情報を自然に組み込み、ユーザーとの関係性を深める対話を行ってください。"""

    # プロンプトパーツを準備（後で結合する）
    prompt_parts = []
    prompt_parts.append(system_prompt)

    # ユーザープロファイル情報のフォーマット
    if user_profile_memories:
        profile_context = "\n--- ユーザープロファイル情報 ---\n"
        profile_items = []

        for mem in user_profile_memories:
            profile_items.append(format_memory_item(mem, "[ユーザープロファイル]: "))

        profile_context += "\n".join(profile_items)
        prompt_parts.append(profile_context)

    # 関連する過去の会話スニペットのフォーマット
    if chat_memories:
        memory_context = "\n--- 関連する過去の会話 ---\n"
        memory_items = []

        for mem in chat_memories:
            sender = mem.get("sender", "不明")
            mem_type = mem.get("type", "message")

            # 日本語に変換
            sender_ja = "ユーザー" if sender == "user" else "AI" if sender == "assistant" else "システム"
            mem_type_ja = "メッセージ" if mem_type == "message" else "要約"

            prefix = f"[過去の{mem_type_ja} by {sender_ja}]: "
            memory_items.append(format_memory_item(mem, prefix))

        memory_context += "\n".join(memory_items)
        prompt_parts.append(memory_context)

    # 最近のチャット履歴のフォーマット
    if buffer:
        history_context = "\n--- 最近のチャット履歴 (古い順) ---\n"
        history_items = []

        # バッファは新しい順に並んでいるので、古い順に反転
        for msg in reversed(buffer):
            if msg.is_deleted:
                continue

            sender = "ユーザー" if msg.sender_type.value == "user" else "AI"
            history_items.append(f"{sender}: {msg.content.value}")

        history_context += "\n".join(history_items)
        prompt_parts.append(history_context)

    # ユーザークエリを追加
    prompt_parts.append(f"\nユーザー: {user_query}")
    prompt_parts.append("\nAI:")  # AIの回答を開始する合図

    # 全てのパーツを結合
    full_prompt = "\n".join(prompt_parts)

    # トークン数チェック
    estimated_tokens = estimate_tokens(full_prompt)
    max_tokens = config.max_prompt_tokens or 8192  # デフォルト値を設定

    if estimated_tokens > max_tokens:
        logger.warning(f"プロンプトが大きすぎます: {estimated_tokens}トークン。{max_tokens}トークン以下に切り詰めます。")

        # 切り詰め戦略
        # 1. システムプロンプトは保持
        # 2. ユーザークエリとAI:は保持
        # 3. 履歴、記憶、プロファイルを適宜切り詰め

        # 保持する必須部分
        system_part = prompt_parts[0]
        query_part = f"\nユーザー: {user_query}\nAI:"

        required_tokens = estimate_tokens(system_part + query_part)
        remaining_tokens = max_tokens - required_tokens

        # 残りのパーツを配分（優先度付け）
        other_parts = prompt_parts[1:-2]  # システムプロンプトとクエリ部分を除く

        if other_parts:
            # 均等に配分する単純な方法
            tokens_per_part = remaining_tokens // len(other_parts)
            truncated_parts = []

            for part in other_parts:
                truncated_parts.append(truncate_text_to_tokens(part, tokens_per_part))

            # 再構築
            full_prompt = system_part + "\n" + "\n".join(truncated_parts) + query_part

    return full_prompt


def create_memory_prompt_with_reranking(
    buffer: list[Message],
    user_query: str,
    user_id: str,
    chat_id: str,
    memory_store,
    embedding_model,
    config: AppConfig | None = None,
) -> str:
    """検索結果の再ランキングを行うプロンプト構築.

    Args:
        buffer: 最新のメッセージバッファ
        user_query: ユーザーの最新のクエリ
        user_id: ユーザーID
        chat_id: チャットID
        memory_store: メモリストア
        embedding_model: 埋め込みモデル
        config: アプリケーション設定

    Returns:
        構築されたプロンプト

    """
    if config is None:
        config = AppConfig.get_config()

    # クエリをベクトル化
    query_vector = memory_store.encode_text(user_query)

    # 関連記憶を検索（通常より多めに取得）
    chat_memories = memory_store.search_chat_memories(
        user_id=user_id, chat_id=chat_id, query_vector=query_vector, limit=config.memory_chat_results * 2
    )

    user_profile_memories = memory_store.search_user_profile(user_id=user_id, query_vector=query_vector, limit=config.memory_profile_results * 2)

    # コンテキストに基づく再ランキング
    if len(chat_memories) > config.memory_chat_results:
        chat_memories = rerank_memories(chat_memories, buffer, user_query, config.memory_chat_results)

    if len(user_profile_memories) > config.memory_profile_results:
        user_profile_memories = rerank_memories(user_profile_memories, buffer, user_query, config.memory_profile_results)

    # 最終的なプロンプトを構築
    return create_memory_prompt(
        buffer=buffer,
        chat_memories=chat_memories,
        user_profile_memories=user_profile_memories,
        user_query=user_query,
        config=config,
    )


def rerank_memories(memories: list[dict[str, Any]], buffer: list[Message], query: str, limit: int) -> list[dict[str, Any]]:
    """コンテキストに基づいて記憶を再ランキング.

    単純なベクトル検索結果に加えて、最近の会話文脈や意味的な重要性を加味して再ランキングする。

    Args:
        memories: 記憶リスト
        buffer: 最新の会話バッファ
        query: ユーザークエリ
        limit: 返す記憶の数

    Returns:
        再ランキングされた記憶リスト

    """
    if not memories or len(memories) <= limit:
        return memories

    # スコアリング用の辞書を作成
    scored_memories = []

    # 最近の会話コンテキスト（バッファから取得）
    recent_context = " ".join([msg.content.value for msg in buffer if not msg.is_deleted])

    for mem in memories:
        base_score = 1.0
        if "_additional" in mem and mem["_additional"].get("certainty"):
            base_score = mem["_additional"]["certainty"]

        # スコア調整要素
        bonus = 0.0

        # タイプに基づくボーナス
        if mem.get("type") == "summary":
            bonus += 0.1  # 要約はやや優先

        # コンテンツに基づくボーナス（クエリの単語が含まれるか）
        content = mem.get("content", "")
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        word_overlap = len(query_words.intersection(content_words)) / max(1, len(query_words))
        bonus += word_overlap * 0.2

        # 最終スコア計算
        final_score = base_score + bonus

        # スコア付き記憶を追加
        scored_mem = mem.copy()
        scored_mem["_rerank_score"] = final_score
        scored_memories.append(scored_mem)

    # スコアでソートして上位を返す
    sorted_memories = sorted(scored_memories, key=lambda x: x.get("_rerank_score", 0), reverse=True)
    return sorted_memories[:limit]
