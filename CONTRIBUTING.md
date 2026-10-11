# Contributing

Corrections, clearer explanations, new exercises, and accessibility improvements are welcome.

## Report a problem

Open a GitHub issue with:

- Your operating system and Python version.
- The chapter and task title.
- What you expected and what happened.
- Relevant error text, with personal paths or sensitive information removed as needed.

Do not upload your entire lab folder, shell history, or process listing. Usually the task title and a short error are enough.

## Make a change

1. Fork and clone the repository.
2. Create a branch for the change.
3. Update code and documentation together.
4. Run `python3 -m unittest discover -s tests -v`.
5. Open a pull request explaining the behavior and how you checked it.

Keep the instructor dependency-free. Add exercises in `build_tasks()` with a unique ID, a clear goal, helpful hints, an explanation, and a meaningful result check. Use the generated fixtures rather than a learner's existing files. Label exercises that cannot be verified automatically as guided.

The test suite runs real recipes inside temporary environments. It must not run installation commands, require elevated access, or rely on external network services. Preserve compatibility with Python 3.10+, macOS, and Linux. Add platform alternatives when commands differ.

Use `--new` for a fresh manual practice run. Check readable output at ordinary terminal widths and confirm that entering `menu`, `skip`, `quit`, and Ctrl+C behaves sensibly.
