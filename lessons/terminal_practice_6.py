#!/usr/bin/env python3
"""Lesson 6: preserve and investigate fictional evidence."""

import secrets
import stat

from lesson_support import capture, path_is, read, run_lesson, task, write


def build_lesson(root, resources):
    code = secrets.token_hex(3)
    brief = root / "fixtures/archive/2026/incident-brief.txt"
    write(brief, "Fictional investigation\nCase code: {}\nReview authentication failures, later successes, and configuration changes.\n".format(code))
    rows = [
        "09:00 INFO service started",
        "09:01 AUTH_OK user=robin source=192.0.2.10",
        "09:02 AUTH_FAIL user=alex source=198.51.100.42",
        "09:03 AUTH_FAIL user=alex source=198.51.100.42",
        "09:04 INFO health check passed",
        "09:05 AUTH_FAIL user=morgan source=203.0.113.7",
        "09:06 AUTH_FAIL user=alex source=198.51.100.42",
        "09:07 AUTH_OK user=alex source=198.51.100.42",
        "09:08 CONFIG_CHANGE user=alex setting=allow_guest",
        "09:09 AUTH_OK user=taylor source=192.0.2.20",
        "09:10 INFO session closed",
        "09:11 INFO service stopped",
    ]
    original = "\n".join(rows) + "\n"
    write(root / "fixtures/logs/auth.log", original)
    write(root / "fixtures/config-before.txt", "mode=training\nallow_guest=false\nport=8000\n")
    write(root / "fixtures/config-after.txt", "mode=training\nallow_guest=true\nport=8000\n")
    failures = [r for r in rows if "AUTH_FAIL" in r]
    alex = [r for r in rows if "user=alex " in r]
    summary = "Failed logins: 4\nAccount to review: alex\nConclusion: needs review\n"
    tasks = [
        capture(root, "Guided: create a working extract", ["Select INFO entries into a separate report.", "Leave the original log intact."], "info.txt", "grep 'INFO' fixtures/logs/auth.log",
                "Redirect into a different file from the one you are reading.",
                "Separate working reports preserve the source. Filtering does not change the original log.", expected="".join(r + "\n" for r in rows if "INFO" in r), source="fixtures/logs/auth.log", guided=True),
        task("Find the case briefing", ["Find incident-brief.txt somewhere under fixtures."],
             lambda a: path_is(a, brief, root), "find fixtures -type f -name 'incident-brief.txt'",
             "Search by filename, starting at fixtures.", "Locate context before interpreting isolated events.", source="fixtures/", submit="Enter the brief's relative or absolute path."),
        task("Read the case context", ["Read the briefing you found.", "Locate its case code."], lambda a: a == code,
             "cat fixtures/archive/2026/incident-brief.txt", "Use the path from your previous search.",
             "The case briefing describes the question. All accounts, events, and source addresses in this exercise are fictional.", submit="Enter only the case code."),
        capture(root, "Preserve failed entries with references", ["Extract AUTH_FAIL lines.", "Include their line numbers from the original log."], "failures.txt", "grep -n 'AUTH_FAIL' fixtures/logs/auth.log",
                "grep -n adds original line numbers.", "Line numbers make it easier to trace findings back to their source.",
                expected="".join("{}:{}\n".format(i, r) for i, r in enumerate(rows, 1) if "AUTH_FAIL" in r), source="fixtures/logs/auth.log"),
        task("Count the failed entries", ["Count AUTH_FAIL entries in the original log."], lambda a: a == str(len(failures)),
             "grep -c 'AUTH_FAIL' fixtures/logs/auth.log", "Count matching lines, not every occurrence of a word.",
             "There are four failed entries in this file. That count alone does not establish account compromise.", source="fixtures/logs/auth.log", submit="Enter only the count."),
        capture(root, "Build an account timeline", ["Extract every event containing the exact account field user=alex.", "Keep their original order."], "alex-timeline.txt",
                "grep -F 'user=alex ' fixtures/logs/auth.log", "Include the space after alex to avoid matching a longer username.",
                "This account has failures followed by a success and a configuration change. The sequence warrants review; it does not prove who performed the actions.", expected="\n".join(alex) + "\n", source="fixtures/logs/auth.log"),
        task("Identify the source of the success", ["Find the AUTH_OK event for alex.", "Read that event's source address."], lambda a: a == "198.51.100.42",
             "grep 'AUTH_OK' fixtures/logs/auth.log | grep -F 'user=alex '", "Select both the event type and the account, then read the source field.",
             "The success uses the same recorded source as the failures for alex. A logged source address is evidence, not proof of a person's identity. Do not contact these fictional addresses.", source="fixtures/logs/auth.log", submit="Enter only the source IPv4 address."),
        capture(root, "Compare configuration evidence", ["Compare the before and after configuration files.", "Capture the difference."], "config-diff.txt", "diff fixtures/config-before.txt fixtures/config-after.txt",
                "diff reports changes; status 1 means differences were found.",
                "allow_guest changed from false to true. Establishing whether the change was authorized would require more evidence.", pattern=r"[\s\S]*< allow_guest=false[\s\S]*> allow_guest=true", source="fixtures/config-before.txt and fixtures/config-after.txt"),
        task("Write a careful summary", ["Create the report shown below with these three lines:", "Failed logins: 4", "Account to review: alex", "Conclusion: needs review"],
             lambda a: read(root / "reports/summary.txt") == summary,
             "printf 'Failed logins: 4\\nAccount to review: alex\\nConclusion: needs review\\n' > reports/summary.txt",
             "Use a text editor or printf with newline characters. Distinguish observed facts from conclusions.",
             "The summary states observed evidence and a cautious next step. It avoids presenting the suspicious sequence as confirmed compromise.", output="reports/summary.txt"),
        task("Challenge: preserve and protect a copy", ["Copy the original auth.log to the output file shown below.", "Give the copy owner read/write only.", "Keep the original unchanged."],
             lambda a: read(root / "reports/auth-evidence.log") == original and read(root / "fixtures/logs/auth.log") == original
             and stat.S_IMODE((root / "reports/auth-evidence.log").stat().st_mode) == 0o600,
             "cp fixtures/logs/auth.log reports/auth-evidence.log\nchmod 600 reports/auth-evidence.log",
             "Combine copying from Lesson 1 with permissions from Lesson 3.",
             "You combined navigation, reading, filtering, comparison, reporting, and permission skills. This training copy is not a forensic acquisition or a chain-of-custody record.", source="fixtures/logs/auth.log", output="reports/auth-evidence.log"),
    ]
    return dict(title="MINI INVESTIGATION", tasks=tasks, learn=[
        ("The case", "A fictional service recorded failed logins, later successes, and a configuration change. Your job is to assemble a small evidence report.\n\nStart with context. Keep original files intact. Save extracts separately. This lesson uses the skills from Lessons 1-5; it needs no external systems."),
        ("Observation versus conclusion", "A failure is an observed event. A later success and a sensitive change may justify further review, but do not prove malicious access by themselves.\n\nWrite what the log shows, distinguish what remains unknown, and protect your working copy. Then use Terminal Academy to revisit any skill that felt difficult."),
    ])


if __name__ == "__main__":
    run_lesson(6, build_lesson)
