"""Prompt templates for podcast generation"""

from src.domain.podcast.value_objects.language import PodcastLanguage


def build_language_prompts(language: PodcastLanguage = PodcastLanguage.EN_US):
    """言語ルールのみ返す"""
    language_instruction = ""

    # Correctly format language instruction based on the selected language
    if language == PodcastLanguage.EN_US:
        language_instruction = "Generate all content in English."
    elif language == PodcastLanguage.JA_JP:
        language_instruction = "Generate all content in Japanese (日本語で生成してください)."
    elif language == PodcastLanguage.CMN_CN:
        language_instruction = "Generate all content in Simplified Chinese (请用简体中文生成)."
    else:
        language_instruction = f"Generate all content in the language: {language.value}."

    return f"""
Important Rules:
- {language_instruction}
- Keep content family-friendly and educational.
- Focus on positive, constructive discussion.
- Avoid any controversial or sensitive topics.
"""


def _build_chapter_summary_prompt(language_rule: str) -> str:
    """章の要約プロンプトを構築"""
    return f"""{language_rule}

Please provide a concise and informative summary of the following book chapter.
Focus on the main ideas, key arguments, and important details.
Keep the summary clear, well-structured, and family-friendly.

{{chapter_content}}

Summary:
"""


def _build_book_summary_prompt(language_rule: str) -> str:
    """本の要約プロンプトを構築"""
    return f"""{language_rule}

Based on the following chapter summaries, create a comprehensive overview of the book "{{book_title}}".
Synthesize the key themes, main arguments, character development (if applicable), and important takeaways.
Present the summary in a clear, engaging, and family-friendly manner that captures the essence of the book.

Chapter Summaries:
{{chapter_summaries}}

Book Overview:
"""


def _build_system_prompt(language_rule: str) -> str:
    """システムプロンプトを構築"""
    return f"""{language_rule}

You are an expert podcast scriptwriter creating engaging, family-friendly dialogues about books.
Your task is to transform book summaries into natural, conversational podcasts between two hosts.

Guidelines:
- Speaker HOST is the main host who leads the discussion
- Speaker GUEST is the co-host who provides insights and asks questions
- Keep the conversation natural, engaging, and family-friendly
- Include specific examples and interesting details from the book
- Balance information with entertainment
- Use conversational language and natural transitions
- Ensure all content is suitable for general audiences
- Focus on positive, educational, and constructive discussion
"""


def _build_script_prompt(language_rule: str) -> str:
    """スクリプト生成プロンプトを構築"""
    return f"""{language_rule}

Create a family-friendly podcast dialogue about "{{book_title}}" for approximately {{target_words}} words.

Book Summary:
{{book_summary}}

Requirements:
- Natural conversation flow between speakers HOST and GUEST
- Engaging opening that hooks the listener
- Clear explanation of the book's main themes
- Interesting insights and analysis
- Personal reactions and recommendations
- Smooth conclusion with key takeaways
- All content must be family-friendly and educational
- Focus on positive, constructive discussion

Generate the dialogue in a structured format with speaker labels and their text.
"""


def get_prompts_with_language(language: PodcastLanguage = PodcastLanguage.EN_US):
    language_rule = build_language_prompts(language)

    return {
        "chapter_summary": _build_chapter_summary_prompt(language_rule),
        "book_summary": _build_book_summary_prompt(language_rule),
        "system": _build_system_prompt(language_rule),
        "script": _build_script_prompt(language_rule),
        "openings": [
            "Welcome to our book discussion podcast! Today we're diving into {book_title}.",
            "Hello everyone! We have an exciting book to talk about today: {book_title}.",
            "Welcome back to another episode! This time we're exploring {book_title}.",
        ],
        "closings": [
            "That's all for today's discussion of {book_title}. Thanks for listening!",
            "We hope you enjoyed our conversation about {book_title}. Until next time!",
            "Thank you for joining us as we explored {book_title}. Happy reading!",
        ],
    }
