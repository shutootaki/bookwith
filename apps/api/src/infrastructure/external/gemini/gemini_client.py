import json
import logging
from typing import Any

import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory
from google.protobuf.json_format import MessageToDict

from src.config.app_config import AppConfig
from src.domain.podcast.value_objects.language import PodcastLanguage
from src.infrastructure.external.gemini.prompts.podcast_prompts import get_prompts_with_language

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
        self.gemini_flash_model = "gemini-2.5-flash"
        self.gemini_pro_model = "gemini-2.5-flash"

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
            raise
            logger.error(f"Error summarizing text with Gemini Pro: {str(e)}")

    async def generate_podcast_script(
        self,
        summary: str,
        book_title: str,
        language: PodcastLanguage,
        target_words: int = 1000,
        temperature: float = 0.7,
    ) -> list[dict[str, str]]:
        """Generate podcast script using Gemini Flash model with function calling

        Args:
            summary: Book summary
            book_title: Title of the book
            target_words: Target word count for the script
            temperature: Sampling temperature (0.0 to 1.0)
            language: Language of the script

        Returns:
            List of dialogue turns with speaker and text

        """
        try:
            # Log input for debugging
            logger.info(f"Generating podcast script for '{book_title}' with target_words={target_words}")
            logger.debug(f"Book summary length: {len(summary)} characters")
            logger.debug(f"Book summary preview: {summary[:500]}...")

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
                                                "speaker": {
                                                    "type": "string",
                                                    "enum": ["HOST", "GUEST"],
                                                    "description": "Speaker identifier (HOST or GUEST)",
                                                },
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
            prompt = self._create_podcast_prompt(summary, book_title, target_words, language)

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

            # Generate response with enhanced error handling
            try:
                response = await model_with_tools.generate_content_async(
                    prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": 4096,
                    },
                )
            except Exception as api_error:
                logger.error(f"Gemini API error: {str(api_error)}")
                # Check if it's a safety-related error
                if "safety" in str(api_error).lower() or "blocked" in str(api_error).lower():
                    raise ValueError(f"Content blocked by safety filters: {str(api_error)}")
                raise

            # Enhanced response validation
            if not response or not response.candidates:
                raise ValueError("No response received from Gemini API")

            # Check for safety blocks in response
            for candidate in response.candidates:
                if hasattr(candidate, "finish_reason") and candidate.finish_reason == 10:
                    logger.error("Response blocked by safety filters (finish_reason=10)")
                    # Try with a simpler prompt
                    logger.info("Retrying with simplified prompt...")
                    return await self._generate_with_simplified_prompt(summary, book_title, target_words, temperature, language)

            # Extract function call result or fallback to text parsing
            dialogue = self._extract_function_call_result(response)
            if dialogue:
                logger.info(f"Successfully extracted {len(dialogue)} dialogue turns from function call")
                logger.debug(f"Dialogue preview: {dialogue[:2] if len(dialogue) >= 2 else dialogue}")

                return dialogue

            # Fallback to text parsing
            logger.warning("Function call extraction failed, falling back to text parsing")
            text = self._extract_response_text(response)
            logger.debug(f"Raw response text length: {len(text)} characters")
            logger.debug(f"Raw response preview: {text[:500]}...")

            parsed_dialogue = self._parse_dialogue_from_text(text)
            logger.info(f"Parsed {len(parsed_dialogue)} dialogue turns from text")

            return parsed_dialogue

        except Exception as e:
            logger.error(f"Error generating podcast script with Gemini Flash: {str(e)}")
            raise

    async def _generate_with_simplified_prompt(
        self,
        summary: str,
        book_title: str,
        target_words: int,
        temperature: float,
        language: PodcastLanguage,
    ) -> list[dict[str, str]]:
        """Generate podcast script with a simplified prompt when safety filters are triggered"""
        logger.info("Using simplified prompt to avoid safety filters")

        # Use a much simpler prompt without structured output
        simplified_prompt = f"""
Create a short educational podcast conversation about the book "{book_title}".

Summary: {summary[:500]}...

Generate a friendly discussion between HOST and GUEST about this book.
Keep it educational and appropriate for all audiences.
Target length: about {target_words} words.

Format each line as:
HOST: [what the host says]
GUEST: [what the guest says]
"""

        try:
            # Use gemini-1.5-pro with simple text generation
            model = genai.GenerativeModel(
                "gemini-1.5-pro",
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                },
            )

            response = await model.generate_content_async(
                simplified_prompt,
                generation_config={
                    "temperature": temperature * 0.7,  # Lower temperature for safety
                    "max_output_tokens": 2048,
                },
            )

            # Parse the simple text response
            text = self._extract_response_text(response)
            dialogue_turns = []

            for line in text.split("\n"):
                line = line.strip()
                if line.startswith("HOST:"):
                    dialogue_turns.append({"speaker": "HOST", "text": line[5:].strip()})
                elif line.startswith("GUEST:"):
                    dialogue_turns.append({"speaker": "GUEST", "text": line[6:].strip()})

            if not dialogue_turns:
                # Fallback: create a minimal dialogue
                dialogue_turns = [
                    {"speaker": "HOST", "text": f"Welcome! Today we're discussing {book_title}."},
                    {"speaker": "GUEST", "text": "I'm excited to talk about this book."},
                    {"speaker": "HOST", "text": "It's a fascinating read with many interesting themes."},
                    {"speaker": "GUEST", "text": "Absolutely. Thanks for having me on the show!"},
                ]

            return dialogue_turns

        except Exception as e:
            logger.error(f"Failed to generate with simplified prompt: {str(e)}")
            # Return a minimal fallback dialogue
            return [
                {"speaker": "HOST", "text": f"Welcome to our podcast about {book_title}."},
                {"speaker": "GUEST", "text": "Thank you for having me."},
                {"speaker": "HOST", "text": "This book offers valuable insights."},
                {"speaker": "GUEST", "text": "I agree. It's worth reading."},
            ]

    def _create_podcast_prompt(self, summary: str, book_title: str, target_words: int, language: PodcastLanguage) -> str:
        """Create the prompt for podcast script generation with enhanced safety"""
        lang_prompts = get_prompts_with_language(language)
        system_prompt = lang_prompts["system"]
        script_template = lang_prompts["script"]

        # script_templateがリストやタプルの場合は先頭要素を使う
        if isinstance(script_template, list | tuple):
            script_template = script_template[0]
        script_template = str(script_template)

        # Format the script prompt with the provided values
        script_prompt = script_template.format(
            book_title=book_title,
            book_summary=summary,
            target_words=target_words,
        )

        # Enhanced safety instructions
        safety_instruction = """
IMPORTANT SAFETY GUIDELINES:
- Keep content family-friendly and educational
- Avoid any potentially harmful or inappropriate content
- Focus on positive, constructive discussion
- Maintain professional and respectful tone
- Ensure all content is suitable for general audiences
"""

        # Combine system and script prompts with safety instructions
        return f"""{system_prompt}

{safety_instruction}

{script_prompt}

Use the generate_podcast_dialogue function to structure your response as an array of dialogue turns.
Each turn should have a \"speaker\" (either \"HOST\" or \"GUEST\") and \"text\" (what they say).
Ensure all content follows the safety guidelines above."""

    def _parse_dialogue_from_text(self, text: str) -> list[dict[str, str]]:
        """Fallback method to parse dialogue from raw text"""
        dialogue = []
        lines = text.strip().split("\n")

        for line in lines:
            line = line.strip()
            if line.startswith("HOST:"):
                speaker = "HOST"
                text_content = line[5:].strip()
                if text_content:
                    dialogue.append({"speaker": speaker, "text": text_content})
            elif line.startswith("GUEST:"):
                speaker = "GUEST"
                text_content = line[6:].strip()
                if text_content:
                    dialogue.append({"speaker": speaker, "text": text_content})

        return dialogue

    async def generate_chapter_summary(
        self,
        chapter_text: str,
        language: PodcastLanguage,
        max_output_tokens: int = 400,
        temperature: float = 0.3,
    ) -> str:
        """Generate a summary for a single chapter

        Args:
            chapter_text: The chapter content
            chapter_title: Optional chapter title
            max_output_tokens: Maximum number of output tokens
            temperature: Sampling temperature
            language: Language of the script

        Returns:
            Chapter summary

        """
        # Get language-specific prompts
        lang_prompts = get_prompts_with_language(language)
        chapter_summary_template = lang_prompts["chapter_summary"]
        # chapter_summary_templateがリストやタプルの場合は先頭要素を使う
        if isinstance(chapter_summary_template, list | tuple):
            chapter_summary_template = chapter_summary_template[0]
        chapter_summary_template = str(chapter_summary_template)

        # Format the prompt
        prompt = chapter_summary_template.format(chapter_content=chapter_text)

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
        language: PodcastLanguage,
        max_output_tokens: int = 800,
        temperature: float = 0.3,
    ) -> str:
        """Combine multiple chapter summaries into a coherent book summary

        Args:
            summaries: List of chapter summaries
            book_title: Title of the book
            max_output_tokens: Maximum number of output tokens
            temperature: Sampling temperature
            language: Language of the script

        Returns:
            Combined book summary

        """
        # Get language-specific prompts
        lang_prompts = get_prompts_with_language(language)
        book_summary_template = lang_prompts["book_summary"]
        if isinstance(book_summary_template, list | tuple):
            book_summary_template = book_summary_template[0]
        book_summary_template = str(book_summary_template)

        # Format chapter summaries based on language
        if language == PodcastLanguage.JA_JP:
            combined_text = "\n\n".join([f"第{i + 1}章:\n{summary}" for i, summary in enumerate(summaries)])
        elif language == PodcastLanguage.CMN_CN:
            combined_text = "\n\n".join([f"第{i + 1}章：\n{summary}" for i, summary in enumerate(summaries)])
        else:
            combined_text = "\n\n".join([f"Chapter {i + 1}:\n{summary}" for i, summary in enumerate(summaries)])
        # Format the prompt
        prompt = book_summary_template.format(book_title=book_title, chapter_summaries=combined_text)
        return await self.summarize_text(prompt, max_output_tokens, temperature)
