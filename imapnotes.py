#!/usr/bin/env python3.7

import os, sys, re, time, io, configparser, imaplib, html.parser, base64
import email.parser, email.header, email.utils
import tkinter, tkinter.font, tkinter.messagebox, PIL.Image, PIL.ImageTk

class HTMLNoteParser(html.parser.HTMLParser):
    style_tag = ""
    style_num = 0
    textField = None

    def __init__(self, textField):
        html.parser.HTMLParser.__init__(self)
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
            font = tkinter.font.Font(overstrike=True)
            self.textField.tag_configure(self.style_tag, font=font)
        elif tag == "b":
            font = tkinter.font.Font(weight="bold")
            self.textField.tag_configure(self.style_tag, font=font)
        elif tag == "i":
            font = tkinter.font.Font(weight="italic")
            self.textField.tag_configure(self.style_tag, font=font)
        elif tag in ("br", "div", "p", "h1", "h2", "h3", "h4"):
            self.textField.insert(tkinter.END, "\n")

        for name, value in attrs:
            if name == "style":
                self.parseStyle(value)

    def handle_endtag(self, tag):
        if tag in ("div", "p", "h1", "h2", "h3", "h4"):
            self.textField.insert(tkinter.END, "\n")

    def handle_startendtag(self, tag, attrs):
        if tag in ("br", "div", "p", "h1", "h2", "h3", "h4"):
            self.textField.insert(tkinter.END, "\n")

    def handle_data(self, data):
        previous_style_tag = self.style_tag
        self.textField.insert(tkinter.END, data.replace("\r", ""),
                              self.style_tag)
        self.style_tag = previous_style_tag

def displayMessage(message):
    if message.is_multipart():
        for part in message.get_payload():
            displayMessage(part)
    else:
        contenttype = message.get_content_type().lower()
        body = message.get_payload(decode=True)
        if contenttype.startswith("text/plain"):
            textField.insert(tkinter.END, body.decode().replace("\r", ""))
        elif contenttype.startswith("text/html"):
            HTMLNoteParser(textField).feed(body.decode())
        elif contenttype.startswith("image/"):
            img = PIL.ImageTk.PhotoImage(data=body)
            textField.image_create(tkinter.END, image=img)
            imgCache.append(img)
        else:
            textField.insert(tkinter.END, "<cannot display " + contenttype +
                             ">")

def displayNote(*args):
    global noteChanged

    if noteChanged:
        index = listBox.index(tkinter.ACTIVE)
        subject = textField.get(1.0, 2.0).strip().encode("utf-8")
        body = textField.get(1.0, tkinter.END).encode("utf-8")
        note = notes[len(notes) - index - 1]
        note["message"].set_payload(body)
        note["subject"] = subject
        note["changed"] = True
        listBox.delete(index)
        listBox.insert(index, subject)
    noteChanged = False

    index = listBox.curselection()

    if len(index) > 0:
        textField.delete(1.0, tkinter.END)
        for tag in textField.tag_names():
            textField.tag_delete(tag)
        index = index[0]
        message = notes[len(notes) - index - 1]["message"]
        imgCache = []
        displayMessage(message)
        deleteButton.config(state=tkinter.NORMAL)
        textField.edit_modified(False)
    else:
        deleteButton.config(state=tkinter.DISABLED)

def newNote():
    subject = "new note"
    message = email.message_from_string("")
    notes.append({
        "uid":     None,
        "message": message,
        "subject": subject,
        "changed": False,
    })
    listBox.insert(0, subject)
    listBox.selection_clear(0, tkinter.END)
    listBox.selection_set(0)
    listBox.activate(0)
    listBox.event_generate("<<ListboxSelect>>")

def deleteNote():
    print("not yet implemented")

def set_header(message, header, value, replace=True):
    if not header in message.keys():
        message[header] = value
    elif replace:
        message.replace_header(header, value)

def imapConnect():
    try:
        config = configparser.ConfigParser()
        config.read(os.path.expanduser("~/.imapnotes.ini"))

        host = config.get("connection", "host")
        if config.has_option("connection", "port"):
            imap = imaplib.IMAP4_SSL(host, config.get("connection", "port"))
        else:
            imap = imaplib.IMAP4_SSL(host)

        imap.login(config.get("connection", "user"),
                   config.get("connection", "pass"))
        imap.select("Notes")

        return imap
    except Exception as e:
        tkinter.messagebox.showerror("Connection failed",
            "Cannot connect to IMAPS server:\n%s" % (str(e),))
        sys.exit(1)

def imapNoop():
    try:
        imap.noop()
    except Exception as e:
        imapConnect()

def saveNotes(*args):
    displayNote(args)
    imapNoop()

    for note in [x for x in notes if x["changed"]]:
        message = note["message"]
        subject = email.header.Header(note["subject"], "utf-8")
        rfc_now = email.utils.formatdate(localtime=True)
        set_header(message, "Subject", subject)
        set_header(message, "Content-Type", "text/plain; charset=utf-8")
        set_header(message, "Content-Transfer-Encoding", "8bit")
        set_header(message, "X-Uniform-Type-Identifier", "com.apple.mail-note")
        set_header(message, "Message-ID", email.utils.make_msgid())
        set_header(message, "Date", email.utils.formatdate(localtime=True))
        set_header(message, "X-Mail-Created-Date", rfc_now, False)
        set_header(message, "X-Universally-Unique-Identifier",
                   email.utils.make_msgid().split("@")[0][1:], False)
        now = imaplib.Time2Internaldate(time.time())
        ret = imap.append("Notes", "", now, message.as_bytes())
        print("changed note:\nsubject=%s\nret=%s\n" % (subject,ret))
        uid = note["uid"]
        if not uid is None:
            ret = imap.uid("COPY", uid, "Trash")
            print("moved note to Trash:\nuid=%s\nret=%s\n" % (uid, ret))
            ret = imap.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
            print("deleted note:\nuid=%s\nret=%s\n" % (uid, ret))
    print("expunged mailbox=%s\n" % (imap.expunge(),))
    print("closed mailbox=%s\n" % (imap.close(),))
    root.destroy()

def textModified(*args):
    global noteChanged
    if textField.edit_modified():
        noteChanged = True


imap = imapConnect()

notes = []
# search returns tuple with list
notes_numbers = imap.uid("search", None, "ALL")[1][0].decode().replace(" ", ",")
# imap fetch expects comma separated list
if len(notes_numbers) > 0:
    notes_list = imap.uid("fetch", notes_numbers, "RFC822")
    uid_re = re.compile(r"UID\s+(\d+)")
    for part in notes_list[1]:
        # imap fetch returns s.th. like:
        # ('OK', [('1 (UID 1 RFC822 {519}', 'From: ...'), ')'])
        if part == b")":
           continue
        match = uid_re.search(part[0].decode())
        uid = None if match is None else match.group(1)
        message = email.message_from_bytes(part[1])
        subject = ""
        raw_subject = message.get("subject")
        for substring, charset in email.header.decode_header(raw_subject):
            if not charset is None:
                substring = substring.decode(charset)
            subject += substring
        notes.append({
            "uid":     uid,
            "message": message,
            "subject": subject,
            "changed": False,
        })

gifdata = base64.b64decode("""
R0lGODlhQABAAKECAAAAAPHKGf///////yH5BAEKAAIALAAAAABAAEAAAAL+lH+gy+0PI0C0Jolz
tvzqDypdtwTmiabqyqLLyJXtTLcvXMn1vt84ouMJWb6fIThMnopGXegJWIqMHin0Y6VWTVdQVitA
KpPMn3gsLOPO6N5Uy27T1LC43Pam2u8r+sjZpfEFp2AVKDGoV8h1iJHYtMjH40cSKVlDGWN5OZNp
scfJOAEGGuqZsxnalwcZJdoI8WgWCYsoChZGWxt7S5qqmnJKUcopDPQLLLuGnBxgvNWs8nzEnDyd
6+q8+6Bcp7vd0P33DQ44Spgd7cI6m67ei/4ezL7s/n5NfIlfDbxvr+7PULlsAV8NFFeJ4EBzuPJJ
KigPnqJ/0SBGtCgP4z0pet4oNoO4kKEvhSERaiK50OQnfqo0AuQ4zqM1mAlDYmhoc8PInBE6FAAA
Ow==
""")

root = tkinter.Tk()
gificon = tkinter.PhotoImage(data=gifdata)
root.tk.call('wm', 'iconphoto', root._w, gificon)
root.title("imapnotes")
root.protocol("WM_DELETE_WINDOW", saveNotes)
root.after(42000, imapNoop)

frameButtons = tkinter.Frame(root)
frameButtons.pack(fill=tkinter.BOTH, expand=1)

frameListAndText = tkinter.Frame(frameButtons)
frameListAndText.pack(side=tkinter.LEFT)

newButton = tkinter.Button(frameListAndText, text="New", command=newNote)
newButton.pack(side=tkinter.TOP, fill=tkinter.X)

deleteButton = tkinter.Button(frameListAndText, text="Delete",
                              command=deleteNote, state=tkinter.DISABLED)
deleteButton.pack(side=tkinter.TOP, fill=tkinter.X)

panedWindow = tkinter.PanedWindow(frameButtons, orient=tkinter.HORIZONTAL)
panedWindow.pack(fill=tkinter.BOTH, expand=1)

listBox = tkinter.Listbox(panedWindow)
vscroll = tkinter.Scrollbar(listBox, command=listBox.yview,
                            orient=tkinter.VERTICAL)
vscroll.pack(side=tkinter.RIGHT, fill=tkinter.Y)
listBox.config(yscrollcommand=vscroll.set)
panedWindow.add(listBox, width=300, height=400)
for note in notes:
    listBox.insert(0, note["subject"])
listBox.bind("<<ListboxSelect>>", displayNote)

textField = tkinter.Text(panedWindow, undo=True, wrap=tkinter.WORD)
vscroll = tkinter.Scrollbar(textField, command=textField.yview,
                            orient=tkinter.VERTICAL)
vscroll.pack(side=tkinter.RIGHT, fill=tkinter.Y)
textField.config(yscrollcommand=vscroll.set)
textField.bind("<<Modified>>", textModified)
panedWindow.add(textField, width=500)

noteChanged = False
imgCache = []

root.mainloop()
