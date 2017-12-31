from alexis import Command


class Help(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'help'
        self.aliases = ['ayuda']
        self.help = 'Muestra la lista de comandos y su ayuda'

    async def handle(self, message, cmd):
        helplist = []
        for i in self.bot.cmds.keys():
            ins = self.bot.cmds[i]
            if ins.owner_only and not cmd.owner:
                continue
            if ins.bot_owner_only and not cmd.bot_owner:
                continue

            cmds = ', $PX'.join(ins.name) if isinstance(ins.name, list) else ins.name
            helpline = "- $PX{}: {}".format(cmds, ins.help)
            if helpline not in helplist:
                helplist.append("- $PX{}: {}".format(cmds, ins.help))

        num_memes = len(helplist)
        if num_memes == 0:
            await cmd.answer('no hay comandos disponibles')
            return

        if not cmd.is_pm:
            await cmd.answer('te enviaré la info vía PM')

        await cmd.answer('estos son mis comandos:', to_author=True)

        # Separar lista de ayuda en mensajes con menos de 2000 carácteres
        resp_list = ''
        for helpitem in helplist:
            if len('```{}\n{}```'.format(resp_list, helpitem)) > 2000:
                await cmd.answer('```{}```'.format(resp_list), to_author=True, withname=False)
                resp_list = ''
            else:
                resp_list = '{}\n{}'.format(resp_list, helpitem)

        # Enviar lista restante
        if resp_list != '':
            await cmd.answer('```{}```'.format(resp_list), to_author=True, withname=False)

        return
