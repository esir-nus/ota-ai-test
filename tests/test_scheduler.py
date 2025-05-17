"""
Unit tests for the TaskScheduler component.

These tests verify the functionality of the scheduler using mocks
to isolate it from other system components.
"""

import datetime
import json
import unittest
from unittest.mock import patch, Mock, MagicMock
import tempfile
from pathlib import Path
import time

from OTA.daemon.scheduler.task_scheduler import TaskScheduler, Task

class TestTask(unittest.TestCase):
    """Test cases for the Task class."""

    def test_task_initialization(self):
        """Test that tasks are initialized correctly."""
        callback = Mock()
        task = Task(
            name="test_task",
            callback=callback,
            schedule_time="03:00",
            args=[1, 2],
            kwargs={"test": True}
        )
        
        self.assertEqual(task.name, "test_task")
        self.assertEqual(task.callback, callback)
        self.assertEqual(task.schedule_time, "03:00")
        self.assertEqual(task.args, [1, 2])
        self.assertEqual(task.kwargs, {"test": True})
        self.assertIsNone(task.last_executed)
        self.assertIsNotNone(task.next_execution)
    
    def test_calculate_next_execution(self):
        """Test that next execution time is calculated correctly."""
        callback = Mock()
        
        # Test with schedule time in the future
        current_time = datetime.datetime.now()
        future_hour = (current_time.hour + 1) % 24
        schedule_time = f"{future_hour:02d}:00"
        
        task = Task(
            name="test_task",
            callback=callback,
            schedule_time=schedule_time
        )
        
        expected_time = current_time.replace(
            hour=future_hour, 
            minute=0, 
            second=0, 
            microsecond=0
        )
        
        self.assertEqual(task.next_execution.hour, expected_time.hour)
        self.assertEqual(task.next_execution.minute, expected_time.minute)
        
        # Test with schedule time in the past
        past_hour = (current_time.hour - 1) % 24
        schedule_time = f"{past_hour:02d}:00"
        
        task = Task(
            name="test_task_past",
            callback=callback,
            schedule_time=schedule_time
        )
        
        # Should be scheduled for tomorrow
        self.assertGreater(task.next_execution, current_time)
    
    def test_is_due(self):
        """Test that is_due correctly identifies due tasks."""
        callback = Mock()
        
        # Task due in the future
        current_time = datetime.datetime.now()
        future_hour = (current_time.hour + 1) % 24
        schedule_time = f"{future_hour:02d}:00"
        
        future_task = Task(
            name="future_task",
            callback=callback,
            schedule_time=schedule_time
        )
        
        self.assertFalse(future_task.is_due())
        
        # Immediate task (no schedule_time)
        immediate_task = Task(
            name="immediate_task",
            callback=callback,
            schedule_time=None
        )
        
        self.assertTrue(immediate_task.is_due())
        
        # Mock a task that is due now
        due_task = Task(
            name="due_task",
            callback=callback,
            schedule_time="00:00"  # Doesn't matter, we'll mock next_execution
        )
        due_task.next_execution = datetime.datetime.now() - datetime.timedelta(minutes=5)
        
        self.assertTrue(due_task.is_due())
    
    def test_execute(self):
        """Test that tasks execute correctly and update last_executed."""
        callback = Mock(return_value=True)
        
        task = Task(
            name="test_task",
            callback=callback,
            args=[1, 2],
            kwargs={"test": True}
        )
        
        result = task.execute()
        
        self.assertTrue(result)
        callback.assert_called_once_with(1, 2, test=True)
        self.assertIsNotNone(task.last_executed)
        
        # Test with failing callback
        callback_fail = Mock(side_effect=Exception("Test exception"))
        
        task_fail = Task(
            name="failing_task",
            callback=callback_fail
        )
        
        result = task_fail.execute()
        
        self.assertFalse(result)
        callback_fail.assert_called_once()
        self.assertIsNotNone(task_fail.last_executed)


class TestTaskScheduler(unittest.TestCase):
    """Test cases for the TaskScheduler class."""
    
    def setUp(self):
        """Set up test fixtures for TaskScheduler tests."""
        # Create a temporary directory for task state file
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Patch the task state file path
        self.patcher = patch('OTA.daemon.scheduler.task_scheduler.Path')
        mock_path = self.patcher.start()
        mock_path.return_value.parent.mkdir.return_value = None
        
        self.scheduler = TaskScheduler()
        self.scheduler.task_state_file = Path(self.temp_dir.name) / "tasks.json"
    
    def tearDown(self):
        """Clean up test fixtures after tests."""
        self.patcher.stop()
        self.temp_dir.cleanup()
    
    def test_add_task(self):
        """Test adding tasks to the scheduler."""
        callback = Mock()
        task = Task(
            name="test_task",
            callback=callback,
            schedule_time="03:00"
        )
        
        self.scheduler.add_task(task)
        
        self.assertIn("test_task", self.scheduler.tasks)
        self.assertEqual(self.scheduler.tasks["test_task"], task)
    
    def test_remove_task(self):
        """Test removing tasks from the scheduler."""
        callback = Mock()
        task = Task(
            name="test_task",
            callback=callback,
            schedule_time="03:00"
        )
        
        self.scheduler.add_task(task)
        self.assertIn("test_task", self.scheduler.tasks)
        
        self.scheduler.remove_task("test_task")
        self.assertNotIn("test_task", self.scheduler.tasks)
        
        # Test removing non-existent task (should not raise an error)
        self.scheduler.remove_task("non_existent_task")
    
    @patch('OTA.daemon.scheduler.task_scheduler.threading.Thread')
    def test_scheduler_start_stop(self, mock_thread):
        """Test starting and stopping the scheduler."""
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        # Test start
        self.scheduler.start()
        mock_thread.assert_called_once()
        self.assertTrue(self.scheduler.running)
        
        # Test that calling start again does nothing
        self.scheduler.start()
        self.assertEqual(mock_thread.call_count, 1)
        
        # Test stop
        self.scheduler.stop()
        mock_thread_instance.join.assert_called_once()
        self.assertFalse(self.scheduler.running)
    
    def test_add_update_check_tasks(self):
        """Test adding update check tasks."""
        check_callback = Mock()
        check_times = ["03:00", "04:00", "05:00"]
        
        self.scheduler.add_update_check_tasks(check_times, check_callback)
        
        for check_time in check_times:
            task_name = f"update_check_{check_time.replace(':', '')}"
            self.assertIn(task_name, self.scheduler.tasks)
            self.assertEqual(self.scheduler.tasks[task_name].schedule_time, check_time)
            self.assertEqual(self.scheduler.tasks[task_name].callback, check_callback)
    
    def test_schedule_update(self):
        """Test scheduling an update installation."""
        update_callback = Mock()
        update_time = "03:00"
        version = "1.2.3"
        update_files = ["file1.txt", "file2.txt"]
        
        self.scheduler.schedule_update(update_time, update_callback, version, update_files)
        
        task_name = f"update_install_1_2_3"
        self.assertIn(task_name, self.scheduler.tasks)
        self.assertEqual(self.scheduler.tasks[task_name].schedule_time, update_time)
        self.assertEqual(self.scheduler.tasks[task_name].callback, update_callback)
        self.assertEqual(self.scheduler.tasks[task_name].kwargs["version"], version)
        self.assertEqual(self.scheduler.tasks[task_name].kwargs["update_files"], update_files)
    
    @patch('OTA.daemon.scheduler.task_scheduler.json.dump')
    def test_save_task_state(self, mock_json_dump):
        """Test saving task state to file."""
        callback = Mock()
        task = Task(
            name="test_task",
            callback=callback,
            schedule_time="03:00"
        )
        
        self.scheduler.add_task(task)
        
        # Mock open to prevent actual file operations
        with patch('builtins.open', unittest.mock.mock_open()) as mock_open:
            self.scheduler._save_task_state()
            mock_open.assert_called_once_with(self.scheduler.task_state_file, 'w')
            mock_json_dump.assert_called_once()
            
            # Check that the saved state contains our task
            args, _ = mock_json_dump.call_args
            state = args[0]
            self.assertIn("tasks", state)
            self.assertIn("test_task", state["tasks"])
            self.assertEqual(state["tasks"]["test_task"]["name"], "test_task")
            self.assertEqual(state["tasks"]["test_task"]["schedule_time"], "03:00")


if __name__ == '__main__':
    unittest.main() 