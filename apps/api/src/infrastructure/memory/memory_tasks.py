import logging
from datetime import datetime

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.app_config import AppConfig
from src.domain.message.entities.message import Message
from src.domain.message.repositories.message_repository import MessageRepository
from src.infrastructure.memory.memory_vector_store import MemoryVectorStore

# ロガーの設定
logger = logging.getLogger(__name__)


def vectorize_text_background(message: Message, memory_store: MemoryVectorStore, config: AppConfig | None = None) -> None:
    """メッセージをベクトル化して保存する非同期タスク.

    Args:
        message: ベクトル化するメッセージ
        memory_store: 記憶ベクトルストア
        config: アプリケーション設定（Noneの場合は初期化される）

    """
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
            "created_at": message.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),  # RFC3339フォーマットに変換
            "token_count": len(text.split()),  # 簡易的なトークンカウント
            "is_summarized": False,  # 初期状態では要約されていない
        }

        # ベクトルストアに保存
        memory_id = memory_store.add_memory(vector=vector, metadata=metadata)
        print(f"メッセージID {message.id.value} をベクトル化して保存 (memory_id: {memory_id})")

        # ユーザーが送信したメッセージの場合、プロファイル情報を抽出
        if message.sender_type.value == "user":
            for keyword in config.memory_profile_keywords:
                if keyword in text:
                    # プロファイル情報としても保存
                    profile_metadata = metadata.copy()
                    profile_metadata["type"] = memory_store.TYPE_USER_PROFILE
                    profile_metadata["chat_id"] = None  # プロファイル情報はチャットに紐づかない
                    profile_id = memory_store.add_memory(vector=vector, metadata=profile_metadata)
                    print(f"ユーザープロファイル情報として保存 (memory_id: {profile_id})")
                    break  # 一度でもキーワードが見つかればプロファイル情報として扱う

    except Exception as e:
        logger.error(f"メッセージベクトル化中にエラーが発生: {str(e)}", exc_info=True)


def summarize_and_vectorize_background(
    chat_id: str, user_id: str, message_repository: MessageRepository, memory_store: MemoryVectorStore, config: AppConfig | None = None
) -> None:
    """チャットメッセージを要約してベクトル化する非同期タスク.

    Args:
        chat_id: 要約対象のチャットID
        user_id: ユーザーID
        message_repository: メッセージリポジトリ
        memory_store: 記憶ベクトルストア
        config: アプリケーション設定（Noneの場合は初期化される）

    """
    if config is None:
        config = AppConfig.get_config()

    try:
        # 要約されていないメッセージを取得（効率化）
        unsummarized_messages = memory_store.get_unsummarized_messages(user_id=user_id, chat_id=chat_id, max_count=config.memory_summarize_threshold)

        # 要約すべきメッセージがない場合は終了
        if len(unsummarized_messages) < config.memory_summarize_threshold // 2:  # 半分以下なら要約しない
            print(f"要約すべきメッセージが不足しています（{len(unsummarized_messages)}件）")
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
            print("要約するメッセージが見つかりませんでした")
            return

        combined_text = "\n".join(message_texts)

        # LLMを使って要約を生成
        print(f"チャットID {chat_id} の要約を生成開始 ({len(message_texts)}件のメッセージ)")
        summary = get_llm_summary(combined_text)

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
        summary_memory_id = memory_store.add_memory(vector=vector, metadata=metadata)
        print(f"チャットID {chat_id} の要約を生成・保存しました (memory_id: {summary_memory_id})")

        # 要約済みフラグを更新
        if message_ids:
            memory_store.mark_messages_as_summarized(user_id=user_id, chat_id=chat_id, message_ids=message_ids)
            print(f"{len(message_ids)}件のメッセージを要約済みとしてマークしました")

    except Exception as e:
        logger.error(f"チャット要約中にエラーが発生: {str(e)}", exc_info=True)


def get_llm_summary(text_to_summarize: str) -> str | None:
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

        summary_chain = prompt | ChatOpenAI(model_name="gpt-4o-mini") | StrOutputParser()
        summary = summary_chain.invoke({"text": text_to_summarize})

        print(f"要約生成完了: {len(summary)}文字")
        return summary
    except Exception as e:
        logger.error(f"要約生成中にエラー発生: {str(e)}", exc_info=True)
        return None


def process_batch_summarization(
    user_id: str, message_repository: MessageRepository, memory_store: MemoryVectorStore, config: AppConfig | None = None
) -> None:
    """バッチ処理で複数チャットの要約を生成する.

    Args:
        user_id: ユーザーID
        message_repository: メッセージリポジトリ
        memory_store: 記憶ベクトルストア
        config: アプリケーション設定（Noneの場合は初期化される）

    """
    if config is None:
        config = AppConfig.get_config()

    try:
        # ユーザーの全チャットIDを取得
        chat_ids = message_repository.find_chat_ids_by_user_id(user_id)

        for chat_id in chat_ids:
            # 各チャットの要約を生成
            summarize_and_vectorize_background(
                chat_id=chat_id,
                user_id=user_id,
                message_repository=message_repository,
                memory_store=memory_store,
                config=config,
            )

        print(f"ユーザー {user_id} の {len(chat_ids)} チャットのバッチ要約処理が完了しました")
    except Exception as e:
        logger.error(f"バッチ要約処理中にエラーが発生: {str(e)}", exc_info=True)
