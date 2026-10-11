"""Exercise Lessons 3-6 through real local commands and the shared instructor."""

import contextlib
import getpass
import importlib
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

LESSONS = Path(__file__).resolve().parents[1] / 'lessons'
sys.path.insert(0, str(LESSONS))
import lesson_support as support


class NewLessonTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        (self.root / 'reports').mkdir()
        self.resources = support.Resources()
        self.addCleanup(self.temporary.cleanup)
        self.addCleanup(self.resources.close)
        # A skipped traversal exercise leaves a directory deliberately blocked.
        self.addCleanup(self.restore_directories)

    def restore_directories(self):
        for path in self.root.rglob('*'):
            if path.is_dir():
                path.chmod(0o700)

    def build(self, number):
        return importlib.import_module('terminal_practice_' + str(number)).build_lesson(self.root, self.resources)

    def command(self, recipe):
        return subprocess.run(recipe, shell=True, cwd=self.root, text=True,
                              capture_output=True, timeout=15)

    def test_lesson_three_real_permissions(self):
        lesson = self.build(3)
        self.assertEqual(len(lesson['tasks']), 10)
        self.assertFalse(lesson['tasks'][4]['check'](''))
        answers = ['', getpass.getuser(), '', 'rw-', '', '',
                   'Permission practice complete', '', 'Traversal works', '']
        for item, answer in zip(lesson['tasks'], answers):
            with self.subTest(task=item['title']):
                result = self.command(item['command'])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(item['check'](answer))
        (self.root / 'fixtures/challenge/secret.txt').chmod(0o644)
        self.assertFalse(lesson['tasks'][-1]['check'](''))

    def test_lesson_four_real_process_and_http_commands(self):
        lesson = self.build(4)
        self.assertEqual(len(lesson['tasks']), 10)
        worker = self.resources.workers[1]
        self.assertFalse(lesson['tasks'][-1]['check'](''))
        for index, item in enumerate(lesson['tasks']):
            with self.subTest(task=item['title']):
                result = self.command(item['command'])
                self.assertEqual(result.returncode, 0, result.stderr)
                if index == 9:
                    worker.wait(timeout=5)
                answer = str(worker.pid) if index == 1 else (str(os.getpid()) if index == 3 else '')
                self.assertTrue(item['check'](answer))
        self.assertIsNone(self.resources.workers[0].poll())

    def test_lesson_five_real_loopback_commands(self):
        lesson = self.build(5)
        self.assertEqual(len(lesson['tasks']), 10)
        for index, item in enumerate(lesson['tasks']):
            with self.subTest(task=item['title']):
                if index == 8:
                    continue  # Optional internet DNS is intentionally not contacted.
                result = self.command(item['command'])
                if index == 3 and result.returncode != 0:
                    continue  # An offline machine may have no default route.
                self.assertEqual(result.returncode, 0, result.stderr)
                answer = '127.0.0.1' if index == 2 else ('no' if index == 9 else '')
                self.assertTrue(item['check'](answer))
        (self.root / 'reports/body.txt').write_text('Different service\n')
        self.assertFalse(lesson['tasks'][7]['check'](''))

    def test_lesson_six_real_investigation_commands(self):
        lesson = self.build(6)
        self.assertEqual(len(lesson['tasks']), 10)
        original = (self.root / 'fixtures/logs/auth.log').read_bytes()
        for index, item in enumerate(lesson['tasks']):
            with self.subTest(task=item['title']):
                result = self.command(item['command'])
                self.assertEqual(result.returncode, 1 if index == 7 else 0, result.stderr)
                answer = ''
                if index == 1:
                    answer = result.stdout.strip()
                elif index == 2:
                    answer = re.search(r'Case code: (\w+)', result.stdout).group(1)
                elif index == 4:
                    answer = result.stdout.strip()
                elif index == 6:
                    answer = re.search(r'source=(\S+)', result.stdout).group(1)
                self.assertTrue(item['check'](answer))
        self.assertEqual((self.root / 'fixtures/logs/auth.log').read_bytes(), original)
        (self.root / 'reports/auth-evidence.log').chmod(0o644)
        self.assertFalse(lesson['tasks'][-1]['check'](''))

    def test_guided_scoring_and_pause(self):
        lesson = self.build(3)
        item = lesson['tasks'][0]
        self.command(item['command'])
        with contextlib.redirect_stdout(io.StringIO()), patch('builtins.input', side_effect=['', '']) as entered:
            result = support.run_task(item, 1, 10, 3, support.Display(no_clear=True))
        self.assertEqual(result, 'guided')
        self.assertIn('continue', entered.call_args.args[0])

    def test_hints_reread_retry_skip_and_quit(self):
        lesson = self.build(3)
        display = support.Display(no_clear=True)
        with contextlib.redirect_stdout(io.StringIO()):
            with patch('builtins.input', side_effect=['task', 'hint', 'hint', 'wrong', getpass.getuser(), '']):
                self.assertEqual(support.run_task(lesson['tasks'][1], 2, 10, 3, display), 'practised')
            with patch('builtins.input', side_effect=['skip', '']):
                self.assertEqual(support.run_task(lesson['tasks'][1], 2, 10, 3, display), 'skipped')
            with patch('builtins.input', return_value='quit'):
                self.assertEqual(support.run_task(lesson['tasks'][1], 2, 10, 3, display), 'quit')

    def test_task_screen_wraps_at_narrow_width(self):
        lesson = self.build(6)
        display = support.Display(no_clear=True)
        display.width = 40
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            display.task(lesson['tasks'][3], 4, 10, 6)
        text = captured.getvalue()
        self.assertIn('YOUR STEPS', text)
        self.assertIn('SUBMIT IN THIS TAB', text)
        self.assertTrue(all(len(line) <= 40 for line in text.splitlines()))

    def test_resources_cleanup_and_no_hostname_lookup(self):
        worker = self.resources.worker('cleanup-test')
        with patch('socket.getfqdn', side_effect=AssertionError('Loopback server must not need DNS')):
            self.resources.http('test')
        self.resources.close()
        self.assertIsNotNone(worker.poll())
        self.assertFalse(self.resources.thread.is_alive())

    def test_all_entry_points_skip_and_exit(self):
        for number in range(3, 7):
            with self.subTest(lesson=number), tempfile.TemporaryDirectory() as temporary:
                environment = dict(os.environ, TMPDIR=temporary, TMP=temporary, TEMP=temporary)
                result = subprocess.run([sys.executable, str(LESSONS / ('terminal_practice_{}.py'.format(number))), '--no-clear'],
                                        input='\n' * 3 + 'skip\n\n' * 10, text=True,
                                        capture_output=True, env=environment, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('Skipped: 10', result.stdout)
                self.assertIn('Guided example completed: 0', result.stdout)
                # Restore traversal on a skipped Lesson 3 fixture before cleanup.
                for blocked in Path(temporary).glob('terminal-lesson3-*/fixtures/blocked'):
                    blocked.chmod(0o700)


if __name__ == '__main__':
    unittest.main()
