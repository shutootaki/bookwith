import logging
from dataclasses import dataclass

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class Chapter:
    """Represents a book chapter"""

    index: int
    title: str | None
    content: str

    def get_text_content(self) -> str:
        """Get plain text content from HTML"""
        soup = BeautifulSoup(self.content, "html.parser")
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        # Get text
        text = soup.get_text()
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        return "\n".join(chunk for chunk in chunks if chunk)
