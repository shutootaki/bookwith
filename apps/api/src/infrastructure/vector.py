import weaviate
from langchain_openai import OpenAIEmbeddings
from langchain_weaviate.vectorstores import WeaviateVectorStore


def get_vector_store(index_name: str) -> WeaviateVectorStore:
    """特定のインデックス名に基づいてベクトルストアを取得します.
    インデックスが存在しない場合はNoneを返します.

    Args:
        index_name: Weaviateのインデックス名

    Returns:
        WeaviateVectorStoreインスタンス、または存在しない場合はNone

    """
    # インデックス（コレクション）が存在するか確認
    try:
        # 既存のインデックスに接続するWeaviateVectorStoreを作成
        return WeaviateVectorStore(
            client=weaviate.connect_to_local(),
            text_key="content",
            index_name=index_name,
            embedding=OpenAIEmbeddings(
                model="text-embedding-3-small",
                max_retries=2,
            ),
        )
    except Exception as e:
        # エラーが発生した場合はログに記録し、Noneを返す
        print(f"ベクトルストアの取得中にエラーが発生しました: {str(e)}")
        raise e
