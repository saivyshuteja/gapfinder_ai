from app.services.embedding_service import (
    generate_embedding
)


text1 = """
Python uses if, elif and else
for conditional execution.
"""

text2 = """
Conditional statements in Python
control which block of code executes.
"""

text3 = """
The capital of France is Paris.
"""


embedding1 = generate_embedding(
    text1
)

embedding2 = generate_embedding(
    text2
)

embedding3 = generate_embedding(
    text3
)


def cosine_similarity(
    a,
    b
):
    dot_product = sum(
        x * y
        for x, y in zip(a, b)
    )

    magnitude_a = sum(
        x * x
        for x in a
    ) ** 0.5

    magnitude_b = sum(
        x * x
        for x in b
    ) ** 0.5

    return (
        dot_product /
        (magnitude_a * magnitude_b)
    )


similarity_1_2 = cosine_similarity(
    embedding1,
    embedding2
)

similarity_1_3 = cosine_similarity(
    embedding1,
    embedding3
)


print(
    f"Python similarity: "
    f"{similarity_1_2:.4f}"
)

print(
    f"Unrelated similarity: "
    f"{similarity_1_3:.4f}"
)