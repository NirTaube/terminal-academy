#!/usr/bin/env python3
"""Level 2: investigate fictional logs with real terminal commands."""

import random
import secrets
import shlex
import stat
import tempfile
from pathlib import Path


def make_lab(parent=None):
    root = Path(tempfile.mkdtemp(prefix="terminal-level2-", dir=parent)).resolve()
    case = root / "case"
    for directory in ("logs", "reports", "archive/2025", "archive/2026"):
        (case / directory).mkdir(parents=True, exist_ok=True)
    code = secrets.token_hex(3)
    (case / "analyst notes.txt").write_text("Case code: {}\n".format(code), encoding="utf-8")
    rows = [
        "09:00 INFO service started",
        "09:01 LOGIN_OK user=robin",
        "09:02 INFO health check passed",
        "09:03 LOGIN_FAILED user=alex",
        "09:04 LOGIN_OK user=taylor",
        "09:05 INFO connection opened",
        "09:06 LOGIN_FAILED user=morgan",
        "09:07 INFO connection closed",
        "09:08 LOGIN_FAILED user=alex",
        "09:09 INFO service stopped",
    ]
    # Vary line positions so the exercise requires inspecting this run's files.
    random.shuffle(rows)
    (case / "logs" / "auth.log").write_text("\n".join(rows) + "\n", encoding="utf-8")
    users = ["alex", "morgan", "alex", "taylor", "robin", "morgan"]
    random.shuffle(users)
    (case / "users.txt").write_text("\n".join(users) + "\n", encoding="utf-8")
    (case / "reports" / "summary.txt").write_text("Investigation summary\n", encoding="utf-8")
    note = case / "archive" / random.choice(["2025", "2026"]) / "incident details.txt"
    note.write_text("Fictional archived evidence.\n", encoding="utf-8")
    private = case / "private.txt"
    private.write_text("Practice data only, no real credentials.\n", encoding="utf-8")
    private.chmod(0o644)
    return root, case, code, rows, users, note


def matches(path, expected):
    try:
        return path.read_text(encoding="utf-8") == expected
    except (OSError, UnicodeError):
        return False


def path_matches(answer, target, base):
    try:
        candidate = Path(answer)
        if not candidate.is_absolute():
            candidate = base / candidate
        return candidate.resolve() == target.resolve()
    except (OSError, ValueError):
        return False


def build_tasks(root, case, code, rows, users, note):
    def task(title, goal, check, clue, command, explain):
        return {"title": title, "goal": goal, "check": check,
                "hints": [clue, command], "explain": explain}

    def file_task(title, goal, filename, expected, clue, command, explain):
        return task(title, goal + " Then press Enter here to check.",
                    lambda answer: matches(case / "reports" / filename, expected),
                    clue, command, explain)

    failed = [row for row in rows if "LOGIN_FAILED" in row]
    first_failed = next(i for i, row in enumerate(rows, 1) if "LOGIN_FAILED" in row)
    return [
        task("Navigate into a directory",
             "From the lab folder, enter the case directory and print your current location. Paste the full path here. Stay in case for all remaining tasks.",
             lambda answer: answer.startswith("/") and path_matches(answer, case, root),
             "cd changes directory; pwd prints the current directory.",
             "Run separately: cd case   THEN   pwd",
             "cd changes your shell's working directory. All subsequent relative paths start there."),
        task("Handle a filename with spaces",
             "Read analyst notes.txt. Enter its case code, just the code.",
             lambda answer: answer == code,
             "Quote a path with spaces so the shell treats it as one argument.",
             'Run: cat "analyst notes.txt"',
             "Quotes keep spaces inside a single filename instead of splitting it into separate arguments."),
        file_task("Save the first three lines",
                  "Save the first THREE lines of logs/auth.log to reports/start.txt.",
                  "start.txt", "\n".join(rows[:3]) + "\n",
                  "head prints the beginning of a file. > sends output to a file.",
                  "Run: head -n 3 logs/auth.log > reports/start.txt",
                  "head -n 3 selects the first three lines. > creates or overwrites the destination file."),
        file_task("Save the last two lines",
                  "Save the last TWO lines of logs/auth.log to reports/end.txt.",
                  "end.txt", "\n".join(rows[-2:]) + "\n",
                  "tail prints the end of a file.",
                  "Run: tail -n 2 logs/auth.log > reports/end.txt",
                  "tail -n 2 selects the final two lines. This file's order is shuffled, so its last line is not necessarily the latest event."),
        file_task("Extract failed logins",
                  "Save every line containing LOGIN_FAILED to reports/failed.txt, preserving their order.",
                  "failed.txt", "\n".join(failed) + "\n",
                  "grep selects matching lines; combine it with output redirection.",
                  "Run: grep 'LOGIN_FAILED' logs/auth.log > reports/failed.txt",
                  "grep returns the full matching lines. Saving them preserves evidence for later inspection."),
        task("Locate a match by line number",
             "Find the LINE NUMBER of the first LOGIN_FAILED entry in logs/auth.log. Enter just that number.",
             lambda answer: answer == str(first_failed),
             "grep has an option to display line numbers alongside matches.",
             "Run: grep -n 'LOGIN_FAILED' logs/auth.log",
             "grep -n prefixes matches with their line numbers, counted from 1."),
        task("Connect commands with a pipe",
             "Use a pipeline to filter LOGIN_FAILED lines from logs/auth.log and count them. Enter just the count.",
             lambda answer: answer == str(len(failed)),
             "The | symbol sends one command's output into another command. wc -l counts lines.",
             "Run: grep 'LOGIN_FAILED' logs/auth.log | wc -l",
             "grep supplies the matching lines to wc -l. A pipe connects commands without needing an intermediate file."),
        file_task("Sort and remove duplicates",
                  "Save the usernames from users.txt in alphabetical order, with each name appearing once, to reports/unique-users.txt.",
                  "unique-users.txt", "\n".join(sorted(set(users))) + "\n",
                  "sort orders lines. uniq removes repeated adjacent lines, so sort first.",
                  "Run: sort users.txt | uniq > reports/unique-users.txt",
                  "Sorting makes equal lines adjacent. uniq then removes their repetitions; sort -u is another valid approach."),
        file_task("Append without overwriting",
                  "Add exactly one line saying Review complete to reports/summary.txt. Preserve its existing first line.",
                  "summary.txt", "Investigation summary\nReview complete\n",
                  ">> appends output; > overwrites. Inspect the file before retrying if you already appended.",
                  "Run: echo 'Review complete' >> reports/summary.txt",
                  "Appending keeps the existing text. Repeating the append adds another line, so inspect your result before rerunning it."),
        task("Search nested folders for a spaced filename",
             "Find incident details.txt beneath archive. Enter its path relative to case, or its absolute path.",
             lambda answer: path_matches(answer, note, case),
             "Use find with a quoted filename pattern.",
             "Run: find archive -type f -name 'incident details.txt'",
             "find searches nested directories. Quoting the filename keeps its embedded space intact."),
        task("Restrict file permissions",
             "Set private.txt so ONLY its owner can read and write it, with no execute permission. Press Enter here to check.",
             lambda answer: stat.S_IMODE((case / "private.txt").stat().st_mode) == 0o600,
             "chmod sets permission bits. Read=4, write=2, execute=1; the digits describe owner, group, and others.",
             "Run: chmod 600 private.txt",
             "600 grants read+write (4+2) to the owner and no permission to group or others. These mode bits do not constrain privileged administrators."),
        file_task("Exclude noisy log lines",
                  "Save all lines from logs/auth.log that do NOT contain INFO to reports/activity.txt, preserving their order.",
                  "activity.txt", "\n".join(row for row in rows if "INFO" not in row) + "\n",
                  "grep -v reverses matching: it selects nonmatching lines.",
                  "Run: grep -v 'INFO' logs/auth.log > reports/activity.txt",
                  "grep -v excludes matching lines. In a real investigation, decide whether excluded events might still be relevant."),
    ]


def run_task(task, number, total):
    print("\nTask {}/{}: {}".format(number, total, task["title"]))
    print(task["goal"])
    print("Run commands in your OTHER terminal. Here: answer/check, hint, skip, or quit.")
    hints_used = attempts = 0
    while True:
        answer = input("Answer/check> ").strip()
        if answer.lower() == "quit":
            return "quit"
        if answer.lower() == "skip":
            print("Skipped. " + task["explain"])
            return "skipped"
        if answer.lower() == "hint":
            print("Hint: " + task["hints"][min(hints_used, 1)])
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
        print("Not there yet. Check the output or file contents. Your commands should run from case.")
        print("Type hint for a clue; type hint again for an example command.")


def main():
    lab = make_lab()
    root, case = lab[:2]
    tasks = build_tasks(*lab)
    results = []
    print("TERMINAL PRACTICE 2: FILES, PIPES, AND LOGS")
    print("Open a SECOND terminal tab for your commands. Run this line there:")
    print("\n  cd {}\n".format(shlex.quote(str(root))))
    print("This tab gives tasks; the other tab executes real commands.")
    print("All evidence is fictional. Work only inside this generated lab folder.")
    print("New concepts are expected: use hints to learn, then try a fresh run without them.")
    print("Each task is independent after navigation, so you can skip and keep going.")
    try:
        input("\nPress Enter when the other tab is ready... ")
        for number, task in enumerate(tasks, 1):
            status = run_task(task, number, len(tasks))
            if status == "quit":
                break
            results.append((task["title"], status))
    except (EOFError, KeyboardInterrupt):
        print("\nPractice stopped.")
    finally:
        print("\nRESULTS")
        for label, status in [("First attempt without hints", "independent"),
                              ("Completed with help or retries", "practised"),
                              ("Skipped", "skipped")]:
            print("{}: {}".format(label, sum(s == status for _, s in results)))
        print("Unfinished: {}".format(len(tasks) - len(results)))
        for title, status in results:
            print("  {}: {}".format(title, status))
        print("The checker verifies answers and file results, not the exact commands used.")
        print("Lab preserved for review: " + str(root))
        print("Send your results and confusing commands to our chat.")


if __name__ == "__main__":
    main()
