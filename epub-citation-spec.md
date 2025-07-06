# ePub引用元情報表示機能 仕様書

## 概要
LLMがePub書籍の内容を参照して回答する際に、参照した箇所の出典情報（章・位置情報）を回答に含める機能。

## 要件

### 1. 表示形式
- **脚注形式**を採用
- 本文中に上付き数字（¹, ²）を挿入
- 回答の末尾に「参照箇所」セクションを設けて詳細を記載

### 2. 引用情報の詳細度

#### Phase 1（MVP）
- **位置情報（％）**を表示
- 例：「¹約25%の位置」
- 書籍全体に対する相対的な位置を示す

#### Phase 2（拡張）
- **章/セクションタイトル**を追加
- 例：「¹第3章: AIの歴史（約25%の位置）」

### 3. インタラクティブ性
- Phase 1では**情報表示のみ**
- 将来的にクリックでジャンプ機能を追加予定

### 4. 複数引用元の扱い
- 同一章/セクションからの複数引用は**統合表示**
- 位置情報は列挙形式で表示

#### 表示例
```
AIの発展は著しく¹、特に2020年以降は急速に進化しています²。
この変化は産業界にも大きな影響を与えています¹。

参照箇所：
¹ 第3章: AIの歴史（約25%、45%の位置）
² 第5章: 最新の動向（約78%の位置）
```

### 5. ハイライトとの連携
- ユーザーがハイライトした箇所を引用する場合は、その情報を優先的に活用
- ハイライト箇所には特別なマーカー（例：★）を付与

## 技術実装方針

### Phase 1: MVP実装

#### 1. VectorStore拡張（バックエンド）
```python
# BookContentStoreでのメタデータ追加
metadata = {
    "book_id": book_id,
    "chunk_index": chunk_index,  # チャンクの順序
    "total_chunks": total_chunks,  # 総チャンク数
    "position_percent": (chunk_index / total_chunks) * 100,  # 位置（％）
    "content_preview": text[:100],  # 内容のプレビュー
}
```

#### 2. AI応答生成の改善（バックエンド）
```python
# _stream_hybrid_responseメソッドの修正
def _format_documents_with_metadata(self, documents: list[Document]) -> tuple[str, list[dict]]:
    """ドキュメントを文字列化し、引用情報を抽出"""
    content_parts = []
    citations = []
    
    for i, doc in enumerate(documents):
        content_parts.append(f"[{i+1}] {doc.page_content}")
        citations.append({
            "index": i + 1,
            "position_percent": doc.metadata.get("position_percent", 0),
            "chapter": doc.metadata.get("chapter_title", "不明"),
        })
    
    return "\n\n".join(content_parts), citations
```

#### 3. プロンプト改善
```
あなたは丁寧で役立つアシスタントです。
書籍の内容を参照する際は、以下の形式で引用してください：
- 参照した内容の後に上付き数字（¹, ²など）を付ける
- 回答の最後に「参照箇所：」セクションを設けて、各番号に対応する位置情報を記載

例：
この技術は革新的です¹。

参照箇所：
¹ 約25%の位置
```

#### 4. ハイライト情報の活用
- `highlight_searcher.search_relevant_highlights`の結果にも位置情報を含める
- ハイライトにはCFIが既に含まれているため、より正確な位置情報を提供可能

### Phase 2: 拡張実装

#### 1. EPUB構造解析の強化
- UnstructuredEPubLoaderを"elements"モードで使用
- Title要素を章/セクションとして認識
- 各チャンクに最も近い前方のTitleを関連付け

#### 2. メタデータの拡張
```python
metadata = {
    # Phase 1のフィールドに加えて
    "chapter_title": nearest_title,
    "chapter_index": chapter_number,
    "section_hierarchy": ["Part 1", "Chapter 3", "Section 2"],  # 階層情報
}
```

#### 3. 表示の改善
- 章タイトルと位置情報の両方を表示
- 階層的な構造の表現

## 実装優先順位

1. **Phase 1 MVP**（完了）
   - ✅ VectorStoreへの位置情報追加
   - ✅ AI応答生成の改善
   - ✅ 基本的な脚注形式の実装

2. **Phase 2 拡張**（完了）
   - ✅ EPUB構造解析（UnstructuredEPubLoaderのelementsモード使用）
   - ✅ 章/セクション情報の追加
   - ✅ 表示の洗練

3. **Phase 3 基盤準備**（完了）
   - ✅ CFI情報の保存フィールド追加
   - ✅ フロントエンドからのCFI受信準備（metadataフィールド活用）
   - 今後の実装：
     - フロントエンドでのCFI生成
     - クリックでジャンプ機能
     - 引用箇所のプレビュー表示

## 成功指標
- LLMの回答に引用元が明確に示される
- ユーザーが参照箇所を把握できる
- 将来的な拡張（ジャンプ機能）への道筋が確保される

## フロントエンド実装ガイド

### CFI情報の送信（将来実装）

メッセージ送信時に、現在の読書位置情報をmetadataに含めることができます：

```typescript
// ChatPane.tsxでの実装例
const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/messages`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    content: trimmedText,
    chat_id: chatId || uuidv4(),
    sender_id: TEST_USER_ID,
    book_id: focusedBookTab?.book.id,
    metadata: {
      // 現在の読書位置情報を追加
      current_cfi: focusedBookTab?.rendition?.currentLocation()?.start?.cfi,
      current_spine: {
        index: focusedBookTab?.section?.index,
        title: focusedBookTab?.section?.navitem?.label
      },
      current_percentage: focusedBookTab?.rendition?.currentLocation()?.start?.percentage
    },
  }),
})
```

### 引用リンクの実装（将来実装）

LLMレスポンス内の引用情報を解析して、クリック可能なリンクを生成：

```typescript
// 引用パターンの解析（例）
const citationPattern = /¹|²|³|⁴|⁵|⁶|⁷|⁸|⁹/g;

// CFIへのジャンプ
const jumpToCFI = (cfi: string) => {
  focusedBookTab?.rendition?.display(cfi);
};
```

## 実装状況サマリー

### 完了した機能
- ✅ 書籍コンテンツの位置情報（％）付与
- ✅ 章構造の解析と保存
- ✅ LLM回答への引用情報（脚注形式）追加
- ✅ ハイライト箇所の引用情報表示
- ✅ CFI情報保存の基盤準備
- ✅ バックエンド引用情報パーサー実装
- ✅ AIメッセージのmetadataに引用情報追加
- ✅ フロントエンド CitationTextコンポーネント実装
- ✅ 引用箇所へのジャンプ機能（位置％ベース）

### 実装詳細

#### バックエンド（2025-07-06実装）
1. **citation_parser.py** - 引用情報抽出
   - 上付き数字（¹²³）の検出
   - 参照箇所セクションのパース
   - ハイライト引用（★）の検出
   
2. **create_message_usecase.py** - メタデータ追加
   - AIレスポンスから引用情報を抽出
   - メッセージ保存時にmetadataに追加

#### フロントエンド（2025-07-06実装）
1. **CitationText.tsx** - 引用レンダリングコンポーネント
   - 引用番号をクリック可能なリンクに変換
   - ツールチップで章情報を表示
   - 位置％を基にジャンプ機能実装
   
2. **ChatMessage.tsx** - CitationText統合
   - AIメッセージでmetadata.citationsがある場合CitationTextを使用
   
3. **ChatView.tsx** - metadata対応
   - APIから取得したメッセージのmetadataを保持

### 今後の実装予定
- フロントエンドでのCFI生成と送信
- より正確なCFIベースのジャンプ
- ジャンプ履歴と「戻る」機能
- 引用箇所のプレビュー改善