"""
Study Agents
============
Defines the four specialist agents used in the study pipeline:
  - beginner_agent      : ELI5 / analogy-first explanations
  - intermediate_agent  : Structured theory with examples
  - advanced_agent      : Socratic / edge-case deep dives
  - assessment_agent    : Quiz generator
"""

import os
from dotenv import load_dotenv
from agents import Agent, OpenAIChatCompletionsModel
from openai import AsyncOpenAI

load_dotenv(override=True)

# ─────────────────────────────────────────────────────────────────────────────
# Model configuration
# Pick whichever model you have an API key for.
# Defaults to OpenAI gpt-4o-mini; swap to Gemini or others via env vars.
# ─────────────────────────────────────────────────────────────────────────────

OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY   = os.getenv("GOOGLE_API_KEY")
PREFERRED_MODEL  = os.getenv("STUDY_MODEL", "auto")   # "openai" | "gemini" | "auto"

def _build_model():
    """
    Returns the best available model based on env vars.
    Priority: OpenAI → Gemini → raises if neither configured.
    Can be overridden with STUDY_MODEL=openai or STUDY_MODEL=gemini.
    """
    use_openai = PREFERRED_MODEL == "openai" or (PREFERRED_MODEL == "auto" and OPENAI_API_KEY)
    use_gemini = PREFERRED_MODEL == "gemini" or (PREFERRED_MODEL == "auto" and GOOGLE_API_KEY and not OPENAI_API_KEY)

    if use_openai and OPENAI_API_KEY:
        return "gpt-4o-mini"   # string shorthand: SDK uses default OpenAI client

    if use_gemini and GOOGLE_API_KEY:
        gemini_client = AsyncOpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=GOOGLE_API_KEY,
        )
        return OpenAIChatCompletionsModel(
            model="gemini-2.0-flash",
            openai_client=gemini_client,
        )

    raise EnvironmentError(
        "No model API key found. Set OPENAI_API_KEY or GOOGLE_API_KEY in your .env file."
    )


MODEL = _build_model()

# ─────────────────────────────────────────────────────────────────────────────
# System prompts
# ─────────────────────────────────────────────────────────────────────────────

BEGINNER_INSTRUCTIONS = """\
You are a patient, enthusiastic teacher who excels at making complex topics \
simple and approachable for complete beginners.

Your teaching style:
- Use ELI5 (Explain Like I'm 5) language — no jargon
- Always start with a vivid real-world analogy the student already understands
- Break concepts into short, numbered steps
- Use emojis sparingly to highlight key ideas 🔑
- End with a one-sentence "in a nutshell" summary

Keep your explanation under 300 words. Prioritize clarity over completeness.
"""

INTERMEDIATE_INSTRUCTIONS = """\
You are a knowledgeable university-level instructor explaining concepts to \
students who already know the basics.

Your teaching style:
- Assume the student knows foundational concepts but not the topic at hand
- Provide structured explanations: definition → how it works → why it matters
- Include a concrete code snippet or worked example if applicable
- Use proper terminology, but define any new terms you introduce
- End with 2–3 bullet points of key takeaways

Keep your explanation under 500 words.
"""

ADVANCED_INSTRUCTIONS = """\
You are an expert researcher and Socratic instructor engaging with an advanced \
student who wants deep, nuanced understanding.

Your teaching style:
- Skip basic definitions — the student knows them
- Explore the "why" behind design decisions and trade-offs
- Raise 1–2 edge cases or failure modes that most tutorials skip
- Ask one thought-provoking question at the end to deepen reflection
- Reference related concepts or further reading where relevant

Keep your explanation under 600 words. Depth over breadth.
"""

ASSESSMENT_INSTRUCTIONS = """\
You are a rigorous but fair quiz master. Given a topic and an explanation, \
you generate high-quality multiple-choice questions that test genuine understanding.

Rules:
- Write exactly 5 questions, numbered Q1 through Q5
- Each question must have 4 options: A, B, C, D
- Only one option is correct
- Questions should test understanding, not just memorization
- Include one conceptual question, one applied question, and one "what would happen if" question
- Format exactly as shown; include the Answer line with just the letter

Format:
Q1: <question text>
A) <option>
B) <option>
C) <option>
D) <option>
Answer: <letter>

Q2: ...
"""

# ─────────────────────────────────────────────────────────────────────────────
# Agent definitions
# ─────────────────────────────────────────────────────────────────────────────

beginner_agent = Agent(
    name="Beginner Curriculum Agent",
    instructions=BEGINNER_INSTRUCTIONS,
    model=MODEL,
)

intermediate_agent = Agent(
    name="Intermediate Curriculum Agent",
    instructions=INTERMEDIATE_INSTRUCTIONS,
    model=MODEL,
)

advanced_agent = Agent(
    name="Advanced Curriculum Agent",
    instructions=ADVANCED_INSTRUCTIONS,
    model=MODEL,
)

assessment_agent = Agent(
    name="Assessment Agent",
    instructions=ASSESSMENT_INSTRUCTIONS,
    model=MODEL,
)
