import glob

from os import path

from ruamel import yaml

from alexis.logger import log


class Language:
    def __init__(self, langpath, default='en', autoload=False):
        self.lib = {}
        self.path = langpath
        self.default = default

        if autoload:
            self.load()

    def load(self):
        log.info('Cargando archivos de idioma...')
        p = path.join(self.path, "**{s}*.yml".format(s=path.sep))
        lang_files = glob.iglob(p, recursive=True)
        fcount = 0

        for lang_file in lang_files:
            fn = path.basename(lang_file)
            if not path.isfile(lang_file) or not fn.endswith('.yml'):
                continue

            with open(lang_file) as f:
                fcount += 1
                yml = yaml.safe_load(f)
                lang = fn[:-4]

                for k, v in yml.items():
                    if not isinstance(v, str) and not isinstance(v, int) and not isinstance(v, float):
                        continue

                    if lang not in self.lib:
                        self.lib[lang] = {}

                    self.lib[lang][k] = str(v)

        log.info('Cargado{s} %i archivo{s}'.format(s=['s', ''][int(fcount == 1)]), fcount)

    def get(self, name, lang=None):
        if lang is None:
            lang = self.default

        if lang not in self.lib:
            return lang + '_' + name

        if name not in self.lib[lang]:
            if lang == self.default:
                return lang + '_' + name
            else:
                return self.get(name, self.default)

        return self.lib[lang][name]


class SingleLanguage:
    def __init__(self, instance, lang):
        self.instance = instance
        self.lang = lang

    def get(self, name):
        return self.instance.get(name, self.lang)
