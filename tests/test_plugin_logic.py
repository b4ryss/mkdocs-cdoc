import pytest
import os
from mkdocs_cdoc.parser import parse_file_regex, SymbolKind, clean_comment, gtkdoc_to_rst
from mkdocs_cdoc.renderer import RenderConfig, render_doc, anchor_id

# --- PARSER TESTS ---

def test_plugin_kind_mapping():
    """Verify that the plugin correctly identifies core symbol types."""
    assert SymbolKind.FUNCTION.name == "FUNCTION"
    assert SymbolKind.VARIABLE.name == "VARIABLE"
    assert SymbolKind.STRUCT.name == "STRUCT"

def test_parser_file_not_found():
    """Ensure the regex parser raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        parse_file_regex("non_existing_file.h")

def test_comment_cleaning():
    """Check if Doxygen-style block comments are correctly cleaned."""
    raw_comment = "/**\n * @brief Test function\n */"
    cleaned = clean_comment(raw_comment)
    assert "Test function" in cleaned
    assert "* " not in cleaned

def test_gtkdoc_to_rst_conversion():
    """Verify the transformation of gtk-doc markup into reST format."""
    text = "Check %MY_CONST and function_name()."
    converted = gtkdoc_to_rst(text)
    assert ":const:`MY_CONST`" in converted
    assert ":func:`function_name`" in converted

def test_struct_parsing_logic():
    """Verify that the regex parser can identify documented C structs."""
    content = "/** Point structure */\nstruct Point { int x; int y; };"
    with open("temp_struct.h", "w") as f:
        f.write(content)
    try:
        results = parse_file_regex("temp_struct.h")
        assert any(r.kind == SymbolKind.STRUCT for r in results)
    finally:
        if os.path.exists("temp_struct.h"): os.remove("temp_struct.h")

def test_junk_comment_cleaning():
    """Ensure the cleaner handles complex comment decorations like separators."""
    junk_comment = "/***********\n * IMPORTANT\n ***********/"
    cleaned = clean_comment(junk_comment)
    assert "IMPORTANT" in cleaned

def test_macro_parsing_logic():
    """Verify the regex parser identifies macros when properly documented."""
    # Added doc comments to ensure regex match
    content = "/** max */\n#define MAX_VAL 1024\n/** log */\n#define LOG(m) printf(m)"
    with open("temp_macro.h", "w") as f:
        f.write(content)
    try:
        results = parse_file_regex("temp_macro.h")
        names = [r.name for r in results]
        assert "MAX_VAL" in names
        assert "LOG" in names
    finally:
        if os.path.exists("temp_macro.h"): os.remove("temp_macro.h")

def test_typedef_enum_logic():
    """Ensure documented typedefs and enums are identified correctly."""
    # Added doc comments to satisfy parser.py regex requirements
    content = "/** myint */\ntypedef int my_int;\n/** status */\nenum Status { OK };"
    with open("temp_types.h", "w") as f:
        f.write(content)
    try:
        results = parse_file_regex("temp_types.h")
        kinds = [r.kind for r in results]
        assert any(k == SymbolKind.TYPEDEF for k in kinds)
        assert any(k == SymbolKind.ENUM for k in kinds)
    finally:
        if os.path.exists("temp_types.h"): os.remove("temp_types.h")

def test_pointer_return_signature():
    """Check if the parser handles functions returning pointers with doc comments."""
    content = "/** get name */\nchar *get_name(int id);"
    with open("temp_ptr.h", "w") as f:
        f.write(content)
    try:
        results = parse_file_regex("temp_ptr.h")
        assert "char *" in results[0].return_type
    finally:
        if os.path.exists("temp_ptr.h"): os.remove("temp_ptr.h")

def test_gtkdoc_codeblock_protection():
    """Verify that |[...] blocks are converted to fenced markdown blocks."""
    text = "Refer: |[ int x = 5; ]|"
    converted = gtkdoc_to_rst(text)
    assert "```c" in converted and "int x = 5;" in converted


# --- RENDERER TESTS (Frontend Logic) ---

def test_function_rendering_output():
    """Verify that the renderer produces correct Markdown headers for symbols."""
    config = RenderConfig(heading_level=2)
    from mkdocs_cdoc.parser import DocComment
    doc = DocComment(name="test_func", kind=SymbolKind.FUNCTION, comment="Desc", signature="void test_func()")
    
    output = render_doc(doc, config)
    assert "## test_func" in output
    assert "void test_func()" in output

def test_anchor_id_logic():
    """Ensure that the renderer creates valid HTML anchors for navigation."""
    from mkdocs_cdoc.parser import DocComment
    doc = DocComment(name="my_var", kind=SymbolKind.VARIABLE, comment="")
    aid = anchor_id(doc)
    assert "my_var" in aid

def test_regex_parser_integration():
    """Integration test to verify full file reading and parsing cycle."""
    content = "/** Integration test */\nint test_pipeline(int a);"
    with open("temp_integration.h", "w") as f:
        f.write(content)
    try:
        results = parse_file_regex("temp_integration.h")
        assert len(results) > 0
        assert results[0].name == "test_pipeline"
    finally:
        if os.path.exists("temp_integration.h"): os.remove("temp_integration.h")
