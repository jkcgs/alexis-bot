from os import path
import glob
import inspect
import sys

from modules.base.command import Command
from modules.logger import log


def get_mod_files(fpath):
    """
    Carga una lista de archivos script
    :param fpath: El directorio a analizar
    :return: La lista de ubicaciones de los script, como nombre de módulo
    """
    result = []
    mod_files = glob.iglob(fpath + "/**/*.py", recursive=True)

    for mod_file in mod_files:
        if not path.isfile(mod_file) or not mod_file.endswith('.py') or mod_file.endswith('__init__.py'):
            continue
        result.append(mod_file.replace(fpath + path.sep, '')[:-3].replace(path.sep, '.'))

    return result


def get_mods(ext_path=''):
    """
    Carga los módulos disponibles
    :param ext_path: Una carpeta de módulos externos
    :return: Una lista de instancias de los módulos de comandos
    """
    log.debug('Cargando módulos...')
    classes = []
    _all = ['modules.commands.' + f for f in get_mod_files(path.dirname(__file__))]

    if ext_path != '' and path.isdir(ext_path):
        ext_mods = get_mod_files(ext_path)
        sys.path.append(ext_path)
        _all += ext_mods

    for imod in _all:
        try:
            mod = __import__(imod, fromlist=[''])
        except ImportError as e:
            log.error('No se pudo cargar un módulo')
            log.exception(e)
            continue

        for name, obj in inspect.getmembers(mod):
            if inspect.isclass(obj) and name != 'Command' and issubclass(obj, Command):
                classes.append(obj)

    log.debug('Se encontraron %i módulos', len(classes))
    return classes
