"""
Comparing document blocks with inline HTML diff for paragraphs
and cell-level diff for tables.
"""
from difflib import SequenceMatcher
from typing import Any, Dict, List
import logging
import html

_LOGGER = logging.getLogger(__name__)


def html_inline_diff(a: str, b: str) -> str:
    """
    Returns a combination of 'a' and 'b' with <del> and <ins> tags.
    Safely escapes source fragments before wrapping them in HTML tags.
    """
    sm = SequenceMatcher(None, a, b)
    parts: List[str] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            parts.append(html.escape(a[i1:i2]))
        elif tag == "delete":
            parts.append(f"<del>{html.escape(a[i1:i2])}</del>")
        elif tag == "insert":
            parts.append(f"<ins>{html.escape(b[j1:j2])}</ins>")
        elif tag == "replace":
            parts.append(
                f"<del>{html.escape(a[i1:i2])}</del>"
                f"<ins>{html.escape(b[j1:j2])}</ins>"
            )
    return "".join(parts)


def _table_cell_diff(old_cell: str, new_cell: str) -> Dict[str, str]:
    """
    Returns a diff structure for a single table cell: type + inline_html.
    """
    if old_cell == new_cell:
        return {"type": "same", "text": old_cell}
    return {
        "type": "changed",
        "old": old_cell,
        "new": new_cell,
        "inline_html": html_inline_diff(old_cell or "", new_cell or ""),
    }


def _diff_tables(old_table: List[List[str]], new_table: List[List[str]]) -> List[List[Dict[str, str]]]:
    """
    Compares two tables at the cell level.
    Returns a list of rows, where each row is a list of cell-diff dictionaries.
    """
    rows_old = len(old_table)
    rows_new = len(new_table)
    max_rows = max(rows_old, rows_new)
    table_changes: List[List[Dict[str, str]]] = []

    for r in range(max_rows):
        old_row = old_table[r] if r < rows_old else []
        new_row = new_table[r] if r < rows_new else []
        cols = max(len(old_row), len(new_row))
        row_changes: List[Dict[str, str]] = []
        for c in range(cols):
            old_cell = old_row[c] if c < len(old_row) else ""
            new_cell = new_row[c] if c < len(new_row) else ""
            cell_diff = _table_cell_diff(old_cell, new_cell)
            row_changes.append(cell_diff)
        table_changes.append(row_changes)

    return table_changes


def compare_blocks(old_blocks: List[Dict[str, Any]], new_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Compares sequences of blocks and returns a list of objects describing the changes.

    For paragraph blocks:
      - 'unchanged': contains the full block (from old)
      - 'changed': contains 'old', 'new' and 'inline_html' (HTML diff)

    For tables:
      - 'changed' contains 'table_changes' (2D list of cell-level diffs).
    """
    result: List[Dict[str, Any]] = []

    def key_of(b: Dict[str, Any]) -> str:
        # Create a comparison key for each block depending on its type
        t = b.get("type", "")
        if t == "paragraph":
            return "paragraph:" + (b.get("text") or "")
        if t == "table":
            rows = b.get("table") or []
            # If the table has a sheet name, include it for better identification
            sheet = b.get("sheet")
            rows_key = "|".join([",".join(row) for row in rows])
            if sheet:
                return f"table:{sheet}:{rows_key}"
            return "table:" + rows_key
        if t == "image":
            return "image:" + (b.get("sha1") or b.get("rel_id", ""))
        return t

    a_keys = [key_of(b) for b in old_blocks]
    b_keys = [key_of(b) for b in new_blocks]

    sm = SequenceMatcher(None, a_keys, b_keys)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            # Unchanged blocks
            for i, j in zip(range(i1, i2), range(j1, j2)):
                result.append({"change": "unchanged", **old_blocks[i]})
        elif tag == "replace":
            len_pairs = min(i2 - i1, j2 - j1)
            # Pairwise replacement: paragraph → paragraph (inline diff),
            # table → table (cell-level diff), image → changed pair
            for k in range(len_pairs):
                old = old_blocks[i1 + k]
                new = new_blocks[j1 + k]
                entry: Dict[str, Any] = {"change": "changed", "old": old, "new": new}
                try:
                    if old.get("type") == "paragraph" and new.get("type") == "paragraph":
                        entry["inline_html"] = html_inline_diff(old.get("text", ""), new.get("text", ""))
                    elif old.get("type") == "table" and new.get("type") == "table":
                        entry["table_changes"] = _diff_tables(old.get("table", []), new.get("table", []))
                except Exception:
                    _LOGGER.debug("Error while generating diff details", exc_info=True)
                result.append(entry)
            # Handle leftover deletions
            for i in range(i1 + len_pairs, i2):
                result.append({"change": "deleted", **old_blocks[i]})
            # Handle leftover insertions
            for j in range(j1 + len_pairs, j2):
                result.append({"change": "added", **new_blocks[j]})
        elif tag == "delete":
            # Entirely removed blocks
            for i in range(i1, i2):
                result.append({"change": "deleted", **old_blocks[i]})
        elif tag == "insert":
            # Entirely new blocks
            for j in range(j1, j2):
                result.append({"change": "added", **new_blocks[j]})

    return result
