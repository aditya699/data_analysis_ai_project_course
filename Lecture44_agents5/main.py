"""
Agents Part 5: Routing

A support desk gets all kinds of messages. One prompt that handles everything
gets long and messy. Instead we ROUTE each message to a specialist:

  ROUTER (LLM)      : read the customer message -> label it as
                      refund / delivery / technical / other
                      using STRUCTURED OUTPUT, so the label is always one of those 4 words
  SEND (Python)     : plain Python looks up the specialist for that label
  SPECIALIST (LLM)  : replies using its own short, focused instructions

The router only classifies. It never writes the reply.

Run:  pip install -r requirments.txt
Needs OPENAI_API_KEY in the .env file.
"""

from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

MODEL = "gpt-6-luna"

load_dotenv()
openai_client = OpenAI()


# ---------------------------------------------------------------------------
# The shape we want back from the router
# Literal means the model can ONLY answer with one of these 4 labels.
# ---------------------------------------------------------------------------
class Route(BaseModel):
    label: Literal["refund", "delivery", "technical", "other"]


# ---------------------------------------------------------------------------
# STEP 1: The router (structured output)
# ---------------------------------------------------------------------------
def route_message(message):
    response = openai_client.responses.parse(
        model=MODEL,
        instructions=(
            "You are the router for an online shoe store's support desk. "
            "Label the customer message with exactly one category:\n"
            "- refund: wants money back, a return or an exchange\n"
            "- delivery: order is late, missing, or has a shipping question\n"
            "- technical: problems with the website, app, login or payment page\n"
            "- other: anything else"
        ),
        input=message,
        text_format=Route,  # <- this is what makes it structured output
    )
    return response.output_parsed.label


# ---------------------------------------------------------------------------
# The specialists: each one only knows its own job
# ---------------------------------------------------------------------------
SPECIALISTS = {
    "refund": {
        "name": "Refund Specialist",
        "instructions": (
            "You handle refunds for an online shoe store. "
            "Policy: returns accepted within 30 days if the shoes are unworn. "
            "Refund goes to the original payment method in 5-7 working days. "
            "Offer an exchange for a different size as an option."
        ),
    },
    "delivery": {
        "name": "Delivery Specialist",
        "instructions": (
            "You handle delivery questions for an online shoe store. "
            "Normal delivery takes 3-5 working days. "
            "Apologise if it is late, ask for the order number, "
            "and promise to escalate to the courier within 24 hours."
        ),
    },
    "technical": {
        "name": "Technical Specialist",
        "instructions": (
            "You handle website and app problems for an online shoe store. "
            "Give simple step-by-step fixes: refresh, clear cache, update the app, "
            "try another browser. If that fails, ask for a screenshot."
        ),
    },
    "other": {
        "name": "General Support",
        "instructions": (
            "You are general support for an online shoe store. "
            "Answer politely. If you don't know, say a team member will reply soon."
        ),
    },
}


# ---------------------------------------------------------------------------
# STEP 2: The specialist writes the reply
# ---------------------------------------------------------------------------
def ask_specialist(label, message):
    specialist = SPECIALISTS[label]
    response = openai_client.responses.create(
        model=MODEL,
        instructions=specialist["instructions"]
        + " Keep the reply under 80 words. Plain text only, no markdown.",
        input=message,
    )
    return specialist["name"], response.output_text


# ---------------------------------------------------------------------------
# The full flow: router -> Python picks specialist -> specialist replies
# ---------------------------------------------------------------------------
def handle(message):
    print("=" * 70)
    print(f"CUSTOMER: {message}")

    label = route_message(message)
    print(f"ROUTER LABEL: {label}")

    name, reply = ask_specialist(label, message)
    print(f"REPLIED BY: {name}")
    print(f"\n{reply}\n")


test_messages = [
    "I want my money back, the shoes don't fit",
    "my order hasn't arrived in 10 days",
    "the app keeps crashing when I click on checkout",
    "do you have any stores in Pune?",
]

for message in test_messages:
    handle(message)
