"""Starter catalogue, local targets, fixture integrity, and available CLI tools."""

import base64
import contextlib
import io
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

TOOLS_DIR = Path(__file__).resolve().parents[1] / 'tool_lessons'
sys.path.insert(0, str(TOOLS_DIR))
import catalog
from lab_environment import PASSWORD, ToolResources, http_capture
from lesson_support import Display, run_task


class ToolStarterTests(unittest.TestCase):
    def test_catalog_and_six_tasks_each(self):
        self.assertEqual(len(catalog.TOOLS), 16)
        self.assertEqual(len({item[0] for item in catalog.TOOLS}), 16)
        for slug, _, _, reference in catalog.TOOLS:
            with self.subTest(tool=slug), tempfile.TemporaryDirectory() as temporary:
                resources = ToolResources()
                try:
                    lesson = catalog.build(slug, Path(temporary), resources)
                    self.assertEqual(len(lesson['tasks']), 6)
                    self.assertEqual(len(lesson['learn']), 2)
                    self.assertTrue(reference.startswith('https://'))
                    self.assertTrue(all(item['explanation'] for item in lesson['tasks']))
                    if resources.server:
                        self.assertEqual(resources.server.server_address[0], '127.0.0.1')
                finally:
                    resources.close()

    def test_http_auth_and_query_boundary(self):
        with ToolResourcesContext() as resources:
            port = resources.web('case-test')
            url = 'http://127.0.0.1:' + str(port)
            request = urllib.request.Request(url + '/protected')
            with self.assertRaises(urllib.error.HTTPError) as failure:
                urllib.request.urlopen(request)
            self.assertEqual(failure.exception.code, 401)
            failure.exception.close()
            request.add_header('Authorization', 'Basic ' + base64.b64encode(('trainee:' + PASSWORD).encode()).decode())
            with urllib.request.urlopen(request) as response:
                self.assertEqual(response.read(), b'Training login accepted\n')
            with urllib.request.urlopen(url + '/item?id=1%20AND%201=1') as response:
                self.assertEqual(response.read(), b'Notebook\n')
            with urllib.request.urlopen(url + '/item?id=1%20AND%201=2') as response:
                self.assertEqual(response.read(), b'\n')
            with urllib.request.urlopen(url + '/safe-item?id=1%20AND%201=1') as response:
                self.assertEqual(response.read(), b'\n')

    def test_synthetic_pcap_container(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'capture.pcap'
            http_capture(path)
            content = path.read_bytes()
            self.assertEqual(struct.unpack('<I', content[:4])[0], 0xa1b2c3d4)
            offset, count = 24, 0
            while offset < len(content):
                _, _, captured, original = struct.unpack('<IIII', content[offset:offset + 16])
                self.assertEqual(captured, original)
                offset += 16 + captured
                count += 1
            self.assertEqual(offset, len(content))
            self.assertEqual(count, 2)
            self.assertIn(b'GET /hello', content)

    def test_loopback_startup_needs_no_dns(self):
        with patch('socket.getfqdn', side_effect=AssertionError('No DNS needed')), ToolResourcesContext() as resources:
            resources.web('case-test')
            self.assertEqual(resources.server.server_name, 'localhost')

    def test_gui_task_is_marked_guided(self):
        with tempfile.TemporaryDirectory() as temporary, ToolResourcesContext() as resources:
            lesson = catalog.build('maltego', Path(temporary), resources)
            item = lesson['tasks'][1]
            self.assertTrue(item['walkthrough'])
            with contextlib.redirect_stdout(io.StringIO()), patch('builtins.input', side_effect=['done', '']):
                self.assertEqual(run_task(item, 2, 6, 8, Display(no_clear=True)), 'guided')

    def test_all_entry_points_and_list(self):
        result = subprocess.run([sys.executable, str(TOOLS_DIR / 'tool_lessons.py'), '--list'], text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('22. burpsuite', result.stdout)
        for slug, _, _, _ in catalog.TOOLS:
            with self.subTest(tool=slug), tempfile.TemporaryDirectory() as temporary:
                environment = dict(os.environ, TMPDIR=temporary, TMP=temporary, TEMP=temporary)
                result = subprocess.run([sys.executable, str(TOOLS_DIR / 'tool_lessons.py'), slug, '--no-clear'],
                                        input='\n' * 3 + 'skip\n\n' * 6, text=True, capture_output=True,
                                        env=environment, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('Skipped: 6', result.stdout)

    def test_real_available_recipes_and_evidence(self):
        answers = {
            'nmap': {2: '8443'}, 'netcat': {2: 'TRAINING'}, 'wireshark': {1: 'GET'},
            'aircrack-ng': {2: '6', 4: 'no'}, 'metasploit': {3: 'auxiliary'},
            'hydra': {4: '3'}, 'sqlmap': {4: 'id'}, 'john': {3: '3'},
            'recon-ng': {3: 'supplied'}, 'maltego': {1: 'done', 2: 'mail.lab.invalid', 4: '3'},
            'empire': {2: 'lab-agent-01', 4: '3'}, 'powersploit': {1: 'Get-LabFiles', 4: 'yes'},
            'timestomp': {3: 'yes', 4: 'metadata-change time'},
            'dnscat2': {3: 'training', 4: '2'}, 'burpsuite': {2: 'Hello analyst', 4: 'name'},
        }
        for slug, _, _, _ in catalog.TOOLS:
            with self.subTest(tool=slug), tempfile.TemporaryDirectory() as temporary, ToolResourcesContext() as resources:
                root = Path(temporary)
                lesson = catalog.build(slug, root, resources)
                token = re.search(r'Case code: (\w+)', (root / 'fixtures/scope.txt').read_text()).group(1)
                for index, item in enumerate(lesson['tasks']):
                    with self.subTest(tool=slug, task=item['title']):
                        program = item.get('requires')
                        if program and not shutil.which(program):
                            continue
                        if program == 'john':
                            formats = subprocess.run(['john', '--list=formats'], text=True, capture_output=True, timeout=10)
                            if 'raw-md5' not in (formats.stdout + formats.stderr).lower():
                                continue
                        if item.get('walkthrough'):
                            if slug == 'burpsuite':
                                result = subprocess.run(item['command'], shell=True, cwd=root, text=True,
                                                        input='', capture_output=True, timeout=10)
                                self.assertEqual(result.returncode, 0, result.stderr)
                            # These check grader behavior, not GUI automation.
                        elif slug == 'timestomp' and index == 4:
                            pass  # A manual page is interactive; the concept answer is checked.
                        elif program in ('msfconsole', 'recon-cli', 'powershell-empire', 'dnscat'):
                            continue  # Framework setup belongs in a separate manually provisioned lab.
                        else:
                            result = subprocess.run(item['command'], shell=True, cwd=root, input='',
                                                    text=True, capture_output=True, timeout=90)
                            self.assertIn(result.returncode, (0, 1), result.stderr[-1500:])
                        answer = token if index == 0 else answers.get(slug, {}).get(index, '')
                        if slug == 'nikto' and index == 4:
                            answer = 'no'
                        self.assertTrue(item['check'](answer), (slug, index, item['title']))
                (root / 'reports/conclusion.txt').write_text('wrong conclusion\n')
                self.assertFalse(lesson['tasks'][-1]['check'](''))


class ToolResourcesContext:
    def __enter__(self):
        self.resources = ToolResources()
        return self.resources

    def __exit__(self, *args):
        self.resources.close()


if __name__ == '__main__':
    unittest.main()
