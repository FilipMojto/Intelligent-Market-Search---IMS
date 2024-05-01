from AOSS.structure.shopping import MarketPlace
from AOSS.components.marexp import MarketExplorer

from tkinter import *
from config_paths import *

root = Tk()

frame = Frame(root, background='red')
frame.pack()

def is_bound(widget, event):
    """
    Check if a widget is bound to a certain event.
    """

    bindtags = widget.bindtags()

    for tag in bindtags:
        bind_info = widget.bind_class(tag, None)

        if event in bind_info:
            return True

    return False

def haha(_):
    print("SLDDLS")

label = Label(frame, text="hahaha")
label.pack()
# label.bind("<Button-1>", haha)

print(is_bound(widget=label, event='<Button-1>'))
root.mainloop()

