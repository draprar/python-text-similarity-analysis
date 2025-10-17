from pathlib import Path
from typing import List, Dict, Any
from .base_extractor import BaseExtractor


class TxtExtractor(BaseExtractor):
    """Simple extractor for text files. Each non-empty line -> paragraph."""

    def extract_blocks(self, path: Path) -> List[Dict[str, Any]]:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File does not exist: {path}")
        blocks: List[Dict[str, Any]] = []
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                text = line.strip()
                if text:
                    blocks.append({"type": "paragraph", "text": text})
        return blocks