"""
Agents Part 6: Parallelization

Screening a CV means checking several separate things. None of these checks
needs the answer of another one, so there is no reason to wait for them one
by one. We run them AT THE SAME TIME:

  SKILLS CHECK     (LLM) : which required skills does the CV have / miss?
  EXPERIENCE CHECK (LLM) : enough years? relevant roles?
  RED FLAGS CHECK  (LLM) : gaps, job hopping, vague claims?

Each check returns STRUCTURED OUTPUT, so we get clean fields, not free text.
asyncio.gather() is what runs the 3 calls in parallel.

Run:  pip install -r requirments.txt
Needs OPENAI_API_KEY in the .env file.
"""

import asyncio
import time

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel

MODEL = "gpt-6-luna"

load_dotenv()
# AsyncOpenAI = same client as before, but its calls can run side by side
openai_client = AsyncOpenAI()


# ---------------------------------------------------------------------------
# Sample job description and CV
# ---------------------------------------------------------------------------
JOB_DESCRIPTION = """
Job: Data Analyst (Mid level), Bengaluru
Required skills: Python, SQL, Pandas, Power BI or Tableau, Statistics
Nice to have: Machine Learning basics, Excel, communication with business teams
Experience: at least 3 years as a data analyst or in a similar role
"""

CV = """
Name: Rohan Mehta
Summary: Data analyst who loves turning messy data into clear dashboards.

Experience:
- Data Analyst, FreshCart (Jan 2023 - present)
  Built SQL reports and Power BI dashboards for the sales team.
  Automated weekly Excel reports with Python and Pandas.
- Junior Analyst, QuickLoans (Mar 2022 - Nov 2022)
  Cleaned loan data in Excel. Helped with monthly reports.
- Intern, StartupX (Jun 2021 - Aug 2021)
  "Worked on many AI projects."
- No job listed between Aug 2021 and Mar 2022.

Skills: Python, Pandas, SQL, Power BI, Excel, communication
Education: B.Com, Delhi University (2021)
"""


# ---------------------------------------------------------------------------
# The shapes we want back: one per check
# ---------------------------------------------------------------------------
class SkillsResult(BaseModel):
    matched_skills: list[str]
    missing_skills: list[str]
    score: int  # 0 to 10


class ExperienceResult(BaseModel):
    total_years: float
    relevant_roles: list[str]
    meets_requirement: bool
    score: int  # 0 to 10


class RedFlagsResult(BaseModel):
    red_flags: list[str]
    severity: str  # "none", "low", "medium" or "high"


# ---------------------------------------------------------------------------
# One helper that every check uses
# Same as responses.parse() before, just with "await" in front.
# ---------------------------------------------------------------------------
async def run_check(name, instructions, result_shape):
    print(f"  started:  {name}")
    response = await openai_client.responses.parse(
        model=MODEL,
        instructions=instructions,
        input=f"JOB DESCRIPTION:\n{JOB_DESCRIPTION}\n\nCV:\n{CV}",
        text_format=result_shape,  # <- structured output
    )
    print(f"  finished: {name}")
    return response.output_parsed


# ---------------------------------------------------------------------------
# The 3 checks: each one only looks at its own thing
# ---------------------------------------------------------------------------
def check_skills():
    return run_check(
        "skills check",
        "You compare a CV with a job description. "
        "Only look at skills, not experience. "
        "List the required skills the CV clearly has and the ones it is missing. "
        "Use short skill names only, like 'SQL'. "
        "Give a score from 0 to 10 for how well the skills match.",
        SkillsResult,
    )


def check_experience():
    return run_check(
        "experience check",
        "You check work experience in a CV against a job description. "
        "Add up the total years of work (internships count as 0). "
        "List the roles that are relevant to the job. "
        "Say if the experience requirement is met, and give a score from 0 to 10.",
        ExperienceResult,
    )


def check_red_flags():
    return run_check(
        "red flags check",
        "You look for red flags in a CV: unexplained gaps, very short jobs, "
        "vague claims with no details, or anything that does not add up. "
        "Keep each red flag to one short sentence. "
        "Set severity to exactly one of: none, low, medium, high.",
        RedFlagsResult,
    )


# ---------------------------------------------------------------------------
# PARALLEL: start all 3 checks together and wait until all are done
# ---------------------------------------------------------------------------
async def screen_cv():
    start = time.time()

    skills, experience, red_flags = await asyncio.gather(
        check_skills(),
        check_experience(),
        check_red_flags(),
    )

    print(f"\nAll 3 checks done in {time.time() - start:.1f} seconds\n")
    return skills, experience, red_flags


def print_report(skills, experience, red_flags):
    print("=" * 70)
    print("SKILLS")
    print(f"  matched: {', '.join(skills.matched_skills)}")
    print(f"  missing: {', '.join(skills.missing_skills) or 'nothing'}")
    print(f"  score:   {skills.score}/10")

    print("\nEXPERIENCE")
    print(f"  total years:    {experience.total_years}")
    print(f"  relevant roles: {', '.join(experience.relevant_roles)}")
    print(f"  meets 3 years:  {experience.meets_requirement}")
    print(f"  score:          {experience.score}/10")

    print("\nRED FLAGS")
    for flag in red_flags.red_flags:
        print(f"  - {flag}")
    print(f"  severity: {red_flags.severity}")

    print("=" * 70)


print("Running 3 checks in parallel...\n")
skills, experience, red_flags = asyncio.run(screen_cv())
print_report(skills, experience, red_flags)
