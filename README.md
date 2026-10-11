# Terminal Academy

Learn your way around a terminal by using real commands on real practice files.

Terminal Academy is a beginner-friendly, hands-on course for macOS and Linux, including Kali. It gives you **87 exercises across 12 chapters**, creates a fictional practice environment, checks your results, and remembers your progress. The instructor uses readable screens with one task at a time.

Built while learning cybersecurity, with AI assistance. Contributions and corrections are welcome.

## Start practising

You need **Python 3.10 or newer**, Git to clone the repository, and two terminal tabs. The instructor has no third-party Python dependencies.

```bash
git clone https://github.com/NirTaube/terminal-academy.git
cd terminal-academy
python3 terminal_academy.py
```

Or download the repository ZIP from GitHub, extract it, open a terminal in that folder, and run the Python command above.

1. Your first tab runs the instructor.
2. Open a second tab to run the exercise commands.
3. Copy the `cd` command printed by the instructor into the second tab.
4. Choose chapter **1** and follow its first task.
5. Run your commands in the second tab; submit answers or type `check` in the instructor tab.

**The instructor prompt does not execute shell commands.** Your second tab is a normal shell. Start each task in the generated lab folder; navigation exercises tell you when to return there.

## Start with the six short lessons

Prefer shorter sessions before the full course? Follow these six hands-on lessons, including the original Lessons 1 and 2. They use real practice files, two-tab instructions, hints, explanations, and results. Lessons 3–6 each start with a brief explanation and a guided example before independent practice.

| Lesson | Exercises | What you practise | Run from the repository folder |
| --- | --- | --- | --- |
| [1. Terminal basics](lessons/terminal_practice.py) | 10 | Finding and reading files, hidden files, searching logs, creating folders, copying, renaming, counting lines | `python3 lessons/terminal_practice.py` |
| [2. Files, pipes, and logs](lessons/terminal_practice_2.py) | 12 | Navigation, spaced filenames, head/tail, filtering logs, pipes, unique names, appending, permissions | `python3 lessons/terminal_practice_2.py` |
| [3. Users and permissions](lessons/terminal_practice_3.py) | 10 | Identity, ownership, symbolic bits, file modes, directory traversal, executable scripts | `python3 lessons/terminal_practice_3.py` |
| [4. Processes and services](lessons/terminal_practice_4.py) | 10 | PIDs, parents, a disposable worker, listening sockets, a local HTTP service, disk/system inspection | `python3 lessons/terminal_practice_4.py` |
| [5. Networking basics](lessons/terminal_practice_5.py) | 10 | Interfaces, loopback, routes, ports, HTTP headers/body, optional DNS | `python3 lessons/terminal_practice_5.py` |
| [6. Mini investigation](lessons/terminal_practice_6.py) | 10 | Context, log extracts, account timeline, configuration differences, cautious reporting, protected copies | `python3 lessons/terminal_practice_6.py` |

Suggested order: **Lessons 1 → 2 → 3 → 4 → 5 → 6 → Terminal Academy**. The short lessons contain 62 exercises, including four guided examples in Lessons 3–6. Experienced learners can start directly with the full course or choose a chapter for review.

Lessons 2–6 present one task per screen, with numbered steps, separate file/output labels, and a pause after feedback. Type `task` to reread the current screen. Add `--no-clear` if you prefer to keep previous screens visible.

Keep the `lessons` folder together: Lessons 3–6 use the sibling `lesson_support.py` instructor. There are no third-party Python dependencies. Run from the repository or download the whole ZIP rather than downloading one of these four scripts alone.

Lessons 4 and 5 start a local HTTP server; Lesson 4 also starts disposable processes. These are cleaned up when the instructor exits. Lesson 5's DNS task is optional and needs a configured DNS resolver. Skip the default-route task if your offline machine has no default route. Lesson 6 uses fictional log entries and documentation addresses; it does not contact them.

Each short lesson generates a fresh temporary lab every time you launch it. The lab stays available for review at the path printed by the script, but short-lesson progress does not resume between sessions or transfer into Terminal Academy. The full course has its own saved progress.

## Controls

| At the chapter menu | Action |
| --- | --- |
| `1` through `12` | Open a chapter |
| `N` | Open the next unfinished task |
| `R` | Review your results |
| `M` | Read the mastery practice method |
| `Q` | Save and quit |

| During a task | Action |
| --- | --- |
| Your answer, `check`, or Enter | Submit what the task requests |
| `hint` | Get a clue |
| `hint` again | See example commands |
| `skip` | Move on |
| `menu` | Return to chapters |
| `quit` | Save and exit |

For the live-log task, follow its special `ready` instructions. Guided keyboard tasks ask you to enter `done`.

## What you learn

| Chapter | Practice |
| --- | --- |
| 1. Navigation and paths | `pwd`, `ls`, `cd`, hidden entries, relative paths, quoting |
| 2. Tree views | Directory structure, depth limits, hidden entries, folders only |
| 3. Creating and managing files | `mkdir`, `touch`, `cp`, `mv`, confirmed removal |
| 4. Reading and editing | `cat`, `less`, `head`, `tail`, `wc`, `file`, `nano`, `diff` |
| 5. Finding files and searching text | `find` and different `grep` options |
| 6. Pipes and redirection | `\|`, `>`, `>>`, `2>`, `&&` |
| 7. Organising text | `sort`, `uniq`, `cut`, `sed` |
| 8. Users and permissions | Identity, groups, permission bits, executable files, `sudo` concepts |
| 9. Processes and system information | `ps`, `top`, a disposable worker, disk usage, system clock |
| 10. Network inspection | Interfaces, routes, listeners, loopback, HTTP headers, optional DNS |
| 11. Help and terminal controls | Manuals, help options, history, shortcuts, common errors |
| 12. Final investigation | Build and verify evidence from a fictional authentication log |

See [CHEATSHEET.md](CHEATSHEET.md) for a quick reference.

## Optional command-line tools

The instructor starts with Python alone. Exercise commands depend on what is installed on your computer. You can skip exercises for missing tools and return to them later.

On macOS, if you already use Homebrew:

```bash
brew install tree nano
```

On Kali or Debian/Ubuntu:

```bash
sudo apt update
sudo apt install tree nano iproute2 iputils-ping curl dnsutils
```

These installation commands change your system packages; the course itself does not install anything or require elevated access. Network exercises automatically choose macOS or Linux commands. Windows is not directly supported; run the course in a Linux environment instead.

## Resume or start fresh

Run the same command to resume:

```bash
python3 terminal_academy.py
```

Create another environment without deleting the old one:

```bash
python3 terminal_academy.py --new
```

Other options:

```bash
python3 terminal_academy.py --list
python3 terminal_academy.py --no-clear
python3 terminal_academy.py --lab /path/to/your/lab
```

By default, files and progress live in `terminal_academy_environment/` beside the script. That folder is ignored by Git. `--new` creates a separate folder with a unique suffix. If you move the course, move its environment folder too, or point `--lab` at the existing location.

The instructor never deletes previous environments. You can inspect them after a session. Use `tree -L 3 terminal_academy_environment` to explore the default one.

## How checking works

- File tasks inspect the actual files, contents, paths, or permission bits.
- Answer tasks compare the submitted answer with the exercise's expected result.
- Keyboard exercises are self-reported and labelled **guided**.
- Some inspection tasks check for expected evidence in captured output, not every option used.

The course does **not** monitor commands in your other tab. A correct result does not prove which command you ran. First-attempt results, assisted completions, and guided exercises are tracked separately; they are learning feedback, not a professional assessment.

For mastery: explain your goal, predict what the command will do, run it, inspect the result, and repeat later without hints.

## What runs during a session

The instructor creates fictional practice files, starts a disposable sleeping process, and runs a training HTTP server bound to `127.0.0.1` on an automatically selected port. These support the process-control and HTTP exercises. Both stop when the instructor exits normally or is interrupted with Ctrl+C.

Files and scores stay on your computer. There is no telemetry. DNS practice is optional and contacts your configured resolver; the other networking tasks inspect your machine or use loopback. Quit the instructor when finished. Commands you type in the second tab are ordinary shell commands, so keep file exercises inside the lab.

## Tests and contributions

```bash
python3 -m unittest discover -s tests -v
```

Tests cover the full course and all six short lessons: fixture creation, real command recipes, incorrect answers, file validation, permission checks, process/server lifecycle, hints, guided versus independent scoring, readable task layouts, the menu, and resuming. Internet DNS, interactive history, and actual keyboard/editor interaction are not automated. Full-course tests skip recipes whose tools are unavailable. GitHub Actions checks macOS and Ubuntu with Python 3.10 and 3.14.

See [CONTRIBUTING.md](CONTRIBUTING.md) to add exercises or report a problem.

## License

[MIT](LICENSE). You can use, modify, and redistribute the project subject to the license terms.
