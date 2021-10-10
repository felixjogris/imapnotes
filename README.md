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
host = <i>hostname of your IMAPS server</i>
# port = <i>optional port number if not 993</i>
user = <i>username to log into your mailbox</i>
pass = <i>your password</i>
```


# Homepage

https://ogris.de/imapnotes/
