# app/services/gemini_service.py
import os
import google.generativeai as genai
import asyncio

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)


async def query_gemini(prompt: str) -> str:
    """Query Gemini for a roadmap text.

    Raises a clear error if GOOGLE_API_KEY is not configured to avoid opaque 500s.
    """
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is not set. Please configure it in your environment to enable roadmap generation.")

    # Run the synchronous Gemini call in thread executor to avoid blocking async loop
    loop = asyncio.get_running_loop()
    model = genai.GenerativeModel("gemini-1.5-flash")

    def sync_call():
        response = model.generate_content(prompt)
        return response.text

    response_text = await loop.run_in_executor(None, sync_call)
    return response_text


def build_prompt_from_responses(document: dict) -> str:
    """Builds a rich structured prompt for Gemini instructing it to return a SINGLE JSON object
    with the following top-level keys (snake_case exactly):
      overview: string (succinct executive summary)
      problem_identification: string (clear articulation of the core problems / gaps)
      possible_solutions: array[ { title, rationale, risks, bizowl_services } ]
      best_recommended_solution: { title, why_best, implementation_focus, key_risks, mitigation }
      roadmap: array[ { sequence, title, description, duration, kpis, dependencies, bizowl_support } ] (sequence starts at 1)
      conclusion: string (motivational closing with call to disciplined execution)
    This is intended to power both textual sections and an interactive vertical timeline UI on the frontend.
    """

    prompt_lines = [
        "You are a senior startup strategist at Bizowl (https://www.bizzowl.com/) providing deeply personalized, execution-focused guidance.",
        "You are given structured assessment responses from a founder. Using ONLY that context, output a SINGLE valid JSON object (UTF-8, no markdown fences, no commentary) adhering EXACTLY to the schema below.",
        "",
        "Return JSON Schema (conceptual – do not include this text in output):",
        '{',
        '  "overview": string,',
        '  "problem_identification": string,',
        '  "possible_solutions": [',
        '     { "title": string, "rationale": string, "risks": string, "bizowl_services": string }',
        '  ],',
        '  "best_recommended_solution": {',
        '     "title": string,',
        '     "why_best": string,',
        '     "implementation_focus": string,',
        '     "key_risks": string,',
        '     "mitigation": string',
        '  },',
        '  "roadmap": [',
        '     { "sequence": number, "title": string, "description": string, "duration": string, "kpis": string, "dependencies": string, "bizowl_support": string }',
        '  ],',
        '  "conclusion": string',
        '}',
        "",
     "Roadmap requirements:",
     "- Provide 6–10 sequential steps from zero (0→1 journey) to initial traction.",
     "- Each step MUST have a unique increasing integer 'sequence' starting at 1.",
     "- 'duration' should be realistic (e.g., '1 week', '2 weeks', '3-4 weeks').",
     "- 'kpis' should list measurable leading indicators (comma-separated is fine).",
     "- 'dependencies' should mention prior step numbers or 'None'.",
     "- 'bizowl_support' must map the step to specific Bizowl service categories (e.g., 'Market Research', 'MVP Development', 'Brand & Digital Marketing', 'Fundraising Readiness', 'Growth Analytics').",
     "- Possible solutions section:",
     "- Offer at least 3 distinct solution approaches.",
     "- 'rationale' should tie directly to the founder's context.",
     "- 'risks' should be realistic and non-generic.",
     "- 'bizowl_services' maps which Bizowl capabilities accelerate that option.",
     "- Select ONE as 'best_recommended_solution' with a defendable reasoning in 'why_best'.",
     "- Style guidelines:",
     "- Be precise, actionable, founder-friendly.",
     "- Avoid fluff, avoid repeating the questions.",
     "- Never invent user context not implied by answers.",
     "- DO NOT return markdown, only raw JSON.",
     "- Escape internal quotes properly.",
     "- Make it user product centric and much more personalized, do not be generic, can be generic in overview and conclusion",
     "- Do not include trailing commas.",
     "- Ensure JSON parses on first attempt.",
     "- Keep paragraphs concise (1–4 sentences each).",
        "- Do NOT hallucinate or introduce unexplained acronyms or tokens like 'sc', 'asc', 'xyz'.",
        "- If the underlying data is missing, write 'Not specified' instead of guessing.",
        "- Any acronym you MUST use (rare) should be expanded on first use (e.g., Customer Acquisition Cost (CAC)).",
        "User assessment responses (ordered):"
    ]

    # Attach user responses
    for i, resp in enumerate(document.get("responses", []), 1):
        question = resp.get("question", "").strip()
        answer = resp.get("answer", "")
        if isinstance(answer, list):
            answer = ", ".join([str(a) for a in answer])
        prompt_lines.append(f"{i}. Q: {question}\n   A: {answer}")

    prompt_lines.append(
        "\nOutput ONLY the JSON object now. Do not wrap in code fences. Do not prepend explanations."
    )
    return "\n".join(prompt_lines)