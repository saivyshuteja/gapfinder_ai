from app.services.llm_service import generate_response


prompt = """
Explain Python exception handling in simple terms.

Explain:
1. What is an exception?
2. Why do we use try?
3. What does except do?
4. What does finally do?

Keep the answer concise.
"""


response = generate_response(
    prompt
)

print("\n================================")
print("GPT-OSS 120B RESPONSE")
print("================================")

print(response)