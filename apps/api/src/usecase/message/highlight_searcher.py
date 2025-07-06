"""ハイライト検索サービス."""

from src.infrastructure.memory.memory_vector_store import MemoryVectorStore


class HighlightSearcher:
    """書籍のハイライト（アノテーション）検索を行うサービス."""

    def __init__(self) -> None:
        """ハイライト検索サービスの初期化."""
        self.memory_vector_store = MemoryVectorStore()

    def search_relevant_highlights(self, question: str, user_id: str, book_id: str, limit: int = 3) -> list[str]:
        """質問に関連するハイライトテキストを検索する."""
        if not (user_id and book_id):
            return ["No highlights found"]

        # 質問をベクトル化
        query_vector = self.memory_vector_store.encode_text(question)

        # ハイライトを検索
        highlights = self.memory_vector_store.search_highlights(user_id=user_id, book_id=book_id, query_vector=query_vector, limit=limit)

        if not highlights:
            return ["No highlights found"]

        # ハイライトテキストを整形
        highlight_texts = []
        for h in highlights:
            highlight_text = h["content"]
            if h.get("notes"):
                highlight_text += f"\n{h['notes']}"
            highlight_texts.append(f"【ハイライト】{highlight_text}")

        return highlight_texts
