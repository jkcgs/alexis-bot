import re
import sys
from os import path, listdir, mkdir


from bot.libs.configuration import StaticConfig
from bot.utils import is_int, get_bot_root

LANG_FOLDER = path.join(get_bot_root(), 'lang')
LANGS = ['en', 'es', 'es_CL']
pat_nombre = re.compile('^[0-9a-zA-Z_\-]{3,20}$')


def yesno(default_yes=True):
    prompt = '[Y/n] ' if default_yes else '[y/N] '
    resp = input(prompt).strip().lower()
    return 'y' == (resp if resp != '' else ('y' if default_yes else 'n'))


def carpetas():
    if not path.exists(LANG_FOLDER) or not path.isdir(LANG_FOLDER):
        raise RuntimeError('Folder "{}" does not exist'.format(LANG_FOLDER))

    if not path.isdir(LANG_FOLDER):
        raise RuntimeError('"{}" is not a folder'.format(LANG_FOLDER))

    return [f for f in listdir(LANG_FOLDER) if path.isdir(path.join(LANG_FOLDER, f))]


def crear_carpeta(nombre):
    if nombre in carpetas():
        print('Folder already exists')
        return None

    mkdir(path.join(LANG_FOLDER, nombre))
    print('Folder created')


def cargar_idiomas(carpeta, crear=False):
    if carpeta not in carpetas():
        if crear:
            crear_carpeta(carpeta)
        else:
            print('Folder does not exist')
            return None

    langs = {}
    for l in LANGS:
        langpath = path.join(LANG_FOLDER, carpeta, l + '.yml')
        with open(langpath, 'a+') as f:
            f.close()
            langs[l] = StaticConfig(langpath, True)

    return langs


def strings(carpeta):
    if carpeta not in carpetas():
        print('Folder does not exist')

    idiomas = cargar_idiomas(carpeta)
    return [f for f in list(idiomas[LANGS[0]].config.keys()) if isinstance(f, str)]


if __name__ == '__main__':
    n_carpetas = carpetas()
    print('Current folders: ', n_carpetas)

    n_carpeta = '+'
    while not pat_nombre.match(n_carpeta):
        print('Input the folder\'s name (if it doesn\'t exist, it will be created)\n')
        n_carpeta = input('> ')
        if not pat_nombre.match(n_carpeta):
            print('Please, type between 3 y 20 characters, numbers, hyphens and underscores.')

    if n_carpeta not in n_carpetas:
        print('The folder does not exist. Create it?')
        respuesta = yesno()

        if not respuesta:
            print('OK, exiting.')
            sys.exit(0)
        else:
            mkdir(path.join(LANG_FOLDER, n_carpeta))

    while True:
        h_langs = cargar_idiomas(n_carpeta)
        strs = strings(n_carpeta)
        if len(strs) == 0:
            print('There are no strings for this folder.')
            print('Input the string name to create it.')
        else:
            print('Strings: ', ', '.join(['({}) {}'.format(i+1, f) for i, f in enumerate(strs)]))
            print('Input the name or number of the string. If it does not exist, it will be created.')

        print('To exit, leave it blank and press <ENTER>.')
        n_string = input('> ').strip()

        if n_string == '':
            break

        if is_int(n_string):
            if len(strs) == 0:
                print('Please, input the string name to create it.')
                continue

            num = int(n_string)
            if num <= 0:
                print('Please input a valid number')
                continue

            if num-1 >= len(strs):
                print('The number is out of bounds.')
                continue

            n_string = strs[num-1]
            print('Selected string:', n_string)
        elif n_string not in strs and len(strs) > 0:
            print('The string does not exist. Create it?')
            if not yesno():
                continue

        if n_string in strs:
            print('Current values for the string in languages:')
            for l in LANGS:
                h_lang = h_langs[l]
                print('{}: {}'.format(l, h_lang[n_string] if n_string in h_lang else '(string not found)'))

        prev = ''
        for l in LANGS:
            exists = n_string in h_langs[l]
            prox = ' (leave empty to keep the current value)' if exists else (
                ' (leave empty to keep the previous value)' if prev != '' else '')

            val = ''
            while val == '':
                val = input('Input the value for the "{}" language{}:\n> '.format(l, prox)).strip()

                if val == '':
                    if not exists and prev == '':
                        print('You must input a value')
                    else:
                        val = h_langs[l][n_string] if exists else prev

                h_langs[l][n_string] = val
                prev = val
