from cmd import Cmd
from logging import WARNING
import os, yaml
import threading, werkzeug
from yaml.loader import SafeLoader

import flask
from werkzeug.exceptions import InternalServerError
from lib.helpers.output import Color, printinfo, success
from server.models import *
import sqlite3
from flask_migrate import Migrate
from lib.listeners.http import HttpListener

#cli = sys.modules['flask.cli']
#cli.show_server_banner = lambda *x: None
api = flask.Flask(__name__)
api.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///../data/crystalc2.db" # TODO path
api.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(api)
migrate = Migrate(api, db)

class ListenerModule:
    def __init__(self, name, file):
        self.name = name
        self.file_path = os.path.join("lib", "listeners", file) # TODO save all paths somewhere centralized

    @property
    def serialized(self):
        return {
            'name': self.name,
            'file_path': self.file_path
        }

class AgentModule:
    def __init__(self, name, path, filename):
        self.name = name
        self.file_path = os.path.join("lib", "agents", path, filename) # TODO save all paths somewhere centralized
        self.generate_script = os.path.join("lib", "agents", path, "generate.py")

    @property
    def serialized(self):
        return {
            'name': self.name,
            'file_path': self.file_path,
            'generate_script': self.generate_script
        }

available_agents: AgentModule = []
available_listeners: ListenerModule = []

def load_modules():
    """
    Read yaml files which contain info on available agents and listeners
    """
    with open(os.path.join("lib", "agents", "agents.yaml")) as f: # TODO save all paths somewhere centralized
        global available_agents
        data = yaml.load(f, Loader=SafeLoader)
        available_agents = [AgentModule(data[a]["name"], data[a]["path"], data[a]["filename"]) for a in data]

    with open(os.path.join("lib", "listeners", "listeners.yaml")) as f: # TODO save all paths somewhere centralized
        global available_listeners
        data = yaml.load(f, Loader=SafeLoader)
        available_listeners = [ListenerModule(data[a]["name"], data[a]["file"]) for a in data]

class CrystalServer(Cmd):
    prompt = f"({Color.B}crystal{Color.NC}) {Color.G}server{Color.NC} > "
    port = 9292 # TODO read from config file

    def __init__(self):
        super().__init__()
        self.setup()

    def do_listeners(self, args):
        'List all listeners'
        print("IP\t\tPort\tName")
        print("----------------------------------")
        with api.app_context():
            for l in ListenerModel.query.order_by(ListenerModel.id).all():
                print(f"{l.ip_address}\t{l.port}\t{l.name}")

    def setup(self):
        os.makedirs("data", exist_ok=True)

        success("Connecting to database")
        self.con = sqlite3.connect('data/crystalc2.db')

        success("Creating database schema")
        with api.app_context():
            db.create_all()
            db.session.commit()

        success("Getting available agent and listener modules")
        load_modules()
        printinfo(f"Loaded {len(available_agents)} agent modules and {len(available_listeners)} listener modules")

        success("Recreating listeners registered in database")
        with api.app_context():
            for l in ListenerModel.query.order_by(ListenerModel.id).all():
                HttpListener(l.name, l.ip_address, l.port).run_as_daemon()

        success("Starting server")
        t = threading.Thread(target = api.run, kwargs={"port":9292})
        t.start() 
        
        printinfo(f"Server running on port {self.port}")

        
# =======================================================================
# API

@api.errorhandler(werkzeug.exceptions.InternalServerError)
def handle_bad_request(e):
    return 'InternalServerError', 500

@api.route("/api/agents/modules", methods=["GET"])
def available_agents():
    """
    Get a list of all available agent modules
    """
    return flask.jsonify({
        'data': [a.serialized for a in available_agents]
    })


@api.route("/api/listeners", methods=["GET", "POST"])
def active_listeners():
    """
    GET: Get all active listeners
    POST: Add a listener to the db and start it
    """
    if flask.request.method == "GET":

        listeners = ListenerModel.query.order_by(ListenerModel.id).all()
        return flask.jsonify({
            'data': [l.serialized for l in listeners]
        })


    if flask.request.method == "POST":

        name = flask.request.form.get('name')
        ip_address = flask.request.form.get('ip_address')
        port = flask.request.form.get('port')

        # check if listener with same ip and port exists
        if ListenerModel.query.filter_by(ip_address=ip_address, port=port).first():
            raise InternalServerError
        else:
            listener = HttpListener(name, ip_address, port)

            try:
                listener.run_as_daemon()
            except:
                raise InternalServerError

            try:
                db.session.add(ListenerModel(
                    name,
                    ip_address,
                    port
                ))
                db.session.commit()

                created = ListenerModel.query.filter_by(ip_address=ip_address, port=port).first()

                return created.serialized
            except OSError:
                raise InternalServerError