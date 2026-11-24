"""
History Viewer
==============
Quick CLI to view a student's past study sessions.

Usage:
    python history.py
    python history.py --student_id alice
"""

import argparse
from tools import print_history


def main():
    parser = argparse.ArgumentParser(description="View study session history")
    parser.add_argument(
        "--student_id",
        type=str,
        default="default_student",
        help="Student ID to look up (default: 'default_student')",
    )
    args = parser.parse_args()
    print_history(args.student_id)


if __name__ == "__main__":
    main()
