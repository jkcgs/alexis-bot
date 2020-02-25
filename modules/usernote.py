import discord
import peewee

from bot import Command, BaseModel, categories


class UserNote(BaseModel):
    userid = peewee.TextField()
    serverid = peewee.TextField()
    note = peewee.TextField(default='')


class UserNoteCmd(Command):
    __author__ = 'makzk'
    __version__ = '1.0.0'

    db_models = [UserNote]

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'usernote'
        self.help = '$[modlog-note-help]'
        self.owner_only = True
        self.allow_pm = False
        self.category = categories.STAFF

    async def handle(self, cmd):
        if cmd.argc < 1:
            return

        member = cmd.get_member(cmd.args[0])
        if member is None:
            await cmd.answer('$[user-not-found]')
            return

        note = ' '.join(cmd.args[1:])
        if len(note) > 1000:
            await cmd.answer('$[modlog-note-err-length]')
            return

        self.set_note(member, ' '.join(cmd.args[1:]))
        await cmd.answer('$[modlog-note-set]')

    @staticmethod
    def get_note(member):
        if not isinstance(member, discord.Member):
            raise RuntimeError('member argument can only be a discord.Member')

        xd, _ = UserNote.get_or_create(serverid=member.guild.id, userid=member.id)
        return xd.note

    @staticmethod
    def set_note(member, note):
        if not isinstance(member, discord.Member):
            raise RuntimeError('member argument can only be a discord.Member')

        xd, _ = UserNote.get_or_create(serverid=member.guild.id, userid=member.id)
        xd.note = note
        xd.save()
