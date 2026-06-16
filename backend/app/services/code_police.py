import re

_CODE_PATTERNS = [
    re.compile(r"def \w+\("),
    re.compile(r"class \w+[:\(]"),
    re.compile(r"for \w+ in "),
    re.compile(r"while .+:"),
    re.compile(r"if .+:"),
    re.compile(r"import \w+"),
    re.compile(r"from \w+ import"),
    re.compile(r"print\(.+\)"),
    re.compile(r"return .+"),
    re.compile(r"int main\("),
    re.compile(r"public static void"),
    re.compile(r"System\.out\.println"),
    re.compile(r"#include\s+<"),
    re.compile(r"console\.log\("),
]


def contains_code_block(text: str) -> bool:
    if "```" in text:
        return True
    line_count = 0
    for line in text.split("\n"):
        stripped = line.strip()
        if any(p.search(stripped) for p in _CODE_PATTERNS):
            line_count += 1
    return line_count >= 2


CORRECTION_MESSAGE = {
    "role": "user",
    "content": (
        "STOP! You violated the rule: NO CODE BLOCKS. "
        "Rewrite your previous response immediately. "
        "Provide a conceptual hint ONLY. Do not write code. "
        "Do not say 'Change X to Y'. Ask 'What should X be?'"
    ),
}

FALLBACK_RESPONSE = (
    "I'm having trouble giving a hint without showing the answer! "
    "Let's focus: look at the line mentioned in the error and think about "
    "what that line is supposed to do. What operation are you trying to perform there?"
)
