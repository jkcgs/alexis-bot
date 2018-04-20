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
        raise RuntimeError('la carpeta "{}" no existe'.format(LANG_FOLDER))

    if not path.isdir(LANG_FOLDER):
        raise RuntimeError('"{}" no es una carpeta'.format(LANG_FOLDER))

    return [f for f in listdir(LANG_FOLDER) if path.isdir(path.join(LANG_FOLDER, f))]


def crear_carpeta(nombre):
    if nombre in carpetas():
        print('La carpeta ya existe')
        return None

    mkdir(path.join(LANG_FOLDER, nombre))
    print('Carpeta creada')


def cargar_idiomas(carpeta, crear=False):
    if carpeta not in carpetas():
        if crear:
            crear_carpeta(carpeta)
        else:
            print('La carpeta no existe')
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
        print('La carpeta no existe')

    idiomas = cargar_idiomas(carpeta)
    return [f for f in list(idiomas[LANGS[0]].config.keys()) if isinstance(f, str)]


if __name__ == '__main__':
    n_carpetas = carpetas()
    print('Carpetas actuales: ', n_carpetas)

    n_carpeta = '+'
    while not pat_nombre.match(n_carpeta):
        print('Ingresa el nombre de carpeta (si no existe, se creará)\n')
        n_carpeta = input('> ')
        if not pat_nombre.match(n_carpeta):
            print('Por favor, ingresa entre 3 y 20 letras, números, guiones y guiones bajos.')

    if n_carpeta not in n_carpetas:
        print('La carpeta no existe, ¿crearla?')
        respuesta = yesno()

        if not respuesta:
            print('ok saliendo')
            sys.exit(0)
        else:
            mkdir(path.join(LANG_FOLDER, n_carpeta))

    while True:
        h_langs = cargar_idiomas(n_carpeta)
        strs = strings(n_carpeta)
        if len(strs) == 0:
            print('No hay strings para esta carpeta.')
            print('Ingresa el nombre de string para crearlo.')
        else:
            print('Strings: ', ', '.join(['({}) {}'.format(i+1, f) for i, f in enumerate(strs)]))
            print('Ingresa el nombre de un string o el número del string. Si no existe se creará.')

        print('Para salir, no ingreses nada y pulsa <ENTER>.')
        n_string = input('> ').strip()

        if n_string == '':
            break

        if is_int(n_string):
            if len(strs) == 0:
                print('Por favor ingresa el nombre de un string para crearlo.')
                continue

            num = int(n_string)
            if num <= 0:
                print('Por favor, ingresa un número válido')
                continue

            if num-1 >= len(strs):
                print('El número está fuera de los índices')
                continue

            n_string = strs[num-1]
            print('String seleccionado:', n_string)
        elif n_string not in strs and len(strs) > 0:
            print('El string no existe, crearlo?')
            if not yesno():
                continue

        if n_string in strs:
            print('Valores actuales del string para los idiomas:')
            for l in LANGS:
                h_lang = h_langs[l]
                print('{}: {}'.format(l, h_lang[n_string] if n_string in h_lang else '(string no encontrado)'))

        prev = ''
        for l in LANGS:
            exists = n_string in h_langs[l]
            prox = ' (deja vacío para dejar el valor actual)' if exists else (
                ' (deja vacío para usar el string anterior)' if prev != '' else '')

            val = ''
            while val == '':
                val = input('Ingresa el valor para el idioma "{}"{}:\n> '.format(l, prox)).strip()

                if val == '':
                    if not exists and prev == '':
                        print('Debes ingresar un valor')
                    else:
                        val = h_langs[l][n_string] if exists else prev

                h_langs[l][n_string] = val
                prev = val
