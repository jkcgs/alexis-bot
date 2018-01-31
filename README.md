# Alexis Bot

## Requisitos

* Python 3.5+
* Soporte para SQLite3
* pip
	* aiohttp
	* appdirs
	* async-timeout
	* charde
	* cleverwrap
	* discord.py
	* multidict
	* packaging
	* peewee
	* pyparsing
	* PyYAML
	* requests
	* six
	* websockets
* virtualenv (opcional, recomendado)

## Instalación

Nota: ejecutar los siguientes comandos en una terminal.

1. Clonar el repositorio.
2. cd alexis-bot
2. Copiar config.yml.example a config.yml y configurar.
3. virtualenv . (con virtualenv instalado)
4. source bin/activate (con virtualenv instalado)
5. pip install -r requirements.txt

## Como usar

Nota: ejecutar los siguientes comandos en una terminal.

1. source bin/activate (con virtualenv instalado)
2. python alexis.py

## Cómo crear un comando

Revisar el archivo commands/ping.py a modo de ejemplo.
Además, ver definiciones base en el archivo commands/base/command.py

### Lo que se dijo en el chat sobre los comandos
(TODO: ordenar)
```
[3:06 PM] makzk: tienes que crear un módulo en la carpeta commands que contenga una o más clases que hereden la clase Command
[3:06 PM] makzk: en el __init__ debes declarar el nombre del comando y/o los hooks startswith o mention(edited)
[3:06 PM] makzk: puedes ver los otros atributos que puedes declarar en commands/base/command.py
[3:07 PM] makzk: luego, debes crear el método async def handle(self, message, cmd):, tal cual esa misma signature
[3:07 PM] makzk: donde message es el objeto MessageCmd desde on_message, y cmd es la clase Message que viene desde
commands/base/command.py que interpreta el mensaje con algunos shorthands
[3:08 PM] makzk: y ahí puedes empezar a jugar
[3:09 PM] makzk: el hook startswith sirve para cuando quieres triggerear el comando cuando empieza con un string,
y el hook mention es cuando el mensaje comienza con la mención al bot
```