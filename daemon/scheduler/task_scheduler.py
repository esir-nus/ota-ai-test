"""
Task Scheduler for the OTA daemon.

This module handles scheduling and executing tasks at specific times,
including update checks and installations.
"""

import datetime
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional
import json

logger = logging.getLogger("ota-daemon.scheduler")

class Task:
    """Represents a scheduled task."""
    
    def __init__(self, 
                 name: str, 
                 callback: Callable, 
                 schedule_time: Optional[str] = None,
                 args: List[Any] = None, 
                 kwargs: Dict[str, Any] = None):
        """Initialize a task.
        
        Args:
            name: The name of the task.
            callback: The function to call when the task is executed.
            schedule_time: The time to execute the task in 24-hour format (HH:MM).
                           If None, the task is executed immediately.
            args: Positional arguments to pass to the callback.
            kwargs: Keyword arguments to pass to the callback.
        """
        self.name = name
        self.callback = callback
        self.schedule_time = schedule_time
        self.args = args or []
        self.kwargs = kwargs or {}
        self.last_executed = None
        self.next_execution = None
        self._calculate_next_execution()
    
    def _calculate_next_execution(self) -> None:
        """Calculate the next execution time for this task."""
        if not self.schedule_time:
            # If no schedule time, execute immediately
            self.next_execution = datetime.datetime.now()
            return
        
        # Parse the schedule time (HH:MM)
        try:
            hour, minute = map(int, self.schedule_time.split(':'))
            now = datetime.datetime.now()
            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If the scheduled time is in the past, move to tomorrow
            if scheduled_time <= now:
                scheduled_time += datetime.timedelta(days=1)
            
            self.next_execution = scheduled_time
            logger.debug(f"Task '{self.name}' next execution: {self.next_execution}")
        except Exception as e:
            logger.error(f"Error calculating next execution for task '{self.name}': {str(e)}")
            self.next_execution = None
    
    def execute(self) -> bool:
        """Execute the task.
        
        Returns:
            True if the task was executed successfully, False otherwise.
        """
        try:
            logger.info(f"Executing task: {self.name}")
            result = self.callback(*self.args, **self.kwargs)
            self.last_executed = datetime.datetime.now()
            self._calculate_next_execution()
            logger.info(f"Task '{self.name}' executed successfully")
            return True
        except Exception as e:
            logger.error(f"Error executing task '{self.name}': {str(e)}")
            self.last_executed = datetime.datetime.now()
            self._calculate_next_execution()
            return False
    
    def is_due(self) -> bool:
        """Check if the task is due for execution.
        
        Returns:
            True if the task is due, False otherwise.
        """
        if not self.next_execution:
            return False
        
        return datetime.datetime.now() >= self.next_execution

class TaskScheduler:
    """Manages scheduled tasks for the OTA daemon."""
    
    def __init__(self):
        """Initialize the task scheduler."""
        self.tasks = {}
        self.running = False
        self.thread = None
        self.task_state_file = Path("/var/lib/robot-ai-ota/tasks.json")
        self.task_state_file.parent.mkdir(parents=True, exist_ok=True)
    
    def add_task(self, task: Task) -> None:
        """Add a task to the scheduler.
        
        Args:
            task: The task to add.
        """
        self.tasks[task.name] = task
        logger.info(f"Added task: {task.name}")
        self._save_task_state()
    
    def remove_task(self, task_name: str) -> None:
        """Remove a task from the scheduler.
        
        Args:
            task_name: The name of the task to remove.
        """
        if task_name in self.tasks:
            del self.tasks[task_name]
            logger.info(f"Removed task: {task_name}")
            self._save_task_state()
    
    def start(self) -> None:
        """Start the task scheduler."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Task scheduler started")
    
    def stop(self) -> None:
        """Stop the task scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            self.thread = None
        logger.info("Task scheduler stopped")
    
    def _run_scheduler(self) -> None:
        """Run the task scheduler loop."""
        while self.running:
            try:
                # Check for due tasks
                for task_name, task in list(self.tasks.items()):
                    if task.is_due():
                        # Execute task in a separate thread to avoid blocking the scheduler
                        threading.Thread(target=task.execute).start()
                
                # Sleep for a short time before checking again
                time.sleep(10)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(30)  # Sleep longer on error
    
    def _save_task_state(self) -> None:
        """Save the task state to a file."""
        try:
            state = {
                "tasks": {
                    name: {
                        "name": task.name,
                        "schedule_time": task.schedule_time,
                        "last_executed": task.last_executed.isoformat() if task.last_executed else None,
                        "next_execution": task.next_execution.isoformat() if task.next_execution else None
                    }
                    for name, task in self.tasks.items()
                }
            }
            
            with open(self.task_state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.debug("Task state saved")
        except Exception as e:
            logger.error(f"Error saving task state: {str(e)}")
    
    def _load_task_state(self) -> None:
        """Load the task state from a file."""
        if not self.task_state_file.exists():
            return
        
        try:
            with open(self.task_state_file, 'r') as f:
                state = json.load(f)
            
            logger.debug("Task state loaded")
            return state
        except Exception as e:
            logger.error(f"Error loading task state: {str(e)}")
            return None
    
    def add_update_check_tasks(self, check_times: List[str], check_callback: Callable) -> None:
        """Add scheduled update check tasks.
        
        Args:
            check_times: List of times to check for updates, in 24-hour format (HH:MM).
            check_callback: Function to call to check for updates.
        """
        for check_time in check_times:
            task_name = f"update_check_{check_time.replace(':', '')}"
            task = Task(
                name=task_name,
                callback=check_callback,
                schedule_time=check_time
            )
            self.add_task(task)
    
    def schedule_update(self, update_time: str, update_callback: Callable, 
                       version: str, update_files: List[str]) -> None:
        """Schedule an update to be installed.
        
        Args:
            update_time: The time to install the update, in 24-hour format (HH:MM).
            update_callback: Function to call to install the update.
            version: The version to update to.
            update_files: List of files to update.
        """
        task_name = f"update_install_{version.replace('.', '_')}"
        task = Task(
            name=task_name,
            callback=update_callback,
            schedule_time=update_time,
            kwargs={
                "version": version,
                "update_files": update_files
            }
        )
        self.add_task(task)
        logger.info(f"Scheduled update to version {version} at {update_time}")
        
        # Save the task state
        self._save_task_state() 