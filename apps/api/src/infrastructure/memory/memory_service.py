import logging
from datetime import datetime
from typing import Any

import tiktoken
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from tiktoken.core import Encoding

from src.config.app_config import AppConfig
from src.domain.annotation.entities.annotation import Annotation
from src.domain.book.entities.book import Book
from src.domain.message.entities.message import Message
from src.infrastructure.memory.memory_vector_store import MemoryVectorStore

# ロガーの設定
logger = logging.getLogger(__name__)

# tiketokenエンコーダー（トークンカウント用）
TIKTOKEN_ENCODING: Encoding | None = None
try:
    TIKTOKEN_ENCODING = tiktoken.get_encoding("cl100k_base")  # GPT-4用のエンコーディング
except Exception as e:
    logger.warning(f"tiktokenの初期化に失敗しました: {str(e)}")


class MemoryService:
    """記憶管理サービス."""

    def __init__(self) -> None:
        """記憶管理サービスの初期化."""
        self.config = AppConfig.get_config()
        self.memory_store = MemoryVectorStore()

    def search_relevant_memories(self, user_id: str, chat_id: str, query: str, chat_limit: int | None = None) -> list[dict[str, Any]]:
        """ユーザークエリに関連する記憶を検索.

        Args:
            user_id: ユーザーID
            chat_id: チャットID
            query: ユーザーの質問/クエリ
            chat_limit: 取得するチャット記憶の数

        Returns:
            チャット記憶リスト

        """
        # デフォルト値設定
        if chat_limit is None:
            chat_limit = self.config.memory_chat_results

        try:
            # クエリをベクトル化
            query_vector = self.memory_store.encode_text(query)

            return self.memory_store.search_chat_memories(user_id=user_id, chat_id=chat_id, query_vector=query_vector, limit=chat_limit)
        except Exception as e:
            logger.error(f"記憶検索中にエラーが発生: {str(e)}", exc_info=True)
            return []

    def vectorize_message(self, message: Message) -> None:
        """メッセージを同期的にベクトル化.

        Args:
            message: ベクトル化するメッセージ

        """
        self.vectorize_text_background(message=message, memory_store=self.memory_store, config=self.config)
        logger.debug(f"メッセージID {message.id.value} のベクトル化を実行")

    def vectorize_text_background(self, message: Message, memory_store: MemoryVectorStore, config: AppConfig | None = None) -> None:
        """メッセージをベクトル化して保存する非同期タスク."""
        if config is None:
            config = AppConfig.get_config()

        try:
            # メッセージの内容をベクトル化
            text = message.content.value
            vector = memory_store.encode_text(text)

            # 基本メタデータを準備
            metadata = {
                "chat_id": message.chat_id,
                "content": text,
                "created_at": message.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "memory_type": memory_store.TYPE_MESSAGE,
                "message_id": str(message.id.value),
                "sender": message.sender_type.value,
                "user_id": message.sender_id,
            }

            # ベクトルストアに保存
            memory_id = memory_store.add_memory(
                vector=vector, metadata=metadata, user_id=message.sender_id, collection_name=self.memory_store.CHAT_MEMORY_COLLECTION_NAME
            )
            logger.info(f"メッセージID {message.id.value} をベクトル化して保存 (memory_id: {memory_id})")

        except ValueError as ve:
            logger.warning(f"メッセージベクトル化中に値エラー: {str(ve)}")  # 空テキストなどの場合
        except Exception as e:
            logger.error(f"メッセージベクトル化中にエラーが発生: {str(e)}", exc_info=True)

    def summarize_chat(self, chat_id: str, user_id: str, message_count: int) -> None:
        """チャットの要約を同期的に生成（条件を満たす場合）."""
        # メッセージ数が閾値の倍数に達した場合に要約を実行
        threshold = self.config.memory_summarize_threshold
        if message_count > 0 and message_count % threshold == 0:
            self.summarize_and_vectorize_background(
                chat_id=chat_id,
                user_id=user_id,
                memory_store=self.memory_store,
                config=self.config,
            )

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
        chat_memories = self.search_relevant_memories(user_id=user_id, chat_id=chat_id, query=user_query)

        # プロンプトを構築
        return self.create_memory_prompt(
            buffer=buffer,
            chat_memories=chat_memories,
            user_query=user_query,
            config=self.config,
        )

    def estimate_tokens(self, text: str) -> int:
        """テキストのトークン数を推定."""
        if TIKTOKEN_ENCODING:
            return len(TIKTOKEN_ENCODING.encode(text))
        # フォールバック: 簡易的なトークン数推定
        return len(text) // 4

    def format_memory_item(self, memory: dict[str, Any], prefix: str = "") -> str:
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

    def truncate_text_to_tokens(self, text: str, max_tokens: int) -> str:
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

    def create_memory_prompt(
        self,
        buffer: list[Message],
        chat_memories: list[dict[str, Any]],
        user_query: str,
        config: AppConfig | None = None,
    ) -> str:
        if config is None:
            config = AppConfig.get_config()

        system_prompt = (
            "ユーザーのプロファイル情報や過去の会話、最近のチャット履歴を考慮して、質問に回答してください。"
            "提供された情報を活用しながら、一貫性のあるパーソナライズされた応答を心がけてください。"
        )

        prompt_parts = [system_prompt]

        if chat_memories:
            memory_items = [
                self.format_memory_item(
                    mem,
                    f"[過去の{'メッセージ' if mem.get('type') == 'message' else '要約'} by "
                    f"{'ユーザー' if mem.get('sender') == 'user' else 'AI' if mem.get('sender') == 'assistant' else 'システム'}]: ",
                )
                for mem in chat_memories
            ]
            prompt_parts.append("\n--- 関連する過去の会話 ---\n" + "\n".join(memory_items))

        if buffer:
            history_items = [
                f"{'ユーザー' if msg.sender_type.value == 'user' else 'AI'}: {msg.content.value}" for msg in reversed(buffer) if not msg.is_deleted
            ]
            prompt_parts.append("\n--- 最近のチャット履歴 (古い順) ---\n" + "\n".join(history_items))

        prompt_parts.append(f"\nユーザー: {user_query}\nAI:")

        full_prompt = "\n".join(prompt_parts)
        estimated_tokens = self.estimate_tokens(full_prompt)
        max_tokens = config.max_prompt_tokens or 8192

        if estimated_tokens > max_tokens:
            # システムプロンプトとクエリ部分は必ず残す
            required = prompt_parts[0] + prompt_parts[-1]
            remain_tokens = max_tokens - self.estimate_tokens(required)
            # 履歴・記憶部分を均等に切り詰め
            middle_parts = prompt_parts[1:-1]
            if middle_parts:
                per_part = max(remain_tokens // len(middle_parts), 1)
                truncated = [self.truncate_text_to_tokens(p, per_part) for p in middle_parts]
                full_prompt = prompt_parts[0] + "\n" + "\n".join(truncated) + prompt_parts[-1]

        return full_prompt

    def summarize_and_vectorize_background(
        self, chat_id: str, user_id: str, memory_store: MemoryVectorStore, config: AppConfig | None = None
    ) -> None:
        """チャットメッセージを要約してベクトル化する非同期タスク."""
        if config is None:
            config = AppConfig.get_config()

        try:
            # 要約されていないメッセージを取得（効率化）
            unsummarized_messages = memory_store.get_unsummarized_messages(
                user_id=user_id, chat_id=chat_id, max_count=config.memory_summarize_threshold
            )

            # 要約すべきメッセージがない場合は終了
            if len(unsummarized_messages) < config.memory_summarize_threshold // 2:  # 半分以下なら要約しない
                return

            # メッセージを時系列順にソート（get_unsummarized_messagesですでにソート済みだが念のため）
            unsummarized_messages.sort(key=lambda msg: msg.get("created_at", ""))

            # 要約するメッセージの内容を結合
            message_texts = []
            message_ids = []

            for msg in unsummarized_messages:
                sender = msg.get("sender", "unknown")
                content = msg.get("content", "")
                message_id = msg.get("message_id", "")

                # 日本語に変換
                sender_ja = "ユーザー" if sender == "user" else "AI" if sender == "assistant" else "システム"

                message_texts.append(f"{sender_ja}: {content}")
                if message_id:
                    message_ids.append(message_id)

            # 要約するメッセージがない場合は終了
            if not message_texts:
                return

            combined_text = "\n".join(message_texts)

            # LLMを使って要約を生成
            summary = self.get_llm_summary(combined_text)

            if not summary:
                logger.error("要約生成に失敗しました")
                return

            # 要約テキストをベクトル化
            vector = memory_store.encode_text(summary)

            # 要約メタデータを準備
            timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")  # RFC3339フォーマットに変換
            summary_id = f"summary_{chat_id}_{timestamp}"

            metadata = {
                "chat_id": chat_id,
                "content": summary,
                "created_at": timestamp,
                "memory_type": memory_store.TYPE_SUMMARY,
                "message_id": summary_id,
                "sender": "system",
                "user_id": user_id,
            }

            # ベクトルストアに保存
            memory_store.add_memory(vector=vector, metadata=metadata, user_id=user_id, collection_name=self.memory_store.CHAT_MEMORY_COLLECTION_NAME)

            # 要約済みフラグを更新
            if message_ids:
                memory_store.mark_messages_as_summarized(user_id=user_id, chat_id=chat_id, message_ids=message_ids)

        except Exception as e:
            logger.error(f"チャット要約中にエラーが発生: {str(e)}", exc_info=True)

    def get_llm_summary(self, text_to_summarize: str) -> str | None:
        """LLMを使用して要約を取得する."""
        try:
            # より詳細なプロンプトを使用して要約品質を向上
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """あなたは高品質な要約を生成するAIアシスタントです。

    以下の会話を要約してください。以下のガイドラインに従ってください：

    1. 重要な情報、話題、キーポイントを保持しつつ、簡潔にまとめてください。
    2. 要約は300文字以内に収めてください。
    3. 時系列順に話の流れがわかるように要約してください。
    4. ユーザーの質問と、その回答の要点を含めてください。
    5. 検索で再利用できるよう、重要なキーワードや専門用語を保持してください。
    6. 箇条書きではなく、流れるような文章で要約してください。

    要約の形式例：
    「ユーザーは〇〇について質問し、AIは△△と回答した。その後、◇◇について議論し、□□という結論に至った。」""",
                    ),
                    ("human", "{text}"),
                ]
            )

            summary_chain = prompt | ChatOpenAI(model_name="gpt-4o") | StrOutputParser()

            return summary_chain.invoke({"text": text_to_summarize})
        except Exception as e:
            logger.error(f"要約生成中にエラー発生: {str(e)}", exc_info=True)
            return None

    def add_book_annotations(self, book: Book, annotations: list[Annotation]):
        # BookDetailの構造に従い、annotationsとname, user_idを取得
        user_id = book.user_id
        book_title = book.name
        for annotation in annotations:
            # ベクトル化するテキスト（ハイライト＋メモ）
            text_for_vector = annotation.text.value
            if annotation.notes:
                text_for_vector += f"\n{annotation.notes.value}"
            vector = self.memory_store.encode_text(text_for_vector)
            metadata: dict[str, Any] = {
                "annotation_id": annotation.id.value,
                "book_id": book.id.value,
                "book_title": book_title.value,
                "content": annotation.text.value,
                "created_at": annotation.created_at if hasattr(annotation, "created_at") else None,
                "notes": annotation.notes.value if annotation.notes else None,
                "user_id": user_id,
            }
            self.memory_store.add_memory(
                vector=vector, metadata=metadata, user_id=user_id, collection_name=self.memory_store.BOOK_ANNOTATION_COLLECTION_NAME
            )

    def delete_book_annotation(self, user_id: str, annotation_id: str) -> None:
        """ブックのアノテーションを削除."""
        self.memory_store.delete_memory(
            user_id=user_id, collection_name=self.memory_store.BOOK_ANNOTATION_COLLECTION_NAME, target="annotation_id", key=annotation_id
        )

    def update_book_annotations(self, book: Book, annotations: list[Annotation]) -> None:
        """ブックのアノテーションを更新."""
        user_id = book.user_id
        book_title = book.name
        for annotation in annotations:
            # ベクトル化するテキスト（ハイライト＋メモ）
            text_for_vector = annotation.text.value
            if annotation.notes:
                text_for_vector += f"\n{annotation.notes.value}"
            vector = self.memory_store.encode_text(text_for_vector)
            metadata: dict[str, Any] = {
                "annotation_id": annotation.id.value,
                "book_id": book.id.value,
                "book_title": book_title.value,
                "content": annotation.text.value,
                "created_at": annotation.created_at if hasattr(annotation, "created_at") else None,
                "notes": annotation.notes.value if annotation.notes else None,
                "user_id": user_id,
            }
            self.memory_store.update_memory(
                user_id=user_id,
                collection_name=self.memory_store.BOOK_ANNOTATION_COLLECTION_NAME,
                target="annotation_id",
                key=annotation.id.value,
                properties=metadata,
                vector=vector,
            )

    def delete_book_memories(self, user_id: str, book_id: str) -> None:
        """本に関連するすべての記憶を削除.

        Args:
            user_id: ユーザーID
            book_id: 削除する本のID

        """
        try:
            self.memory_store.delete_book_data(user_id, book_id)
            logger.info(f"Book {book_id} memories deleted for user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting book memories: {str(e)}")
            # エラーを再スローしない（本の削除処理を継続）
