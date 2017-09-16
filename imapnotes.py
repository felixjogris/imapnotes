#!/usr/bin/python

# X-Uniform-Type-Identifier: com.apple.mail-note

import Tkinter, threading, Queue, time, os, ConfigParser

def run2(*args):
    f = q.get_nowait()
    f(None)
    pass

root = Tkinter.Tk()

w = Tkinter.Label(root, text="Hello, world!")
w.pack()
w.bind("<<foobar>>", run2)

b = Tkinter.Button(root, text="Ok")
b.pack()

l = Tkinter.Listbox(root)
l.pack()

def invokeLater(func):
    q.put(func)
    time.sleep(3)
    w.event_generate("<<foobar>>")

def run():
    b.config(text="wurst")
    invokeLater(lambda _: b.config(text="blabla"))
    pass

q = Queue.Queue()

t = threading.Thread(target=run)
t.start()

root.mainloop()

print "ende"
