"""
Agents Part 3: Give the LLM tools

Steps 1-7 are our RAG pipeline from Lecture 39 (load, clean, chunk, embed, store, search).
New in this lecture: instead of always searching, the LLM gets TOOLS and decides itself
which one to use:
  1. calculator      - exact maths (LLMs are bad at arithmetic)
  2. joke_writer     - writes clean Indian jokes (a tool that calls another LLM)
  3. search_hr_docs  - our retrieval from step 7, wrapped as a tool

The agent loop: ask the LLM -> it requests a tool -> we run it -> send the result back
-> repeat until the LLM gives a final text answer.

Run:  pip install -r requirments.txt
Needs OPENAI_API_KEY in the .env file.
"""

import ast
import json
import operator
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
# STEP 8: The tools
# A tool is just a normal Python function. The LLM never runs it itself:
# it only ASKS us to run it (by name, with arguments). We run it and send
# the result back. Every tool returns a string.
# ---------------------------------------------------------------------------

# Tool 1: calculator
# LLMs are bad at exact arithmetic, so we let Python do the maths.
# Never use eval() on text from an LLM (it could run any code), so we parse
# the expression and only allow numbers and + - * / // % ** ( ).
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def evaluate(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left, right = evaluate(node.left), evaluate(node.right)
        # Stop things like 9 ** 9 ** 9 from freezing the program
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("exponent too large")
        return OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](evaluate(node.operand))
    raise ValueError("only numbers and + - * / // % ** ( ) are allowed")


def calculator(expression):
    try:
        result = evaluate(ast.parse(expression, mode="eval").body)
        return str(round(result, 4))
    except Exception as error:
        # Send the error back to the LLM so it can fix the expression and try again
        return f"Error: {error}"


# Tool 2: joke_writer
# A tool can call another LLM! It has its own instructions,
# so the main assistant doesn't need to know how to write jokes.
JOKE_INSTRUCTIONS = """
You write short, clean, family-friendly Indian jokes.
Use everyday Indian life: chai, cricket, traffic, Indian parents, Bollywood, office life, exams.
Never make fun of any religion, caste, region, gender or community.
Return only the joke, at most 5 lines.
"""


def joke_writer(topic):
    response = openai_client.responses.create(
        model="gpt-6-luna",
        reasoning={"effort": "low"},
        instructions=JOKE_INSTRUCTIONS,
        input=f"Write a joke about: {topic}",
    )
    return response.output_text


# Tool 3: search_hr_docs
# Our retrieval from STEP 7, wrapped as a tool.
# Before, we searched on EVERY question. Now the LLM decides WHEN to search
# and writes the query itself, so a follow-up like "what about interns?"
# becomes a full query like "leave policy for interns".
def search_hr_docs(query):
    matches = search(query)

    # Show which chunks were retrieved (useful for checking the search works)
    for match in matches:
        print(f"      score {match['score']:.3f} | page {match['page']} | {match['section']}")

    context = ""
    for number, match in enumerate(matches, start=1):
        context += f"[Extract {number}] {match['section']} (page {match['page']})\n"
        context += match["text"] + "\n\n"
    return context


# ---------------------------------------------------------------------------
# STEP 9: Describe the tools to the LLM
# The LLM never sees our Python code, only these descriptions. The name,
# description and parameters (a JSON schema) are how it decides which tool
# to call and what arguments to pass, so write them carefully.
# strict=True makes the model always send arguments that match the schema.
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "name": "calculator",
        "description": "Evaluate a maths expression exactly. Use this for ANY calculation, "
                       "e.g. leave balances, reimbursement totals, percentages.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A Python-style maths expression, e.g. '(24 - 7) * 1.5'",
                },
            },
            "required": ["expression"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "joke_writer",
        "description": "Write a short, clean Indian joke about a topic. Use when the user asks for a joke.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "What the joke should be about"},
            },
            "required": ["topic"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "search_hr_docs",
        "description": "Search the Nimbus Retail India HR handbook. Returns the most relevant "
                       "extracts with section and page. Use for ANY question about HR policy.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A complete, standalone search query, e.g. 'sick leave for interns'",
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

# Tool name (what the LLM asks for) -> Python function (what we run)
TOOL_FUNCTIONS = {
    "calculator": calculator,
    "joke_writer": joke_writer,
    "search_hr_docs": search_hr_docs,
}

INSTRUCTIONS = """
You are the HR helpdesk assistant for Nimbus Retail India. You have three tools:
- search_hr_docs: for any HR policy question. Policy facts must come ONLY from its extracts.
- calculator: for any arithmetic. Never do maths in your head.
- joke_writer: when the user asks for a joke.

Rules:
- Do not use outside knowledge for HR answers and do not guess,
  because a wrong HR answer (wrong leave count, wrong expense rule) can cost the employee.
- If the extracts do not contain the answer, reply exactly:
  "I couldn't find that in the HR handbook. Please contact HR."
- End every HR answer with the section and page you used, e.g. (Section 3.1, page 2).
- You can call several tools one after another (e.g. search, then calculate).
- Keep answers short and simple.
"""


# ---------------------------------------------------------------------------
# STEP 10: The agent loop
# 1. Send the question + tool descriptions to the LLM
# 2. If it replies with tool calls -> run them, send the results back, repeat
# 3. If it replies with plain text  -> that's the final answer
# ---------------------------------------------------------------------------
def ask_llm(input_items, previous_id):
    return openai_client.responses.create(
        model="gpt-6-luna",
        reasoning={"effort": "low"},
        # Instructions do NOT carry over from previous responses, so send them every time
        instructions=INSTRUCTIONS,
        tools=TOOLS,
        input=input_items,
        # Links this call to the last response, so the model remembers the chat
        previous_response_id=previous_id,
    )


MAX_STEPS = 10   # safety limit, so a confused model can't loop forever

previous_id = None   # None = start a new conversation

print("\nHR Agent (type q to quit)")
while True:
    question = input("\nYou: ").strip()
    if question.lower() == "q":
        break
    if not question:
        continue

    response = ask_llm(question, previous_id)

    for step in range(MAX_STEPS):
        tool_calls = [item for item in response.output if item.type == "function_call"]
        if not tool_calls:
            break   # no tool requested: the model has its final answer

        tool_outputs = []
        for call in tool_calls:
            arguments = json.loads(call.arguments)   # the LLM sends arguments as a JSON string
            print(f"  [tool] {call.name}({arguments})")

            result = TOOL_FUNCTIONS[call.name](**arguments)

            # call_id tells the LLM which of its requests this result answers
            tool_outputs.append({
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": result,
            })

        # Send only the tool results: previous_response_id carries the rest of the chat
        response = ask_llm(tool_outputs, response.id)

    print(f"\nBot: {response.output_text}")

    # Remember this turn for the next one
    previous_id = response.id
