from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

topic = input("What should the story be about? ")

response = client.responses.create(
    model="gpt-6-luna",
    reasoning={"effort": "low"},
    instructions="Talk like a Funny Person.",
    input=f"Write a short story on {topic}",
)

print(response.output_text)
