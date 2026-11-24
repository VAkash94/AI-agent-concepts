"""
Personalized Study Plan & Quiz Agent
======================================
Multi-agent system built with the OpenAI Agents SDK.

Architecture:
  - 3 Curriculum Agents run in parallel (Beginner / Intermediate / Advanced)
  - Student picks their preferred level
  - Assessment Agent generates a 5-question quiz for the chosen explanation
  - Results persisted to SQLite via function_tool
  - Full traces via OpenAI Traces (platform.openai.com/traces)

Usage:
    python main.py
    python main.py --topic "explain transformers" --student_id "alice"
"""

import asyncio
import argparse
import os
from dotenv import load_dotenv

from agents import Runner, trace
from agents.memory import SQLiteSession

from study_agents import (
    beginner_agent,
    intermediate_agent,
    advanced_agent,
    assessment_agent,
)
from tools import save_progress

load_dotenv(override=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def pick_level() -> str:
    """Interactive level picker."""
    print("\n📚 Choose your learning level:")
    print("  [1] Beginner    — ELI5 analogies, no jargon")
    print("  [2] Intermediate — Structured theory, examples")
    print("  [3] Advanced    — Socratic questioning, edge cases")
    while True:
        choice = input("\nEnter 1, 2, or 3: ").strip()
        if choice in ("1", "2", "3"):
            return {"1": "beginner", "2": "intermediate", "3": "advanced"}[choice]
        print("Please enter 1, 2, or 3.")


def print_divider(title: str = ""):
    width = 70
    if title:
        pad = (width - len(title) - 2) // 2
        print("\n" + "─" * pad + f" {title} " + "─" * pad + "\n")
    else:
        print("\n" + "─" * width + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Core pipeline
# ─────────────────────────────────────────────────────────────────────────────

async def run_study_session(topic: str, student_id: str):
    """
    Full pipeline:
      1. Run all 3 curriculum agents in parallel
      2. Present explanations and let the student choose
      3. Run assessment agent to generate a quiz
      4. Grade the student interactively
      5. Persist progress to SQLite
    """

    print_divider("STUDY SESSION START")
    print(f"📖 Topic      : {topic}")
    print(f"👤 Student ID : {student_id}")

    # ── Step 1: Parallel curriculum generation ────────────────────────────────
    print_divider("Generating explanations (all 3 levels in parallel)...")

    with trace("Study Session - Parallel Curriculum"):
        results = await asyncio.gather(
            Runner.run(beginner_agent,      f"Explain the following topic: {topic}"),
            Runner.run(intermediate_agent,  f"Explain the following topic: {topic}"),
            Runner.run(advanced_agent,      f"Explain the following topic: {topic}"),
        )

    explanations = {
        "beginner":     results[0].final_output,
        "intermediate": results[1].final_output,
        "advanced":     results[2].final_output,
    }

    # ── Step 2: Show all three & let student pick ─────────────────────────────
    labels = {
        "beginner":     "🟢 BEGINNER — ELI5 Style",
        "intermediate": "🟡 INTERMEDIATE — Structured Theory",
        "advanced":     "🔴 ADVANCED — Deep Dive",
    }

    for level, label in labels.items():
        print_divider(label)
        print(explanations[level])

    chosen_level = pick_level()
    chosen_explanation = explanations[chosen_level]

    print_divider(f"You chose: {labels[chosen_level]}")
    print("Great! Generating your quiz now...\n")

    # ── Step 3: Assessment agent generates quiz ───────────────────────────────
    quiz_prompt = f"""
Topic: {topic}
Explanation used:
{chosen_explanation}

Generate a 5-question multiple-choice quiz based on the explanation above.
Format each question exactly like this:

Q1: <question>
A) <option>
B) <option>
C) <option>
D) <option>
Answer: <letter>

Q2: ...
"""

    with trace("Study Session - Quiz Generation"):
        quiz_result = await Runner.run(assessment_agent, quiz_prompt)

    quiz_text = quiz_result.final_output
    print_divider("YOUR QUIZ")
    print(quiz_text)

    # ── Step 4: Interactive grading ───────────────────────────────────────────
    score = grade_quiz(quiz_text)

    # ── Step 5: Save progress ─────────────────────────────────────────────────
    save_progress(
        student_id=student_id,
        topic=topic,
        level_chosen=chosen_level,
        score=score,
    )

    print_divider("SESSION COMPLETE")
    print(f"✅ Score: {score}/5")
    print(f"💾 Progress saved for student '{student_id}'")
    print(f"📊 View your history: check study_progress.db\n")

    return score


def grade_quiz(quiz_text: str) -> int:
    """
    Parse answer keys from the quiz text and prompt the student
    to answer each question. Returns number correct out of 5.
    """
    import re
    answers = re.findall(r"Answer:\s*([A-D])", quiz_text, re.IGNORECASE)

    if not answers:
        print("⚠️  Could not parse answer keys from quiz — skipping grading.")
        return 0

    print_divider("ANSWER YOUR QUIZ")
    print("Enter A, B, C, or D for each question:\n")

    score = 0
    for i, correct in enumerate(answers[:5], 1):
        while True:
            user_ans = input(f"Q{i}: ").strip().upper()
            if user_ans in ("A", "B", "C", "D"):
                break
            print("  Please enter A, B, C, or D.")
        if user_ans == correct.upper():
            print("  ✅ Correct!\n")
            score += 1
        else:
            print(f"  ❌ Incorrect. Correct answer: {correct.upper()}\n")

    return score


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Personalized Study Plan & Quiz Agent"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Topic to study (e.g. 'explain LSTMs'). Prompted if omitted.",
    )
    parser.add_argument(
        "--student_id",
        type=str,
        default="default_student",
        help="Unique student identifier for progress tracking.",
    )
    args = parser.parse_args()

    topic = args.topic
    if not topic:
        print("\n🎓 Personalized Study Plan & Quiz Agent")
        print("=" * 45)
        topic = input("What topic would you like to study? > ").strip()
        if not topic:
            topic = "explain how neural networks learn"

    asyncio.run(run_study_session(topic=topic, student_id=args.student_id))


if __name__ == "__main__":
    main()
