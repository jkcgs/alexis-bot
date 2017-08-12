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

## Instalación

### Linux

1. Clonar el repositorio.
2. cd alexis-bot
2. Renombrar config.yml.example a config.yml y configurar.
3. virtualenv .
4. source bin/activate
5. pip install -r requirements.txt

## Windows

Usa Linux.

## Como usar

### Linux

1. source bin/activate
2. python alexis.py

### Windows

Referirse a la intalación en Windows.

## Cómo crear un comando

Revisar el archivo commands/ping.py a modo de ejemplo.
Además, ver definiciones base en el archivo commands/base/command.py
