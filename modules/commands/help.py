from modules.base.command import Command


class Help(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'help'
        self.aliases = ['ayuda']
        self.help = 'Muestra la lista de comandos y su ayuda'

    async def handle(self, message, cmd):
        helplist = []
        pfx = self.bot.config['command_prefix']
        for i in self.bot.cmds.keys():
            ins = self.bot.cmds[i]
            if ins.owner_only and not cmd.owner:
                continue

            cmds = ', {}'.format(pfx).join(ins.name) if isinstance(ins.name, list) else ins.name
            helpline = "- {}{}: {}".format(pfx, cmds, ins.help)
            if helpline not in helplist:
                helplist.append("- {}{}: {}".format(pfx, cmds, ins.help))

        num_memes = len(helplist)
        if num_memes == 0:
            await cmd.answer('No hay comandos disponibles')
            return

        if not cmd.is_pm:
            await cmd.answer('{}, te enviaré la info vía PM'.format(message.author.mention))

        await self.bot.send_message(message.author, 'Estos son mis comandos:')

        # Separar lista de ayuda en mensajes con menos de 2000 carácteres
        resp_list = ''
        for helpitem in helplist:
            if len('```{}\n{}```'.format(resp_list, helpitem)) > 2000:
                await self.bot.send_message(message.author, '```{}```'.format(resp_list))
                resp_list = ''
            else:
                resp_list = '{}\n{}'.format(resp_list, helpitem)

        # Enviar lista restante
        if resp_list != '':
            await self.bot.send_message(message.author, '```{}```'.format(resp_list))

        return
