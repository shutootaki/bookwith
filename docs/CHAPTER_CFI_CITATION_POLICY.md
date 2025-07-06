# 書籍引用時に章番号／CFI を提示するための実装方針

## 目的

LLM が EPUB 由来の内容を回答に引用する際、出典を **章番号** または **CFI (Canonical Fragment Identifier)** で明示し、ユーザーが情報源を容易に特定できるようにする。

---

## 全体アーキテクチャへの影響

1. **インジェスト (`apps/api/src/infrastructure/memory/book_content_store.py`)**
   - EPUB 解析時に以下のメタデータを各チャンクへ付与してベクトル化する。
     | キー | 型 | 説明 |
     |------|----|------|
     | `chapter_index` | int | 1,2,3 … の章番号 |
     | `chapter_title` | str | 章タイトル |
     | `cfi` | str | `epubcfi(/6/2[item]!...)` 形式 |
2. **検索／RAG (`apps/api/src/usecase/message/ai_response_generator.py`)**
   - `_format_documents_as_string()` を改修し、チャンクを
     ```text
     【{idx}】(章:{chapter_index}, CFI:{cfi})\n{page_content}
     ```
     の形でフォーマットする。
3. **プロンプト**
   - `ChatPromptTemplate` の system メッセージに下記ルールを追記。
     > 書籍から引用する場合は、回答内で “【n】” を用いて出典を示し、必要に応じて章番号または CFI を括弧内に付記してください。
4. **回答生成**
   - LLM にはフォーマット済みコンテキストが渡るため、回答中に自動で `【1】` 等の出典ラベルを付けさせることができる。

---

## 実装ステップ

### 1. EPUB 解析拡張

```python
# 既存ロジックの一部イメージ
chapter_idx = 0
for spine_idx, item in enumerate(book.spine):
    chapter_idx += 1
    cfi = f"/6/{spine_idx}[{item.id}]"
    title = item.get_title()
    text = extract_text(item)  # ユーティリティ関数
    split_docs = splitter.split_text(text)
    for d in split_docs:
        d.metadata.update({
            "book_id": book_id,
            "chapter_index": chapter_idx,
            "chapter_title": title,
            "cfi": cfi,
        })
```

### 2. フォーマッタ改修

```python
def _format_documents_as_string(self, documents: list[Document]) -> str:
    formatted = []
    for i, doc in enumerate(documents, 1):
        ci = doc.metadata.get("chapter_index")
        cfi = doc.metadata.get("cfi")
        formatted.append(f"【{i}】(章:{ci}, CFI:{cfi})\n{doc.page_content}")
    return "\n\n".join(formatted)
```

### 3. プロンプト追記

```
…書籍の情報を引用する場合は、回答中に【番号】を付し、
例:「…とされています【1】(章:3)」または「…【2】(CFI:/6/4[chap4])」
```

### 4. テスト

1. 任意の EPUB をアップロードし、`Weaviate` に `chapter_index`/`cfi` が格納されていることを確認。
2. `pnpm test` に以下を追加。
   - 質問 → レスポンスに `【数字】` が含まれること。
   - 章番号／CFI が表示されていること。

---

## 既存コードへの変更点概要

- `BookContentStore.create_book_vector_index`
  - EPUB 解析ロジックを差し替え、メタデータ追加。
- `AIResponseGenerator._format_documents_as_string`
  - 新しいフォーマット関数へ置換。
- プロンプト定義
  - 出典表記の指針文を追記。

---

## 移行プラン

1. 既存 EPUB を再インジェストするバッチを用意し、新メタデータを付与した状態で再ベクトル化。
2. ベクトルストア再構築完了後、本番環境の RAG 生成チェーンを新ロジックに切替える。
