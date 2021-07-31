import base64
import re

def powershell_encode(data):
    powershell_command = ""

    n = re.compile(u'(\xef|\xbb|\xbf)')
    for char in (n.sub("", data)):
        powershell_command += char + "\x00"

    powershell_command = base64.b64encode(powershell_command.encode())
    return powershell_command.decode("utf-8")