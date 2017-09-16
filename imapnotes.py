#!/usr/bin/python

# X-Uniform-Type-Identifier: com.apple.mail-note

import Tkinter, threading, Queue, time, os, ConfigParser

def invokeLaterCallback(*args):
    func = eventQueue.get_nowait()
    func(None)

def invokeLater(func):
    eventQueue.put(func)
    root.event_generate("<<invokeLater>>")

def sendTestEvent():
    invokeLater(lambda _: root.title("foobar"))

root = Tkinter.Tk()
root.title("imapnotes")

frame1 = Tkinter.Frame(root)
frame1.pack(fill=Tkinter.BOTH, expand=1)

frame2 = Tkinter.Frame(frame1)
frame2.pack(side=Tkinter.LEFT)

button = Tkinter.Button(frame2, text="New")
button.pack(side=Tkinter.TOP, fill=Tkinter.X)

button = Tkinter.Button(frame2, text="Delete")
button.pack(side=Tkinter.TOP, fill=Tkinter.X)

panedWindow = Tkinter.PanedWindow(frame1, orient=Tkinter.HORIZONTAL)
panedWindow.pack(fill=Tkinter.BOTH, expand=1)

listbox = Tkinter.Listbox(panedWindow)
panedWindow.add(listbox)

text = Tkinter.Text(panedWindow)
panedWindow.add(text)

eventQueue = Queue.Queue()
root.bind("<<invokeLater>>", invokeLaterCallback)

threading.Timer(2, sendTestEvent).start()

root.mainloop()

print "ende"
