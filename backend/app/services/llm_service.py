from groq import Groq

from app.core.config import settings


client = Groq(
    api_key=settings.GROQ_API_KEY
)


def generate_response(
    prompt: str,
    temperature: float = 0.2,
    timeout: float | None = None,
) -> str:
    """
    Generate a response using GPT-OSS 120B
    through the Groq API.
    """

    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=temperature,
        timeout=timeout,
    )

    return response.choices[0].message.content