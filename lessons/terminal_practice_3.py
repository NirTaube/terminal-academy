#!/usr/bin/env python3
"""Lesson 3: users, ownership, and permissions."""

import getpass
import os
import stat

from lesson_support import capture, read, run_lesson, task, write


def build_lesson(root, resources):
    write(root / "demo-note.txt", "Guided permissions example\n", 0o644)
    write(root / "fixtures/readme.txt", "Ordinary file\n", 0o644)
    write(root / "fixtures/private.txt", "Fictional private data\n", 0o644)
    write(root / "fixtures/shared.txt", "Team reference\n", 0o600)
    write(root / "fixtures/run-me.sh", "#!/bin/sh\nprintf 'Permission practice complete\\n'\n", 0o644)
    write(root / "fixtures/blocked/marker.txt", "Traversal works\n", 0o600)
    write(root / "fixtures/challenge/secret.txt", "Challenge data\n", 0o644)
    write(root / "fixtures/challenge/run.sh", "#!/bin/sh\nprintf 'Challenge complete\\n'\n", 0o644)
    (root / "fixtures/blocked").chmod(0o600)
    (root / "workspace").mkdir()
    def mode(path):
        return stat.S_IMODE((root / path).stat().st_mode)

    tasks = [
        task("Guided: set and inspect permissions", ["Set the demo file to owner read/write and group read.", "Inspect the result with a detailed listing."],
             lambda a: mode("demo-note.txt") == 0o640,
             "chmod 640 demo-note.txt\nls -l demo-note.txt",
             "Read=4, write=2, execute=1. Each digit represents one category of users.",
             "640 means owner rw-, group r--, others ---. The leading file-type character is separate.", source="demo-note.txt", guided=True),
        task("Identify your user", ["Print your effective username."], lambda a: a == getpass.getuser(),
             "whoami", "Use the username command from the earlier lessons.", "whoami identifies the user running the command.", submit="Enter the username."),
        capture(root, "Inspect user and group IDs", ["Capture your user and group identity information."], "identity.txt", "id",
                "id shows numeric identities and group memberships.", "Numeric user/group IDs help the operating system decide who is requesting access.", pattern=r"uid={}[\s\S]*gid=".format(os.geteuid())),
        task("Read symbolic permission bits", ["Inspect this file's detailed listing.", "Identify the OWNER's three permission characters."],
             lambda a: a == "rw-", "ls -l fixtures/readme.txt", "In -rw-r--r--, the owner's bits are the first group after the file-type character.",
             "rw- grants the owner read/write but no execute permission.", source="fixtures/readme.txt", submit="Enter the three characters, such as r--."),
        task("Protect a private file", ["Give the owner read/write.", "Give group and others no permission. Leave execute disabled."],
             lambda a: mode("fixtures/private.txt") == 0o600, "chmod 600 fixtures/private.txt", "The owner needs 4+2; the other two categories need 0.",
             "600 restricts the file's mode bits. ACLs and privileged users can affect access separately.", source="fixtures/private.txt"),
        task("Share a readable reference", ["Give the owner read/write.", "Give group and others read only."],
             lambda a: mode("fixtures/shared.txt") == 0o644, "chmod 644 fixtures/shared.txt", "Read-only is 4; read/write is 6.",
             "644 is a common readable-file mode. It allows other users to read this file through these mode bits.", source="fixtures/shared.txt"),
        task("Make a script executable", ["Add execute permission for the owner only.", "Run the script and read its output."],
             lambda a: mode("fixtures/run-me.sh") == 0o744 and a == "Permission practice complete",
             "chmod u+x fixtures/run-me.sh\n./fixtures/run-me.sh", "u+x adds owner execute without replacing the existing read/write bits.",
             "Execute permission allows running the script. ./ supplies an explicit path.", source="fixtures/run-me.sh", submit="Enter the line printed by the script."),
        task("Create a private directory", ["Create workspace/private if needed.", "Give only the owner read, write, and traversal permission."],
             lambda a: (root / "workspace/private").is_dir() and mode("workspace/private") == 0o700,
             "mkdir -p workspace/private\nchmod 700 workspace/private", "Directories need execute permission for traversal; owner rwx is 7.",
             "For directories, read lists names, write changes entries, and execute permits traversal.", source="workspace/private"),
        task("Fix directory traversal", ["The blocked folder has owner read/write but no traversal permission.", "Give the owner rwx and leave group/others with no permissions.", "Read its marker file."],
             lambda a: mode("fixtures/blocked") == 0o700 and a == "Traversal works",
             "chmod 700 fixtures/blocked\ncat fixtures/blocked/marker.txt", "A readable file can still be inaccessible through a directory lacking traversal permission.",
             "Check the full path, including parent-directory permissions, when investigating access failures.", source="fixtures/blocked", submit="Enter the marker file's text."),
        task("Challenge: secure a small project", ["Set fixtures/challenge to owner rwx only.", "Set secret.txt inside it to owner read/write only.", "Set run.sh inside it to owner rwx only."],
             lambda a: mode("fixtures/challenge") == 0o700 and mode("fixtures/challenge/secret.txt") == 0o600 and mode("fixtures/challenge/run.sh") == 0o700,
             "chmod 700 fixtures/challenge\nchmod 600 fixtures/challenge/secret.txt\nchmod 700 fixtures/challenge/run.sh",
             "Choose modes separately for the directory, data file, and executable script.",
             "Permissions should fit each object's purpose. A data file needs no execute bit; a traversable directory does.", source="fixtures/challenge"),
    ]
    return dict(title="USERS AND PERMISSIONS", tasks=tasks, learn=[
        ("Who is asking for access?", "Files have an owner, a group, and permission bits. The OS considers the user making a request.\n\nUse whoami and id to inspect your identity; ls -l shows a file's basic ownership and permissions. No exercise needs sudo."),
        ("Read, write, and execute", "For files: read views data, write changes it, execute allows running it.\n\nValues: read=4, write=2, execute=1. A mode such as 640 has owner/group/others digits.\n\nDirectories differ: execute means traversal. ACLs and administrator privileges can also affect access. Let's practise on fictional files."),
    ])


if __name__ == "__main__":
    run_lesson(3, build_lesson)
