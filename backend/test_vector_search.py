from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

from app.services.vector_search_service import (
    search_similar_chunks
)


engine = create_engine(
    settings.DATABASE_URL
)

SessionLocal = sessionmaker(
    bind=engine
)

db = SessionLocal()


try:

    query = """
    Explain exception handling in Python
    using try, except and finally.
    """

    print("\n================================")
    print("QUERY")
    print("================================")

    print(query)

    results = search_similar_chunks(
        db=db,
        query=query,
        top_k=5,
        min_similarity=0.0
    )

    print("\n================================")
    print("RETRIEVED CHUNKS")
    print("================================")

    for index, result in enumerate(
        results,
        start=1
    ):

        print("\n-------------------------------")

        print(
            f"Result #{index}"
        )

        print(
            f"Chunk ID: {result['id']}"
        )

        print(
            f"Page: {result['page_number']}"
        )

        print(
            f"Unit: {result['unit']}"
        )

        print(
            f"Topic: {result['topic']}"
        )

        print(
            f"Distance: "
            f"{result['distance']:.4f}"
        )

        print(
            f"Similarity: "
            f"{result['similarity']:.4f}"
        )

        print("\nContent:")

        print(
            result["content"][:500]
        )

finally:

    db.close()