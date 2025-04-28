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

    def search_relevant_memories(
        self, user_id: str, chat_id: str, query: str, chat_limit: int | None = None, profile_limit: int | None = None
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """ユーザークエリに関連する記憶を検索.

        Args:
            user_id: ユーザーID
            chat_id: チャットID
            query: ユーザーの質問/クエリ
            chat_limit: 取得するチャット記憶の数
            profile_limit: 取得するプロファイル記憶の数

        Returns:
            (チャット記憶リスト, ユーザープロファイル記憶リスト)のタプル

        """
        # デフォルト値設定
        if chat_limit is None:
            chat_limit = self.config.memory_chat_results
        if profile_limit is None:
            profile_limit = self.config.memory_profile_results

        try:
            # クエリをベクトル化
            query_vector = self.memory_store.encode_text(query)

            # チャット記憶を検索
            chat_memories = self.memory_store.search_chat_memories(user_id=user_id, chat_id=chat_id, query_vector=query_vector, limit=chat_limit)

            # ユーザープロファイル記憶を検索
            user_profile_memories = self.memory_store.search_user_profile(user_id=user_id, query_vector=query_vector, limit=profile_limit)

            return chat_memories, user_profile_memories
        except Exception as e:
            logger.error(f"記憶検索中にエラーが発生: {str(e)}", exc_info=True)
            return [], []  # エラー時は空リストを返す

    def vectorize_message(self, message: Message) -> None:
        """メッセージを同期的にベクトル化.

        Args:
            message: ベクトル化するメッセージ

        """
        self.vectorize_text_background(message=message, memory_store=self.memory_store, config=self.config)
        logger.debug(f"メッセージID {message.id.value} のベクトル化を実行")

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
        chat_memories, user_profile_memories = self.search_relevant_memories(user_id=user_id, chat_id=chat_id, query=user_query)

        # プロンプトを構築
        return self.create_memory_prompt(
            buffer=buffer,
            chat_memories=chat_memories,
            user_profile_memories=user_profile_memories,
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

    def create_memory_prompt(  # noqa: C901
        self,
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
        system_prompt = """ユーザーのプロファイル情報や過去の会話、最近のチャット履歴を考慮して、質問に回答してください。
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
                profile_items.append(self.format_memory_item(mem, "[ユーザープロファイル]: "))

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
                memory_items.append(self.format_memory_item(mem, prefix))

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
        estimated_tokens = self.estimate_tokens(full_prompt)
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

            required_tokens = self.estimate_tokens(system_part + query_part)
            remaining_tokens = max_tokens - required_tokens

            # 残りのパーツを配分（優先度付け）
            other_parts = prompt_parts[1:-2]  # システムプロンプトとクエリ部分を除く

            if other_parts:
                # 均等に配分する単純な方法
                tokens_per_part = remaining_tokens // len(other_parts)
                truncated_parts = []

                for part in other_parts:
                    truncated_parts.append(self.truncate_text_to_tokens(part, tokens_per_part))

                # 再構築
                full_prompt = system_part + "\n" + "\n".join(truncated_parts) + query_part

        return full_prompt

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
                "content": text,
                "type": memory_store.TYPE_MESSAGE,
                "user_id": message.sender_id,
                "chat_id": message.chat_id,
                "message_id": str(message.id.value),
                "sender": message.sender_type.value,
                "created_at": message.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "token_count": len(text.split()),
                # "is_summarized" は add_memory 内でデフォルト設定される
            }

            # ベクトルストアに保存
            memory_id = memory_store.add_memory(vector=vector, metadata=metadata)
            logger.info(f"メッセージID {message.id.value} をベクトル化して保存 (memory_id: {memory_id})")

        except ValueError as ve:
            logger.warning(f"メッセージベクトル化中に値エラー: {str(ve)}")  # 空テキストなどの場合
        except Exception as e:
            logger.error(f"メッセージベクトル化中にエラーが発生: {str(e)}", exc_info=True)

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
                "content": summary,
                "type": memory_store.TYPE_SUMMARY,
                "user_id": user_id,
                "chat_id": chat_id,
                "message_id": summary_id,
                "sender": "system",
                "created_at": timestamp,
                "token_count": len(summary.split()),  # 簡易的なトークンカウント
            }

            # ベクトルストアに保存
            memory_store.add_memory(vector=vector, metadata=metadata)

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

    def add_highlights_to_vector_store(self, book: Book, annotations: list[Annotation]):
        # BookDetailの構造に従い、annotationsとname, user_idを取得
        user_id = book.user_id
        book_title = book.name
        for annotation in annotations:
            # ベクトル化するテキスト（ハイライト＋メモ）
            text_for_vector = annotation.text.value
            if annotation.notes:
                text_for_vector += f"\n{annotation.notes.value}"
            vector = self.memory_store.encode_text(text_for_vector)
            metadata = {
                "type": self.memory_store.TYPE_HIGHLIGHT,
                "content": annotation.text.value,
                "user_id": user_id,
                "book_id": book.id.value,
                "book_title": book_title.value,
                "notes": annotation.notes.value if annotation.notes else None,
                "created_at": annotation.created_at if hasattr(annotation, "created_at") else None,
                "annotation_id": annotation.id.value,
            }
            self.memory_store.add_memory(vector, metadata)
