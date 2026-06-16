import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_java as tsjava
import tree_sitter_cpp as tscpp
from tree_sitter import Language, Parser

LANGUAGES = {
    "python": Language(tspython.language()),
    "javascript": Language(tsjavascript.language()),
    "java": Language(tsjava.language()),
    "cpp": Language(tscpp.language()),
}

_PARSERS: dict[str, Parser] = {}

for _lang_name, _lang_obj in LANGUAGES.items():
    _PARSERS[_lang_name] = Parser(_lang_obj)

_DETECT_PATTERNS = [
    ("cpp", ["#include", "std::", "cout", "cin", "nullptr", "int main("]),
    ("java", ["public class", "System.out", "public static void main"]),
    ("python", ["def ", "import ", "print(", "elif ", "self."]),
    ("javascript", ["console.log", "function ", "const ", "let ", "=> ", "document."]),
]


def detect_language(code_snippet: str) -> str:
    scores: dict[str, int] = {}
    for lang, patterns in _DETECT_PATTERNS:
        scores[lang] = sum(1 for p in patterns if p in code_snippet)
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "unknown"


def _find_errors(node, errors=None):
    if errors is None:
        errors = []
    if node.type == "ERROR" or node.is_missing:
        errors.append({
            "line": node.start_point.row + 1,
            "column": node.start_point.column,
            "end_line": node.end_point.row + 1,
            "message": f"Syntax error at line {node.start_point.row + 1}, column {node.start_point.column}",
        })
    for child in node.children:
        _find_errors(child, errors)
    return errors


def analyze_code(code_snippet: str) -> dict:
    lang = detect_language(code_snippet)

    parser = _PARSERS.get(lang)
    if parser is None:
        return {
            "is_valid": True,
            "language": lang,
            "feedback": f"Language detection inconclusive. The AI tutor will review your code.",
            "errors": [],
        }

    tree = parser.parse(code_snippet.encode("utf-8"))
    root = tree.root_node

    if not root.has_error:
        return {
            "is_valid": True,
            "language": lang,
            "feedback": f"Syntax is valid {lang.capitalize()}.",
            "errors": [],
        }

    errors = _find_errors(root)
    error_messages = [e["message"] for e in errors[:5]]
    return {
        "is_valid": False,
        "language": lang,
        "feedback": f"{lang.capitalize()} Syntax Error: {'; '.join(error_messages)}",
        "errors": errors[:5],
    }
