from app.services.embedding_service import generate_embedding


text = """
Python is a programming language.
It supports variables, functions,
loops and conditional statements.
"""


embedding = generate_embedding(text)


print("Embedding generated successfully.")
print(f"Embedding dimension: {len(embedding)}")

print("\nFirst 10 values:")
print(embedding[:10])