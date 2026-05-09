import logging
from dataclasses import dataclass
from functools import cached_property

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class Chapter:
    """Represents a book chapter"""

    index: int
    title: str | None
    content: str

    @cached_property
    def text_content(self) -> str:
        """Plain text extracted from HTML, computed once per instance."""
        soup = BeautifulSoup(self.content, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return "\n".join(chunk for chunk in chunks if chunk)

    def get_text_content(self) -> str:
        return self.text_content
