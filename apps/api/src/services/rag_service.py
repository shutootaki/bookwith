import shutil
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

    Returns:
        処理結果を含む辞書
    """
    try:
        # 一時ファイルを作成
        temp_dir = Path("tmp")
        temp_dir.mkdir(exist_ok=True)

        if file.filename is None:
            file_name = "uploaded_file.epub"
        else:
            file_name = file.filename

        file_path = temp_dir / file_name

        # アップロードされたファイルを保存
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # EPubローダーでドキュメントを読み込み
        docs = UnstructuredEPubLoader(file_path).load()

        # テキスト分割
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_docs = splitter.split_documents(docs)

        # 埋め込みとベクトルストアの作成
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            max_retries=2,
        )

        tenant_id = f"{user_id}_{book_id}"

        # Weaviateベクトルストアを作成（テナントIDを指定）
        WeaviateVectorStore.from_documents(
            documents=split_docs,
            embedding=embeddings,
            client=weaviate.connect_to_local(),
            index_name="BookContentIndex",
            text_key="content",
            tenant=tenant_id,  # テナントを指定
        )

        # 一時ファイルを削除
        file_path.unlink(missing_ok=True)

        return {
            "message": "アップロードと処理が正常に完了しました",
            "file_name": file_name,
            "chunk_count": len(split_docs),
            "index_name": "BookContentIndex",
            "tenant_id": tenant_id,
            "success": True,
        }

    except Exception as e:
        # エラーを発生元に伝播させる
        raise ValueError(f"RAG処理中にエラーが発生しました: {str(e)}")
