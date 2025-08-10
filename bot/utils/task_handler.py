"""
Task handler for managing Discord bot async tasks.
"""

import asyncio
import logging
from typing import List, Optional
from discord.ext import tasks


class TaskHandler:
    """Handle starting, stopping, and managing async tasks."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.managed_tasks = {}
    
    async def start_tasks(self, coroutine_task: List = None):
        """Start specified tasks."""
        if not coroutine_task:
            return
        
        for task in coroutine_task:
            try:
                if hasattr(task, 'start') and not task.is_running():
                    task.start()
                    self.logger.info(f"Started task: {task.coro.__name__}")
                    self.managed_tasks[task.coro.__name__] = task
            except Exception as e:
                self.logger.error(f"Error starting task {task.coro.__name__}: {e}")
    
    async def stop_tasks(self, coroutine_task: List = None):
        """Stop specified tasks."""
        if not coroutine_task:
            return
        
        for task in coroutine_task:
            try:
                if hasattr(task, 'stop') and task.is_running():
                    task.stop()
                    self.logger.info(f"Stopped task: {task.coro.__name__}")
                    # Remove from managed tasks
                    self.managed_tasks.pop(task.coro.__name__, None)
            except Exception as e:
                self.logger.error(f"Error stopping task {task.coro.__name__}: {e}")
    
    async def restart_task(self, task):
        """Restart a specific task."""
        try:
            if hasattr(task, 'restart'):
                task.restart()
                self.logger.info(f"Restarted task: {task.coro.__name__}")
            else:
                # Manual restart
                if task.is_running():
                    task.stop()
                await asyncio.sleep(1)
                task.start()
                self.logger.info(f"Manually restarted task: {task.coro.__name__}")
        except Exception as e:
            self.logger.error(f"Error restarting task {task.coro.__name__}: {e}")
    
    async def evaluate_task_schedule(self, task):
        """Evaluate if a task should be running based on schedule."""
        try:
            # This is a placeholder for more complex scheduling logic
            if hasattr(task, 'is_running') and not task.is_running():
                self.logger.info(f"Task {task.coro.__name__} is not running, considering restart")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Error evaluating task schedule: {e}")
            return False
    
    def get_task_status(self, task_name: str) -> dict:
        """Get status information for a specific task."""
        if task_name in self.managed_tasks:
            task = self.managed_tasks[task_name]
            return {
                'name': task_name,
                'running': task.is_running() if hasattr(task, 'is_running') else False,
                'current_loop': task.current_loop if hasattr(task, 'current_loop') else None,
                'next_iteration': task.next_iteration if hasattr(task, 'next_iteration') else None
            }
        return {'name': task_name, 'status': 'not_managed'}
    
    def get_all_task_status(self) -> dict:
        """Get status for all managed tasks."""
        status = {}
        for task_name in self.managed_tasks:
            status[task_name] = self.get_task_status(task_name)
        return status
    
    async def graceful_shutdown(self):
        """Gracefully shutdown all managed tasks."""
        self.logger.info("Starting graceful shutdown of all tasks")
        
        for task_name, task in self.managed_tasks.items():
            try:
                if hasattr(task, 'stop') and task.is_running():
                    task.stop()
                    self.logger.info(f"Gracefully stopped task: {task_name}")
            except Exception as e:
                self.logger.error(f"Error during graceful shutdown of {task_name}: {e}")
        
        self.managed_tasks.clear()
        self.logger.info("Graceful shutdown completed")
