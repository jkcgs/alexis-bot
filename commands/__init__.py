from os.path import dirname, basename, isfile
import glob
import inspect
from commands.base.command import Command
modules = glob.glob(dirname(__file__)+"/*.py")
modules = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
__all__ = modules

classes = []
for imod in __all__:
    mod = __import__('commands.' + imod, fromlist=[''])

    for name, obj in inspect.getmembers(mod):
        if inspect.isclass(obj) and name != 'Command' and issubclass(obj, Command):
            classes.append(obj)
