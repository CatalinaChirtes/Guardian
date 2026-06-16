from app.services.code_police import contains_code_block


def test_detects_markdown_code_fence():
    assert contains_code_block("Here is code:\n```python\ndef foo():\n    pass\n```") is True


def test_detects_code_patterns_without_fence():
    text = "Try this approach:\ndef solve(n):\n    return n * 2"
    assert contains_code_block(text) is True


def test_allows_single_code_like_line():
    text = "Think about what the return value should be."
    assert contains_code_block(text) is False


def test_allows_normal_prose():
    text = "Consider what happens when you call the function with an empty list."
    assert contains_code_block(text) is False


def test_allows_mentioning_keywords_in_prose():
    text = "The import statement brings modules into scope.\nThink about which class you need."
    assert contains_code_block(text) is False


def test_detects_java_code():
    text = "public static void main(String[] args) {\n    System.out.println(\"Hello\");\n}"
    assert contains_code_block(text) is True


def test_detects_cpp_code():
    text = "#include <iostream>\nint main() {\n    return 0;\n}"
    assert contains_code_block(text) is True
