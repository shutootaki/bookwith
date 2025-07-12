"""Prompt templates for podcast generation"""

CHAPTER_SUMMARY_PROMPT = """
Please provide a concise and informative summary of the following book chapter.
Focus on the main ideas, key arguments, and important details.
Keep the summary clear and well-structured.

{chapter_content}

Summary:
"""

BOOK_SUMMARY_PROMPT = """
Based on the following chapter summaries, create a comprehensive overview of the book "{book_title}".
Synthesize the key themes, main arguments, character development (if applicable), and important takeaways.
Present the summary in a clear, engaging manner that captures the essence of the book.

Chapter Summaries:
{chapter_summaries}

Book Overview:
"""

PODCAST_SCRIPT_SYSTEM_PROMPT = """
You are an expert podcast scriptwriter creating engaging dialogues about books.
Your task is to transform book summaries into natural, conversational podcasts between two hosts.

Guidelines:
- Speaker HOST is the main host who leads the discussion
- Speaker GUEST is the co-host who provides insights and asks questions
- Keep the conversation natural and engaging
- Include specific examples and interesting details from the book
- Balance information with entertainment
- Use conversational language and natural transitions
"""

PODCAST_SCRIPT_PROMPT = """
Create a podcast dialogue about "{book_title}" for approximately {target_words} words.

Book Summary:
{book_summary}

Requirements:
- Natural conversation flow between speakers HOST and GUEST
- Engaging opening that hooks the listener
- Clear explanation of the book's main themes
- Interesting insights and analysis
- Personal reactions and recommendations
- Smooth conclusion with key takeaways

Generate the dialogue in a structured format with speaker labels and their text.
"""

PODCAST_OPENING_TEMPLATES = [
    "Welcome to our book discussion podcast! Today we're diving into {book_title}.",
    "Hello everyone! We have an exciting book to talk about today: {book_title}.",
    "Welcome back to another episode! This time we're exploring {book_title}.",
]

PODCAST_CLOSING_TEMPLATES = [
    "That's all for today's discussion of {book_title}. Thanks for listening!",
    "We hope you enjoyed our conversation about {book_title}. Until next time!",
    "Thank you for joining us as we explored {book_title}. Happy reading!",
]
