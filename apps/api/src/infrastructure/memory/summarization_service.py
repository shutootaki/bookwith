"""要約生成サービス."""

import logging
from datetime import datetime

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.app_config import AppConfig
from src.infrastructure.memory.memory_vector_store import MemoryVectorStore

logger = logging.getLogger(__name__)


class SummarizationService:
    """チャット要約に特化したサービス."""

    def __init__(self, memory_store: MemoryVectorStore | None = None) -> None:
        """要約サービスの初期化."""
        self.config = AppConfig.get_config()
        self.memory_store = memory_store or MemoryVectorStore()
        self.memory_summarize_threshold = 20

    def summarize_chat(self, chat_id: str, user_id: str, message_count: int) -> None:
        """チャットの要約を同期的に生成（条件を満たす場合）."""
        # メッセージ数が閾値の倍数に達した場合に要約を実行
        if message_count > 0 and message_count % self.memory_summarize_threshold == 0:
            self._summarize_and_vectorize_background(chat_id=chat_id, user_id=user_id)

    def _summarize_and_vectorize_background(self, chat_id: str, user_id: str) -> None:
        """チャットメッセージを要約してベクトル化する処理."""
        try:
            # 要約されていないメッセージを取得
            unsummarized_messages = self.memory_store.get_unsummarized_messages(
                user_id=user_id, chat_id=chat_id, max_count=self.memory_summarize_threshold
            )

            # 要約すべきメッセージがない場合は終了
            if len(unsummarized_messages) < self.memory_summarize_threshold // 2:
                return

            # メッセージを時系列順にソート
            unsummarized_messages.sort(key=lambda msg: msg.get("created_at", ""))

            # 要約するメッセージの内容を結合
            message_texts = []
            message_ids = []

            for msg in unsummarized_messages:
                sender = msg.get("sender", "unknown")
                content = msg.get("content", "")
                message_id = msg.get("message_id", "")

                # 日本語に変換
                sender_ja = self._convert_sender_to_japanese(sender)
                message_texts.append(f"{sender_ja}: {content}")

                if message_id:
                    message_ids.append(message_id)

            # 要約するメッセージがない場合は終了
            if not message_texts:
                return

            combined_text = "\n".join(message_texts)

            # LLMを使って要約を生成
            summary = self._get_llm_summary(combined_text)

            if not summary:
                logger.error("要約生成に失敗しました")
                return

            # 要約テキストをベクトル化して保存
            self._save_summary_to_vector_store(summary, chat_id, user_id)

            # 要約済みフラグを更新
            if message_ids:
                self.memory_store.mark_messages_as_summarized(user_id=user_id, chat_id=chat_id, message_ids=message_ids)

        except Exception as e:
            logger.error(f"チャット要約中にエラーが発生: {str(e)}", exc_info=True)

    def _convert_sender_to_japanese(self, sender: str) -> str:
        """送信者を日本語に変換."""
        if sender == "user":
            return "ユーザー"
        if sender == "assistant":
            return "AI"
        return "システム"

    def _save_summary_to_vector_store(self, summary: str, chat_id: str, user_id: str) -> None:
        """要約をベクトル化してストアに保存."""
        # 要約テキストをベクトル化
        vector = self.memory_store.encode_text(summary)

        # 要約メタデータを準備
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        summary_id = f"summary_{chat_id}_{timestamp}"

        metadata = {
            "chat_id": chat_id,
            "content": summary,
            "created_at": timestamp,
            "memory_type": self.memory_store.TYPE_SUMMARY,
            "message_id": summary_id,
            "sender": "system",
            "user_id": user_id,
        }

        # ベクトルストアに保存
        self.memory_store.add_memory(vector=vector, metadata=metadata, user_id=user_id, collection_name=self.memory_store.CHAT_MEMORY_COLLECTION_NAME)

    def _get_llm_summary(self, text_to_summarize: str) -> str | None:
        """LLMを使用して要約を取得する."""
        try:
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
