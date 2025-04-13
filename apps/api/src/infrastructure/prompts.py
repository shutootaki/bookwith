from langchain_core.prompts import ChatPromptTemplate

# RAG用のプロンプトテンプレート
rag_template = """あなたは親切で役立つAIアシスタントです。
ユーザーの質問に対して、以下のコンテキスト情報を使って回答してください。
コンテキストに含まれていない情報がある場合は、「その情報はコンテキストには含まれていません」と正直に答えてください。

コンテキスト:
{context}

質問: {question}
"""

rag_prompt = ChatPromptTemplate.from_template(rag_template)
