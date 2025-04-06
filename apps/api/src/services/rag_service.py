import tempfile
from pathlib import Path

import weaviate
from fastapi import UploadFile
from langchain_community.document_loaders import UnstructuredEPubLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_weaviate.vectorstores import WeaviateVectorStore


async def process_epub_file(file: UploadFile, user_id: str, book_id: str) -> dict:
    """
    EPUBファイルを処理しベクトルストアを設定するサービス関数

    Args:
        file: アップロードされたEPUBファイル
        user_id: ユーザーID（テナントを分離するために使用）
        book_id: 書籍ID

    Returns:
        処理結果を含む辞書
    """
    try:
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as temp_file:
            # ファイルの内容を一度に読み込み、ディスクI/Oを最小化
            file_content = await file.read()
            temp_file.write(file_content)
            temp_path = temp_file.name

        try:
            # EPubローダーでドキュメントを読み込み
            docs = UnstructuredEPubLoader(temp_path).load()

            # テキスト分割
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200
            )
            split_docs = splitter.split_documents(docs)

            tenant_id = f"{user_id}_{book_id}"

            # Weaviateベクトルストアを作成（テナントIDを指定）
            WeaviateVectorStore.from_documents(
                documents=split_docs,
                embedding=OpenAIEmbeddings(
                    model="text-embedding-3-large",
                    max_retries=2,
                ),
                client=weaviate.connect_to_local(),
                index_name="BookContentIndex",
                text_key="content",
                tenant=tenant_id,  # テナントを指定
            )

            return {
                "message": "アップロードと処理が正常に完了しました",
                "file_name": file.filename,
                "chunk_count": len(split_docs),
                "index_name": "BookContentIndex",
                "tenant_id": tenant_id,
                "success": True,
            }
        finally:
            # 処理が終わったら必ず一時ファイルを削除
            Path(temp_path).unlink(missing_ok=True)

    except Exception as e:
        # エラーを発生元に伝播させる
        raise ValueError(f"RAG処理中にエラーが発生しました: {str(e)}")
