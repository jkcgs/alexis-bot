import glob

from os import path

from ruamel import yaml


class Language:
    def __index__(self, langpath, default='en', autoload=False):
        self.lib = {}
        self.path = langpath
        self.default = default

        if autoload:
            self.load()

    def load(self):
        lang_files = glob.iglob(self.path + "/**/*.yml", recursive=True)

        for lang_file in lang_files:
            fn = path.basename(lang_file)
            if not path.isfile(lang_file) or not fn.endswith('.yml'):
                continue

            yml = yaml.safe_load(lang_file)
            lang = fn[:-3]
            for k, v in yml.items():
                if not isinstance(v, str) and not isinstance(v, int) and not isinstance(v, float):
                    continue

                self.lib[lang][k] = str(v)

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
