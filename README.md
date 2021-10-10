# imapnotes

imapnotes is a Python / Tkinter application to read and write notes stored on an IMAPS server. It expects that your notes reside in the folder _Notes_ in your mailbox

It is still being developed.

![ScreenShot](https://ogris.de/imapnotes/imapnotes.png)


# Requirements

* Python 3.9
* tkinter (on Gentoo Linux, emerge python with USE="tk")
* Pillow: https://python-pillow.org/


# Configuration

Create a file called _.imapnotes.ini_ in your home directory:

```
[connection]
host = _hostname of your IMAPS server_
# port = _optional port number if not 993_
user = _username to log into your mailbox_
pass = _your password_
```


# Homepage

https://ogris.de/imapnotes/
