#!/usr/bin/env python3
"""Level 2: investigate fictional logs with real terminal commands."""

import argparse
import random
import secrets
import shlex
import stat
import shutil
import sys
import tempfile
import textwrap
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
    tasks = [
        task("Navigate into a directory",
             "From the lab folder, enter the case directory and print your current location. Paste the full path here. Stay in case for all remaining tasks.",
             lambda answer: answer.startswith("/") and path_matches(answer, case, root),
             "cd changes directory; pwd prints the current directory.",
             "cd case\npwd",
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
    layouts = [
        {
            "steps": ["Move into the case folder.", "Print your current folder's full path."],
            "submit": "Paste the full path. Stay in case for the remaining tasks.",
        },
        {
            "file": "analyst notes.txt",
            "steps": ["Read the file shown above.", "Find the line labelled Case code."],
            "submit": "Enter only the code, without the Case code label.",
        },
        {
            "file": "logs/auth.log", "save": "reports/start.txt",
            "steps": ["Select the first THREE lines.", "Save those lines to the output file shown above."],
        },
        {
            "file": "logs/auth.log", "save": "reports/end.txt",
            "steps": ["Select the last TWO lines.", "Save those lines to the output file shown above."],
        },
        {
            "file": "logs/auth.log", "save": "reports/failed.txt",
            "steps": ["Select every line containing LOGIN_FAILED.", "Keep their original order and save them."],
        },
        {
            "file": "logs/auth.log",
            "steps": ["Find the first line containing LOGIN_FAILED.", "Identify that line's number in the original file."],
            "submit": "Enter only the line number.",
        },
        {
            "file": "logs/auth.log",
            "steps": ["Filter the lines containing LOGIN_FAILED.", "Use a pipe to send those lines into a line counter."],
            "submit": "Enter only the count.",
        },
        {
            "file": "users.txt", "save": "reports/unique-users.txt",
            "steps": ["Sort the usernames alphabetically.", "Keep each name only once.", "Save the result to the output file shown above."],
        },
        {
            "file": "reports/summary.txt",
            "steps": ["Preserve the file's existing first line.", "Append exactly one new line: Review complete"],
        },
        {
            "file": "archive/ (search this folder and its subfolders)",
            "steps": ["Find the file named incident details.txt."],
            "submit": "Enter its path relative to case, or its full absolute path.",
        },
        {
            "file": "private.txt",
            "steps": ["Give the owner read and write permissions.", "Give group and others no permissions.", "Do not allow anyone to execute the file."],
        },
        {
            "file": "logs/auth.log", "save": "reports/activity.txt",
            "steps": ["Select lines that do NOT contain INFO.", "Keep their original order and save them."],
        },
    ]
    for number, (item, layout) in enumerate(zip(tasks, layouts), 1):
        item.update(layout)
        item.setdefault("submit", "Return to this tab and press Enter to check your work.")
        item["location"] = "lab folder" if number == 1 else "case folder"
    return tasks


class Display:
    def __init__(self, no_clear=False):
        self.clear = sys.stdout.isatty() and not no_clear
        self.width = max(32, min(72, shutil.get_terminal_size((74, 24)).columns - 2))

    def text(self, content=""):
        for line in content.split("\n"):
            print(textwrap.fill(line, self.width) if line else "")

    def screen(self, title):
        if self.clear:
            print("\033[2J\033[H", end="")
        print("=" * self.width)
        self.text(title)
        print("=" * self.width)

    def task(self, item, number, total):
        self.screen("LESSON 2  |  TASK {:02d} OF {:02d}".format(number, total))
        self.text(item["title"])
        self.text("\nCOMMAND TAB: work in the " + item["location"] + ".")
        if item.get("file"):
            self.text("FILE: " + item["file"])
        if item.get("save"):
            self.text("SAVE TO: " + item["save"])
        self.text("\nYOUR STEPS")
        for index, step in enumerate(item["steps"], 1):
            print(textwrap.fill("{}. {}".format(index, step), self.width, subsequent_indent="   "))
        self.text("\nSUBMIT IN THIS TAB\n" + item["submit"])
        self.text("\nCONTROLS: hint | skip | quit | task (show this screen again)")


def run_task(task, number, total, display=None):
    display = display or Display()
    display.task(task, number, total)
    hints_used = attempts = 0
    while True:
        answer = input("\nAnswer / Enter to check > ").strip()
        if answer.lower() == "quit":
            return "quit"
        if answer.lower() == "skip":
            display.text("\nSKIPPED\n\nWHAT TO REMEMBER\n" + task["explain"])
            input("\nPress Enter for the next task > ")
            return "skipped"
        if answer.lower() == "task":
            display.task(task, number, total)
            continue
        if answer.lower() == "hint":
            if hints_used == 0:
                display.text("\nHINT\n" + task["hints"][0])
                display.text("Type hint again to see an example command.")
            else:
                display.text("\nEXAMPLE COMMAND (run in your command tab)")
                display.text(task["hints"][1].removeprefix("Run: "))
            hints_used += 1
            continue
        attempts += 1
        try:
            correct = task["check"](answer)
        except (OSError, ValueError, UnicodeError):
            correct = False
        if correct:
            display.text("\nPASSED\n\nWHAT YOU LEARNED\n" + task["explain"])
            input("\nPress Enter for the next task > ")
            return "independent" if attempts == 1 and hints_used == 0 else "practised"
        display.text("\nNOT YET\nCheck the output or file contents and your working folder.")
        display.text("Use hint for help, or task to reread the instructions.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-clear", action="store_true", help="Keep earlier screens visible")
    args = parser.parse_args()
    display = Display(args.no_clear)
    lab = make_lab()
    root, case = lab[:2]
    tasks = build_tasks(*lab)
    results = []
    display.screen("LESSON 2: FILES, PIPES, AND LOGS")
    display.text("12 hands-on tasks. One task per screen. Take your time.")
    display.text("\nSETUP\n1. Keep this tab open as your instructor.\n2. Open a SECOND tab for your commands.\n3. Run this line in the second tab:")
    print("\n  cd {}\n".format(shlex.quote(str(root))))
    display.text("4. Return here when the second tab is ready.")
    display.text("\nAll files are fictional. Work inside this practice lab.")
    display.text("Use hints to learn unfamiliar commands. After Task 1, stay in the case folder. You can skip a task and continue.")
    try:
        input("\nPress Enter when the other tab is ready... ")
        for number, task in enumerate(tasks, 1):
            status = run_task(task, number, len(tasks), display)
            if status == "quit":
                break
            results.append((task["title"], status))
    except (EOFError, KeyboardInterrupt):
        display.text("\nPractice stopped.")
    finally:
        display.screen("LESSON 2: RESULTS")
        for label, status in [("First attempt without hints", "independent"),
                              ("Completed with help or retries", "practised"),
                              ("Skipped", "skipped")]:
            display.text("{}: {}".format(label, sum(s == status for _, s in results)))
        display.text("Unfinished: {}".format(len(tasks) - len(results)))
        print()
        for title, status in results:
            display.text("[{}] {}".format(status, title))
        display.text("\nThe checker verifies answers and file results, not the exact commands used.")
        display.text("\nYour practice files are kept here for review:")
        print(str(root))
        display.text("\nSave your results or share them with your instructor.")


if __name__ == "__main__":
    main()
