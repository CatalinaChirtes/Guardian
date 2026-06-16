from app.services.llm.base import LLMProvider


async def classify_intent(
    query: str,
    code: str,
    has_documents: bool,
    provider: LLMProvider,
) -> str:
    if not has_documents:
        return "socratic"

    if len(code.strip()) > 10:
        return "socratic"

    resp = await provider.generate(
        messages=[{
            "role": "user",
            "content": (
                "Classify this student question as either THEORY (about concepts, "
                "definitions, or course material) or SOCRATIC (about writing, "
                "debugging, or understanding specific code).\n\n"
                f"Question: {query}\n\n"
                "Reply with one word: THEORY or SOCRATIC."
            ),
        }],
        temperature=0.0,
    )
    return "theory" if "THEORY" in resp.content.upper() else "socratic"
