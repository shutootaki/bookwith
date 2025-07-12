"""プロンプト構築サービス."""

import logging
from typing import Any

import tiktoken
from tiktoken.core import Encoding

from src.config.app_config import AppConfig
from src.domain.message.entities.message import Message
from src.infrastructure.memory.memory_retrieval_service import MemoryRetrievalService

logger = logging.getLogger(__name__)

# tiketokenエンコーダー（トークンカウント用）
TIKTOKEN_ENCODING: Encoding | None = None
try:
    TIKTOKEN_ENCODING = tiktoken.get_encoding("cl100k_base")  # GPT-4用のエンコーディング
except Exception as e:
    logger.warning(f"tiktokenの初期化に失敗しました: {str(e)}")


class PromptBuilderService:
    """プロンプト構築に特化したサービス."""

    def __init__(self, memory_retrieval_service: MemoryRetrievalService | None = None) -> None:
        """プロンプト構築サービスの初期化."""
        self.config = AppConfig.get_config()
        self.memory_retrieval = memory_retrieval_service or MemoryRetrievalService()

    def build_memory_prompt(self, buffer: list[Message], user_query: str, user_id: str, chat_id: str) -> str:
        """記憶に基づくプロンプトを構築.

        Args:
            buffer: 最新のメッセージバッファ
            user_query: ユーザーの質問/クエリ
            user_id: ユーザーID
            chat_id: チャットID

        Returns:
            構築されたプロンプト

        """
        # 関連する記憶を検索
        chat_memories = self.memory_retrieval.search_relevant_memories(user_id=user_id, chat_id=chat_id, query=user_query)

        # プロンプトを構築
        return self._create_memory_prompt(buffer=buffer, chat_memories=chat_memories, user_query=user_query)

    def _create_memory_prompt(
        self,
        buffer: list[Message],
        chat_memories: list[dict[str, Any]],
        user_query: str,
    ) -> str:
        """記憶とバッファからプロンプトを作成."""
        system_prompt = (
            "ユーザーのプロファイル情報や過去の会話、最近のチャット履歴を考慮して、質問に回答してください。"
            "提供された情報を活用しながら、一貫性のあるパーソナライズされた応答を心がけてください。"
        )

        prompt_parts = [system_prompt]

        # 過去の会話記憶を追加
        if chat_memories:
            memory_items = [
                self.memory_retrieval.format_memory_item(
                    mem,
                    f"[過去の{'メッセージ' if mem.get('type') == 'message' else '要約'} by "
                    f"{'ユーザー' if mem.get('sender') == 'user' else 'AI' if mem.get('sender') == 'assistant' else 'システム'}]: ",
                )
                for mem in chat_memories
            ]
            prompt_parts.append("\n--- 関連する過去の会話 ---\n" + "\n".join(memory_items))

        # 最近のチャット履歴を追加
        if buffer:
            history_items = [
                f"{'ユーザー' if msg.sender_type.value == 'user' else 'AI'}: {msg.content.value}" for msg in reversed(buffer) if not msg.is_deleted
            ]
            prompt_parts.append("\n--- 最近のチャット履歴 (古い順) ---\n" + "\n".join(history_items))

        prompt_parts.append(f"\nユーザー: {user_query}\nAI:")

        # プロンプトを結合
        full_prompt = "\n".join(prompt_parts)

        # トークン数制限を適用
        return self._apply_token_limit(full_prompt, prompt_parts)

    def _apply_token_limit(self, full_prompt: str, prompt_parts: list[str]) -> str:
        """トークン数制限を適用してプロンプトを調整."""
        estimated_tokens = self._estimate_tokens(full_prompt)
        max_tokens = 8192

        if estimated_tokens > max_tokens:
            # システムプロンプトとクエリ部分は必ず残す
            required = prompt_parts[0] + prompt_parts[-1]
            remain_tokens = max_tokens - self._estimate_tokens(required)

            # 履歴・記憶部分を均等に切り詰め
            middle_parts = prompt_parts[1:-1]
            if middle_parts:
                per_part = max(remain_tokens // len(middle_parts), 1)
                truncated = [self._truncate_text_to_tokens(p, per_part) for p in middle_parts]
                full_prompt = prompt_parts[0] + "\n" + "\n".join(truncated) + prompt_parts[-1]

        return full_prompt

    def _estimate_tokens(self, text: str) -> int:
        """テキストのトークン数を推定."""
        if TIKTOKEN_ENCODING:
            return len(TIKTOKEN_ENCODING.encode(text))
        # フォールバック: 簡易的なトークン数推定
        return len(text) // 4

    def _truncate_text_to_tokens(self, text: str, max_tokens: int) -> str:
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
