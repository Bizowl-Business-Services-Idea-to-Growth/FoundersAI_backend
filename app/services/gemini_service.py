# app/services/gemini_service.py
import os
import google.generativeai as genai
import asyncio

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)


async def query_gemini(prompt: str) -> str:
    # Run the synchronous Gemini call in thread executor to avoid blocking async loop
    loop = asyncio.get_running_loop()
    model = genai.GenerativeModel("gemini-1.5-flash")

    def sync_call():
        response = model.generate_content(prompt)
        return response.text

    response_text = await loop.run_in_executor(None, sync_call)
    return response_text


def build_prompt_from_responses(document: dict) -> str:
    prompt_lines = [
        "You are an expert startup advisor.",
        "Based on the following user responses, create a detailed, step-by-step roadmap for their startup.",
        "Include action steps, timelines, resources, and success metrics."
    ]
    for resp in document.get("responses", []):
        question = resp.get("question", "")
        answer = resp.get("answer", "")
        if isinstance(answer, list):
            answer = ", ".join(answer)
        prompt_lines.append(f"Q: {question}\nA: {answer}\n")

    prompt_lines.append("\nGenerate the roadmap:")
    return "\n".join(prompt_lines)
