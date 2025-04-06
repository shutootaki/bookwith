from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import setup_routes

# FastAPIアプリケーションの作成
app = FastAPI(title="BookWith API", description="Book related API service")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では特定のオリジンに制限すべき
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルートのセットアップ
setup_routes(app)
