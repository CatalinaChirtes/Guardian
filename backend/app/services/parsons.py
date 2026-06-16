import random

from app.services.llm.base import LLMProvider


def generate_puzzle(correct_code: str) -> dict:
    lines = [line for line in correct_code.split("\n") if line.strip()]
    correct_order = list(lines)
    shuffled = list(lines)
    random.shuffle(shuffled)
    # ensure shuffled order differs from correct
    attempts = 0
    while shuffled == correct_order and attempts < 10:
        random.shuffle(shuffled)
        attempts += 1

    return {
        "correct_order": correct_order,
        "shuffled_lines": shuffled,
    }


async def generate_golden_solution(
    broken_code: str, provider: LLMProvider
) -> str:
    messages = [
        {
            "role": "user",
            "content": (
                "You are an expert programmer.\n"
                "TASK: Identify the programming language and fix the bugs in the following code.\n"
                "OUTPUT: Provide ONLY the raw corrected code. No markdown, no explanations, no comments.\n\n"
                f"BROKEN CODE:\n{broken_code}"
            ),
        }
    ]
    response = await provider.generate(
        messages=messages, temperature=0.0, max_tokens=512
    )
    # strip markdown fences if the model adds them
    code = response.content.strip()
    if code.startswith("```"):
        lines = code.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        code = "\n".join(lines).strip()
    return code


def check_puzzle_solution(
    student_order: list[str], correct_order: list[str]
) -> bool:
    return student_order == correct_order
