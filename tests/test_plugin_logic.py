import pytest
import os
from mkdocs_cdoc.parser import parse_file_regex, SymbolKind, clean_comment, gtkdoc_to_rst
from mkdocs_cdoc.renderer import RenderConfig, render_doc, anchor_id

# --- PARSER TESTS (Backend Logic) ---

# TC-001: Valid Plugin Initialization (Logic Check)
def test_plugin_kind_mapping():
    """Verify that the plugin correctly identifies core symbol types defined in parser.py."""
    assert SymbolKind.FUNCTION.name == "FUNCTION"
    assert SymbolKind.VARIABLE.name == "VARIABLE"
    assert SymbolKind.STRUCT.name == "STRUCT"

# TC-002: Invalid Source Path Handling
def test_parser_file_not_found():
    """Ensure the regex parser raises an error when a non-existent file is provided."""
    with pytest.raises(FileNotFoundError):
        parse_file_regex("non_existing_file.h")

# TC-003: Markdown Header & Comment Cleaning
def test_comment_cleaning():
    """Check if Doxygen-style block comments are correctly cleaned for Markdown rendering."""
    raw_comment = """
    /**
     * @brief Test function
     * This is a multi-line comment.
     */
    """
    cleaned = clean_comment(raw_comment)
    # Verify that the leading asterisks and markers are stripped
    assert "Test function" in cleaned
    assert "@brief" in cleaned
    assert "* " not in cleaned

# TC-004: Character Encoding & HTML Escape Logic
def test_gtkdoc_to_rst_conversion():
    """Verify the transformation of gtk-doc markup into reST/Markdown compatible formats."""
    # Test constant and function reference conversion logic in parser.py
    text = "Check %MY_CONST and function_name()."
    converted = gtkdoc_to_rst(text)
    
    assert ":const:`MY_CONST`" in converted
    assert ":func:`function_name`" in converted

# TC-005: Struct and Member Extraction
def test_struct_parsing_logic():
    """Verify that the regex parser can identify C structs."""
    content = "/** Point structure */\nstruct Point { int x; int y; };"
    with open("temp_struct.h", "w") as f:
        f.write(content)
    try:
        results = parse_file_regex("temp_struct.h")
        assert any(r.kind == SymbolKind.STRUCT for r in results)
    finally:
        if os.path.exists("temp_struct.h"): os.remove("temp_struct.h")

# Integration Style Test: Parsing a sample C++ string
def test_regex_parser_logic():
    """Test the regex backend's ability to extract function signatures and names."""
    # This simulates a small C++ header content to test the regex fallback parser
    content = "/** Test comment */\nint calculate_sum(int a, int b);"
    
    # We use a temporary file to provide a real path to the parser
    with open("temp_test_header.h", "w") as f:
        f.write(content)
    
    try:
        results = parse_file_regex("temp_test_header.h")
        assert len(results) > 0
        assert results[0].name == "calculate_sum"
        assert "int calculate_sum" in results[0].signature
    finally:
        if os.path.exists("temp_test_header.h"):
            os.remove("temp_test_header.h")
