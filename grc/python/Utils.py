"""
Copyright 2008-2011 Free Software Foundation, Inc.
This file is part of GNU Radio

GNU Radio Companion is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

GNU Radio Companion is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
"""

import imp
import sys
import runpy
import multiprocessing


class LoggedImport:
    """Works just like the build-in importer but logs each module"""

    def __init__(self, path):
        self.path = [path] if isinstance(path, str) else list(path)
        self.cache = dict()
        self.log = []

    @classmethod
    def log_from_exec_file(cls, filepath, path):
        """
        Get a list of depending modules from path by running script in a
        separate process (clean module cache).

        Args:
            script: filepath of the flow graph
            path: str or list of paths to filter loaded modules with
        Returns:
            a list of filepaths to the (compiled) modules
        Exception:
            ...are thrown from the process, ...
        """

        def worker(queue, filepath, path):
            """Run script and return logged imports"""
            try:
                with cls(path) as log:
                    runpy.run_path(filepath)
                queue.put(log)
            except:
                pass

        queue = multiprocessing.Queue()

        proc = multiprocessing.Process(
            target=worker, args=(queue, filepath, path)
        )
        proc.start()
        proc.join(timeout=5)
        if queue.empty():
            raise RuntimeError("No result from proc")
        return queue.get()

    def __call__(self, path):
        """Called to see if path can be handled, return finder"""
        if path in self.path:
            return self
        else:
            raise ImportError()

    def find_module(self, fullname):  # no path when used from path_hooks
        """Try to find module in path, return loader"""
        try:
            self.cache[fullname] = imp.find_module(fullname, self.path)
        except ImportError:
            pass  # return None means not found
        else:
            return self

    def load_module(self, fullname):
        """Try to load previously found module, return module"""
        file = None
        try:
            file, pathname, description = self.cache.pop(fullname)
            module = imp.load_module(fullname, file, pathname, description)
            self.log.append(pathname)
            return module
        finally:
            if file:
                file.close()

    def __enter__(self):
        """Register the logger and return the log"""
        sys.path_hooks.append(self)
        sys.path.append(self.path)
        return self.log

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Unregister the logger and clear cache"""
        try:
            sys.path_hooks.remove(self)
        except ValueError:
            pass  # somebody else removed the hook already
        sys.path_importer_cache.clear()


def get_dependencies(script, path):
    """
    Get a list of depending modules from path by running script in a separate
    process (clean module cache).

    This alternative implementation gets the list by filtering the loaded
    modules by path. Simpler than a path hook, but gets the bytecode, instead
    of sources.

    Args:
        script: filepath of the flow graph
        path: str or list of paths to filter loaded modules with
    Returns:
        a list of filepaths to the (compiled) modules
    Exception:
        ...are thrown from the process, ...
    """
    if isinstance(path, str):
        path = [path]

    def worker(queue, script, path):
        """Run script and return modules loaded from path"""
        runpy.run_path(script)
        for module in sys.modules.itervalues():
            dep_file = getattr(module, '__file__', None)
            if dep_file and any(dep_file.startswith(entry) for entry in path):
                queue.put(dep_file)

    queue = multiprocessing.queues.SimpleQueue()

    proc = multiprocessing.Process(target=worker, args=(queue, script, path))
    proc.start()
    proc.join(timeout=5)  # should be enough for loading the modules

    dependencies = []
    while not queue.empty():
        dependencies.append(queue.get())
    return dependencies
