"""
RAG Part 3: Chunking

So far: we loaded the PDF and extracted the text, page by page.
Now: we split that text into small, focused pieces called "chunks".

Why? A whole page mixes several topics (leave table, new joiners, applying
for leave...). Its embedding becomes a blurry average of all of them.
A small chunk is about ONE thing, so search can match it precisely.

Our method: split by section headings. Each section of the handbook
("3.1 Leave for new joiners", "4.2 Notice period"...) is one complete
topic, which makes it a perfect chunk.

Run:  pip install pypdf
"""

import re
from pypdf import PdfReader

PDF_PATH = "HR_Handbook.pdf"

# Chunks shorter than this are just a heading with no content
# (e.g. "2. Working Hours and Hybrid Work"). They add noise, so we skip them.
MIN_CHARS = 80


# ---------------------------------------------------------------------------
# STEP 1: Load and extract (same as the last lecture)
# ---------------------------------------------------------------------------
reader = PdfReader(PDF_PATH)
pages = []
for page_number, page in enumerate(reader.pages, start=1):
    pages.append({"page": page_number, "text": page.extract_text() or ""})


# ---------------------------------------------------------------------------
# STEP 2: Clean the text
# Last lecture we saw the footer repeated on every page. It's noise:
# if we keep it, it ends up inside every single chunk.
# ---------------------------------------------------------------------------
def clean_text(text):
    clean_lines = []
    for line in text.split("\n"):
        line = line.strip()

        # Skip the footer line, e.g. "Nimbus Retail India Pvt. Ltd. | Employee Handbook v3.2 | ..."
        if "Employee Handbook v3.2" in line:
            continue

        # Skip page-number lines, e.g. "Page 2"
        if re.fullmatch(r"Page \d+", line):
            continue

        # Skip empty lines
        if not line:
            continue

        clean_lines.append(line)
    return "\n".join(clean_lines)


# ---------------------------------------------------------------------------
# STEP 3: Split by section headings
# A heading looks like "3. Leave Policy" or "3.1 Leave for new joiners".
# We require the dot so table rows like "26 January" aren't mistaken for headings.
# ---------------------------------------------------------------------------
HEADING_PATTERN = re.compile(r"^(\d+\.\s+|\d+\.\d+\s+)[A-Z]")


def split_by_section(text):
    sections = []
    current_title = "Introduction"   # text before the first heading
    current_lines = []

    for line in text.split("\n"):
        if HEADING_PATTERN.match(line):
            # A new heading starts: save the section we were building
            if current_lines:
                sections.append((current_title, "\n".join(current_lines)))
            current_title = line
            current_lines = [line]   # keep the heading inside the chunk too
        else:
            current_lines.append(line)

    # Don't forget the last section on the page
    if current_lines:
        sections.append((current_title, "\n".join(current_lines)))
    return sections


# ---------------------------------------------------------------------------
# STEP 4: Build the chunks, keeping metadata
# Every chunk remembers its source, page and section, so the final answer
# can say "HR_Handbook.pdf, page 2, section 3.1".
# ---------------------------------------------------------------------------
chunks = []
for page in pages:
    text = clean_text(page["text"])

    for section_title, section_text in split_by_section(text):

        # Skip heading-only sections: nothing useful to search for
        if len(section_text) < MIN_CHARS:
            continue

        chunks.append({
            "id": len(chunks) + 1,
            "source": PDF_PATH,
            "page": page["page"],
            "section": section_title,
            "text": section_text,
        })


# ---------------------------------------------------------------------------
# STEP 5: Look at the result (always check your chunks!)
# ---------------------------------------------------------------------------
print(f"{len(pages)} pages  ->  {len(chunks)} chunks\n")

for chunk in chunks:
    print(f"[Chunk {chunk['id']}] page {chunk['page']} | {chunk['section']} | {len(chunk['text'])} chars")
    print(chunk["text"][:150].replace("\n", " "), "...\n")

# Next lecture: turn each chunk into an embedding and store it,
# so we can search the handbook by meaning.