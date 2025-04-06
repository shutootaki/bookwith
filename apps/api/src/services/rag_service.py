import shutil
from pathlib import Path

from fastapi import UploadFile
from langchain_community.document_loaders import UnstructuredEPubLoader
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.vector import set_shared_vector_store


async def process_epub_file(file: UploadFile) -> dict:
    """EPUBファイルを処理しベクトルストアを設定するサービス関数"""
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

        vector_store = InMemoryVectorStore.from_documents(split_docs, embeddings)

        # グローバル変数にベクトルストアを保存
        set_shared_vector_store(vector_store)

        # 一時ファイルを削除
        file_path.unlink(missing_ok=True)

        return {
            "message": "アップロードと処理が正常に完了しました",
            "file_name": file_name,
            "chunk_count": len(split_docs),
            "success": True,
        }

    except Exception as e:
        # エラーを発生元に伝播させる
        raise ValueError(f"RAG処理中にエラーが発生しました: {str(e)}")
