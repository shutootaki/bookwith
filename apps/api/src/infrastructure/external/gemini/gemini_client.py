import json
import logging
from typing import Any

import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory
from google.protobuf.json_format import MessageToDict

from src.config.app_config import AppConfig

logger = logging.getLogger(__name__)


def _map_to_dict(obj: Any) -> Any:  # noqa: ANN401
    """Recursively convert MapComposite / protobuf Struct-like mappings to native dict.

    Gemini Flash (google-generativeai >= 0.4) may return `MapComposite` objects for
    function_call.args. These do not inherit from `Message` and therefore lack a
    `DESCRIPTOR`, which makes `MessageToDict` fail.  This helper safely converts any
    mapping / sequence structure (except str/bytes) into plain Python containers so
    that downstream JSON handling works regardless of the underlying SDK version.
    """
    # Lazy import to avoid adding hard dependencies
    from collections.abc import Mapping, Sequence

    if isinstance(obj, Mapping):
        return {k: _map_to_dict(v) for k, v in obj.items()}

    # Treat list / tuple of composite objects
    if isinstance(obj, Sequence) and not isinstance(obj, str | bytes | bytearray):
        return [_map_to_dict(v) for v in obj]

    # Base case – primitive value
    return obj


class GeminiClient:
    """Google Gemini API client for text generation and summarization"""

    def __init__(self) -> None:
        self.config = AppConfig.get_config()
        self.gemini_flash_model = "gemini-2.0-flash"
        self.gemini_pro_model = "gemini-2.0-pro"

        genai.configure(api_key=self.config.gemini_api_key)

        # Initialize models
        self.pro_model = genai.GenerativeModel(
            self.gemini_pro_model,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            },
        )

        self.flash_model = genai.GenerativeModel(
            self.gemini_flash_model,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            },
        )

    async def summarize_text(
        self,
        text: str,
        max_output_tokens: int = 600,
        temperature: float = 0.3,
    ) -> str:
        """Summarize text using Gemini Pro model

        Args:
            text: Text to summarize
            max_output_tokens: Maximum number of output tokens
            temperature: Sampling temperature (0.0 to 1.0)

        Returns:
            Summarized text

        """
        try:
            response = await self.pro_model.generate_content_async(
                text,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                },
            )

            return self._extract_response_text(response)

        except Exception as e:
            logger.error(f"Error summarizing text with Gemini Pro: {str(e)}")
            raise

    async def generate_podcast_script(
        self,
        summary: str,
        book_title: str,
        target_words: int = 1000,
        temperature: float = 0.7,
    ) -> list[dict[str, str]]:
        """Generate podcast script using Gemini Flash model with function calling

        Args:
            summary: Book summary
            book_title: Title of the book
            target_words: Target word count for the script
            temperature: Sampling temperature (0.0 to 1.0)

        Returns:
            List of dialogue turns with speaker and text

        """
        try:
            # Define the function schema for structured output
            tools = [
                {
                    "function_declarations": [
                        {
                            "name": "generate_podcast_dialogue",
                            "description": "Generate a podcast dialogue between two speakers",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "dialogue": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "speaker": {"type": "string", "enum": ["R", "S"], "description": "Speaker identifier (R or S)"},
                                                "text": {"type": "string", "description": "What the speaker says"},
                                            },
                                            "required": ["speaker", "text"],
                                        },
                                    }
                                },
                                "required": ["dialogue"],
                            },
                        }
                    ]
                }
            ]

            # Create the prompt
            prompt = self._create_podcast_prompt(summary, book_title, target_words)

            # Configure the model with tools
            model_with_tools = genai.GenerativeModel(
                self.gemini_flash_model,
                tools=tools,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                },
            )

            # Generate response
            response = await model_with_tools.generate_content_async(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": 4096,
                },
            )

            # Extract function call result or fallback to text parsing
            dialogue = self._extract_function_call_result(response)
            if dialogue:
                return dialogue

            # Fallback to text parsing
            text = self._extract_response_text(response)
            return self._parse_dialogue_from_text(text)

        except Exception as e:
            logger.error(f"Error generating podcast script with Gemini Flash: {str(e)}")
            raise

    def _create_podcast_prompt(self, summary: str, book_title: str, target_words: int) -> str:
        """Create the prompt for podcast script generation"""
        return f"""
You are tasked with creating an engaging podcast dialogue about the book "{book_title}".

Book Summary:
{summary}

Create a natural, conversational dialogue between two podcast hosts (R and S) discussing this book.
The dialogue should:
- Be approximately {target_words} words in total
- Feel like a real podcast conversation with natural flow
- Include interesting insights and analysis
- Use only speakers R and S
- Maintain an engaging and informative tone

Use the generate_podcast_dialogue function to structure your response as an array of dialogue turns.
Each turn should have a "speaker" (either "R" or "S") and "text" (what they say).
"""

    def _parse_dialogue_from_text(self, text: str) -> list[dict[str, str]]:
        """Fallback method to parse dialogue from raw text"""
        dialogue = []
        lines = text.strip().split("\n")

        for line in lines:
            line = line.strip()
            if line.startswith(("R:", "S:")):
                speaker = line[0]
                text = line[2:].strip()
                if text:
                    dialogue.append({"speaker": speaker, "text": text})

        return dialogue

    async def generate_chapter_summary(
        self,
        chapter_text: str,
        chapter_title: str | None = None,
        max_output_tokens: int = 400,
        temperature: float = 0.3,
    ) -> str:
        """Generate a summary for a single chapter

        Args:
            chapter_text: The chapter content
            chapter_title: Optional chapter title
            max_output_tokens: Maximum number of output tokens
            temperature: Sampling temperature

        Returns:
            Chapter summary

        """
        prompt = "Please provide a concise summary of the following chapter"
        if chapter_title:
            prompt += f" titled '{chapter_title}'"
        prompt += f":\n\n{chapter_text}"

        return await self.summarize_text(prompt, max_output_tokens, temperature)

    def _extract_response_text(self, response: Any) -> str:  # noqa: ANN401
        """Extract text from Gemini response safely

        Args:
            response: Gemini response object

        Returns:
            Extracted text

        Raises:
            ValueError: If no text was generated

        """
        # Prefer content.parts (reliable even when quick accessor fails)
        if response.candidates and response.candidates[0].content.parts:
            parts_text = "".join(getattr(part, "text", "") for part in response.candidates[0].content.parts).strip()
            if parts_text:
                return parts_text

        # Fallback to the quick accessor, guarding against ValueError when no Part exists
        try:
            if response.text:
                return response.text.strip()
        except ValueError:
            # `.text` is unavailable when LLM returned no Part (e.g., finish_reason=MAX_TOKENS)
            pass

        # Nothing was generated; include finish_reason for easier debugging
        finish_reason = response.candidates[0].finish_reason if response.candidates else "UNKNOWN"
        raise ValueError(f"No response text generated (finish_reason={finish_reason})")

    def _extract_function_call_result(self, response: Any) -> list[dict[str, str]] | None:  # noqa: ANN401
        """Extract function call result from Gemini response

        Args:
            response: Gemini response object

        Returns:
            Dialogue list if found, None otherwise

        """
        if not (response.candidates and response.candidates[0].content.parts):
            return None

        for part in response.candidates[0].content.parts:
            if not hasattr(part, "function_call"):
                continue

            args_obj = part.function_call.args
            # Skip if no arguments
            if args_obj is None:
                continue

            # Parse arguments based on type
            dialogue_data = self._parse_function_args(args_obj)

            # Return if valid dialogue found
            if isinstance(dialogue_data, dict) and "dialogue" in dialogue_data:
                return dialogue_data["dialogue"]

        return None

    def _parse_function_args(self, args_obj: Any) -> dict:  # noqa: ANN401
        """Parse function call arguments based on their type

        Args:
            args_obj: Function call arguments

        Returns:
            Parsed arguments as dictionary

        """
        # JSON string format
        if isinstance(args_obj, str | bytes | bytearray):
            return json.loads(args_obj)

        # Regular protobuf Message
        if hasattr(args_obj, "DESCRIPTOR"):
            return MessageToDict(args_obj, preserving_proto_field_name=True)

        # MapComposite or other mapping-like structure
        return _map_to_dict(args_obj)

    async def combine_summaries(
        self,
        summaries: list[str],
        book_title: str,
        max_output_tokens: int = 800,
        temperature: float = 0.3,
    ) -> str:
        """Combine multiple chapter summaries into a coherent book summary

        Args:
            summaries: List of chapter summaries
            book_title: Title of the book
            max_output_tokens: Maximum number of output tokens
            temperature: Sampling temperature

        Returns:
            Combined book summary

        """
        combined_text = "\n\n".join([f"Chapter {i + 1}:\n{summary}" for i, summary in enumerate(summaries)])

        prompt = f"""
Please create a comprehensive summary of the book "{book_title}" based on the following chapter summaries.
Synthesize the key themes, main arguments, and important takeaways into a coherent overview.

Chapter Summaries:
{combined_text}
"""

        return await self.summarize_text(prompt, max_output_tokens, temperature)
