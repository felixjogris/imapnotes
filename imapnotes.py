#!/usr/bin/python

# X-Uniform-Type-Identifier: com.apple.mail-note

import Tkinter, threading, Queue, os, ConfigParser, imaplib
import email.parser, email.header, HTMLParser, re, tkFont

class HTMLNoteParser(HTMLParser.HTMLParser):
    style_tag = ""
    style_num = 0

    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        for tag in text.tag_names():
            text.tag_delete(tag)

    def getColor(self, cssvalue):
        rgba_re = re.compile(r"rgba?\((\d{1,3}),\s*(\d{1,3}),\s*(\d{1,3})")
        match = rgba_re.match(cssvalue)
        if match is None:
            return cssvalue
        else:
            return "#%02x%02x%02x" % tuple(map(int, match.group(1, 2, 3)))

    def parseStyle(self, css):
        style = {}

        for setting in [x for x in css.split(";") if ":" in x]:
            cssname, cssvalue = map(str.strip, setting.split(":", 1))
            if cssname == "color":
                style["foreground"] = self.getColor(cssvalue)
            elif cssname == "background-color":
                style["background"] = self.getColor(cssvalue)

        text.tag_configure(self.style_tag, style)
                
    def handle_starttag(self, tag, attrs):
        self.style_tag = "tag%d" % (self.style_num,)
        self.style_num += 1

        for name, value in attrs:
            if name == "style":
                self.parseStyle(value)
        if tag == "strike":
            text.tag_configure(self.style_tag, font=tkFont.Font(overstrike=True))

    def handle_endtag(self, tag):
        if tag in ("br", "div", "p", "h1", "h2", "h3", "h4"):
            text.insert(Tkinter.END, "\n")

    def handle_startendtag(self, tag, attrs):
        if tag in ("br", "div", "p", "h1", "h2", "h3", "h4"):
            text.insert(Tkinter.END, "\n")

    def handle_data(self, data):
        previous_style_tag = self.style_tag
        text.insert(Tkinter.END, data, self.style_tag)
        self.style_tag = previous_style_tag

def invokeLaterCallback(*args):
    func = eventQueue.get_nowait()
    func(None)

def invokeLater(func):
    eventQueue.put(func)
    root.event_generate("<<invokeLater>>")

def displayMessage(message):
    if message.is_multipart():
        for part in message.get_payload():
            displayMessage(part)
    else:
        contenttype = message.get_content_type().lower()
        body = message.get_payload(decode=True)
        if contenttype.startswith("text/plain"):
            text.insert(Tkinter.END, body)
        elif contenttype.startswith("text/html"):
            HTMLNoteParser().feed(body)
        else:
            text.insert(Tkinter.END, "<cannot display " + contenttype + ">")

def displayNote(*args):
    index = listbox.curselection()[0]
    message = notes[len(notes) - index - 1]["message"]
    text.delete(1.0, Tkinter.END)
    displayMessage(message)

config = ConfigParser.SafeConfigParser()
config.read(os.path.expanduser("~/.imapnotes.ini"))

host = config.get("connection", "host")
if config.has_option("connection", "port"):
    imap = imaplib.IMAP4_SSL(host, config.get("connection", "port"))
else:
    imap = imaplib.IMAP4_SSL(host)
imap.login(config.get("connection", "user"), config.get("connection", "pass"))

imap.select("Notes")
# search returns tuple with list
notes_numbers = imap.search(None, "ALL")[1][0].replace(" ", ",")
# imap fetch expects comma separated list
notes_list = imap.fetch(notes_numbers, "RFC822")
notes = []

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
    notes.append({"num": num, "message": message, "subject": subject})

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
vscroll = Tkinter.Scrollbar(listbox, command=listbox.yview, orient=Tkinter.VERTICAL)
vscroll.pack(side=Tkinter.RIGHT, fill=Tkinter.Y)
listbox.config(yscrollcommand=vscroll.set)
panedWindow.add(listbox, width=300, height=400)
for note in notes:
    listbox.insert(0, note["subject"])
listbox.bind("<<ListboxSelect>>", displayNote)

text = Tkinter.Text(panedWindow, undo=True, wrap=Tkinter.WORD)
vscroll = Tkinter.Scrollbar(text, command=text.yview, orient=Tkinter.VERTICAL)
vscroll.pack(side=Tkinter.RIGHT, fill=Tkinter.Y)
text.config(yscrollcommand=vscroll.set)
panedWindow.add(text, width=500)

eventQueue = Queue.Queue()
root.bind("<<invokeLater>>", invokeLaterCallback)

#threading.Timer(2, lambda _: root.title("foobar"), (None,)).start()

root.mainloop()

print "ende"
