from dataclasses import dataclass

from app.config import settings
from app.services.code_police import (
    CORRECTION_MESSAGE,
    FALLBACK_RESPONSE,
    contains_code_block,
)
from app.services.llm.base import LLMProvider, LLMResponse
from app.services.parsons import generate_golden_solution, generate_puzzle
from app.services.session_manager import SessionState
from app.services.static_analysis import analyze_code


@dataclass
class TutorResult:
    content: str
    mode: str  # "socratic" | "theory" | "puzzle" | "code_police_fallback"
    llm_response: LLMResponse | None = None
    puzzle_data: dict | None = None
    analysis: dict | None = None
    code_police_triggered: bool = False
    code_police_retries: int = 0
    challenge_solved: bool = False
    sources: str | None = None


def _build_socratic_prompt(
    student_code: str,
    analysis_feedback: str,
    exercise_question: str | None = None,
    exercise_starter_code: str | None = None,
    exercise_solution: str | None = None,
) -> str:
    base = (
        "You are a Socratic Teaching Assistant.\n"
        "GOAL: Guide the student towards the solution. Give them HINTS.\n"
        "RULES: Do NOT write code for them. NO CODE BLOCKS. NO DIRECT FIXES.\n\n"
    )

    if exercise_question and exercise_solution:
        base += (
            "CHALLENGE CONTEXT (visible only to you, NEVER reveal the solution):\n"
            f"- Exercise:\n{exercise_question}\n"
        )
        if exercise_starter_code:
            base += f"- Starter Code (given to the student):\n{exercise_starter_code}\n"
        base += (
            f"- Reference Solution (HIDDEN from student):\n{exercise_solution}\n\n"
            "Use the reference solution to give ACCURATE hints about what the "
            "student is doing wrong or what they should think about next. "
            "Compare their code to the reference to identify gaps, but NEVER "
            "show, quote, or paraphrase the solution code.\n\n"
        )

    base += (
        "CURRENT CONTEXT:\n"
        f"- Student Code:\n{student_code}\n"
        f"- Analysis Report: {analysis_feedback}\n\n"
        "INSTRUCTIONS:\n"
        "- You are strictly FORBIDDEN from writing code solutions.\n"
        "- If the Analysis Report reports an error OR if you see an obvious syntax error, "
        "point it out. Do NOT fix it.\n"
        "- If the user asks for code, refuse politely. Give a conceptual hint instead. "
        "Do not say 'Change X to Y'. Ask 'What should X be?'\n"
        "- Keep answers focused but thorough (3-5 sentences). Explain your reasoning.\n"
        "- Be friendly but firm.\n\n"
        "SOLUTION CHECK:\n"
        "- If the student's code is functionally correct (solves the exercise "
        "and matches the expected behavior of the reference solution), "
        "congratulate them warmly! Tell them their solution works and highlight "
        "what they did well. You may suggest minor improvements but make it "
        "clear that they have SOLVED the challenge.\n"
        "- If their code is ALMOST correct (close but has a small bug or "
        "edge case issue), encourage them, tell them they're very close "
        "and give a targeted hint about the remaining issue."
    )
    return base


async def _is_solution_correct(
    student_code: str,
    exercise_solution: str,
    provider: LLMProvider,
) -> bool:
    prompt = (
        "You are evaluating whether a student's code correctly solves a programming exercise.\n"
        f"Reference solution:\n{exercise_solution}\n\n"
        f"Student code:\n{student_code}\n\n"
        "Does the student's code produce the SAME correct result as the reference solution? "
        "Minor style differences are fine. Focus on functional correctness.\n"
        "Reply with ONLY the word CORRECT or INCORRECT."
    )
    resp = await provider.generate(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    return "CORRECT" in resp.content.upper() and "INCORRECT" not in resp.content.upper()


async def _is_student_stuck(
    student_code: str,
    exercise_solution: str,
    history: list[dict],
    provider: LLMProvider,
) -> bool:
    prompt = (
        "You are evaluating whether a programming student is stuck.\n"
        f"Reference solution:\n{exercise_solution}\n\n"
        f"Student code:\n{student_code}\n\n"
        "Based on how far the student's code is from the solution, "
        "is the student STUCK (making no meaningful progress) or "
        "PROGRESSING (getting closer to a correct solution)?\n"
        "Reply with ONLY the word STUCK or PROGRESSING."
    )
    resp = await provider.generate(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    return "STUCK" in resp.content.upper()


async def generate_tutor_response(
    student_code: str,
    user_query: str,
    state: SessionState,
    provider: LLMProvider,
    skip_solution_check: bool = False,
) -> TutorResult:
    has_code = len(student_code.strip()) > 10
    mode = "socratic"

    # increment attempts and check for puzzle trigger (requires code in editor)
    state.attempt_count += 1
    if (
        has_code
        and state.attempt_count >= settings.max_attempts_before_puzzle
        and not state.puzzle_triggered
    ):
        stuck = True
        if state.active_exercise_solution:
            stuck = await _is_student_stuck(
                student_code,
                state.active_exercise_solution,
                state.history_window,
                provider,
            )

        if stuck:
            state.puzzle_triggered = True
            state.attempt_count = 0

            if state.active_exercise_solution:
                solution_code = state.active_exercise_solution
            else:
                solution_code = await generate_golden_solution(
                    student_code, provider
                )

            puzzle_data = generate_puzzle(solution_code)
            return TutorResult(
                content="You seem stuck, so let's try a different approach! "
                "Instead of writing code, can you arrange these scrambled lines "
                "in the correct order?",
                mode="puzzle",
                puzzle_data=puzzle_data,
            )

    # static analysis
    analysis = analyze_code(student_code) if has_code else None
    analysis_feedback = analysis["feedback"] if analysis else "No code submitted."

    messages = []
    if settings.enable_socratic_prompt:
        system_prompt = _build_socratic_prompt(
            student_code,
            analysis_feedback,
            exercise_question=state.active_exercise_question,
            exercise_starter_code=state.active_exercise_starter_code,
            exercise_solution=state.active_exercise_solution,
        )
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(state.history_window)
    
    user_content = user_query
    if not settings.enable_socratic_prompt and has_code:
        user_content = f"{user_query}\n\nMy code:\n```\n{student_code}\n```"
    messages.append({"role": "user", "content": user_content})

    llm_response = await provider.generate(messages=messages, temperature=0.6)
    response_text = llm_response.content

    code_police_triggered = False
    code_police_retries = 0

    if settings.enable_code_police and mode == "socratic" and contains_code_block(response_text):
        code_police_triggered = True
        code_police_retries = 1

        # re-prompt demanding hints only
        correction_messages = messages.copy()
        correction_messages.append({"role": "assistant", "content": response_text})
        correction_messages.append(CORRECTION_MESSAGE)

        retry_response = await provider.generate(
            messages=correction_messages, temperature=0.6
        )
        response_text = retry_response.content
        llm_response = retry_response

        # if it fails again, use the hardcoded fallback
        if contains_code_block(response_text):
            code_police_retries = 2
            response_text = FALLBACK_RESPONSE
            mode = "code_police_fallback"

    challenge_solved = False
    if has_code and state.active_exercise_solution and not skip_solution_check:
        challenge_solved = await _is_solution_correct(
            student_code, state.active_exercise_solution, provider
        )

    return TutorResult(
        content=response_text,
        mode=mode,
        llm_response=llm_response,
        analysis=analysis,
        code_police_triggered=code_police_triggered,
        code_police_retries=code_police_retries,
        challenge_solved=challenge_solved,
    )


async def generate_theory_response(
    user_query: str,
    rag_results: list[dict],
    state: SessionState,
    provider: LLMProvider,
) -> TutorResult:
    context_parts = []
    for i, r in enumerate(rag_results, 1):
        source = r["filename"]
        if r["page"] is not None:
            source += f", page {r['page'] + 1}"
        context_parts.append(f"Excerpt {i} (from {source}):\n{r['content']}")
    context = "\n\n".join(context_parts)

    sources_summary = "\n".join(
        f"- {r['filename']}" + (f" (page {r['page'] + 1})" if r["page"] is not None else "")
        for r in rag_results
    )

    system_prompt = (
        "You are a knowledgeable Professor answering a student's question "
        "based on their course materials.\n\n"
        "INSTRUCTIONS:\n"
        "- Base your answer ONLY on the excerpts provided below.\n"
        "- Synthesize information across multiple excerpts when relevant.\n"
        "- If the excerpts don't contain enough information to fully answer "
        "the question, clearly state what is and isn't covered.\n"
        "- Be thorough but concise. Use clear structure (paragraphs, bullet points).\n"
        "- Do NOT make up information that isn't in the excerpts.\n"
        "- Consider the conversation history for context on follow-up questions.\n\n"
        "--- COURSE MATERIAL EXCERPTS ---\n"
        f"{context}\n"
        "--- END EXCERPTS ---"
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(state.history_window)
    messages.append({"role": "user", "content": user_query})

    llm_response = await provider.generate(messages=messages, temperature=0.3)

    return TutorResult(
        content=llm_response.content,
        mode="theory",
        llm_response=llm_response,
        sources=sources_summary,
    )
