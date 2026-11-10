from app.services.pdf_service import extract_text_from_pdf


PDF_PATH = (
    "storage/uploads/"
    "54b85096-0453-40e8-b496-a4627dab7ded.pdf"
)


pages = extract_text_from_pdf(PDF_PATH)


print(f"Total pages: {len(pages)}")

for page in pages[:3]:

    print("\n----------------------------")
    print(f"Page: {page['page_number']}")
    print("----------------------------")

    print(
        page["text"][:1000]
    )