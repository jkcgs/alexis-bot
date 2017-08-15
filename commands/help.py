from commands.base.command import Command


class Help(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'help'
        self.help = 'Muestra la lista de comandos y su ayuda'

    async def handle(self, message, cmd):
        helplist = []
        for i in self.bot.cmds.keys():
            for j in self.bot.cmds[i]:
                if j.owner_only and not cmd.owner:
                    continue

                cmds = ', !'.join(j.name) if isinstance(j.name, list) else j.name
                helpline = "- !{}: {}".format(cmds, j.help)
                if helpline not in helplist:
                    helplist.append("- !{}: {}".format(cmds, j.help))

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
