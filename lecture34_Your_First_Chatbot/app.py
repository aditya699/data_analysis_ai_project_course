# Review Chatbot: paste a customer review, then ask follow-up questions about it.
# The model remembers the conversation using previous_response_id.
# Bonus: every message is also turned into an embedding so we can see what one looks like.

import math

from dotenv import load_dotenv
from openai import OpenAI

# Load OPENAI_API_KEY from the .env file (never hardcode the key)
load_dotenv()

client = OpenAI()

# Instructions tell the model HOW to behave. Rules come with a reason.
INSTRUCTIONS = """
You are a helpful assistant for the OrderIQ support team. OrderIQ is an Indian online store.

When the user pastes a customer review, analyze it and answer in exactly this format:
Sentiment: positive, neutral or negative
Topic: delivery, quality, price, packaging or other
Urgency: low, medium or high
Summary: one sentence describing the review
Suggested reply: a short, polite reply to the customer from the OrderIQ team

Urgency is high when the item arrived damaged or wrong, because those customers
need a refund or replacement quickly.

When the user asks a follow-up question (for example "make the reply more formal"),
answer it using the conversation so far. Keep answers short.
"""


def get_embedding(text):
    # An embedding is a list of numbers that captures the MEANING of the text.
    # Texts with similar meaning get similar lists of numbers.
    result = client.embeddings.create(model="text-embedding-3-small", input=text)
    return result.data[0].embedding


def cosine_similarity(a, b):
    # cos(A, B) = (A · B) / (|A| × |B|)
    dot = sum(x * y for x, y in zip(a, b))          # A · B : multiply pairs, add them up
    length_a = math.sqrt(sum(x * x for x in a))     # |A|   : length of vector A
    length_b = math.sqrt(sum(y * y for y in b))     # |B|   : length of vector B
    return dot, length_a, length_b, dot / (length_a * length_b)


# Starts empty. After each turn we store the id of the model's last response here.
previous_id = None

# The embedding of the previous message, so we can compare it with the new one
previous_embedding = None
previous_message = None

print("Review Chatbot (type q to quit)")
print("Paste a review, then ask follow-up questions about it.")

while True:
    user_message = input("\nYou: ").strip()

    if user_message.lower() == "q":
        print("Bye!")
        break
    if not user_message:
        continue

    # --- Embedding demo -------------------------------------------------
    embedding = get_embedding(user_message)
    print(f"\nEmbedding: {len(embedding)} numbers. First 8:")
    print([round(x, 4) for x in embedding[:8]], "...")

    # Compare this message with the previous one
    if previous_embedding is not None:
        dot, length_a, length_b, similarity = cosine_similarity(previous_embedding, embedding)
        print("\nCosine similarity with your previous message:")
        print(f'  A = "{previous_message}"')
        print(f'  B = "{user_message}"')
        print("  cos(A, B) = (A · B) / (|A| × |B|)")
        print(f"            = {dot:.4f} / ({length_a:.4f} × {length_b:.4f})")
        print(f"            = {similarity:.4f}   (closer to 1 = more similar meaning)")

    previous_embedding = embedding
    previous_message = user_message
    # ---------------------------------------------------------------------

    response = client.responses.create(
        model="gpt-6-luna",
        reasoning={"effort": "low"},
        # Instructions do NOT carry over from previous responses, so send them every time
        instructions=INSTRUCTIONS,
        input=user_message,
        # This links the call to the last response, so the model sees the whole chat history.
        # On the first turn it is None, which means "start a new conversation".
        previous_response_id=previous_id,
    )

    print(f"\nBot: {response.output_text}")

    # Input tokens grow each turn because the whole history is sent to the model again
    print(f"\n(input tokens this turn: {response.usage.input_tokens})")

    # Remember this response so the next turn continues the same conversation
    previous_id = response.id
