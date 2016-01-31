"""
Contains functions and classes to aid in the unit testing process within Maya.

To write tests for this system you need to,
    a) Derive from cmt.mayaunittest.TestCase
    b) Write one or more tests that use the unittest module's assert methods to validate the
       results.

Example usage:

# test_sample.py
import cmt.mayaunittest as mayaunittest
class SampleTests(mayaunittest.TestCase):
    def test_create_sphere(self):
        sphere = cmds.polySphere(n='mySphere')[0]
        self.assertEqual('mySphere', sphere)

# To run just this test case in Maya
import cmt.mayaunittest as mayaunittest
mayaunittest.run_tests(test='test_sample.SampleTests')

# To run an individual test in a test case
mayaunittest.run_tests(test='test_sample.SampleTests.test_create_sphere')

# To run all tests
mayaunittest.run_tests()
"""
import __builtin__
import os
import sys
import unittest
import tempfile
import uuid
import logging
import maya.cmds as cmds


def run_tests(directories=None, test=None):
    """
    Runs all the tests in given paths.
    @param directories: A generator or list of paths containing tests to run.
    @param test: Optional name of a specific test to run.
    """
    rollback_importer = RollbackImporter()

    if directories is None:
        directories = maya_module_tests()

    # Populate a TestSuite with all the tests
    test_suite = TestSuite()

    if test:
        # Find the specied test to run
        directories_added_to_path = [p for p in directories if add_to_path(p)]
        discovered_suite = unittest.TestLoader().loadTestsFromName(test)
        if discovered_suite.countTestCases():
            test_suite.addTests(discovered_suite)
    else:
        # Find all tests to run
        directories_added_to_path = []
        for p in directories:
            discovered_suite = unittest.TestLoader().discover(p)
            if discovered_suite.countTestCases():
                test_suite.addTests(discovered_suite)

    runner = unittest.TextTestRunner(verbosity=2)
    runner.failfast = False
    runner.buffer = Settings.buffer_output
    runner.run(test_suite)

    # Remove the added paths.
    for path in directories_added_to_path:
        sys.path.remove(path)

    rollback_importer.uninstall()


def run_tests_from_commandline():

    import maya.standalone
    maya.standalone.initialize()

    # Make sure all paths in PYTHONPATH are also in sys.path
    # When a maya module is loaded, the scripts folder is added to PYTHONPATH, but it doesn't seem
    # to be added to sys.path. So we are unable to import any of the python files that are in the
    # module/scripts folder. To workaround this, we simply add the paths to sys ourselves.
    realsyspath = [os.path.realpath(p) for p in sys.path]
    pythonpath = os.environ.get('PYTHONPATH', '')
    for p in pythonpath.split(os.pathsep):
        p = os.path.realpath(p) # Make sure symbolic links are resolved
        if p not in realsyspath:
            sys.path.insert(0, p)

    run_tests()

    if float(cmds.about(v=True)) >= 2016.0:
        maya.standalone.uninitialize()


class Settings(object):
    """
    Contains options for running tests.
    """
    # Specifies where files generated during tests should be stored
    # Use a uuid subdirectory so tests that are running concurrently such as on a build server
    # do not conflict with each other.
    temp_dir = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))

    # Controls whether temp files should be deleted after running all tests in the test case
    delete_files = True

    # Specifies whether the standard output and standard error streams are buffered during the test run.
    # Output during a passing test is discarded. Output is echoed normally on test fail or error and is
    # added to the failure messages.
    buffer_output = True

    # Controls whether we should do a file new between each test case
    file_new = True


def set_temp_dir(directory):
    """
    Sets where files generated from tests should be stored.
    @param directory: A directory path.
    """
    if os.path.exists(directory):
        Settings.temp_dir = directory
    else:
        raise RuntimeError('{0} does not exist.'.format(directory))


def set_delete_files(value):
    """
    Sets whether temp files should be deleted after running all tests in a test case.
    @param value: True to delete files registered with a TestCase.
    """
    Settings.delete_files = value


def set_buffer_output(value):
    """
    Set whether the standard output and standard error streams are buffered during the test run.
    @param value: True or False
    """
    Settings.buffer_output = value


def set_file_new(value):
    """
    Set whether a new file should be created after each test.
    @param value: True or False
    """
    Settings.file_new = value


def add_to_path(path):
    """
    Adds the specified path to the system path.
    @param path: Path to add.
    @return True if path was added. Return false if path does not exist or path was already in sys.path
    """
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)
        return True
    return False


class TestCase(unittest.TestCase):
    """
    Base class for unit test cases run in Maya.
    """

    # Keep track of all temporary files that were created so they can be cleaned up after all tests have been run
    files_created = []

    # Keep track of which plugins were loaded so we can unload them after all tests have been run
    plugins_loaded = set()

    @classmethod
    def tearDownClass(cls):
        super(TestCase, cls).tearDownClass()
        cls.delete_temp_files()
        cls.unload_plugins()

    @classmethod
    def load_plugin(cls, plugin):
        """
        Loads the given plug-in and saves it to be unloaded when the TestCase is finished.
        @param plugin: Plug-in name.
        """
        cmds.loadPlugin(plugin, qt=True)
        cls.plugins_loaded.add(plugin)

    @classmethod
    def unload_plugins(cls):
        # Unload any plugins that this test case loaded
        for plugin in cls.plugins_loaded:
            cmds.unloadPlugin(plugin)
        cls.plugins_loaded = []

    @classmethod
    def delete_temp_files(cls):
        """
        Deletes the temp files in the cache and clears the cache.
        """
        # If we don't want to keep temp files around for debugging purposes, delete them when
        # all tests in this TestCase have been run
        if Settings.delete_files:
            for f in cls.files_created:
                if os.path.exists(f):
                    os.remove(f)
            cls.files_create = []

    @classmethod
    def get_temp_filename(cls, file_name):
        """
        Get a unique filepath name in the testing directory.  The file will not be created, that is up to the caller.
        This file will be deleted when the tests are finished
        @param file_name: A partial path ex: 'directory/somefile.txt'
        @return The full path to the temporary file.
        """
        temp_dir = Settings.temp_dir
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        base_name, ext = os.path.splitext(file_name)
        path = '{0}/{1}{2}'.format(temp_dir, base_name, ext)
        count = 0
        while os.path.exists(path):
            # If the file already exists, add an incrememted number
            count += 1
            path = '{0}/{1}{2}{3}'.format(temp_dir, base_name, count, ext)
        cls.files_created.append(path)
        return path

    def assertListAlmostEqual(self, first, second, places=7, msg=None, delta=None):
        """
        Asserts that a list of floating point values is almost equal.  unittest has assertAlmostEqual and
        assertListEqual but no assertListAlmostEqual.
        """
        self.assertEqual(len(first), len(second), msg)
        for a, b in zip(first, second):
            self.assertAlmostEqual(a, b, places, msg, delta)


class TestResult(unittest.TextTestResult):
    """
    Customize the test result so we can do things like do a file new between each test and suppress script
    editor output.
    """
    def startTestRun(self):
        """
        Called before any tests are run.
        """
        super(TestResult, self).startTestRun()
        suppress_script_editor_output()

    def stopTestRun(self):
        """
        Called after all tests are run.
        """
        restore_script_editor_output()
        super(TestResult, self).stopTestRun()

    def stopTest(self, test):
        """
        Called after an individual test is run
        """
        super(TestResult, self).stopTest(test)
        if Settings.file_new:
            cmds.file(f=1, new=1)

# Used to restore logging states in the script editor
_PREV_SUPPRESS_RESULTS = None
_PREV_SUPPRESS_ERRORS = None
_PREV_SUPPRESS_WARNINGS = None
_PREV_SUPPRESS_INFO = None


def suppress_script_editor_output():
    """
    Hides all script editor output.
    """
    global _PREV_SUPPRESS_RESULTS
    global _PREV_SUPPRESS_ERRORS
    global _PREV_SUPPRESS_WARNINGS
    global _PREV_SUPPRESS_INFO

    # If we want to see all output, don't bother hiding Maya's script editor output
    if Settings.buffer_output:
        _PREV_SUPPRESS_RESULTS = cmds.scriptEditorInfo(q=1, suppressResults=1)
        _PREV_SUPPRESS_ERRORS = cmds.scriptEditorInfo(q=1, suppressErrors=1)
        _PREV_SUPPRESS_WARNINGS = cmds.scriptEditorInfo(q=1, suppressWarnings=1)
        _PREV_SUPPRESS_INFO = cmds.scriptEditorInfo(q=1, suppressInfo=1)
        cmds.scriptEditorInfo(e=1, suppressResults=1, suppressInfo=1, suppressWarnings=1, suppressErrors=1)


def restore_script_editor_output():
    """
    Restores the script editor output settings to their original values.
    """
    global _PREV_SUPPRESS_RESULTS
    if _PREV_SUPPRESS_RESULTS is not None:
        cmds.scriptEditorInfo(e=1, suppressResults=_PREV_SUPPRESS_RESULTS)
        _PREV_SUPPRESS_RESULTS = None

    global _PREV_SUPPRESS_ERRORS
    if _PREV_SUPPRESS_ERRORS is not None:
        cmds.scriptEditorInfo(e=1, suppressErrors=_PREV_SUPPRESS_ERRORS)
        _PREV_SUPPRESS_ERRORS = None

    global _PREV_SUPPRESS_WARNINGS
    if _PREV_SUPPRESS_WARNINGS is not None:
        cmds.scriptEditorInfo(e=1, suppressWarnings=_PREV_SUPPRESS_WARNINGS)
        _PREV_SUPPRESS_WARNINGS = None

    global _PREV_SUPPRESS_INFO
    if _PREV_SUPPRESS_INFO is not None:
        cmds.scriptEditorInfo(e=1, suppressInfo=_PREV_SUPPRESS_INFO)
        _PREV_SUPPRESS_INFO = None


class TestRunner(unittest.TextTestRunner):
    """
    Customize the test runner so it uses our test result class.
    """

    def _makeResult(self):
        return TestResult(stream=self.stream, descriptions=self.descriptions, verbosity=2)


class TestSuite(unittest.TestSuite):
    """ Override unittests's TestSuite so we can do custom processing before running any of our
        tests. For example, setting/unsetting an environment variable that indicates that we're
        running unittests
    """
    def run(self, result):

        if Settings.buffer_output:
            # Disable any logging while running tests. By disabling critical, we are disabling logging
            # at all levels below critical as well
            logging.disable(logging.CRITICAL)

        # Run all tests in the suite
        super(TestSuite, self).run(result)

        if Settings.buffer_output:
            # Restore logging state
            logging.disable(logging.NOTSET)


def maya_module_tests():
    """
    Generator function to iterate over all the Maya module tests directories.
    """
    for path in os.environ['MAYA_MODULE_PATH'].split(os.pathsep):
        p = '{0}/tests'.format(path)
        if os.path.exists(p):
            yield p


class RollbackImporter(object):
    """
    Used to remove imported modules from the module list.  This allows tests to be rerun after code updates without
    doing any reloads.
    From: http://pyunit.sourceforge.net/notes/reloading.html

    Usage:
    def run_tests(self):
        if self.rollback_importer:
            self.rollback_importer.uninstall()
        self.rollback_importer = RollbackImporter()
        self.load_and_execute_tests()
    """
    def __init__(self):
        """
        Creates an instance and installs as the global importer.
        """
        self.previous_modules = sys.modules.copy()
        self.real_import = __builtin__.__import__
        __builtin__.__import__ = self._import
        self.new_modules = {}

    def _import(self, name, globals=None, locals=None, fromlist=[]):
        result = apply(self.real_import, (name, globals, locals, fromlist))
        self.new_modules[name] = 1
        return result

    def uninstall(self):
        for modname in self.new_modules.keys():
            if modname not in self.previous_modules.keys():
                # Force reload when modname next imported
                del(sys.modules[modname])
        __builtin__.__import__ = self.real_import


if __name__ == '__main__':
    run_tests_from_commandline()
