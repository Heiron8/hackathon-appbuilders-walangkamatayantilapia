"""Failure-path checks; the product smoke exercises real shared server lifecycle."""
from contextlib import ExitStack
import io
import signal
import socket
import subprocess
import unittest
from unittest.mock import Mock, patch

from scripts import dev


class LauncherTests(unittest.TestCase):
    def test_missing_node_does_not_start_any_process(self):
        with patch.object(dev.shutil, "which", return_value=None), patch.object(dev.subprocess, "Popen") as start:
            with self.assertRaisesRegex(RuntimeError, "Node.js is missing"):
                with dev.running_services():
                    self.fail("Unexpected startup")
            start.assert_not_called()

    def test_missing_backend_dependencies_has_setup_instruction(self):
        with patch.object(dev.shutil, "which", return_value="node"), \
             patch.object(dev.subprocess, "run", return_value=Mock(returncode=1)):
            with self.assertRaisesRegex(RuntimeError, "backend/requirements.lock.txt"):
                dev.check_dependencies()

    def test_missing_frontend_dependencies_has_setup_instruction(self):
        with patch.object(dev.shutil, "which", return_value="node"), \
             patch.object(dev.subprocess, "run", side_effect=[Mock(returncode=0), Mock(returncode=1)]):
            with self.assertRaisesRegex(RuntimeError, "npm ci in frontend"):
                dev.check_dependencies()

    def test_occupied_port_is_reported_and_existing_listener_preserved(self):
        with socket.socket() as existing:
            existing.bind(("127.0.0.1", 0))
            existing.listen()
            port = existing.getsockname()[1]
            with patch.object(dev, "PORTS", (port,)):
                with self.assertRaisesRegex(RuntimeError, f"Port {port} is unavailable"):
                    dev.check_ports()
            self.assertEqual(existing.getsockname(), ("127.0.0.1", port))

    def test_partial_startup_failure_cleans_both_owned_processes(self):
        processes = [Mock(), Mock()]
        with patch.object(dev, "check_dependencies", return_value="node"), \
             patch.object(dev, "check_ports"), \
             patch.object(dev.subprocess, "Popen", side_effect=processes), \
             patch.object(dev, "wait_ready", side_effect=["ok", RuntimeError("not ready")]), \
             patch.object(dev, "stop_services") as stop:
            with self.assertRaisesRegex(RuntimeError, "not ready"):
                with dev.running_services():
                    self.fail("Unexpected readiness")
            stop.assert_called_once_with(processes)

    def test_interrupt_during_startup_cleans_started_backend(self):
        process = Mock()
        with patch.object(dev, "check_dependencies", return_value="node"), \
             patch.object(dev, "check_ports"), \
             patch.object(dev.subprocess, "Popen", return_value=process), \
             patch.object(dev, "wait_ready", side_effect=KeyboardInterrupt), \
             patch.object(dev, "stop_services") as stop:
            with self.assertRaises(KeyboardInterrupt):
                with dev.running_services():
                    self.fail("Unexpected readiness")
            stop.assert_called_once_with([process])

    def test_exited_service_abandons_session_with_error(self):
        with patch.object(dev, "running_services") as servers, \
             patch.object(dev.signal, "signal"), \
             patch.object(dev.sys, "stderr", new_callable=io.StringIO) as errors, \
             patch.object(dev.sys, "stdout", new_callable=io.StringIO):
            servers.return_value.__enter__.return_value = [Mock(returncode=7, poll=lambda: 7), Mock()]
            self.assertEqual(dev.main(), 1)
            self.assertIn("Backend exited unexpectedly (code 7)", errors.getvalue())
            servers.return_value.__exit__.assert_called_once()

    def test_shutdown_escalates_only_its_unresponsive_child(self):
        process = Mock(pid=12345)
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired("child", 5), 0]
        with ExitStack() as stack:
            kill_group = stack.enter_context(patch.object(dev.os, "killpg", create=True))
            dev.stop_services([process])
        if dev.os.name == "nt":
            process.send_signal.assert_called_once_with(signal.CTRL_BREAK_EVENT)
            process.kill.assert_called_once()
        else:
            self.assertEqual([call.args for call in kill_group.call_args_list],
                             [(12345, signal.SIGTERM), (12345, signal.SIGKILL)])
        self.assertEqual(process.wait.call_count, 2)

    def test_shutdown_without_console_falls_back_to_owned_process_termination(self):
        process = Mock(pid=12345)
        process.poll.return_value = None
        process.send_signal.side_effect = OSError("No console")
        with patch.object(dev.os, "killpg", create=True, side_effect=OSError("No group")):
            dev.stop_services([process])
        process.terminate.assert_called_once()
        process.wait.assert_called_once_with(timeout=5)


if __name__ == "__main__":
    unittest.main()
