from pathlib import Path
from typing import List, Dict, Any


class BaseExtractor:
    """Base class for extractors. Each extractor should implement
    the method `extract_blocks(path: Path) -> List[Dict[str, Any]]`.
    The returned structure should be compatible with `diff_engine.compare_blocks`.
    """

    def extract_blocks(self, path: Path) -> List[Dict[str, Any]]:
        raise NotImplementedError
