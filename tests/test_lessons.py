"""Check the original standalone lessons using real commands on temporary files."""

import importlib.util
import contextlib
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]


def load_lesson(filename):
    spec = importlib.util.spec_from_file_location(filename.removesuffix('.py'), REPO / 'lessons' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OriginalLessonTests(unittest.TestCase):
    def command(self, command, cwd):
        return subprocess.run(command, shell=True, cwd=cwd, text=True,
                              capture_output=True, check=True, timeout=10).stdout

    def test_lesson_one_real_commands(self):
        lesson = load_lesson('terminal_practice.py')
        with tempfile.TemporaryDirectory() as parent:
            for trial in range(3):
                with self.subTest(trial=trial):
                    root, code, username, incident = lesson.make_lab(parent)
                    tasks = lesson.build_tasks(root, code, username, incident)
                    self.assertEqual(len(tasks), 10)
                    output = lambda command: self.command(command, root)
                    answers = [
                        output('pwd').strip(),
                        next(name for name in output('ls').splitlines() if name.endswith('.txt')),
                        re.search(r'Training code: (\w+)', output('cat briefing.txt')).group(1),
                        next(name for name in output('ls -a').splitlines() if name.startswith('.') and name not in ('.', '..')),
                        output("find . -type f -name 'incident-note.txt'").strip(),
                        re.search(r'user=(\w+)', output("grep 'LOGIN_FAILED' evidence/login.log")).group(1),
                    ]
                    output('mkdir -p reports')
                    answers.append('')
                    output('cp briefing.txt reports/briefing-copy.txt')
                    answers.append('')
                    output('mv inbox/draft.txt inbox/final.txt')
                    answers.append('')
                    answers.append(output('wc -l evidence/login.log').split()[0])
                    for task, answer in zip(tasks, answers):
                        self.assertTrue(task['check'](answer), task['title'])
                    (root / 'reports/briefing-copy.txt').write_text('incorrect\n')
                    self.assertFalse(tasks[7]['check'](''))
                    self.assertFalse(tasks[4]['check']('not-a-real-file.txt'))

    def test_lesson_two_real_commands(self):
        lesson = load_lesson('terminal_practice_2.py')
        with tempfile.TemporaryDirectory() as parent:
            for trial in range(3):
                with self.subTest(trial=trial):
                    lab = lesson.make_lab(parent)
                    root, case = lab[:2]
                    tasks = lesson.build_tasks(*lab)
                    self.assertEqual(len(tasks), 12)
                    output = lambda command: self.command(command, case)
                    answers = [self.command('cd case && pwd', root).strip(),
                               output('cat "analyst notes.txt"').strip().split(': ')[1]]
                    output('head -n 3 logs/auth.log > reports/start.txt')
                    answers.append('')
                    output('tail -n 2 logs/auth.log > reports/end.txt')
                    answers.append('')
                    output("grep 'LOGIN_FAILED' logs/auth.log > reports/failed.txt")
                    answers.append('')
                    answers.append(output("grep -n 'LOGIN_FAILED' logs/auth.log").splitlines()[0].split(':')[0])
                    answers.append(output("grep 'LOGIN_FAILED' logs/auth.log | wc -l").strip())
                    output('sort users.txt | uniq > reports/unique-users.txt')
                    answers.append('')
                    output("echo 'Review complete' >> reports/summary.txt")
                    answers.append('')
                    answers.append(output("find archive -type f -name 'incident details.txt'").strip())
                    output('chmod 600 private.txt')
                    answers.append('')
                    output("grep -v 'INFO' logs/auth.log > reports/activity.txt")
                    answers.append('')
                    for task, answer in zip(tasks, answers):
                        self.assertTrue(task['check'](answer), task['title'])
                    output("echo 'Review complete' >> reports/summary.txt")
                    self.assertFalse(tasks[8]['check'](''))
                    output('chmod 644 private.txt')
                    self.assertFalse(tasks[10]['check'](''))

    def test_both_standalone_entry_points(self):
        for filename, count in [('terminal_practice.py', 10), ('terminal_practice_2.py', 12)]:
            with self.subTest(lesson=filename), tempfile.TemporaryDirectory() as temporary:
                environment = dict(os.environ, TMPDIR=temporary, TMP=temporary, TEMP=temporary)
                result = subprocess.run([sys.executable, str(REPO / 'lessons' / filename)],
                                        input='\n' + ('skip\n\n' if filename == 'terminal_practice_2.py' else 'skip\n') * count, text=True, capture_output=True,
                                        env=environment, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('RESULTS', result.stdout)
                self.assertIn('Skipped: ' + str(count), result.stdout)

    def test_lesson_two_readable_task_screen(self):
        lesson = load_lesson('terminal_practice_2.py')
        with tempfile.TemporaryDirectory() as parent:
            tasks = lesson.build_tasks(*lesson.make_lab(parent))
            display = lesson.Display(no_clear=True)
            display.width = 40
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                display.task(tasks[1], 2, 12)
            text = captured.getvalue()
            self.assertIn('TASK 02 OF 12', text)
            self.assertIn('FILE: analyst notes.txt', text)
            self.assertIn('YOUR STEPS', text)
            self.assertIn('SUBMIT IN THIS TAB', text)
            self.assertNotIn('\033', text)
            self.assertTrue(all(len(line) <= 40 for line in text.splitlines()))

    def test_lesson_two_pauses_after_feedback_and_keeps_hint_scoring(self):
        lesson = load_lesson('terminal_practice_2.py')
        with tempfile.TemporaryDirectory() as parent:
            lab = lesson.make_lab(parent)
            tasks = lesson.build_tasks(*lab)
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured), patch('builtins.input', side_effect=['task', 'hint', 'hint', lab[2], '']) as entered:
                result = lesson.run_task(tasks[1], 2, 12, lesson.Display(no_clear=True))
            self.assertEqual(result, 'practised')
            self.assertIn('WHAT YOU LEARNED', captured.getvalue())
            self.assertIn('next task', entered.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
