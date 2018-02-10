import os
from os import path
from alexis.configuration import StaticConfig

LANG_FOLDER = 'lang'
LANGS = ['en', 'es', 'es_CL']


def carpetas():
    if not path.exists(LANG_FOLDER) or not path.isdir(LANG_FOLDER):
        raise RuntimeError('la carpeta "{}" no existe'.format(LANG_FOLDER))

    if not path.isdir(LANG_FOLDER):
        raise RuntimeError('"{}" no es una carpeta'.format(LANG_FOLDER))

    return [f for f in os.listdir(LANG_FOLDER) if path.isdir(path.join(LANG_FOLDER, f))]


def crear_carpeta(nombre):
    if nombre in carpetas():
        print('La carpeta ya existe')
        return None

    os.mkdir(os.path.join(LANG_FOLDER, nombre))
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
        with open(langpath, 'w+') as f:
            f.close()
            langs[l] = StaticConfig(langpath, True)

    return langs


def strings(carpeta):
    if carpeta not in carpetas():
        print('La carpeta no existe')


def gestionar(carpeta):
    while True:
        print('Carpeta: ', carpeta)
        print('Idiomas: ', LANGS)
        print("""
1. Listar strings actuales
2. Mostrar string
3. Agregar string
4. Volver al menú anterior
""")
        y = input('> ')
        if y not in ['1', '2', '3', '4']:
            print('Ingresa una opción válida')

        if y == '1':
            print('listar strings')
        elif y == '2':
            print('mostrar string')
        elif y == '3':
            print('mostrar string actual')


x = ''

while x != '0':
    print("""
Ingresa una opción:
1. usar carpeta existente
2. crear nueva carpeta

0. cancelar
""")

    x = input('> ')
    if x not in ['0', '1', '2']:
        print('Elije una opción válida')
    else:
        break

if x == '1':
    print('elegiste usar carpeta existente')
    print('carpetas: ', carpetas())
elif x == '2':
    print()
    nueva_carpeta = input('Ingresa nombre de nueva carpeta:\n> ')
else:
    print('elegiste: ', x)

print('bye')
