#!/usr/bin/python

# X-Uniform-Type-Identifier: com.apple.mail-note

import Tkinter, threading, Queue, os, ConfigParser, imaplib, email.parser, email.header

def invokeLaterCallback(*args):
    func = eventQueue.get_nowait()
    func(None)

def invokeLater(func):
    eventQueue.put(func)
    root.event_generate("<<invokeLater>>")

config = ConfigParser.SafeConfigParser()
config.read(os.path.expanduser("~/.imapnotes.ini"))

host = config.get("connection", "host")
if config.has_option("connection", "port"):
    imap = imaplib.IMAP4_SSL(host, config.get("connection", "port"))
else:
    imap = imaplib.IMAP4_SSL(host)
imap.login(config.get("connection", "user"), config.get("connection", "pass"))

imap.select("Notes")
notes_numbers = imap.search(None, "ALL")[1][0].replace(" ", ",") # search returns tuple with list
notes_list = imap.fetch(notes_numbers, "RFC822") # imap fetch expects comma separated list
notes = {}

for part in notes_list[1]:
    # imap fetch returns s.th. like: ('OK', [('1 (RFC822 {519}', 'From: ...'), ')'])
    if part == ")":
       continue
    num = int(part[0].split()[0])
    message = email.message_from_string(part[1])
    subject = ""
    for substring, charset in email.header.decode_header(message.get("subject")):
        if not charset is None:
            substring.decode(charset)
        subject += substring
    notes[num] = {"message": message, "subject": subject}

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
for num in sorted(notes):
    listbox.insert(0, notes[num]["subject"])

text = Tkinter.Text(panedWindow)
panedWindow.add(text)

eventQueue = Queue.Queue()
root.bind("<<invokeLater>>", invokeLaterCallback)

#threading.Timer(2, lambda _: root.title("foobar"), (None,)).start()

root.mainloop()

print "ende"
