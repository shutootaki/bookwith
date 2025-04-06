import json
import shutil
from pathlib import Path
from typing import Any, List, Optional

from fastapi import Cookie, FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from langchain_community.document_loaders import UnstructuredEPubLoader
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableSerializable
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel
from src.prompts import rag_prompt
from src.utils import TOKEN_MAPPING, get_dropbox_client
from src.vector import get_shared_vector_store, set_shared_vector_store

app = FastAPI(title="BookWith API", description="Book related API service")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では特定のオリジンに制限すべき
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 共有ベクトルストアを保持するグローバル変数
shared_vector_store: Optional[InMemoryVectorStore] = None


# モデル定義
class Question(BaseModel):
    question: str


class Answer(BaseModel):
    answer: str


class TokenResponse(BaseModel):
    access_token: str
    access_token_expires_at: Optional[int] = None


@app.get("/")
async def root():
    return {"message": "BookWith FastAPI Server"}


# ドキュメントをフォーマット
def format_documents_as_string(documents: List[Document]) -> str:
    return "\n\n".join([doc.page_content for doc in documents])


# LLM APIエンドポイント
@app.post("/llm", response_model=Answer)
async def process_llm(question: Question):
    print("Received question:", question.question)
    try:
        # ベクトルストアを取得
        vector_store = get_shared_vector_store()
        if not vector_store:
            raise HTTPException(
                status_code=500,
                detail="Vector store is not initialized. Please upload a document via the /rag endpoint first.",
            )

        # リトリーバーを使って関連ドキュメントを取得
        vector_store_retriever = vector_store.as_retriever()

        # OpenAIモデルの設定
        model = ChatOpenAI(model="gpt-4o-mini")

        # チェーンの構築
        chain: RunnableSerializable[Any, str] = (
            {
                "context": vector_store_retriever | format_documents_as_string,
                "question": RunnablePassthrough(),
            }
            | rag_prompt
            | model
            | StrOutputParser()
        )

        # 質問を処理
        answer = chain.invoke(question.question)

        return Answer(answer=answer)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# RAG APIエンドポイント (ファイルアップロード)
@app.post("/rag")
async def process_rag(file: UploadFile = File(...)):
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
            "vector_store_status": True,
        }

    except Exception as e:
        print("Error during RAG processing:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# Dropboxコールバック処理
@app.get("/callback/{provider}")
async def callback(provider: str, state: str, code: str, response: Response):
    if provider != "dropbox":
        raise HTTPException(status_code=400, detail="Unsupported provider")

    try:
        state_data = json.loads(state)
        redirect_uri = state_data.get("redirectUri")

        # Dropboxクライアント取得
        dbx = get_dropbox_client()

        # アクセストークン取得
        token_result = dbx.auth.get_access_token_from_code(redirect_uri, code)

        # リフレッシュトークンをクッキーに設定
        response.set_cookie(
            key=TOKEN_MAPPING["dropbox"],
            value=token_result.refresh_token,
            max_age=365 * 24 * 60 * 60,
            secure=True,
            httponly=True,
            samesite="lax",
        )

        # 成功ページへリダイレクト
        return RedirectResponse(url="/success")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")


# リフレッシュトークン処理
@app.get("/refresh", response_model=TokenResponse)
async def refresh(dropbox_refresh_token: str = Cookie(None)):
    if not dropbox_refresh_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # Dropboxクライアント取得
        dbx = get_dropbox_client()

        # リフレッシュトークン設定
        dbx.auth.set_refresh_token(dropbox_refresh_token)

        # アクセストークンを更新
        dbx.auth.refresh_access_token()

        return TokenResponse(
            access_token=dbx.auth.get_access_token(),
            access_token_expires_at=dbx.auth.get_access_token_expires_at(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh error: {str(e)}")
