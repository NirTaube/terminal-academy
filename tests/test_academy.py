"""Local, dependency-free checks. Real recipes run only inside temporary labs."""

import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import terminal_academy as academy

SCRIPT = Path(academy.__file__).resolve()


class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'lab'
        self.state = academy.create_environment(self.root)
        self.tasks = {t['id']: t for t in academy.build_tasks(self.root, self.state, None)}

    def test_catalog_and_unique_ids(self):
        tasks = academy.build_tasks(self.root, self.state, None)
        self.assertEqual(len(tasks), 87)
        self.assertEqual(len({t['id'] for t in tasks}), len(tasks))
        self.assertEqual({t['chapter'] for t in tasks}, set(range(12)))

    def test_environment_contains_fixtures_and_no_progress(self):
        self.assertTrue((self.root / 'fixtures/logs/auth.log').is_file())
        self.assertTrue((self.root / 'fixtures/docs/analyst notes.txt').is_file())
        self.assertEqual(self.state['results'], {})
        self.assertIn(self.state['code'], academy.read_text(self.root / 'fixtures/docs/briefing.txt'))

    def test_existing_files_are_preserved(self):
        original = (self.root / '.academy.json').read_text()
        with self.assertRaises(ValueError):
            academy.create_environment(self.root)
        self.assertEqual((self.root / '.academy.json').read_text(), original)

    def test_missing_paths_and_wrong_output_are_rejected(self):
        self.assertFalse(self.tasks['head']['check']('check'))
        academy.write(self.root / 'reports/head.txt', 'incorrect\n')
        self.assertFalse(self.tasks['head']['check']('check'))
        self.assertFalse(self.tasks['find-name']['check']('fixtures/not-present.txt'))

    def test_relative_and_absolute_paths(self):
        self.assertTrue(self.tasks['find-name']['check']('fixtures/archive/2026/incident-note.txt'))
        self.assertTrue(self.tasks['find-name']['check'](str(self.root / 'fixtures/archive/2026/incident-note.txt')))

    def test_permission_checks_reject_readable_private_file(self):
        self.assertFalse(self.tasks['chmod-private']['check']('check'))
        (self.root / 'fixtures/private.txt').chmod(0o600)
        self.assertTrue(self.tasks['chmod-private']['check']('check'))

    def test_append_rejects_duplicate_lines(self):
        target = self.root / 'reports/summary.txt'
        academy.write(target, 'Investigation summary\nReview complete\n')
        self.assertTrue(self.tasks['append']['check']('check'))
        academy.write(target, 'Investigation summary\nReview complete\nReview complete\n')
        self.assertFalse(self.tasks['append']['check']('check'))

    def test_live_log_appends_without_rewriting(self):
        target = self.root / 'fixtures/live.log'
        before = target.read_bytes()
        academy.append_live_line(self.root, self.state['token'])
        self.assertTrue(target.read_bytes().startswith(before))
        self.assertIn(self.state['token'], target.read_text())

    def test_platform_recipes(self):
        for system, address, routes, sockets in [
            ('Linux', 'ip -br address', 'ip route', 'ss -lnt'),
            ('Darwin', 'ifconfig', 'route -n get default', 'lsof -nP -iTCP -sTCP:LISTEN'),
        ]:
            with self.subTest(system=system), patch.object(academy.platform, 'system', return_value=system):
                tasks = {t['id']: t for t in academy.build_tasks(self.root, self.state, None)}
                self.assertTrue(tasks['net-address']['command'].startswith(address))
                self.assertTrue(tasks['net-route']['command'].startswith(routes))
                self.assertTrue(tasks['net-listeners']['command'].startswith(sockets))

    def run_task(self, key, inputs):
        with contextlib.redirect_stdout(io.StringIO()), patch('builtins.input', side_effect=inputs):
            return academy.run_task(self.tasks[key], 1, 1, self.root, self.state, academy.Display(no_clear=True))

    def test_hints_scoring_and_persistence(self):
        self.assertEqual(self.run_task('cat', ['hint', 'hint', self.state['code'], '']), 'next')
        result = self.state['results']['cat']
        self.assertEqual(result['status'], 'practised')
        self.assertEqual(result['hints'], 2)
        saved = json.loads((self.root / '.academy.json').read_text())
        self.assertEqual(saved['results']['cat']['status'], 'practised')

    def test_first_attempt_and_guided_are_distinct(self):
        self.run_task('cat', [self.state['code'], ''])
        self.run_task('less', ['done', ''])
        self.assertEqual(self.state['results']['cat']['status'], 'independent')
        self.assertEqual(self.state['results']['less']['status'], 'guided')

    def test_skip_menu_and_quit(self):
        self.assertEqual(self.run_task('pwd', ['skip', '']), 'next')
        self.assertEqual(self.state['results']['pwd']['status'], 'skipped')
        self.assertEqual(self.run_task('pwd', ['menu']), 'menu')
        self.assertEqual(self.run_task('pwd', ['quit']), 'quit')

    def test_incorrect_answer_then_retry(self):
        self.run_task('cat', ['wrong', self.state['code'], ''])
        self.assertEqual(self.state['results']['cat']['status'], 'practised')
        self.assertEqual(self.state['results']['cat']['attempts'], 2)


@unittest.skipUnless(academy.platform.system() in ('Darwin', 'Linux'), 'Recipes target macOS and Linux')
class RecipeTests(unittest.TestCase):
    def test_real_command_recipes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'lab'
            state = academy.create_environment(root)
            runtime = academy.Runtime(state['token'])
            try:
                tasks = academy.build_tasks(root, state, runtime)
                answers = {
                    'pwd': str(root.resolve()), 'ls': 'START_HERE.txt', 'ls-hidden': '.hidden-note',
                    'cd-path': str((root / 'fixtures/docs').resolve()),
                    'cd-parent': str((root / 'fixtures').resolve()), 'cd-home': str(Path.home()),
                    'space': state['token'], 'cat': state['code'], 'file-type': 'text',
                    'find-name': 'fixtures/archive/2026/incident-note.txt', 'whoami': academy.getpass.getuser(),
                    'sudo': 'yes', 'man': '-n', 'errors': 'no', 'final-count': '2',
                    'final-verify': 'head -n 5 reports/final-failures.txt',
                    'chmod-execute': 'Training script ran', 'error-command': 'command -v',
                    'error-permission': 'ls -l fixtures/private.txt',
                }
                checked = 0
                for task in tasks:
                    key = task['id']
                    with self.subTest(task=key):
                        if task['manual'] or key in ('dig', 'history', 'tail-follow'):
                            continue
                        if key == 'nano':
                            # The file validator can be tested without an interactive editor.
                            academy.write(root / 'fixtures/edit-me.txt', 'Status: reviewed\n')
                        elif key not in ('sudo', 'man', 'final-verify', 'error-command'):
                            command = task['command']
                            executable = command.split()[0] if command else ''
                            if executable not in ('cd', 'echo', 'kill') and not shutil.which(executable):
                                continue
                            if key in ('curl', 'net-listeners') and not runtime.server:
                                continue
                            result = subprocess.run(command, shell=True, cwd=root, input='y\n', text=True,
                                                    capture_output=True, timeout=20)
                            if key == 'net-route' and not (root / 'reports/net-route.txt').read_text().strip():
                                continue  # A default route is not guaranteed in an offline runner.
                            allowed = (0, 1, 2) if key == 'stderr' else ((0, 1) if key == 'diff' else (0,))
                            self.assertIn(result.returncode, allowed, result.stderr)
                            if key == 'kill':
                                runtime.worker.wait(timeout=5)
                        self.assertTrue(task['check'](answers.get(key, 'check')), key)
                        checked += 1
                self.assertGreaterEqual(checked, 50)
            finally:
                runtime.close()
            self.assertIsNotNone(runtime.worker.poll())

    def test_worker_and_server_cleanup(self):
        runtime = academy.Runtime('test-token')
        self.assertIsNone(runtime.worker.poll())
        runtime.close()
        self.assertIsNotNone(runtime.worker.poll())
        if runtime.server:
            self.assertFalse(runtime.thread.is_alive())

    def test_local_server_does_not_perform_hostname_lookup(self):
        with patch('socket.getfqdn', side_effect=AssertionError('Local startup must not depend on DNS')):
            runtime = academy.Runtime('test-token')
            try:
                self.assertIsNotNone(runtime.port)
                self.assertEqual(runtime.server.server_name, 'localhost')
            finally:
                runtime.close()


class CommandLineTests(unittest.TestCase):
    def invoke(self, *args, inputs=''):
        return subprocess.run([sys.executable, str(SCRIPT), *args], input=inputs,
                              text=True, capture_output=True, timeout=20)

    def test_list_does_not_create_a_lab(self):
        with tempfile.TemporaryDirectory() as temporary:
            lab = Path(temporary) / 'not-created'
            result = self.invoke('--list', '--lab', str(lab))
            self.assertEqual(result.returncode, 0)
            self.assertIn('12. Final investigation', result.stdout)
            self.assertFalse(lab.exists())

    def test_menu_save_and_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = (Path(temporary) / 'lab').resolve()
            inputs = '\n1\n' + str(root) + '\n\nmenu\nq\n'
            result = self.invoke('--lab', str(root), '--no-clear', inputs=inputs)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Progress saved.', result.stdout)
            saved = json.loads((root / '.academy.json').read_text())
            self.assertEqual(saved['results']['pwd']['status'], 'independent')
            resumed = self.invoke('--lab', str(root), '--no-clear', inputs='\nq\n')
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            self.assertEqual(json.loads((root / '.academy.json').read_text())['results']['pwd']['status'], 'independent')

    def test_new_preserves_old_environment(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'lab'
            state = academy.create_environment(root)
            result = self.invoke('--lab', str(root), '--new', '--no-clear', inputs='\nq\n')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads((root / '.academy.json').read_text()), state)
            self.assertEqual(len(list(Path(temporary).glob('lab-*'))), 1)

    def test_eof_saves_and_exits(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = self.invoke('--lab', str(Path(temporary) / 'lab'), '--no-clear')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Progress saved.', result.stdout)


if __name__ == '__main__':
    unittest.main()
