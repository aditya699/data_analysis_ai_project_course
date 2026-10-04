# Review Chatbot: paste a customer review, then ask follow-up questions about it.
# The model remembers the conversation using previous_response_id.

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

# Starts empty. After each turn we store the id of the model's last response here.
previous_id = None

print("Review Chatbot (type q to quit)")
print("Paste a review, then ask follow-up questions about it.")

while True:
    user_message = input("\nYou: ").strip()

    if user_message.lower() == "q":
        print("Bye!")
        break
    if not user_message:
        continue

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
