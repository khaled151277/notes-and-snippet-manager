# database/db_worker.py

from PyQt6.QtCore import QRunnable, pyqtSignal, QObject
from typing import Callable, Any
import traceback
import time

# Helper class to emit signals from the QRunnable
class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.

    Supported signals:
    - result: Emits (task_id, result_object) on successful completion.
    - error: Emits (task_id, error_string) if an exception occurs.
    - finished: Emits (task_id) when the task execution completes (success or error).
    """
    result = pyqtSignal(str, object)
    error = pyqtSignal(str, str)
    finished = pyqtSignal(str)

class DBWorker(QRunnable):
    """
    A QRunnable task designed to execute a database method in a separate thread.

    Args:
        task_id: A unique identifier for this task instance.
        method: The function/method to execute in the background.
        args: Positional arguments to pass to the method.
        kwargs: Keyword arguments to pass to the method.
    """
    def __init__(self, task_id: str, method: Callable, args: tuple = (), kwargs: dict = {}):
        super().__init__()
        self.task_id = task_id
        self.method = method
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Enable auto-deletion of the QRunnable after run() finishes
        self.setAutoDelete(True)

    def run(self):
        """
        Executes the assigned database method and emits signals based on the outcome.
        """
        print(f"DBWorker ({self.task_id}): Starting execution of '{self.method.__name__}'...")
        start_time = time.time()
        try:
            # Execute the target method with provided arguments
            result = self.method(*self.args, **self.kwargs)
            # Emit result signal on success
            self.signals.result.emit(self.task_id, result)
            status = "Success"
        except Exception as e:
            # Catch any exception during execution
            error_string = f"Task '{self.task_id}' failed: {e}\n{traceback.format_exc()}"
            print(error_string) # Log error to console
            # Emit error signal
            self.signals.error.emit(self.task_id, str(e)) # Emit only the exception message for UI
            status = "Error"
        finally:
            # Always emit finished signal
            self.signals.finished.emit(self.task_id)
            end_time = time.time()
            print(f"DBWorker ({self.task_id}): Finished execution in {end_time - start_time:.4f}s. Status: {status}")

# database/db_worker.py
# --- END OF FILE db_worker.py ---
