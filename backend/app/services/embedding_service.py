from sentence_transformers import SentenceTransformer

from app.core.config import settings


# Load the embedding model once when the service starts
model = SentenceTransformer(
    settings.EMBEDDING_MODEL
)


def generate_embedding(
    text: str
) -> list[float]:
    """
    Generate a 384-dimensional embedding
    for a single piece of text.
    """

    embedding = model.encode(
        text,
        normalize_embeddings=True
    )

    return embedding.tolist()


def generate_embeddings(
    texts: list[str]
) -> list[list[float]]:
    """
    Generate embeddings for multiple texts.
    """

    embeddings = model.encode(
        texts,
        normalize_embeddings=True
    )

    return embeddings.tolist()