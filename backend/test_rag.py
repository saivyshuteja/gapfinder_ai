from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

from app.services.rag_service import (
    answer_question
)


engine = create_engine(
    settings.DATABASE_URL
)

SessionLocal = sessionmaker(
    bind=engine
)

db = SessionLocal()


try:

    question = """
   Who is the President of the United States?
    """

    result = answer_question(
        db=db,
        question=question,
        top_k=5
    )

    print("\n================================")
    print("GAPFINDER AI - RAG ANSWER")
    print("================================")

    print("\nQuestion:")
    print(question)

    print("\nAnswer:")
    print(result["answer"])

    print("\n================================")
    print("SOURCES")
    print("================================")

    for source in result["sources"]:

        print("\n-------------------------------")

        print(
            f"Chunk ID: "
            f"{source['chunk_id']}"
        )

        print(
            f"Document ID: "
            f"{source['document_id']}"
        )

        print(
            f"Page: "
            f"{source['page_number']}"
        )

        print(
            f"Unit: "
            f"{source['unit']}"
        )

        print(
            f"Topic: "
            f"{source['topic']}"
        )

        print(
            f"Similarity: "
            f"{source['similarity']:.4f}"
        )

finally:

    db.close()