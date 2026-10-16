"""
RAG Part 4: Embed, Store and Chat

So far: we loaded the PDF, cleaned it and split it into chunks (one per section).
Now:
  1. Turn every chunk into an embedding (a list of numbers that captures its meaning)
  2. Store the embeddings in ChromaDB, a vector database that lives in a local folder
  3. Retrieve: embed the user's question -> find the 3 closest chunks
  4. Augment:  put the question + those 3 chunks into one message
  5. Generate: the LLM answers using ONLY those chunks, remembering the chat history

Run:  pip install -r requirments.txt
Needs OPENAI_API_KEY in the .env file.
"""

import re
import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

PDF_PATH = "HR_Handbook.pdf"

# OpenAI's current recommended embedding model: cheap, fast, 1536 numbers per text
EMBEDDING_MODEL = "text-embedding-3-small"

# ChromaDB saves everything inside this folder, so it survives between runs
CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "hr_handbook"

# How many matching chunks to show for each question
TOP_K = 3

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


print(f"{len(pages)} pages  ->  {len(chunks)} chunks")


# ---------------------------------------------------------------------------
# STEP 5: Open (or create) the ChromaDB collection
# A "collection" is like a table: each row holds an id, the chunk text,
# its embedding and its metadata.
# "cosine" tells Chroma to compare embeddings with cosine distance,
# the same measure we used in the embeddings lecture.
# ---------------------------------------------------------------------------
load_dotenv()            # read OPENAI_API_KEY from .env (never hardcode the key)
openai_client = OpenAI()

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)


# ---------------------------------------------------------------------------
# STEP 6: Embed the chunks and store them
# Embeddings cost money (a tiny amount), so we only do this when the
# collection doesn't already have all our chunks.
# Delete the chroma_db folder if you change the chunking and want to rebuild.
# ---------------------------------------------------------------------------
if collection.count() == len(chunks):
    print(f"Collection already has {collection.count()} chunks, skipping embedding.")
else:
    print(f"Embedding {len(chunks)} chunks with {EMBEDDING_MODEL}...")

    # One API call for all chunks: we send a list of texts, we get back a list of embeddings
    texts = [chunk["text"] for chunk in chunks]
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    embeddings = [item.embedding for item in response.data]

    # upsert = insert, or overwrite if the id already exists (so no duplicates)
    collection.upsert(
        ids=[str(chunk["id"]) for chunk in chunks],     # Chroma wants ids as strings
        documents=texts,
        embeddings=embeddings,
        metadatas=[
            {"source": chunk["source"], "page": chunk["page"], "section": chunk["section"]}
            for chunk in chunks
        ],
    )
    print(f"Stored {collection.count()} chunks in ChromaDB ({CHROMA_PATH}/)")


# ---------------------------------------------------------------------------
# STEP 7: Retrieve - search by meaning
# The question goes through the SAME embedding model as the chunks,
# so both live in the same "meaning space" and can be compared.
# ---------------------------------------------------------------------------
def search(question):
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=question)
    question_embedding = response.data[0].embedding

    results = collection.query(query_embeddings=[question_embedding], n_results=TOP_K)

    # Chroma returns lists of lists (one list per question). We asked one question, so take [0].
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    # Put each match into a simple dictionary so it's easy to use later
    matches = []
    for text, meta, distance in zip(documents, metadatas, distances):
        matches.append({
            "text": text,
            "source": meta["source"],
            "page": meta["page"],
            "section": meta["section"],
            # Chroma gives a distance (0 = identical). Score = 1 - distance, so higher = better match.
            "score": 1 - distance,
        })
    return matches


# ---------------------------------------------------------------------------
# STEP 8: Augment - build the message for the LLM
# We paste the top chunks into the message, each labelled with its section
# and page, so the model can quote where the answer came from.
# ---------------------------------------------------------------------------
INSTRUCTIONS = """
You are the HR helpdesk assistant for Nimbus Retail India.
You answer employee questions using ONLY the handbook extracts given in each message.

Rules:
- Use only the facts in the extracts. Do not use outside knowledge and do not guess,
  because a wrong HR answer (wrong leave count, wrong expense rule) can cost the employee.
- If the extracts do not contain the answer, reply exactly:
  "I couldn't find that in the HR handbook. Please contact HR."
- End every answer with the section and page you used, e.g. (Section 3.1, page 2).
- Keep answers short and simple.
- You may use the earlier conversation to understand follow-up questions
  like "what about interns?", but the facts must still come from the extracts.
"""


def build_message(question, matches):
    context = ""
    for number, match in enumerate(matches, start=1):
        context += f"[Extract {number}] {match['section']} (page {match['page']})\n"
        context += match["text"] + "\n\n"

    return f"Handbook extracts:\n\n{context}Question: {question}"


# ---------------------------------------------------------------------------
# STEP 9: Generate - the chat loop
# Conversation history: like our Lecture 34 chatbot, we pass the id of the
# last response (previous_response_id), so the model sees the whole chat.
# ---------------------------------------------------------------------------
previous_id = None          # None = start a new conversation
previous_question = ""

print("\nHR Handbook Chatbot (type q to quit)")
while True:
    question = input("\nYou: ").strip()
    if question.lower() == "q":
        break
    if not question:
        continue

    # Follow-ups like "what about interns?" mean nothing on their own, so we
    # search with the previous question + this one to find the right chunks.
    search_text = f"{previous_question} {question}".strip()
    matches = search(search_text)

    # Show which chunks were retrieved (useful for checking the search works)
    print("\nRetrieved chunks:")
    for match in matches:
        print(f"  score {match['score']:.3f} | page {match['page']} | {match['section']}")

    response = openai_client.responses.create(
        model="gpt-6-luna",
        reasoning={"effort": "low"},
        # Instructions do NOT carry over from previous responses, so send them every time
        instructions=INSTRUCTIONS,
        input=build_message(question, matches),
        # Links this call to the last response, so the model remembers the chat
        previous_response_id=previous_id,
    )

    print(f"\nBot: {response.output_text}")

    # Remember this turn for the next one
    previous_id = response.id
    previous_question = question
