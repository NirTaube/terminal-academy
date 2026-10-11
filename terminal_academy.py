#!/usr/bin/env python3
"""A persistent, hands-on terminal course for macOS and Linux. Python 3 only."""

import argparse
import getpass
import http.server
import json
import os
from pathlib import Path
import platform
import re
import secrets
import shlex
import shutil
import stat
import subprocess
import sys
import textwrap
import threading
import time


VERSION = 1
CHAPTERS = [
    "Navigation and paths", "Tree views", "Creating and managing files",
    "Reading and editing", "Finding files and searching text",
    "Pipes and redirection", "Organising text", "Users and permissions",
    "Processes and system information", "Network inspection",
    "Help and terminal controls", "Final investigation",
]


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def append_live_line(root, token):
    with (root / "fixtures/live.log").open("a", encoding="utf-8") as handle:
        handle.write("Live code: {}\n".format(token))


def create_environment(root):
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise ValueError("This folder already contains files. Use --new or choose another --lab folder.")
    token = secrets.token_hex(3)
    code = secrets.token_hex(3)
    rows = [
        "09:00 INFO service started", "09:01 LOGIN_OK user=robin ip=192.168.1.5",
        "09:02 LOGIN_FAILED user=alex ip=192.168.1.50", "09:03 INFO health check",
        "09:04 LOGIN_FAILED user=morgan ip=192.168.1.5",
        "09:05 LOGIN_OK user=taylor ip=192.168.1.5",
        "09:06 LOGIN_FAILED user=alex ip=192.168.1.50", "09:07 INFO service stopped",
    ]
    files = {
        "START_HERE.txt": "Practice environment only. Your progress is stored in .academy.json.\n",
        ".hidden-note": "Hidden does not mean access-controlled.\n",
        "fixtures/docs/briefing.txt": "Training brief\nCase code: {}\nReview the logs before drawing conclusions.\n".format(code),
        "fixtures/docs/analyst notes.txt": "Spaced filename code: {}\n".format(token),
        "fixtures/archive/2026/incident-note.txt": "Archived practice evidence.\n",
        "fixtures/logs/auth.log": "\n".join(rows) + "\n",
        "fixtures/live.log": "Live exercise ready.\n",
        "fixtures/users.txt": "morgan\nalex\nalex\nrobin\nmorgan\ntaylor\n",
        "fixtures/adjacent.txt": "alex\nalex\nmorgan\nmorgan\nalex\n",
        "fixtures/data.csv": "name,role\nalex,analyst\nmorgan,engineer\n",
        "fixtures/original.txt": "mode=training\nport=8000\n",
        "fixtures/revised.txt": "mode=training\nport=8080\n",
        "fixtures/edit-me.txt": "Status: pending\n",
        "fixtures/rename-me.txt": "Rename exercise\n",
        "fixtures/move-me.txt": "Move exercise\n",
        "fixtures/delete-me.txt": "Disposable exercise file\n",
        "fixtures/private.txt": "Fictional practice data\n",
        "fixtures/script.sh": "#!/bin/sh\nprintf 'Training script ran\\n'\n",
        "fixtures/overwrite-source.txt": "New training contents\n",
        "reports/overwrite-target.txt": "Old training contents\n",
        "reports/summary.txt": "Investigation summary\n",
        "fixtures/payload.bin": "Plain text despite the filename extension.\n",
    }
    for name, content in files.items():
        write(root / name, content)
    for name in ("workspace", "fixtures/empty-folder", "reports", "workspace/moved"):
        (root / name).mkdir(parents=True, exist_ok=True)
    (root / "fixtures/private.txt").chmod(0o644)
    (root / "fixtures/script.sh").chmod(0o644)
    state = {"version": VERSION, "token": token, "code": code, "results": {}}
    save_state(root, state)
    return state


def save_state(root, state):
    temporary = root / ".academy.json.tmp"
    temporary.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    temporary.replace(root / ".academy.json")


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def path_is(answer, target, base):
    try:
        p = Path(answer).expanduser()
        return (p if p.is_absolute() else base / p).resolve() == target.resolve()
    except (OSError, ValueError):
        return False


class Runtime:
    """Owns only the local HTTP server and the disposable worker it starts."""

    def __init__(self, token):
        self.worker = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(86400)", "terminal-academy-worker"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_HEAD(self):
                self.send_response(200)
                self.send_header("X-Academy-Token", token)
                self.end_headers()

            def do_GET(self):
                self.do_HEAD()
                self.wfile.write(b"Terminal Academy: local practice server\n")

            def log_message(self, *args):
                pass

        try:
            self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            self.port = self.server.server_address[1]
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
        except OSError:
            self.server = None
            self.port = None

    def close(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.worker.poll() is None:
            self.worker.terminate()
            try:
                self.worker.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.worker.kill()
                self.worker.wait()


def build_tasks(root, state, runtime):
    tasks = []
    docs = root / "fixtures/docs"
    briefing = read_text(docs / "briefing.txt")
    log = read_text(root / "fixtures/logs/auth.log")
    rows = log.splitlines()
    failures = [row for row in rows if "LOGIN_FAILED" in row]
    system = platform.system()
    pid = runtime.worker.pid if runtime else 12345
    port = runtime.port if runtime and runtime.port else 8000

    def add(chapter, slug, title, goal, command, checker=None, clue="", why="", manual=False, prepare=None):
        tasks.append({"id": slug, "chapter": chapter, "title": title, "goal": goal,
                      "command": command, "check": checker, "clue": clue or "Read the command's manual with man.",
                      "why": why, "manual": manual, "prepare": prepare})

    def output(chapter, slug, title, goal, command, expected=None, pattern=None, why="", clue=""):
        target = root / "reports" / (slug + ".txt")
        if expected is not None:
            check = lambda answer: target.is_file() and read_text(target) == expected
        else:
            check = lambda answer: bool(read_text(target).strip()) and bool(re.search(pattern, read_text(target), re.M))
        add(chapter, slug, title, goal + " Save the output to reports/{}.txt, then enter check here.".format(slug),
            command + " > reports/{}.txt".format(slug), check, clue, why)

    # Every command is entered by the learner in a real, separate terminal.
    add(0, "pwd", "Locate yourself", "Print your current directory. Paste its absolute path here.", "pwd",
        lambda a: a.startswith("/") and path_is(a, root, root), why="pwd describes your current location; relative paths start there.")
    add(0, "ls", "List entries", "List the top-level folder. Enter the filename ending in .txt at this level.", "ls",
        lambda a: a == "START_HERE.txt", why="ls with no path lists the current directory.")
    output(0, "ls-long", "Detailed file listing", "List fixtures/private.txt with ownership and permissions.",
           "ls -l fixtures/private.txt", pattern=r"private\.txt", why="The first field shows file type and permission bits; other fields include owner, group, and size.")
    add(0, "ls-hidden", "Discover a hidden entry", "Include hidden entries in a listing. Enter the name of the file ending in -note.", "ls -a",
        lambda a: a == ".hidden-note", why="A leading dot hides an entry from ordinary ls; it does not protect its contents.")
    output(0, "ls-readable", "Readable directory listing", "List all top-level entries with details and human-readable sizes.",
           "ls -lah", pattern=r"\.hidden-note", why="-l gives details, -a includes hidden entries, and -h changes size formatting.")
    add(0, "cd-path", "Enter a folder", "Enter fixtures/docs and print your path. Paste it here, then return to the lab folder before continuing.",
        "cd fixtures/docs\npwd\ncd ../..", lambda a: a.startswith("/") and path_is(a, docs, root), why="cd changes your shell's location. ../.. goes up two levels.")
    add(0, "cd-parent", "Use the parent directory", "From fixtures/docs, move up one level and print your location. Submit the path, then return to the lab.",
        "cd fixtures/docs\ncd ..\npwd\ncd ..", lambda a: a.startswith("/") and path_is(a, root / "fixtures", root), why=".. is the parent of the current directory.")
    add(0, "cd-home", "Home and previous directory", "From the lab, go home and print your location. Submit that path. Use cd - to return to the lab.",
        "cd ~\npwd\ncd -", lambda a: a.startswith("/") and path_is(a, Path.home(), root), why="~ expands to your home directory; cd - returns to the previous directory.")
    add(0, "space", "Quote a spaced filename", "Read fixtures/docs/analyst notes.txt. Enter only its code.",
        'cat "fixtures/docs/analyst notes.txt"', lambda a: a == state["token"], why="Quoting keeps the filename's spaces inside one argument.")

    output(1, "tree-basic", "View the folder structure", "Display fixtures as a tree.", "tree fixtures", pattern=r"incident-note\.txt", why="tree shows directory relationships. If unavailable on Kali, install its tree package or skip this chapter.")
    output(1, "tree-depth", "Limit tree depth", "Display fixtures to a maximum depth of two levels.", "tree -L 2 fixtures", pattern=r"docs", why="-L limits how deeply tree descends.")
    output(1, "tree-hidden", "Include hidden entries", "Display the lab tree, including hidden entries, to depth one.", "tree -a -L 1", pattern=r"\.hidden-note", why="-a includes hidden entries.")
    output(1, "tree-dirs", "Show only folders", "Display only directories under fixtures.", "tree -d fixtures", pattern=r"archive", why="-d filters the display to directories.")

    add(2, "mkdir", "Create a directory", "Create workspace/reports. Enter check.", "mkdir workspace/reports",
        lambda a: (root / "workspace/reports").is_dir(), why="mkdir creates a directory.")
    add(2, "mkdir-parents", "Create nested directories", "Create workspace/daily/notes even if the parent does not exist. Enter check.", "mkdir -p workspace/daily/notes",
        lambda a: (root / "workspace/daily/notes").is_dir(), why="-p creates missing parents and accepts existing directories.")
    add(2, "touch", "Create an empty file", "Create workspace/notes.txt without writing any text into it. Enter check.", "touch workspace/notes.txt",
        lambda a: (root / "workspace/notes.txt").is_file() and (root / "workspace/notes.txt").stat().st_size == 0,
        why="touch creates an absent file; on existing files it updates timestamps without clearing contents.")
    add(2, "copy", "Copy and preserve the source", "Copy fixtures/docs/briefing.txt to workspace/briefing-copy.txt. Enter check.",
        "cp fixtures/docs/briefing.txt workspace/briefing-copy.txt",
        lambda a: read_text(root / "workspace/briefing-copy.txt") == briefing and (docs / "briefing.txt").is_file(), why="cp takes source then destination.")
    add(2, "copy-interactive", "Confirm an overwrite", "Use interactive copying to replace reports/overwrite-target.txt with fixtures/overwrite-source.txt. Answer y at the shell prompt, then check here.",
        "cp -i fixtures/overwrite-source.txt reports/overwrite-target.txt",
        lambda a: read_text(root / "reports/overwrite-target.txt") == "New training contents\n", why="-i asks before replacing an existing destination.")
    add(2, "copy-folder", "Copy a folder recursively", "Copy fixtures/docs to workspace/docs-backup. Keep the original. Enter check.",
        "cp -R fixtures/docs workspace/docs-backup",
        lambda a: read_text(root / "workspace/docs-backup/briefing.txt") == briefing and read_text(root / "workspace/docs-backup/analyst notes.txt") == read_text(docs / "analyst notes.txt"),
        why="-R copies a directory and its descendants. On a repeat run, an existing destination changes how cp places the copy.")
    add(2, "rename", "Rename a file", "Rename fixtures/rename-me.txt to fixtures/renamed.txt. Enter check.", "mv -i fixtures/rename-me.txt fixtures/renamed.txt",
        lambda a: not (root / "fixtures/rename-me.txt").exists() and read_text(root / "fixtures/renamed.txt") == "Rename exercise\n", why="mv can rename within the same directory; -i requests confirmation before an overwrite.")
    add(2, "move", "Move into a folder", "Move fixtures/move-me.txt into workspace/moved. Enter check.", "mv fixtures/move-me.txt workspace/moved/",
        lambda a: not (root / "fixtures/move-me.txt").exists() and read_text(root / "workspace/moved/move-me.txt") == "Move exercise\n", why="A destination directory keeps the source filename.")
    add(2, "remove-file", "Remove a disposable file", "Remove ONLY fixtures/delete-me.txt with confirmation. Enter check.", "rm -i fixtures/delete-me.txt",
        lambda a: not (root / "fixtures/delete-me.txt").exists(), why="rm removes files without sending them to Trash. This fixture is disposable.")
    add(2, "remove-dir", "Remove an empty directory", "Remove fixtures/empty-folder. Enter check.", "rmdir fixtures/empty-folder",
        lambda a: not (root / "fixtures/empty-folder").exists(), why="rmdir refuses to remove a nonempty directory.")

    add(3, "cat", "Read a small file", "Print fixtures/docs/briefing.txt. Enter only its case code.", "cat fixtures/docs/briefing.txt",
        lambda a: a == state["code"], why="cat prints the complete contents; it is useful for small files.")
    add(3, "less", "Browse and search", "Open fixtures/logs/auth.log in less. Search for LOGIN_FAILED using /, use n for the next match, and q to exit. Enter done.",
        "less fixtures/logs/auth.log", manual=True, why="This is a guided control exercise: the instructor cannot observe your keys in another terminal.")
    output(3, "head", "Read the beginning", "Extract the first three lines of fixtures/logs/auth.log.", "head -n 3 fixtures/logs/auth.log", expected="\n".join(rows[:3]) + "\n", why="head -n 3 selects the first three lines.")
    output(3, "tail", "Read the end", "Extract the final two lines of fixtures/logs/auth.log.", "tail -n 2 fixtures/logs/auth.log", expected="\n".join(rows[-2:]) + "\n", why="tail selects the end of the file.")
    add(3, "tail-follow", "Follow an updating log", "Run tail -f fixtures/live.log in your command tab. Return here and enter ready; then read the new code in that tab. Stop tail with Ctrl+C and submit the code here.",
        "tail -f fixtures/live.log", lambda a: a == state["token"], why="tail -f follows appended content. Ctrl+C interrupts the foreground command.",
        prepare=lambda: append_live_line(root, state["token"]))
    output(3, "wc", "Count lines", "Count newline characters in fixtures/logs/auth.log. Save only the number, without a filename.",
           "wc -l < fixtures/logs/auth.log", pattern=r"^\s*8\s*$", why="wc -l counts newlines. < provides the file as standard input, avoiding a filename in the output.")
    add(3, "file-type", "Inspect a file type", "Use file to inspect fixtures/payload.bin. Enter text if its contents are text, or binary if they are binary.",
        "file fixtures/payload.bin", lambda a: a.lower() == "text", why="An extension is a naming convention; it does not guarantee a file's actual format.")
    add(3, "nano", "Edit a file", "Use nano to replace pending with reviewed in fixtures/edit-me.txt. Preserve the rest of the line. Save and exit, then enter check.",
        "nano fixtures/edit-me.txt", lambda a: read_text(root / "fixtures/edit-me.txt") == "Status: reviewed\n", why="In nano: Ctrl+O saves, Enter confirms the filename, and Ctrl+X exits. If nano is unavailable, skip or use another editor.")
    output(3, "diff", "Compare two versions", "Compare fixtures/original.txt and fixtures/revised.txt.",
           "diff fixtures/original.txt fixtures/revised.txt", pattern=r"[\s\S]*8000[\s\S]*8080", why="diff reports changed lines. Its exit status 1 means differences were found, not that reading the files failed.")

    add(4, "find-name", "Find a nested file", "Locate incident-note.txt under fixtures. Submit its relative or absolute path.",
        "find fixtures -type f -name 'incident-note.txt'", lambda a: path_is(a, root / "fixtures/archive/2026/incident-note.txt", root), why="find searches directory entries; -type f selects files.")
    output(4, "find-pattern", "Find by filename pattern", "Find all .log files under fixtures.", "find fixtures -type f -name '*.log'", pattern=r"fixtures/logs/auth\.log", why="Quote the pattern so find receives it unchanged.")
    output(4, "find-dir", "Find directories", "Find directories named docs under fixtures.", "find fixtures -type d -name 'docs'", expected="fixtures/docs\n", why="-type d selects directories.")
    output(4, "grep", "Select matching lines", "Extract all LOGIN_FAILED lines from fixtures/logs/auth.log.", "grep 'LOGIN_FAILED' fixtures/logs/auth.log", expected="\n".join(failures) + "\n", why="grep searches text and prints matching lines.")
    output(4, "grep-number", "Include line numbers", "Print LOGIN_FAILED lines with their original line numbers.", "grep -n 'LOGIN_FAILED' fixtures/logs/auth.log", expected="".join("{}:{}\n".format(i, row) for i, row in enumerate(rows, 1) if "LOGIN_FAILED" in row), why="-n shows the line number before the matching text.")
    output(4, "grep-case", "Ignore letter case", "Find LOGIN_FAILED lines using the lowercase pattern login_failed.", "grep -i 'login_failed' fixtures/logs/auth.log", expected="\n".join(failures) + "\n", why="-i ignores differences in letter case.")
    output(4, "grep-invert", "Exclude noisy entries", "Extract lines that do not contain INFO.", "grep -v 'INFO' fixtures/logs/auth.log", expected="".join(row + "\n" for row in rows if "INFO" not in row), why="-v selects nonmatching lines.")
    output(4, "grep-count", "Count matching lines", "Count LOGIN_FAILED lines in fixtures/logs/auth.log.", "grep -c 'LOGIN_FAILED' fixtures/logs/auth.log", expected="3\n", why="-c counts matching lines, not occurrences within each line.")
    output(4, "grep-recursive", "Search a folder's contents", "Search files under fixtures/logs recursively for LOGIN_FAILED.", "grep -r 'LOGIN_FAILED' fixtures/logs", pattern=r"auth\.log:.*LOGIN_FAILED", why="-r descends into directories.")
    output(4, "grep-literal", "Literal text versus patterns", "Select only lines containing the exact text ip=192.168.1.5 followed by a space or the end of the line. This log ends each matching IP at the end of its line.",
           "grep -F 'ip=192.168.1.5' fixtures/logs/auth.log | grep -v -F 'ip=192.168.1.50'", expected="".join(row + "\n" for row in rows if row.endswith("ip=192.168.1.5")), why="-F treats dots literally. Literal substring matching alone would also match .50, so the second filter excludes those entries.")

    output(5, "pipe", "Connect two commands", "Filter LOGIN_FAILED lines and pipe them into a line counter.", "grep 'LOGIN_FAILED' fixtures/logs/auth.log | wc -l", pattern=r"^\s*3\s*$", why="A pipe sends standard output to the next command's standard input.")
    output(5, "redirect", "Save output", "Print the text Review started into a new report using redirection.", "echo 'Review started'", expected="Review started\n", why="> creates a file or truncates an existing one before the command runs.")
    add(5, "append", "Preserve existing text", "Append exactly one line Review complete to reports/summary.txt, preserving its header. Enter check.",
        "echo 'Review complete' >> reports/summary.txt", lambda a: read_text(root / "reports/summary.txt") == "Investigation summary\nReview complete\n", why=">> appends. Repeating it adds another line, so inspect before retrying.")
    add(5, "stderr", "Separate error output", "Try listing fixtures/not-present.txt and redirect its error into reports/search-errors.txt. Enter check.",
        "ls fixtures/not-present.txt 2> reports/search-errors.txt", lambda a: "not-present.txt" in read_text(root / "reports/search-errors.txt"), why="2> redirects standard error rather than normal output.")
    add(5, "and", "Run only after success", "Create workspace/conditional, then use && to create workspace/conditional/ok.txt only if directory creation succeeds. Enter check.",
        "mkdir -p workspace/conditional && touch workspace/conditional/ok.txt", lambda a: (root / "workspace/conditional/ok.txt").is_file(), why="&& runs its right-hand command only if the left-hand command succeeds.")

    users = read_text(root / "fixtures/users.txt").splitlines()
    output(6, "sort", "Sort lines", "Sort fixtures/users.txt alphabetically, preserving duplicates.", "sort fixtures/users.txt", expected="\n".join(sorted(users)) + "\n", why="sort orders lines; duplicates remain unless requested otherwise.")
    output(6, "sort-unique", "Sort and deduplicate", "Sort fixtures/users.txt and keep each name once.", "sort -u fixtures/users.txt", expected="\n".join(sorted(set(users))) + "\n", why="sort -u sorts and removes duplicate lines.")
    output(6, "uniq", "Remove adjacent duplicates", "Run uniq on fixtures/adjacent.txt without sorting first.", "uniq fixtures/adjacent.txt", expected="alex\nmorgan\nalex\n", why="uniq removes adjacent repeats; the final alex remains because it is not next to the earlier alex.")
    output(6, "uniq-count", "Count repeated names", "Sort fixtures/users.txt and use uniq to count occurrences.", "sort fixtures/users.txt | uniq -c", pattern=r"^\s*2 alex\n\s*2 morgan\n\s*1 robin\n\s*1 taylor\s*$", why="Sorting places equal lines together; uniq -c prefixes each group with its count.")
    output(6, "cut", "Extract a field", "Extract the second comma-separated field from fixtures/data.csv, including its header.", "cut -d ',' -f 2 fixtures/data.csv", expected="role\nanalyst\nengineer\n", why="cut works for this simple data. It is not a full parser for quoted CSV fields containing commas.")
    output(6, "sed", "Extract a range", "Print lines 5 through 7 of fixtures/logs/auth.log.", "sed -n '5,7p' fixtures/logs/auth.log", expected="\n".join(rows[4:7]) + "\n", why="-n suppresses ordinary printing; 5,7p prints the selected range.")

    add(7, "whoami", "Identify your user", "Print your current username. Enter it here.", "whoami", lambda a: a == getpass.getuser(), why="whoami identifies the effective user running the command.")
    output(7, "id", "Inspect user and group IDs", "Show your user and group identity information.", "id", pattern=r"uid={}[\s\S]*gid=".format(os.geteuid()), why="IDs are numeric identities used by the operating system.")
    output(7, "groups", "Inspect group membership", "Show the groups your user belongs to.", "groups", pattern=r"\S+", why="Group membership can affect access; the checker only verifies that you captured nonempty output.")
    add(7, "chmod-private", "Restrict a file", "Set fixtures/private.txt to owner read/write, with no group, other, or execute bits. Enter check.", "chmod 600 fixtures/private.txt", lambda a: stat.S_IMODE((root / "fixtures/private.txt").stat().st_mode) == 0o600, why="600 grants owner read+write (4+2). Directory execute bits and ACLs need separate consideration.")
    add(7, "chmod-readable", "Set ordinary file permissions", "Set workspace/readable.txt to owner read/write and group/other read. Create it first. Enter check.", "touch workspace/readable.txt\nchmod 644 workspace/readable.txt", lambda a: (root / "workspace/readable.txt").is_file() and stat.S_IMODE((root / "workspace/readable.txt").stat().st_mode) == 0o644, why="644 means owner read/write and everyone else read, through these mode bits.")
    add(7, "chmod-execute", "Make your script executable", "Add only owner execute permission to fixtures/script.sh, then run it. Enter the printed line here.", "chmod u+x fixtures/script.sh\n./fixtures/script.sh", lambda a: a == "Training script ran" and stat.S_IMODE((root / "fixtures/script.sh").stat().st_mode) == 0o744, why="u+x adds owner execute. ./ tells the shell to run the file in the current path.")
    add(7, "sudo", "Understand elevated access", "Read man sudo. Does sudo normally run a command as root unless another user is specified? Enter yes or no. No elevated command is needed in this lab.", "man sudo", lambda a: a.lower() == "yes", why="sudo commonly defaults to root and applies the configured policy. This is a concept check, not a permissions change.")

    output(8, "ps", "Inspect running processes", "List processes and locate the disposable training worker PID {}.".format(pid), "ps aux", pattern=r"\b{}\b".format(pid), why="ps lists processes; PID identifies a running instance.")
    add(8, "top", "Watch live process activity", "Run top, inspect its changing process list, then press q to exit. Enter done.", "top", manual=True, why="top is interactive. This guided exercise cannot verify the keys pressed in the other terminal.")
    output(8, "df", "Inspect filesystem space", "Show filesystem usage in readable sizes.", "df -h", pattern=r"Filesystem", why="df reports space at the filesystem level.")
    output(8, "du", "Measure a directory", "Show the total disk usage of fixtures in readable units.", "du -sh fixtures", pattern=r"fixtures", why="du reports storage used by directory contents; it differs from df.")
    output(8, "uname", "Inspect kernel information", "Show full kernel/system identification.", "uname -a", pattern=re.escape(system), why="uname describes the kernel/system; it is not a complete hardware inventory.")
    output(8, "date", "Inspect the clock", "Print the current date and time.", "date", pattern=r"\d{2}:\d{2}:\d{2}", why="date uses the execution machine's timezone unless configured otherwise.")
    add(8, "kill", "Stop an identified process", "Ask ONLY the disposable worker with PID {} to stop, using SIGTERM. Enter check. The instructor stays running.".format(pid),
        "kill -TERM {}".format(pid), lambda a: runtime is not None and runtime.worker.poll() is not None, why="SIGTERM requests termination. This check watches only the worker started by this instructor.")

    if system == "Darwin":
        output(9, "net-address", "Inspect Mac interfaces", "Display interface information on this Mac.", "ifconfig", pattern=r"\binet\b", why="ifconfig shows interface settings, including loopback and assigned addresses.")
        output(9, "net-route", "Inspect the Mac default route", "Inspect the default route. If this machine has no default route, skip this exercise.", "route -n get default", pattern=r"gateway:", why="The gateway field identifies the next hop for the selected route.")
        output(9, "net-listeners", "Inspect listening TCP sockets", "Find the local instructor's listening TCP socket on port {}.".format(port), "lsof -nP -iTCP -sTCP:LISTEN", pattern=r":{}\b".format(port), why="-n avoids name lookup; -P keeps numeric ports. Visibility depends on user permissions.")
    elif system == "Linux":
        output(9, "net-address", "Inspect Kali/Linux interfaces", "Show a brief list of interfaces and their addresses.", "ip -br address", pattern=r"127\.0\.0\.1", why="ip -br address shows brief interface address information.")
        output(9, "net-route", "Inspect Kali/Linux routes", "Display routes. If this machine has no default route, skip this exercise.", "ip route", pattern=r"^default", why="The default route is the fallback when no more specific matching route exists.")
        output(9, "net-listeners", "Inspect listening TCP sockets", "Find the local instructor's listening TCP socket on port {}.".format(port), "ss -lnt", pattern=r":{}\b".format(port), why="-l selects listeners, -n numeric addresses, and -t TCP.")
    else:
        add(9, "net-platform", "Platform support", "Networking commands in this course target Mac and Linux. Enter done to acknowledge.", "", manual=True)
    output(9, "ping", "Test loopback connectivity", "Send four echo requests to your own machine's loopback address.", "ping -c 4 127.0.0.1", pattern=r"0(?:\.0)?% packet loss", why="Loopback reaches your own computer. Ping results alone do not establish that a website is reachable.")
    output(9, "curl", "Read local HTTP headers", "Request HEAD headers from the local training server at http://127.0.0.1:{}/. No internet is needed.".format(port),
           "curl -sSI http://127.0.0.1:{}/".format(port), pattern=r"(?i)X-Academy-Token: {}".format(state["token"]), why="curl -I requests headers. The training server binds only to the local loopback interface.")
    output(9, "dig", "Query DNS (optional internet exercise)", "If dig is installed and internet DNS is available, query example.com. Otherwise skip this task.", "dig example.com", pattern=r"status: NOERROR", why="dig queries DNS. This optional task contacts your configured DNS resolver.")

    add(10, "man", "Read the installed manual", "Open man grep, search for line number using /, then exit with q. Which option adds line numbers? Enter the option.", "man grep", lambda a: a == "-n", why="Installed manuals describe the version on this computer.")
    output(10, "command-path", "Locate a command", "Show how your shell resolves python3.", "command -v python3", pattern=r"python3", why="command -v checks shell resolution. Many Linux programs accept --help; many Mac utilities do not.")
    output(10, "tool-help", "Use a program's help option", "Ask Python for its command-line help. Capture the help instead of running a script.", "python3 --help", pattern=r"(?i)usage:", why="--help is useful when a program supports it. Use the installed manual for commands whose help syntax differs.")
    output(10, "history", "Inspect shell history", "Save your command tab's history. If that shell disables history, skip this exercise.", "history", pattern=r"\S+", why="History helps you review work. The checker only verifies that the file is nonempty.")
    add(10, "shortcuts", "Practise completion and recall", "In the command tab, start typing cat fixtures/doc and press Tab to complete the path. Cancel that line with Ctrl+C. Use Up to recall an earlier command. Enter done.", "", manual=True, why="Completion and recall reduce typing. This guided exercise is self-reported, not automatically verified.")
    add(10, "ctrl-d", "End input", "Run cat with no filename. Type a practice line and press Enter, then press Ctrl+D at an empty line to end input. Enter done here.", "cat", manual=True, why="Ctrl+D signals end of input. At an empty shell prompt it may exit the shell, so practise it inside cat.")
    add(10, "clear", "Clear the display", "Run clear in the command tab. Enter done here.", "clear", manual=True, why="clear changes the display; it does not undo commands or erase files.")
    add(10, "exit", "Leave a temporary shell", "Start a nested shell with sh, then run exit to return to your command tab's original shell. Enter done.", "sh\nexit", manual=True, why="exit leaves the current shell. A nested shell lets you practise without closing your tab.")
    add(10, "errors", "Recover from a wrong path", "Try cat fixtures/not-present.txt, then use pwd and ls fixtures to investigate. Does this error prove you need sudo? Enter yes or no.",
        "cat fixtures/not-present.txt\npwd\nls fixtures", lambda a: a.lower() == "no", why="A missing path is a location/name problem. Permission denied and command not found require different checks.")
    add(10, "error-command", "Understand command not found", "Try the nonexistent command academy_missing_command. Which command from this course checks whether a real command is available? Enter its two-word name.",
        "academy_missing_command\ncommand -v python3", lambda a: a == "command -v", why="command not found concerns shell resolution, spelling, or installation; it is different from a missing data file.")
    add(10, "error-permission", "Understand permission denied", "If reading an existing file fails with Permission denied, which command would show its owner and basic mode bits? Enter the command, using fixtures/private.txt as your example path.",
        "ls -l fixtures/private.txt", lambda a: a == "ls -l fixtures/private.txt", why="Inspect ownership, file and parent-directory permissions, and relevant ACLs before deciding whether different access is required.")

    output(11, "final-failures", "Build an evidence report", "Create a report of failed logins, with their original line numbers. Choose the commands yourself.",
           "grep -n 'LOGIN_FAILED' fixtures/logs/auth.log", expected="".join("{}:{}\n".format(i, row) for i, row in enumerate(rows, 1) if "LOGIN_FAILED" in row), why="Preserving line numbers makes it easier to refer back to original evidence.")
    add(11, "final-count", "State what the evidence shows", "Using your evidence, how many FAILED login entries mention user=alex? Enter the count.",
        "grep 'LOGIN_FAILED' fixtures/logs/auth.log | grep -c 'user=alex'", lambda a: a == "2", why="Two failed login entries do not establish that an account was compromised.")
    add(11, "final-verify", "Verify your report", "Enter the command that prints the first five lines of reports/final-failures.txt.",
        "head -n 5 reports/final-failures.txt", lambda a: a in ("head -n 5 reports/final-failures.txt", "head -5 reports/final-failures.txt"), why="Inspect generated reports before relying on them. This is a command-writing check; it accepts these two forms.")
    if runtime and not runtime.server:
        for task in tasks:
            if task["id"] in ("net-listeners", "curl"):
                task["goal"] = "The local training server could not start. Type skip; other exercises remain available."
                task["command"] = ""
                task["check"] = lambda answer: False
    return tasks


class Display:
    def __init__(self, no_clear=False):
        self.clear = sys.stdout.isatty() and not no_clear
        self.width = max(36, min(78, shutil.get_terminal_size((78, 24)).columns - 2))

    def screen(self, title, subtitle=""):
        if self.clear:
            print("\033[2J\033[H", end="")
        print("=" * self.width)
        self.text(title)
        if subtitle:
            self.text(subtitle)
        print("=" * self.width)

    def text(self, text=""):
        for paragraph in text.split("\n"):
            print(textwrap.fill(paragraph, self.width) if paragraph else "")

    def command(self, command):
        for line in command.splitlines():
            print("  " + line)


def run_task(task, index, total, root, state, display):
    results = state["results"]
    record = results.setdefault(task["id"], {"attempts": 0, "hints": 0, "status": "unfinished"})
    display.screen("{} | Task {} of {}".format(CHAPTERS[task["chapter"]], index, total), task["title"])
    display.text("\nWORK IN YOUR OTHER TERMINAL, starting in this lab folder:")
    display.command("cd " + shlex.quote(str(root)))
    display.text("\nTASK\n" + task["goal"])
    if task["id"] in ("net-address", "net-route", "net-listeners"):
        alternative = {"net-address": "Mac: ifconfig | Kali: ip -br address",
                       "net-route": "Mac: route -n get default | Kali: ip route",
                       "net-listeners": "Mac: lsof -nP -iTCP -sTCP:LISTEN | Kali: ss -lnt"}
        display.text("\nPLATFORM REFERENCE\n" + alternative[task["id"]])
    if task["manual"]:
        display.text("\nGUIDED EXERCISE: completion is self-reported and scored separately.")
    display.text("\nCONTROLS: answer/check | hint | skip | menu | quit")
    prepared = False
    while True:
        answer = input("\nAnswer/check > ").strip()
        action = answer.lower()
        if action in ("quit", "menu"):
            save_state(root, state)
            return action
        if action == "hint":
            record["hints"] += 1
            if record["hints"] == 1:
                display.text("\nHINT: " + task["clue"])
            else:
                display.text("\nEXAMPLE COMMANDS (run each line separately):")
                display.command(task["command"] or "Follow the task's keyboard instructions.")
            save_state(root, state)
            continue
        if action == "skip":
            if record["status"] not in ("independent", "practised", "guided"):
                record["status"] = "skipped"
            save_state(root, state)
            display.text("\nSKIPPED\n" + task["why"])
            input("\nEnter to continue > ")
            return "next"
        if task["prepare"] and action == "ready":
            task["prepare"]()
            prepared = True
            display.text("\nA new line was appended. Read it in your command tab, stop tail with Ctrl+C, then submit the code here.")
            continue
        record["attempts"] += 1
        try:
            correct = action == "done" if task["manual"] else bool(task["check"](answer))
            if task["prepare"]:
                correct = correct and prepared
        except (OSError, ValueError, UnicodeError):
            correct = False
        if correct:
            if record["status"] not in ("independent", "practised", "guided"):
                record["status"] = "guided" if task["manual"] else ("independent" if record["attempts"] == 1 and record["hints"] == 0 else "practised")
            save_state(root, state)
            display.text("\n{}\n{}".format("RECORDED" if task["manual"] else "PASSED", task["why"]))
            input("\nEnter to continue > ")
            return "next"
        save_state(root, state)
        display.text("\nNOT YET. Check your current folder, filenames, and output. Type hint for help.")


def show_results(tasks, state, display):
    display.screen("YOUR PRACTICE RESULTS")
    results = state["results"]
    for label, status in [("Verified: first attempt without hints", "independent"),
                          ("Verified: completed with hints or retries", "practised"),
                          ("Guided exercises acknowledged", "guided"), ("Skipped", "skipped")]:
        count = sum(results.get(t["id"], {}).get("status") == status for t in tasks)
        display.text("{}: {}".format(label, count))
    display.text("\nVerification checks answers and file outcomes; it cannot prove which commands you used in another terminal.")
    for task in tasks:
        status = results.get(task["id"], {}).get("status", "unfinished")
        if status != "unfinished":
            display.text("[{}] {}".format(status, task["title"]))
    input("\nEnter to return to menu > ")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab", type=Path, help="Use or resume a specified environment folder")
    parser.add_argument("--new", action="store_true", help="Create a fresh environment without deleting the old one")
    parser.add_argument("--no-clear", action="store_true", help="Keep earlier screens visible")
    parser.add_argument("--list", action="store_true", help="List chapters without creating an environment")
    args = parser.parse_args()
    if args.list:
        for i, title in enumerate(CHAPTERS, 1):
            print("{:2}. {}".format(i, title))
        return
    base = args.lab or Path(__file__).resolve().parent / "terminal_academy_environment"
    if args.new:
        base = base.with_name(base.name + "-" + time.strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(2))
    root = base.expanduser().resolve()
    marker = root / ".academy.json"
    if marker.is_file():
        state = json.loads(marker.read_text(encoding="utf-8"))
        if state.get("version") != VERSION:
            raise ValueError("Environment version differs. Start a fresh one with --new.")
    else:
        state = create_environment(root)
    display = Display(args.no_clear)
    runtime = Runtime(state["token"])
    tasks = build_tasks(root, state, runtime)
    try:
        display.screen("TERMINAL ACADEMY", "Real commands. Fictional files. Saved progress.")
        display.text("\nOpen a SECOND terminal tab and run this line there:")
        display.command("cd " + shlex.quote(str(root)))
        display.text("\nThis tab is your instructor. The other tab executes your commands. Start each task from the lab folder; task screens print its exact path.")
        display.text("\nEverything needed for file exercises is included. Some commands such as tree, nano, or networking tools may need installation; see the README. Optional DNS practice needs internet; all other network exercises are local inspection or loopback.")
        display.text("\nThe instructor starts a disposable worker and a loopback-only HTTP server for practice. Both stop when you exit. Files and progress stay here for your next session.")
        display.text("\nEnter answers at the instructor prompt, not shell commands, unless a task asks you to write a command. Type hint twice to see an example solution. Reading hints is part of learning.")
        input("\nEnter when your second tab is ready > ")
        while True:
            display.screen("TERMINAL ACADEMY", "Choose a chapter | {} exercises".format(len(tasks)))
            for chapter, title in enumerate(CHAPTERS):
                subset = [t for t in tasks if t["chapter"] == chapter]
                complete = sum(state["results"].get(t["id"], {}).get("status") in ("independent", "practised", "guided") for t in subset)
                display.text("{:2}. {:42} {}/{}".format(chapter + 1, title, complete, len(subset)))
            display.text("\nR = results | N = next unfinished | M = mastery method | Q = quit")
            choice = input("\nChoose > ").strip().lower()
            if choice == "q":
                break
            if choice == "r":
                show_results(tasks, state, display)
                continue
            if choice == "m":
                display.screen("HOW TO MASTER A COMMAND")
                display.text("1. State the task in plain English.\n2. Choose the command and explain its options and paths.\n3. Predict its output or changes.\n4. Run it on practice files.\n5. Inspect the result.\n6. Repeat later in a fresh environment without hints.")
                display.text("\nStart with navigation, files, and search. Build toward pipes, permissions, processes, and networking. Use man and hints as learning tools.")
                display.text("\nA result check confirms an answer or file outcome; it cannot prove understanding. Explain your reasoning out loud. Guided keyboard exercises are reported separately.")
                display.text("\nUse --new when launching this script to generate another environment. Your previous lab is preserved.")
                input("\nEnter to return > ")
                continue
            if choice == "n":
                remaining = [t for t in tasks if state["results"].get(t["id"], {}).get("status") not in ("independent", "practised", "guided")]
                selected = remaining[:1]
                if not selected:
                    display.text("All tasks completed. Use --new for another fresh practice run.")
                    input("\nEnter > ")
                    continue
            elif choice.isdigit() and 1 <= int(choice) <= len(CHAPTERS):
                selected = [t for t in tasks if t["chapter"] == int(choice) - 1 and state["results"].get(t["id"], {}).get("status") not in ("independent", "practised", "guided")]
                if not selected:
                    display.text("This chapter is complete. A fresh environment lets you practise again.")
                    input("\nEnter > ")
                    continue
            else:
                continue
            for task in selected:
                chapter_tasks = [t for t in tasks if t["chapter"] == task["chapter"]]
                action = run_task(task, chapter_tasks.index(task) + 1, len(chapter_tasks), root, state, display)
                if action == "quit":
                    return
                if action == "menu":
                    break
    except (KeyboardInterrupt, EOFError):
        print("\nSession stopped.")
    finally:
        save_state(root, state)
        runtime.close()
        print("\nProgress saved. Resume by running the same script again.")
        print("Environment: " + str(root))
        print("Specific resume command:")
        print("python3 {} --lab {}".format(shlex.quote(str(Path(__file__).resolve())), shlex.quote(str(root))))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print("Could not start the environment: {}".format(error), file=sys.stderr)
        sys.exit(1)
