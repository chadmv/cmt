"""Contains a context manager class used to measure execution time of blocks of code

Example Usage
=============

    with Section("Mesh Processor", "Import files"):
        # Code to run

    with Section("Mesh Processor", "Process sata"):
        # Code to run

    with Section("Publish Asset", "Upload data"):
        # Code to run

    Section.print_timing()

"""
import functools
import time
from collections import OrderedDict

_workspaces = OrderedDict()


class Section(object):
    @classmethod
    def clear(cls, workspace=None):
        """Clears the stored timing data.

        :param workspace: Optional workspace to clear. If omitted, all data is cleared.
        """
        global _workspaces
        if workspace:
            del _workspaces[workspace]
        else:
            _workspaces = OrderedDict()

    @classmethod
    def print_timing(cls):
        """Prints the existing timing data"""
        global _workspaces
        for workspace, tasks in _workspaces.items():
            total_time = sum(tasks.values())
            print("-- {}: {:.6f} seconds".format(workspace, total_time))
            for task, run_time in tasks.items():
                print("  - {}: {:.6f} seconds".format(task, run_time))

    def __init__(self, workspace, task):
        self.workspace = workspace
        self.task = task

    def __enter__(self):
        self.start_time = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _workspaces
        run_time = time.time() - self.start_time
        workspace = _workspaces.setdefault(self.workspace, OrderedDict())
        workspace[self.task] = run_time


def timed(workspace, task):
    def decorator_timed(func):
        @functools.wraps(func)
        def wrapper_timed(*args, **kwargs):
            with Section(workspace, task):
                result = func(*args, **kwargs)
            return result

        return wrapper_timed

    return decorator_timed
