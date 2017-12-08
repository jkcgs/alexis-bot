from os.path import dirname, isfile, sep, isdir, join
import glob
import inspect

import sys
import yaml

from modules.base.command import Command


def get_mods(path):
    result = []
    mod_files = glob.iglob(path + "/**/*.py", recursive=True)

    for mod_file in mod_files:
        if not isfile(mod_file) or mod_file.endswith('__init__.py'):
            continue
        result.append(mod_file.replace(path + sep, '')[:-3].replace(sep, '.'))

    return result


__all__ = get_mods(dirname(__file__))
n_mods = len(__all__)

with open(join('.', 'config.yml'), 'r') as file:
    config = yaml.safe_load(file)
    if config is None:
        config = {}
    mods_path = config.get('ext_modpath', '')
    if mods_path != '' and isdir(mods_path):
        ext_mods = get_mods(mods_path)
        ne_mods = len(ext_mods)
        sys.path.append(mods_path)
        __all__ += ext_mods

classes = []
for imod in __all__:
    try:
        mod = __import__('modules.commands.' + imod, fromlist=[''])
    except ImportError:
        mod = __import__(imod, fromlist=[''])

    for name, obj in inspect.getmembers(mod):
        if inspect.isclass(obj) and name != 'Command' and issubclass(obj, Command):
            classes.append(obj)
