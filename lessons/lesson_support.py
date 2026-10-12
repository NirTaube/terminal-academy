"""Shared, standard-library-only instructor for Lessons 3-6."""

import argparse
import http.server
import os
from pathlib import Path
import platform
import re
import secrets
import shlex
import shutil
import socketserver
import subprocess
import sys
import tempfile
import textwrap
import threading


def write(path, content, mode=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if mode is not None:
        path.chmod(mode)


def read(path):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def path_is(answer, expected, root):
    try:
        path = Path(answer)
        return (path if path.is_absolute() else root / path).resolve() == expected.resolve()
    except (OSError, ValueError):
        return False


def task(title, steps, check, command, clue, explanation, source=None,
         output=None, submit="Press Enter here to check your work.", guided=False):
    return dict(title=title, steps=steps, check=check, command=command,
                clue=clue, explanation=explanation, source=source,
                output=output, submit=submit, guided=guided)


def capture(root, title, steps, filename, command, clue, explanation,
            expected=None, pattern=None, source=None, guided=False):
    target = root / "reports" / filename
    def check(answer):
        if not target.is_file():
            return False
        contents = read(target)
        return contents == expected if expected is not None else bool(re.search(pattern, contents, re.M))
    # Redirect stdout first, then duplicate stderr, so help written to stderr
    # reaches the report instead of the instructor's original output stream.
    combined = command.endswith(" 2>&1")
    if combined:
        command = command[:-5]
    recipe = command + " > reports/" + filename + (" 2>&1" if combined else "")
    return task(title, steps, check, recipe,
                clue, explanation, source=source, output="reports/" + filename,
                guided=guided)


class Resources:
    def __init__(self):
        self.workers = []
        self.server = None
        self.thread = None
        self.port = None

    def worker(self, label):
        worker = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(86400)", label],
                                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
        self.workers.append(worker)
        return worker

    def http(self, token):
        body = "Training server\nCase code: {}\n".format(token).encode()
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_HEAD(self):
                self.send_response(200)
                self.send_header("X-Lesson-Code", token)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()

            def do_GET(self):
                self.do_HEAD()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        class LocalServer(http.server.ThreadingHTTPServer):
            def server_bind(self):
                socketserver.TCPServer.server_bind(self)
                self.server_name = "localhost"
                self.server_port = self.server_address[1]

        self.server = LocalServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self.port

    def close(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        for worker in self.workers:
            if worker.poll() is None:
                worker.terminate()
                try:
                    worker.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    worker.kill()
                    worker.wait()


class Display:
    def __init__(self, no_clear=False):
        self.clear = sys.stdout.isatty() and not no_clear
        self.width = max(32, min(72, shutil.get_terminal_size((74, 24)).columns - 2))

    def text(self, text=""):
        for line in text.split("\n"):
            print(textwrap.fill(line, self.width) if line else "")

    def screen(self, title):
        if self.clear:
            print("\033[2J\033[H", end="")
        print("=" * self.width)
        self.text(title)
        print("=" * self.width)

    def commands(self, commands):
        # Preserve each command as one copyable line, even if the terminal wraps it.
        for line in commands.splitlines():
            print("  " + line)

    def task(self, item, number, total, lesson):
        self.screen("LESSON {} | TASK {:02d} OF {:02d}".format(lesson, number, total))
        self.text(item["title"])
        self.text("\nCOMMAND TAB: stay in your lesson's lab folder.")
        if item.get("target"):
            self.text("LOCAL TARGET: " + item["target"])
        if item["source"]:
            self.text("FILE / TARGET: " + item["source"])
        if item["output"]:
            self.text("SAVE TO: " + item["output"])
        self.text("\nYOUR STEPS")
        for index, step in enumerate(item["steps"], 1):
            print(textwrap.fill("{}. {}".format(index, step), self.width, subsequent_indent="   "))
        if item["guided"]:
            if item.get("walkthrough"):
                self.text("\nGUIDED GUI EXERCISE: follow the steps in the named application. Completion is self-reported.")
            else:
                self.text("\nGUIDED EXAMPLE: run these lines in the command tab.")
                self.commands(item["command"])
        self.text("\nSUBMIT IN THIS TAB\n" + item["submit"])
        self.text("\nCONTROLS: hint | task (reread) | skip | quit")


def run_task(item, number, total, lesson, display):
    display.task(item, number, total, lesson)
    attempts = hints = 0
    while True:
        answer = input("\nAnswer / Enter to check > ").strip()
        action = answer.lower()
        if action == "quit":
            return "quit"
        if action == "task":
            display.task(item, number, total, lesson)
            continue
        if action == "hint":
            hints += 1
            if hints == 1:
                display.text("\nHINT\n" + item["clue"])
            else:
                display.text("\nEXAMPLE COMMANDS")
                display.commands(item["command"])
            continue
        if action == "skip":
            display.text("\nSKIPPED\n" + item["explanation"])
            input("\nEnter to continue > ")
            return "skipped"
        attempts += 1
        try:
            correct = item["check"](answer)
        except (OSError, UnicodeError, ValueError):
            correct = False
        if correct:
            status = "guided" if item["guided"] else ("independent" if attempts == 1 and hints == 0 else "practised")
            display.text("\nPASSED\n\nWHAT YOU LEARNED\n" + item["explanation"])
            input("\nEnter to continue > ")
            return status
        display.text("\nNOT YET. Check the result, filenames, and working folder. Use hint for help.")


def run_lesson(number, builder, argv=None, resource_factory=Resources):
    parser = argparse.ArgumentParser(description="Hands-on Terminal Academy Lesson {}".format(number))
    parser.add_argument("--no-clear", action="store_true", help="Keep earlier screens visible")
    args = parser.parse_args(argv)
    if platform.system() not in ("Darwin", "Linux"):
        parser.error("Use macOS or a Linux terminal, including Kali.")
    root = Path(tempfile.mkdtemp(prefix="terminal-lesson{}-".format(number))).resolve()
    (root / "reports").mkdir()
    resources = resource_factory()
    display = Display(args.no_clear)
    results = []
    lesson = None
    try:
        lesson = builder(root, resources)
        display.screen("LESSON {}: {}".format(number, lesson["title"]))
        display.text("\nSETUP\n1. Keep this instructor tab open.\n2. Open a SECOND terminal tab for commands.\n3. Run this line in your command tab:")
        display.commands("cd " + shlex.quote(str(root)))
        display.text("\nAll files are fictional. This is a fresh lab for this session. No exercise needs sudo. Keep this instructor running until you finish.")
        if resources.workers or resources.server:
            display.text("The instructor owns the disposable workers and loopback server used here. It stops them when you exit.")
        input("\nEnter when your command tab is ready > ")
        for title, text in lesson["learn"]:
            display.screen("LESSON {}: {}".format(number, title))
            display.text("\n" + text)
            input("\nEnter to continue > ")
        tasks = lesson["tasks"]
        for index, item in enumerate(tasks, 1):
            status = run_task(item, index, len(tasks), number, display)
            if status == "quit":
                break
            results.append((item["title"], status))
    except (EOFError, KeyboardInterrupt):
        display.text("\nSession stopped.")
    except OSError as error:
        display.text("\nCould not prepare part of the lesson: " + str(error))
    finally:
        resources.close()
        if lesson is not None:
            display.screen("LESSON {}: RESULTS".format(number))
            for label, status in [("Guided example completed", "guided"),
                                  ("First attempt without hints", "independent"),
                                  ("Completed with help or retries", "practised"),
                                  ("Skipped", "skipped")]:
                display.text("{}: {}".format(label, sum(s == status for _, s in results)))
            display.text("Unfinished: {}".format(len(lesson["tasks"]) - len(results)))
            display.text("")
            for title, status in results:
                display.text("[{}] {}".format(status, title))
            display.text("\nResults check answers and file outcomes, not which commands you entered. Guided examples are counted separately.")
        display.text("\nPractice files are kept for review at:")
        print(root)
        display.text("\nRun the lesson again for fresh practice. Short lessons do not save progress.")
