from app.services.static_analysis import analyze_code, detect_language


def test_detect_python():
    assert detect_language("def hello():\n    print('hi')") == "python"


def test_detect_javascript():
    assert detect_language("console.log('hello');\nconst x = 5;") == "javascript"


def test_detect_java():
    assert detect_language("public class Main {\n    public static void main(String[] args) {}") == "java"


def test_detect_cpp():
    assert detect_language("#include <iostream>\nint main() {}") == "cpp"


def test_detect_unknown():
    assert detect_language("hello world") == "unknown"


def test_valid_python_code():
    result = analyze_code("def add(a, b):\n    return a + b")
    assert result["is_valid"] is True
    assert result["language"] == "python"
    assert result["errors"] == []


def test_invalid_python_code():
    result = analyze_code("def add(a, b)\n    return a + b")
    assert result["is_valid"] is False
    assert result["language"] == "python"
    assert len(result["errors"]) > 0


def test_valid_javascript():
    result = analyze_code("function add(a, b) {\n    return a + b;\n}")
    assert result["is_valid"] is True
    assert result["language"] == "javascript"


def test_unknown_language_passes():
    result = analyze_code("hello world")
    assert result["is_valid"] is True
    assert result["language"] == "unknown"
