import pytest
from pathlib import Path
from extractors.base_extractor import BaseExtractor


@pytest.mark.unit
def test_base_extractor_can_be_instantiated():
    """Ensure BaseExtractor can be created without errors."""
    extractor = BaseExtractor()
    assert isinstance(extractor, BaseExtractor)


@pytest.mark.unit
def test_extract_blocks_raises_not_implemented_error():
    """Ensure extract_blocks() must be implemented by subclasses."""
    extractor = BaseExtractor()
    dummy_path = Path("dummy.txt")

    with pytest.raises(NotImplementedError):
        extractor.extract_blocks(dummy_path)
