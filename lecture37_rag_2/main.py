"""
RAG Part 2, Step 1: Load a PDF and extract its text, page by page.

Before an AI can answer questions about a document, we need the document's
text in Python. This script opens a PDF, reads every page, and stores the
text together with where it came from (file name + page number).

Run:  pip install pypdf
"""

# pypdf is a free Python library that can open and read PDF files
from pypdf import PdfReader

# The PDF we want to load. Keep it in the same folder as this script.
PDF_PATH = "HR_Handbook.pdf"

# Open the PDF. "reader" now gives us access to every page inside it.
reader = PdfReader(PDF_PATH)

# reader.pages is a list of all pages, so len() tells us how many there are
print(f"Loaded {PDF_PATH}: {len(reader.pages)} pages\n")

# We'll collect one entry per page in this list.
# Why keep pages separate instead of one big string?
# Because later the AI's answer should say WHERE it found the information,
# e.g. "HR_Handbook.pdf, page 2". So we must remember the page number now.
documents = []

# Go through the pages one by one.
# enumerate(..., start=1) gives us the page number (1, 2, 3...) alongside each page.
for page_number, page in enumerate(reader.pages, start=1):

    # Pull the text out of this page.
    # Scanned PDFs (photos of paper) have no real text, so extract_text()
    # can return None. "or ''" turns that into an empty string instead of crashing.
    text = page.extract_text() or ""

    # Save the text with its source and page number.
    # .strip() removes extra spaces and blank lines at the start and end.
    documents.append({
        "source": PDF_PATH,       # which file it came from
        "page": page_number,      # which page it came from
        "text": text.strip(),     # the actual words on the page
    })

# Print what we extracted, so we can check it looks right.
# Always look at your extracted text: this is where most RAG problems start.
for doc in documents:
    print(f"--- {doc['source']} | page {doc['page']} | {len(doc['text'])} characters ---")

    # Show only the first 300 characters of each page to keep the output short
    print(doc["text"][:300], "...\n")

# Things to notice in the output:
# 1. The footer ("Nimbus Retail India Pvt. Ltd. | ... | Page 1") repeats on
#    every page. It's noise that will end up in our search results later.
# 2. Tables lose their shape: each cell comes out on its own line, so
#    "Earned leave | 18 | Up to 10 days" turns into separate lines.
# We'll deal with both when we split the text into chunks in the next step.