#!/usr/bin/env python3
"""Hands-on terminal practice for macOS and Linux. Requires only Python 3."""

import random
import secrets
import shlex
import tempfile
from pathlib import Path


def make_lab(parent=None):
    root = Path(tempfile.mkdtemp(prefix="terminal-practice-", dir=parent)).resolve()
    for directory in ("docs", "archive/old", "evidence/session", "inbox"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    code = secrets.token_hex(3)
    username = random.choice(["morgan", "alex", "jamie", "casey"])
    (root / "briefing.txt").write_text(
        "Welcome to your terminal practice lab.\n"
        "All exercises use the files in this folder.\n"
        "Training code: {}\n".format(code), encoding="utf-8")
    (root / ".access-note").write_text("Hidden files often start with a dot.\n", encoding="utf-8")
    location = random.choice(["docs", "archive/old", "evidence/session"])
    incident = root / location / "incident-note.txt"
    incident.write_text("A fictional incident note for file-search practice.\n", encoding="utf-8")
    (root / "docs" / "readme.md").write_text("Practice files only.\n", encoding="utf-8")
    (root / "inbox" / "draft.txt").write_text("Fictional incident report draft.\n", encoding="utf-8")
    (root / "evidence" / "login.log").write_text(
        "08:00 INFO service started\n"
        "08:01 LOGIN_OK user=robin\n"
        "08:02 INFO session opened\n"
        "08:03 LOGIN_FAILED user={}\n"
        "08:04 LOGIN_OK user=taylor\n"
        "08:05 INFO session closed\n"
        "08:06 INFO service stopped\n".format(username), encoding="utf-8")
    return root, code, username, incident


def same_path(answer, target, root):
    try:
        candidate = Path(answer.strip())
        if not candidate.is_absolute():
            candidate = root / candidate
        return candidate.resolve() == target.resolve()
    except (OSError, ValueError):
        return False


def same_contents(source, target):
    try:
        return target.is_file() and target.read_bytes() == source.read_bytes()
    except OSError:
        return False


def build_tasks(root, code, username, incident):
    return [
        {
            "title": "Find your current location",
            "goal": "In your practice terminal, print the current directory. Paste the resulting path here.",
            "check": lambda answer: same_path(answer, root, root) and answer.strip().startswith("/"),
            "hints": ["Use the command whose name means 'print working directory'.", "Run: pwd"],
            "explain": "pwd prints your current directory. Relative paths are interpreted from that location.",
        },
        {
            "title": "List files",
            "goal": "List the contents of the lab's top-level folder. Enter the name of the .txt file there.",
            "check": lambda answer: answer.strip() == "briefing.txt",
            "hints": ["The short command for listing directory contents is ls.", "Run: ls"],
            "explain": "ls lists directory entries. With no path supplied, it lists your current directory.",
        },
        {
            "title": "Read a file",
            "goal": "Read briefing.txt in the terminal. Enter its training code (just the code).",
            "check": lambda answer: answer.strip() == code,
            "hints": ["cat can print a text file's contents.", "Run: cat briefing.txt"],
            "explain": "cat briefing.txt prints this small text file so you can inspect its contents.",
        },
        {
            "title": "Find a hidden file",
            "goal": "List hidden entries in the top-level folder. Enter the hidden filename, excluding . and .. .",
            "check": lambda answer: answer.strip() == ".access-note",
            "hints": ["ls has an option that includes entries starting with a dot.", "Run: ls -a"],
            "explain": "ls -a includes hidden entries. A leading dot hides a file from ordinary ls output; it does not secure it.",
        },
        {
            "title": "Search for a file",
            "goal": "Find incident-note.txt somewhere under the lab folder. Enter its relative or absolute path.",
            "check": lambda answer: same_path(answer, incident, root),
            "hints": ["find searches through directories. Start at . and filter by filename.", "Run: find . -type f -name 'incident-note.txt'"],
            "explain": "find starts at the supplied path. Here, . means this directory, -type f selects files, and -name matches their names.",
        },
        {
            "title": "Search inside a file",
            "goal": "Search evidence/login.log for LOGIN_FAILED. Enter the username from that line (just the name).",
            "check": lambda answer: answer.strip() == username,
            "hints": ["grep selects lines containing a matching pattern.", "Run: grep 'LOGIN_FAILED' evidence/login.log"],
            "explain": "grep searches file contents. find searches for directory entries. Choosing between them depends on what you are looking for.",
        },
        {
            "title": "Create a directory",
            "goal": "Create a directory called reports directly inside the lab. Then press Enter here to check.",
            "check": lambda answer: (root / "reports").is_dir(),
            "hints": ["Use mkdir followed by the new directory's name.", "Run: mkdir -p reports"],
            "explain": "mkdir creates directories. The -p option also allows the directory to exist already.",
        },
        {
            "title": "Copy a file",
            "goal": "Copy briefing.txt to reports/briefing-copy.txt, keeping the original. Create reports if needed. Press Enter here to check.",
            "check": lambda answer: same_contents(root / "briefing.txt", root / "reports" / "briefing-copy.txt"),
            "hints": ["cp takes a source path followed by a destination path.", "Run these separately: mkdir -p reports   THEN   cp briefing.txt reports/briefing-copy.txt"],
            "explain": "cp source destination creates a copy. The checker verifies both files exist and have matching contents.",
        },
        {
            "title": "Rename a file",
            "goal": "Rename inbox/draft.txt to inbox/final.txt. Keep its contents intact. Press Enter here to check.",
            "check": lambda answer: not (root / "inbox" / "draft.txt").exists()
                and (root / "inbox" / "final.txt").is_file()
                and (root / "inbox" / "final.txt").read_text(encoding="utf-8") == "Fictional incident report draft.\n",
            "hints": ["mv can rename a file by moving it to a new filename.", "Run: mv inbox/draft.txt inbox/final.txt"],
            "explain": "mv source destination moves or renames a file. Here, the directory stays the same and the filename changes.",
        },
        {
            "title": "Count lines",
            "goal": "Count the lines in evidence/login.log. Enter just the number.",
            "check": lambda answer: answer.strip() == "7",
            "hints": ["wc counts text. Its -l option counts newline characters.", "Run: wc -l evidence/login.log"],
            "explain": "wc -l counts newline characters. Every line in this practice log ends with a newline, so the count matches its lines.",
        },
    ]


def run_task(task, number, total):
    print("\nTask {}/{}: {}".format(number, total, task["title"]))
    print(task["goal"])
    print("Run commands in your OTHER terminal, then return here.")
    print("Here: enter your answer, or use hint / skip / quit.")
    hints_used = 0
    attempts = 0
    while True:
        answer = input("Answer/check> ").strip()
        action = answer.lower()
        if action == "quit":
            return "quit"
        if action == "skip":
            print("Skipped. " + task["explain"])
            return "skipped"
        if action == "hint":
            print("Hint: " + task["hints"][min(hints_used, len(task["hints"]) - 1)])
            hints_used += 1
            continue
        attempts += 1
        try:
            correct = task["check"](answer)
        except (OSError, ValueError, UnicodeError):
            correct = False
        if correct:
            print("Passed. " + task["explain"])
            return "independent" if attempts == 1 and hints_used == 0 else "practised"
        print("Not there yet. Check your command's output and the task's requested answer.")
        print("For file tasks, confirm you're working inside the lab folder. Type hint for help.")


def show_summary(results, total):
    print("\nRESULTS")
    independent = sum(status == "independent" for _, status in results)
    practised = sum(status == "practised" for _, status in results)
    skipped = sum(status == "skipped" for _, status in results)
    print("First attempt, without hints: {}/{}".format(independent, total))
    print("Completed with hints or retries: {}".format(practised))
    print("Skipped: {} | Unfinished: {}".format(skipped, total - len(results)))
    for title, status in results:
        print("  {}: {}".format(title, status))
    print("This checks your answers and file results, not which commands you used.")
    print("Send these results and any confusing commands to our chat.")


def main():
    root, code, username, incident = make_lab()
    tasks = build_tasks(root, code, username, incident)
    results = []
    print("HANDS-ON TERMINAL PRACTICE")
    print("This window is your instructor. Open a SECOND terminal window or tab for commands.")
    print("In that second terminal, copy and run this entire line:")
    print("\n  cd {}\n".format(shlex.quote(str(root))))
    print("Keep the second terminal in this lab folder throughout the test.")
    print("The lab contains new, fictional files. No downloads, sudo, or network access needed.")
    print("Commands typed at Answer/check> are answers, not executed commands.")
    print("Use only the lab files for the exercises. Your usual terminal runs real commands.")
    print("The lab is left in the temporary folder above for review; this script does not delete it.")
    try:
        input("\nPress Enter here when your second terminal is ready... ")
        for number, task in enumerate(tasks, 1):
            status = run_task(task, number, len(tasks))
            if status == "quit":
                break
            results.append((task["title"], status))
    except (KeyboardInterrupt, EOFError):
        print("\nPractice stopped.")
    finally:
        show_summary(results, len(tasks))
        print("\nLab folder: " + str(root))


if __name__ == "__main__":
    main()
