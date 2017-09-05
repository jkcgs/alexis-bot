from os.path import dirname, isfile, sep
import glob
import inspect
from modules.base.command import Command

cdir = dirname(__file__)
modules = glob.iglob(cdir + "/**/*.py", recursive=True)
__all__ = [f.replace(cdir+sep, '')[:-3].replace(sep, '.') for f in modules if isfile(f) and not f.endswith('__init__.py')]

classes = []
for imod in __all__:
    try:
        mod = __import__('modules.commands.' + imod, fromlist=[''])
    except ModuleNotFoundError as e:
        print(e)
        continue

    for name, obj in inspect.getmembers(mod):
        if inspect.isclass(obj) and name != 'Command' and issubclass(obj, Command):
            classes.append(obj)
