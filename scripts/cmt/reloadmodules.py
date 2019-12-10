import sys


class RollbackImporter(object):
    """Used to remove imported modules from the module list.

    This allows tests to be rerun after code updates without doing any reloads.
    Original idea from: http://pyunit.sourceforge.net/notes/reloading.html

    Usage:
    def run_tests(self):
        if self.rollback_importer:
            self.rollback_importer.uninstall()
        self.rollback_importer = RollbackImporter()
        self.load_and_execute_tests()
    """

    def __init__(self):
        """Creates an instance and installs as the global importer."""
        self.previous_modules = set(sys.modules.keys())

    def uninstall(self):
        for modname in sys.modules.keys():
            if modname not in self.previous_modules:
                # Force reload when modname next imported
                del (sys.modules[modname])


_rollbackimporter = RollbackImporter()


def save_modules():
    global _rollbackimporter
    _rollbackimporter = RollbackImporter()


def reload_modules():
    global _rollbackimporter
    _rollbackimporter.uninstall()
