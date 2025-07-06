"""ハイライト検索サービス."""

from src.infrastructure.memory.memory_vector_store import MemoryVectorStore


class HighlightSearcher:
    """書籍のハイライト（アノテーション）検索を行うサービス."""

    def __init__(self) -> None:
        """ハイライト検索サービスの初期化."""
        self.memory_vector_store = MemoryVectorStore()

    def search_relevant_highlights(self, question: str, user_id: str, book_id: str, limit: int = 3) -> str:
        """質問に関連するハイライトテキストを検索し、引用情報付きで返す."""
        if not (user_id and book_id):
            return "No highlights found"

        # 質問をベクトル化
        query_vector = self.memory_vector_store.encode_text(question)

        # ハイライトを検索
        highlights = self.memory_vector_store.search_highlights(user_id=user_id, book_id=book_id, query_vector=query_vector, limit=limit)

        if not highlights:
            return "No highlights found"

        # ハイライトテキストを整形（引用番号付き）
        highlight_parts = []
        citation_info = []

        for idx, h in enumerate(highlights):
            highlight_text = h["content"]
            if h.get("notes"):
                highlight_text += f"\n【メモ】{h['notes']}"

            # 引用番号を付けてハイライトを追加
            highlight_parts.append(f"【ハイライト{idx + 1}】 {highlight_text}")

            # 引用情報を収集（CFIまたはspine情報を使用）
            cfi = h.get("cfi", "")
            spine_info = h.get("spine", {})

            # ハイライト用の記号（★）
            if spine_info and isinstance(spine_info, dict):
                chapter = spine_info.get("title", "不明な章")
                citation_info.append(f"★{idx + 1} {chapter}（ハイライト箇所）")
            elif cfi:
                citation_info.append(f"★{idx + 1} 位置情報: CFI {cfi}（ハイライト箇所）")
            else:
                citation_info.append(f"★{idx + 1} 位置情報なし（ハイライト箇所）")

        # ハイライトと引用情報を結合
        formatted_highlights = "\n\n".join(highlight_parts)
        citations = "\n".join(citation_info)

        return f"{formatted_highlights}\n\n【ハイライト引用情報】\n{citations}"
