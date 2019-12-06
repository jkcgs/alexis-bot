from discord import Embed

from bot import Command, categories


class SetLanguage(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'setlanguage'
        self.aliases = ['setlang', 'lang']
        self.help = '$[lang-cmd-help]'
        self.format = '$[lang-format]'
        self.category = categories.STAFF
        self.allow_pm = False
        self.owner_only = True

    async def handle(self, cmd):
        if cmd.argc == 0:
            if cmd.config.has('lang#'+str(cmd.channel.id)):
                emb = Embed(title='$[lang-title]',
                            description='$[lang-current-guild] \n$[lang-current-chan] \n$[lang-available-list]')
                await cmd.answer(emb, locales={
                    'lang': cmd.config.get('lang', self.bot.config['default_lang'], create=False),
                    'lang_list': ', '.join(self.bot.lang.lib.keys()),
                    'chan_lang': cmd.config.get('lang#'+str(cmd.channel.id))
                })
            else:
                emb = Embed(title='$[lang-title]',
                            description='$[current-lang]\n$[lang-available-list]')
                await cmd.answer(emb, locales={
                    'lang': cmd.config.get('lang'),
                    'lang_list': ', '.join(self.bot.lang.lib.keys())
                })
            return

        lang = cmd.args[1] if cmd.argc > 1 else cmd.args[0]
        chan = cmd.args[0] if cmd.argc > 1 else None

        if chan is not None:
            chan = cmd.channel if chan in cmd.lang.get_list('lang-cmd-chan-here') else cmd.find_channel(chan)
            if chan is None:
                await cmd.answer('$[channel-not-found]')
                return

        if lang != 'unset' and not self.bot.lang.has(lang):
            await cmd.answer('$[lang-not-available]')
            return

        if chan is not None:
            if lang == 'unset':
                if not cmd.config.has('lang#'+str(chan.id)):
                    await cmd.answer('$[lang-chan-no-custom]')
                    return

                cmd.config.unset('lang#'+str(chan.id))
                self.log.debug('Set default language for channel %s in guild %s', cmd.config.get('lang'), cmd.guild)
                sv_default = cmd.config.get('lang', self.bot.config['default_lang'], create=False)
                await cmd.answer(self.bot.lang.get('lang-unset-chan', sv_default, lang=sv_default))
            else:
                cmd.config.set('lang#'+str(chan.id), lang)
                self.log.debug('Lang updated to %s for channel %s in guild %s',
                               lang, cmd.config.get('lang'), cmd.guild)
                await cmd.answer(self.bot.lang.get('lang-set-chan', lang, lang=lang))
        else:
            if lang == 'unset':
                if not cmd.config.has('lang'):
                    await cmd.answer('$[lang-no-custom]')
                    return

                cmd.config.unset('lang')
                self.log.debug('Set default language for guild %s', cmd.guild)
                await cmd.answer(self.bot.lang.get('lang-unset', None, lang=self.bot.config['default_lang']))
            else:
                cmd.config.set('lang', cmd.text)
                self.log.debug('Lang updated to %s for guild %s', cmd.config.get('lang'), cmd.guild)
                await cmd.answer(self.bot.lang.get('lang-set-to', lang, lang=cmd.text))


