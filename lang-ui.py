from random import randint
from tkinter import *
from tkinter.ttk import *


class Application(Frame):
    def __init__(self, master=None):
        super().__init__(master)

        self.master.title = 'Bot Language Manager'

        self.list_files_text = Label(self.master, text='Language folders')
        self.list_files_text.grid(column=0, row=0, sticky=W)
        self.list_files_btn = Button(self.master, text='+', width=2, command=self.load_strings)
        self.list_files_btn.grid(column=1, row=0, sticky=E)
        self.list_files = Listbox(self.master, width=33, height=20)
        self.list_files.grid(column=0, row=1, columnspan=2, sticky=NW)

        self.langlist_label = Label(self.master, text='Language list')
        self.langlist_label.grid(row=0, column=2, sticky=W)
        self.langlist = Combobox(self.master, width=30, state='readonly')
        self.langlist.grid(row=0, column=3, sticky=W)

        self.frm_strings = Frame(self.master, height=330, width=400)
        self.frm_strings.grid(row=1, column=2, columnspan=2, sticky=NW)
        self.frm_strings.grid_propagate(0)

        self.strings_col1_title = Label(self.frm_strings, text='Name', width=15)
        self.strings_col1_title.grid(row=0, column=0, sticky=W)
        self.strings_col2_title = Label(self.frm_strings, text='Value')
        self.strings_col2_title.grid(row=0, column=1, sticky=W)

        self.strings_inputs = []
        self.load_strings('xd', 'jaj')

    def load_strings(self, folder='', lang=''):
        for inp in self.strings_inputs:
            [i.grid_forget() and i.destroy() for i in list(inp)]

        self.strings_inputs = []

        for i in range(40):
            l1 = Label(self.frm_strings, text=('xddd'+str(i+1)))
            l1.grid(row=i+1, column=0, sticky=W)
            l2 = Label(self.frm_strings, text=('random text jsjsj '+str(randint(1000, 9999))))
            l2.grid(row=i+1, column=1, sticky=W)

            self.strings_inputs.append((l1, l2))


if __name__ == '__main__':
    root = Tk()
    app = Application(master=root)
    app.mainloop()
