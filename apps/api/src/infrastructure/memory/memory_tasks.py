from datetime import datetime

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.app_config import AppConfig
from src.domain.message.entities.message import Message
from src.domain.message.repositories.message_repository import MessageRepository
from src.infrastructure.memory.memory_vector_store import MemoryVectorStore


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
            "created_at": message.created_at.isoformat(),
            "token_count": len(text.split()),  # 簡易的なトークンカウント
        }

        # ベクトルストアに保存
        memory_store.add_memory(vector=vector, metadata=metadata)

        # ユーザーが送信したメッセージの場合、プロファイル情報を抽出
        if message.sender_type.value == "user":
            for keyword in config.memory_profile_keywords:
                if keyword in text:
                    # プロファイル情報としても保存
                    profile_metadata = metadata.copy()
                    profile_metadata["type"] = memory_store.TYPE_USER_PROFILE
                    profile_metadata["chat_id"] = None  # プロファイル情報はチャットに紐づかない
                    memory_store.add_memory(vector=vector, metadata=profile_metadata)
                    break  # 一度でもキーワードが見つかればプロファイル情報として扱う

    except Exception as e:
        print(f"メッセージベクトル化中にエラーが発生: {str(e)}")


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
        # チャットに関連するメッセージを取得（全件取得して処理）
        messages = message_repository.find_by_chat_id(chat_id)

        # 要約すべきメッセージがない場合は終了
        if len(messages) < config.memory_summarize_threshold:
            return

        # メッセージを時系列順にソート
        messages.sort(key=lambda msg: msg.created_at)

        # 要約するメッセージの内容を結合
        message_texts = []
        for msg in messages:
            if not msg.is_deleted:
                prefix = f"{msg.sender_type.value}: "
                message_texts.append(f"{prefix}{msg.content.value}")

        # 要約するメッセージがない場合は終了
        if not message_texts:
            return

        combined_text = "\n".join(message_texts)

        # LLMを使って要約を生成
        summary = get_llm_summary(combined_text)

        if not summary:
            print("要約生成に失敗しました")
            return

        # 要約テキストをベクトル化
        vector = memory_store.encode_text(summary)

        # 要約メタデータを準備
        timestamp = datetime.now().isoformat()
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

        print(f"チャットID {chat_id} の要約を生成・保存しました")

    except Exception as e:
        print(f"チャット要約中にエラーが発生: {str(e)}")


def get_llm_summary(text_to_summarize: str) -> str | None:
    """LLMを使用して要約を取得する."""
    try:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """以下の会話を要約してください。重要な情報、話題、キーポイントを保持しつつ、簡潔にまとめてください。
要約は200文字以内に収めてください。""",
                ),
                ("human", "{text}"),
            ]
        )

        summary_chain = prompt | ChatOpenAI(model_name="gpt-4o-mini", temperature=0.3) | StrOutputParser()
        summary = summary_chain.invoke({"text": text_to_summarize})

        return summary
    except Exception as e:
        print(f"要約生成中にエラー発生: {str(e)}")
        return None
