from os import path
import glob
import inspect
import sys

from alexis.base.command import Command
from alexis.logger import log


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
    classes = []

    # Listar módulos internos
    _all = ['alexis.modules.' + f for f in get_mod_files(path.dirname(__file__))]

    local_ext = path.join(path.dirname(__file__), '..', '..', 'external_modules')
    if path.isdir(local_ext):
        _all += ['external_modules.' + f for f in get_mod_files(local_ext)]

    # Listar módulos externos
    if ext_path != '' and path.isdir(ext_path):
        ext_mods = get_mod_files(ext_path)
        sys.path.append(ext_path)
        _all += ext_mods

    # Cargar todos los módulos
    for imod in _all:
        try:
            mod = __import__(imod, fromlist=[''])
        except ImportError as e:
            log.error('No se pudo cargar un módulo')
            log.exception(e)
            continue

        # Instanciar módulos disponibles
        for name, obj in inspect.getmembers(mod):
            if inspect.isclass(obj) and name != 'Command' and issubclass(obj, Command):
                classes.append(obj)

    return classes
