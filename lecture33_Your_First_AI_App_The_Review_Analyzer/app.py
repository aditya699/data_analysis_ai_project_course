# Review Analyzer: paste a customer review, get structured data back.

from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

# Load OPENAI_API_KEY from the .env file (never hardcode the key)
load_dotenv()

client = OpenAI()


# The exact shape we want back. Literal means the model can ONLY use these values.
class ReviewAnalysis(BaseModel):
    sentiment: Literal["positive", "neutral", "negative"]
    topic: Literal["delivery", "quality", "price", "packaging", "other"]
    urgency: Literal["low", "medium", "high"]
    summary: str
    suggested_reply: str


# Instructions tell the model HOW to behave. Rules come with a reason.
INSTRUCTIONS = """
You analyze customer reviews for OrderIQ, an Indian online store.

For each review, decide:
- sentiment: positive, neutral or negative.
- topic: the main thing the review is about (delivery, quality, price, packaging or other).
- urgency: low, medium or high.
  Urgency is high when the item arrived damaged or wrong, because those customers
  need a refund or replacement quickly.
- summary: one sentence describing the review.
- suggested_reply: a short, polite reply to the customer from the OrderIQ team.
"""

print("Review Analyzer (type q to quit)")

while True:
    review = input("\nPaste a review: ").strip()

    if review.lower() == "q":
        print("Bye!")
        break
    if not review:
        continue

    # responses.parse() turns our Pydantic class into a JSON schema,
    # forces the model to follow it, and parses the answer back for us.
    response = client.responses.parse(
        model="gpt-6-luna",
        reasoning={"effort": "low"},
        instructions=INSTRUCTIONS,
        input=review,
        text_format=ReviewAnalysis,
    )

    result = response.output_parsed

    # output_parsed is None if the model refused to answer
    if result is None:
        print("Sorry, the model could not analyze that review.")
        continue

    # Print each field on its own line
    print(f"Sentiment:       {result.sentiment}")
    print(f"Topic:           {result.topic}")
    print(f"Urgency:         {result.urgency}")
    print(f"Summary:         {result.summary}")
    print(f"Suggested reply: {result.suggested_reply}")

    # Then the full result as JSON
    print(result.model_dump_json(indent=2))
