#!/usr/bin/env python3
"""Lesson 4: processes and a local service."""

import os
import platform
import secrets

from lesson_support import capture, run_lesson, task, write


def build_lesson(root, resources):
    token = secrets.token_hex(3)
    label = "terminal-lesson-worker-" + token
    demo = resources.worker("terminal-lesson-demo-" + token)
    worker = resources.worker(label)
    port = resources.http(token)
    write(root / "fixtures/readme.txt", "Process and service practice\n")
    system = platform.system()
    listener = "lsof -nP -iTCP -sTCP:LISTEN" if system == "Darwin" else "ss -lnt"
    tasks = [
        capture(root, "Guided: inspect one process", ["Inspect the demo process by PID.", "Save its PID and command name to the output file."],
                "demo-process.txt", "ps -p {} -o pid=,comm=".format(demo.pid),
                "-p selects a PID; -o chooses output fields.", "A PID identifies a running process instance. You can select fields instead of inspecting every process.",
                pattern=r"\b{}\b".format(demo.pid), guided=True),
        task("Find a process by its label", ["List running processes.", "Find the process whose command contains the target label."],
             lambda a: a == str(worker.pid), "ps aux | grep '" + label + "'",
             "The matching grep process may also appear; choose the sleeping Python worker, not grep.",
             "Searching process commands helps locate an instance. Similar names alone do not prove its purpose.", source=label, submit="Enter the worker's PID only."),
        capture(root, "Inspect process details", ["Inspect the training worker's PID, parent PID, and command."],
                "worker-details.txt", "ps -p {} -o pid=,ppid=,command=".format(worker.pid),
                "ps can choose multiple fields with -o.", "The parent process created this worker; its command explains what the worker was launched to do.",
                pattern=r"\b{}\s+{}\b.*{}".format(worker.pid, os.getpid(), label)),
        task("Identify the parent", ["Inspect the worker's parent process ID."], lambda a: a == str(os.getpid()),
             "ps -p {} -o ppid=".format(worker.pid), "ppid is the parent PID, distinct from the worker's own PID.",
             "This instructor is the parent of the disposable worker. Parent-child relationships help explain how a program started.",
             source="Worker PID " + str(worker.pid), submit="Enter its parent PID only."),
        capture(root, "Find a listening service", ["Inspect listening TCP sockets.", "Find the instructor's local port {}.".format(port)],
                "listeners.txt", listener, "Mac uses lsof; Kali/Linux uses ss. Keep port numbers numeric.",
                "A listener waits for incoming connections. Listening does not itself prove that the application behaves correctly.", pattern=r":{}\b".format(port)),
        capture(root, "Check the service's response", ["Request headers from the local training server."],
                "headers.txt", "curl -sSI http://127.0.0.1:{}/".format(port), "curl -I makes an HTTP HEAD request.",
                "An HTTP response is application-level evidence beyond merely seeing a listening socket.", pattern=r"(?i)X-Lesson-Code: " + token, source="http://127.0.0.1:{}/".format(port)),
        capture(root, "Inspect filesystem space", ["Show filesystem usage in readable units."], "filesystems.txt", "df -h",
                "df reports space at the filesystem level.", "A filesystem running out of space can affect services and logging.", pattern=r"Filesystem"),
        capture(root, "Measure the fixture directory", ["Show the total storage used by fixtures in readable units."], "directory-size.txt", "du -sh fixtures",
                "du measures directory contents; -s gives a summary.", "du and df answer different questions: directory usage versus filesystem capacity.", pattern=r"fixtures"),
        capture(root, "Inspect system identification", ["Show the kernel/system identification information."], "system.txt", "uname -a",
                "uname reports kernel information, with -a selecting all available fields.", "System information gives context for choosing compatible commands; it is not a full hardware inventory.", pattern=system),
        task("Challenge: stop only the worker", ["Confirm you identified the disposable worker.", "Request termination of ONLY worker PID {}.".format(worker.pid), "Check the result here. Keep the instructor running."],
             lambda a: worker.poll() is not None, "kill -TERM {}".format(worker.pid),
             "SIGTERM requests termination. Select the PID from this exercise, not the instructor or another program.",
             "You inspected a process, established its identity, and stopped the disposable instance. Other workers and the server are cleaned up when this lesson exits.",
             source=label),
    ]
    return dict(title="PROCESSES AND SERVICES", tasks=tasks, learn=[
        ("Programs that are running", "A process is a running program instance. Its PID identifies it while it exists; its PPID identifies its parent.\n\nps shows a snapshot. top shows changing activity. This lesson starts two harmless sleeping workers for inspection. We stop only the designated one."),
        ("From process to service", "A service may listen on a network port. Mac uses lsof to inspect visible listeners; Kali/Linux uses ss.\n\nOur HTTP service listens only on 127.0.0.1, your own machine. curl lets you inspect its response. The instructor stops its workers and server when you exit."),
    ])


if __name__ == "__main__":
    run_lesson(4, build_lesson)
