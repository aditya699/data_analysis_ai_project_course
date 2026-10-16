"""
Agents Part 7: Built-in Multi-agent (OpenAI Responses API, beta)

In Part 6 WE wrote the parallel code ourselves with asyncio.gather().
Here the MODEL does the orchestration for us:

  /root               : reads the question, decides how to split it
  ├── /root/<role 1>  : researches one career role
  ├── /root/<role 2>  : researches another role
  └── /root/<role 3>  : ...
  /root               : collects their answers -> comparison table + recommendation

We only switch on multi_agent and stream the events. The API spawns the
subagents, runs them in parallel and passes their answers back to /root.

Run:  pip install -r requirments.txt
Needs OPENAI_API_KEY in the .env file.
"""

import json
import time

from dotenv import load_dotenv
from openai import OpenAI

MODEL = "gpt-6.1-sol"  # Multi-agent works with GPT-6.1 Sol and GPT-5.6 models
ROOT = "/root"

load_dotenv()
client = OpenAI()


# ---------------------------------------------------------------------------
# Extra instructions for the root agent (added on top of OpenAI's own
# multi-agent instructions). This is where we say HOW to split the work.
# ---------------------------------------------------------------------------
DEVELOPER_MESSAGE = """
You are a career guide for students in India.
When the user asks to compare career roles:
1. Spawn exactly ONE subagent per role. Name each subagent after its role,
   for example "data_analyst".
2. Tell each subagent to cover, for a fresher in India: key skills, main tools,
   a typical day of work, and how AI is changing that role.
   Each subagent should answer in short bullet points (max 150 words).
3. Wait for all subagents, then write the final answer yourself:
   - one markdown comparison table (rows = skills, tools, daily work, AI impact;
     one column per role)
   - a short recommendation (3-4 sentences) for the person the user describes.
"""

QUESTION = (
    "Compare data analyst, data engineer and AI engineer for a fresher in India: "
    "skills, tools, daily work and how AI is changing each role, then recommend "
    "one for someone who likes SQL but wants to work with AI."
)


# ---------------------------------------------------------------------------
# Start ONE streaming request with multi-agent switched on
# ---------------------------------------------------------------------------
def compare_careers(question):
    stream = client.beta.responses.create(
        model=MODEL,
        input=[
            {"role": "developer", "content": DEVELOPER_MESSAGE},
            {"role": "user", "content": question},
        ],
        multi_agent={
            "enabled": True,
            "max_concurrent_subagents": 3,  # one per role, all at the same time
        },
        stream=True,
        betas=["responses_multi_agent=v1"],
    )

    item_agents = {}  # output_index -> which agent wrote that item
    lines = {}        # agent -> text of its current (unfinished) line
    final_answer = ""

    for event in stream:
        # A new output item started: remember which agent it belongs to
        if event.type == "response.output_item.added":
            agent = event.item.agent.agent_name if event.item.agent else ROOT
            item_agents[event.output_index] = agent

        # A piece of text arrived
        elif event.type == "response.output_text.delta":
            agent = item_agents.get(event.output_index, ROOT)

            if agent == ROOT:
                # keep the root's text and print it at the end
                final_answer += event.delta
                continue

            # Subagent text: the 3 subagents write at the same time, so their
            # pieces arrive mixed up. We collect each agent's text and print
            # it one full line at a time, labelled with the agent's name.
            lines[agent] = lines.get(agent, "") + event.delta
            while "\n" in lines[agent]:
                line, lines[agent] = lines[agent].split("\n", 1)
                if line.strip():
                    print(f"[{agent}] {line}", flush=True)

        # An item finished
        elif event.type == "response.output_item.done":
            item = event.item
            agent = item_agents.get(event.output_index, ROOT)

            # print whatever is left of a subagent's last line
            if lines.get(agent, "").strip():
                print(f"[{agent}] {lines[agent]}", flush=True)
            lines[agent] = ""

            # show when /root spawns a subagent
            if item.type == "multi_agent_call_output" and item.action == "spawn_agent":
                spawned = json.loads(item.output[0].text)["task_name"]
                print(f">> {item.agent.agent_name} spawned {spawned}")

        elif event.type == "response.completed":
            print(f"\nTokens used: {event.response.usage.total_tokens}")

        elif event.type in ("error", "response.failed", "response.incomplete"):
            raise RuntimeError(event)

    return final_answer


print(f"QUESTION: {QUESTION}\n")
start = time.time()
answer = compare_careers(QUESTION)
print(f"Finished in {time.time() - start:.1f} seconds")

print("\n" + "=" * 70)
print("[/root] FINAL COMPARISON AND RECOMMENDATION")
print("=" * 70)
print(answer)
