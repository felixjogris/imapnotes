#!/usr/bin/python

import Tkinter, os, ConfigParser, imaplib, email.parser, email.header
import HTMLParser, re, tkFont, time, StringIO
from PIL import Image, ImageTk

class HTMLNoteParser(HTMLParser.HTMLParser):
    style_tag = ""
    style_num = 0
    textField = None

    def __init__(self, textField):
        HTMLParser.HTMLParser.__init__(self)
        self.textField = textField

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

        self.textField.tag_configure(self.style_tag, style)
                
    def handle_starttag(self, tag, attrs):
        self.style_tag = "tag%d" % (self.style_num,)
        self.style_num += 1

        if tag == "strike":
            font = tkFont.Font(overstrike=True)
            self.textField.tag_configure(self.style_tag, font=font)
        elif tag == "b":
            font = tkFont.Font(weight="bold")
            self.textField.tag_configure(self.style_tag, font=font)
        elif tag == "i":
            font = tkFont.Font(weight="italic")
            self.textField.tag_configure(self.style_tag, font=font)
        elif tag in ("div", "p", "h1", "h2", "h3", "h4"):
            self.textField.insert(Tkinter.END, "\n")

        for name, value in attrs:
            if name == "style":
                self.parseStyle(value)

    def handle_endtag(self, tag):
        if tag in ("br", "div", "p", "h1", "h2", "h3", "h4"):
            self.textField.insert(Tkinter.END, "\n")

    def handle_startendtag(self, tag, attrs):
        if tag in ("br", "div", "p", "h1", "h2", "h3", "h4"):
            self.textField.insert(Tkinter.END, "\n")

    def handle_data(self, data):
        previous_style_tag = self.style_tag
        self.textField.insert(Tkinter.END, data, self.style_tag)
        self.style_tag = previous_style_tag

def displayMessage(message):
    if message.is_multipart():
        for part in message.get_payload():
            displayMessage(part)
    else:
        contenttype = message.get_content_type().lower()
        body = message.get_payload(decode=True)
        if contenttype.startswith("text/plain"):
            textField.insert(Tkinter.END, body)
        elif contenttype.startswith("text/html"):
            HTMLNoteParser(textField).feed(body)
        elif contenttype.startswith("image/"):
            img = ImageTk.PhotoImage(Image.open(StringIO.StringIO(body)))
            textField.image_create(Tkinter.END, image=img)
        else:
            textField.insert(Tkinter.END, "<cannot display " + contenttype + ">")

def displayNote(*args):
    global noteChanged

    if noteChanged:
        index = listBox.index(Tkinter.ACTIVE)
        subject = textField.get(1.0, 2.0).strip().encode("utf-8")
        body = textField.get(1.0, Tkinter.END).encode("utf-8")
        note = notes[len(notes) - index - 1]
        note["message"].set_payload(body)
        note["subject"] = subject
        note["changed"] = True
        listBox.delete(index)
        listBox.insert(index, subject)
    noteChanged = False

    index = listBox.curselection()

    if len(index) > 0:
        textField.delete(1.0, Tkinter.END)
        for tag in textField.tag_names():
            textField.tag_delete(tag)
        index = index[0]
        message = notes[len(notes) - index - 1]["message"]
        displayMessage(message)
        deleteButton.config(state=Tkinter.NORMAL)
        textField.edit_modified(False)
    else:
        deleteButton.config(state=Tkinter.DISABLED)

def newNote():
    subject = "new note"
    message = email.message_from_string("")
    notes.append({
        "uid":     -1,
        "message": message,
        "subject": subject,
        "changed": False,
    })
    listBox.insert(0, subject)
    listBox.selection_clear(0, Tkinter.END)
    listBox.selection_set(0)
    listBox.activate(0)
    listBox.event_generate("<<ListboxSelect>>")

def deleteNote():
    pass

def set_header(message, header, value):
    if message.has_key(header):
        message.replace_header(header, value)
    else:
        message[header] = value

def saveNotes(*args):
    for note in [x for x in notes if x["changed"]]:
        message = note["message"]
        subject = email.header.Header(note["subject"], "utf-8")
        set_header(message, "Subject", subject)
        set_header(message, "Content-Type", "text/plain; charset=utf-8")
        set_header(message, "Content-Transfer-Encoding", "8bit")
        set_header(message, "X-Uniform-Type-Identifier", "com.apple.mail-note")
        now = imaplib.Time2Internaldate(time.time())
        ret = imap.append("Notes", "", now, message.as_string())
        print "changed note:\nsubject=%s\nret=%s\n" % (subject,ret)
    root.destroy()

def textModified(*args):
    global noteChanged
    if textField.edit_modified():
        noteChanged = True

def imapNoop():
    imap.noop()


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
notes_numbers = imap.uid("search", None, "ALL")[1][0].replace(" ", ",")
# imap fetch expects comma separated list
notes_list = imap.uid("fetch", notes_numbers, "RFC822")
notes = []

for part in notes_list[1]:
    # imap fetch returns s.th. like: ('OK', [('1 (RFC822 {519}', 'From: ...'), ')'])
    if part == ")":
       continue
    uid = int(part[0].split()[0])
    message = email.message_from_string(part[1])
    subject = ""
    raw_subject = message.get("subject")
    for substring, charset in email.header.decode_header(raw_subject):
        if not charset is None:
            substring.decode(charset)
        subject += substring
    notes.append({
        "uid":     uid,
        "message": message,
        "subject": subject,
        "changed": False,
    })

root = Tkinter.Tk()
root.protocol("WM_DELETE_WINDOW", saveNotes)
root.after(42000, imapNoop)
root.title("imapnotes")

frameButtons = Tkinter.Frame(root)
frameButtons.pack(fill=Tkinter.BOTH, expand=1)

frameListAndText = Tkinter.Frame(frameButtons)
frameListAndText.pack(side=Tkinter.LEFT)

newButton = Tkinter.Button(frameListAndText, text="New", command=newNote)
newButton.pack(side=Tkinter.TOP, fill=Tkinter.X)

deleteButton = Tkinter.Button(frameListAndText, text="Delete",
                              command=deleteNote, state=Tkinter.DISABLED)
deleteButton.pack(side=Tkinter.TOP, fill=Tkinter.X)

panedWindow = Tkinter.PanedWindow(frameButtons, orient=Tkinter.HORIZONTAL)
panedWindow.pack(fill=Tkinter.BOTH, expand=1)

listBox = Tkinter.Listbox(panedWindow)
vscroll = Tkinter.Scrollbar(listBox, command=listBox.yview,
                            orient=Tkinter.VERTICAL)
vscroll.pack(side=Tkinter.RIGHT, fill=Tkinter.Y)
listBox.config(yscrollcommand=vscroll.set)
panedWindow.add(listBox, width=300, height=400)
for note in notes:
    listBox.insert(0, note["subject"])
listBox.bind("<<ListboxSelect>>", displayNote)

textField = Tkinter.Text(panedWindow, undo=True, wrap=Tkinter.WORD)
vscroll = Tkinter.Scrollbar(textField, command=textField.yview,
                            orient=Tkinter.VERTICAL)
vscroll.pack(side=Tkinter.RIGHT, fill=Tkinter.Y)
textField.config(yscrollcommand=vscroll.set)
textField.bind("<<Modified>>", textModified)
panedWindow.add(textField, width=500)

noteChanged = False

root.mainloop()
