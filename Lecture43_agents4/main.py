"""
Agents Part 4: Prompt chaining

Instead of one giant prompt, we split the job into small steps.
The output of one step becomes the input of the next:

  STEP 1 (LLM)    : read messy meeting notes -> pull out action items (owner, task, deadline)
                    using STRUCTURED OUTPUT, so we get clean Python objects, not free text
  GATE (Python)   : no action items? stop here. No point writing an email about nothing.
  STEP 2 (LLM)    : turn the action items into a short follow-up email

The gate is plain Python - no LLM needed to check if a list is empty.

Run:  pip install -r requirments.txt
Needs OPENAI_API_KEY in the .env file.
"""

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

MODEL = "gpt-6-luna"

load_dotenv()
openai_client = OpenAI()


# ---------------------------------------------------------------------------
# Sample meeting notes
# ---------------------------------------------------------------------------
NOTES_WITH_ACTIONS = """
weekly sync - tues
ppl: priya, rahul, ankit, me (neha)
- dashboard still slow?? rahul thinks its the orders query. he'll look into it by thurs
- priya: client deck for nimbus retail, needs to go out before friday EOD
- talked abt diwali offsite, no decision yet
- ankit to fix the dup rows in customers table... said "early next week"
- coffee machine broken again lol
"""

NOTES_WITHOUT_ACTIONS = """
friday catch-up
ppl: priya, rahul, ankit
- everyone shared weekend plans
- rahul showed pics from his trip to manali, looked amazing
- quick chat about the new cricket season
- nothing urgent this week, all good
"""


# ---------------------------------------------------------------------------
# The shape we want back from step 1
# Pydantic classes describe the structure. The API forces the LLM to follow it.
# ---------------------------------------------------------------------------
class ActionItem(BaseModel):
    owner: str
    task: str
    deadline: str  # free text like "Thursday" or "not mentioned"


class ActionItems(BaseModel):
    items: list[ActionItem]


# ---------------------------------------------------------------------------
# STEP 1: Extract action items (structured output)
# ---------------------------------------------------------------------------
def extract_action_items(notes):
    response = openai_client.responses.parse(
        model=MODEL,
        instructions=(
            "You extract action items from meeting notes. "
            "An action item is a specific task that a specific person agreed to do. "
            "Discussions, updates and undecided topics are NOT action items. "
            "If no deadline is given, write 'not mentioned'. "
            "If there are no action items, return an empty list."
        ),
        input=notes,
        text_format=ActionItems,  # <- this is what makes it structured output
    )
    # output_parsed is already an ActionItems object, not a string
    return response.output_parsed.items


# ---------------------------------------------------------------------------
# STEP 2: Write the follow-up email
# ---------------------------------------------------------------------------
def write_follow_up_email(items):
    # Turn the Python objects back into simple text for the next prompt
    items_text = "\n".join(
        f"- {item.owner}: {item.task} (deadline: {item.deadline})" for item in items
    )

    response = openai_client.responses.create(
        model=MODEL,
        instructions=(
            "Write a short, friendly follow-up email after a team meeting. "
            "Include a subject line. List each action item with its owner and deadline. "
            "Keep it under 150 words. Sign off as Neha."
        ),
        input=items_text,
    )
    return response.output_text


# ---------------------------------------------------------------------------
# The chain: step 1 -> gate -> step 2
# ---------------------------------------------------------------------------
def run_chain(notes):
    print("=" * 70)
    print("INPUT: meeting notes")
    print("=" * 70)
    print(notes.strip())

    # STEP 1
    print("\n--- STEP 1: extract action items ---")
    items = extract_action_items(notes)
    print(f"Found {len(items)} action item(s):")
    for item in items:
        print(f"  owner={item.owner!r}  task={item.task!r}  deadline={item.deadline!r}")

    # GATE
    print("\n--- GATE: any action items? ---")
    if not items:
        print("No action items -> stopping the chain. Step 2 is skipped.\n")
        return None
    print("Yes -> continue to step 2")

    # STEP 2
    print("\n--- STEP 2: write follow-up email ---")
    email = write_follow_up_email(items)
    print(email)
    print()
    return email


run_chain(NOTES_WITH_ACTIONS)
run_chain(NOTES_WITHOUT_ACTIONS)
