from cmd import Cmd
import os, yaml
import threading, werkzeug
from typing import List

from yaml.loader import SafeLoader

import flask, sys
from werkzeug.exceptions import InternalServerError

from lib.helpers.obfuscation_engine import obfuscate_powershell
from lib.helpers.output import Color, printinfo, success, printlog
from server.models import *
import sqlite3
from flask_migrate import Migrate
from lib.listeners.http import HttpListener
import logging, time

from flask_socketio import SocketIO, emit

from server.models import db

api = flask.Flask(__name__)
api.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///../data/crystalc2.db" # TODO path
api.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(api)
migrate = Migrate(api, db)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

socketio = SocketIO(api)

class ListenerModule:
    def __init__(self, name, file):
        self.name      = name
        self.file_path = os.path.join("lib", "listeners", file) # TODO save all paths somewhere centralized

    @property
    def serialized(self):
        return {
            'name': self.name,
            'file_path': self.file_path
        }

class AgentModule:
    def __init__(self, name, path, filename):
        self.name            = name
        self.file_path       = os.path.join("lib", "agents", path, filename) # TODO save all paths somewhere centralized
        self.generate_script = os.path.join("lib", "agents", path, "generate.py")

    @property
    def serialized(self):
        return {
            'name': self.name,
            'file_path': self.file_path,
            'generate_script': self.generate_script
        }

class ScriptModule:
    def __init__(self, name, filename, command, os_type, description):
        self.name        = name
        self.file_path   = os.path.join("common", "post", filename) # TODO save all paths somewhere centralized
        self.command     = command
        self.os_type     = os_type
        self.description = description

    @property
    def serialized(self):
        return {
            'name': self.name,
            'file_path': self.file_path,
            'command': self.command,
            'type': self.os_type,
            'description': self.description
        }

available_agents: List[AgentModule] = []
available_listeners: List[ListenerModule] = []
available_post_modules: List[ScriptModule] = []

def load_modules():
    """
    Read yaml files which contain info on available agents, modules and listeners
    """
    with open(os.path.join("lib", "agents", "agents.yaml")) as f: # TODO save all paths somewhere centralized
        global available_agents
        data = yaml.load(f, Loader=SafeLoader)
        available_agents = [AgentModule(data[a]["name"], data[a]["path"], data[a]["filename"]) for a in data]

    with open(os.path.join("lib", "listeners", "listeners.yaml")) as f: # TODO save all paths somewhere centralized
        global available_listeners
        data = yaml.load(f, Loader=SafeLoader)
        available_listeners = [ListenerModule(data[a]["name"], data[a]["file"]) for a in data]

    with open(os.path.join("common", "post", "modules.yaml")) as f: # TODO save all paths somewhere centralized
        global available_post_modules
        data = yaml.load(f, Loader=SafeLoader)
        available_post_modules = [ScriptModule(data[s]["name"], data[s]["filename"], data[s]['command'], data[s]['type'], data[s]["description"]) for s in data]

class CrystalServer(Cmd):
    def __init__(self, port, ip="0.0.0.0"):
        super().__init__()
        self.port      = port
        self.listen_ip = ip
        self.prompt    = f"\n({Color.B}crystal{Color.NC}) {Color.G}server{Color.NC} > "
        self.setup()

    def do_exit(self, inp):
        sys.exit(0) # TODO: shutdown

    def help_exit(self):
        print("Exit the console. You can also use the Ctrl-D shortcut")

    do_EOF = do_exit
    help_EOF = help_exit
    emptyline = lambda x: None

    def cmdloop(self):
        try:
            Cmd.cmdloop(self)

        except KeyboardInterrupt as e:
            try:
                choice = input(f"\n{Color.R}[!]{Color.NC} Exit? [y/N]")
                if choice.lower() != "" and choice.lower()[0] == "y":
                    sys.exit(0)
                else:
                    self.cmdloop()
            except KeyboardInterrupt as e:
                print("")
                self.cmdloop()

    def do_agents(self, args):
        'List all agents'
        print("IP\t\tName\t\tHostname\tUser")
        print("----------------------------------------------------")
        with api.app_context():
            for a in AgentModel.query.order_by(AgentModel.id).all():
                print(f"{a.ip_address}\t{a.name}\t{a.hostname}\t{a.username}") # TODO info about session

    def do_listeners(self, args):
        'List all listeners'
        print("IP\t\tPort\tName")
        print("----------------------------------------------------")
        with api.app_context():
            for l in ListenerModel.query.order_by(ListenerModel.id).all():
                print(f"{l.ip_address}\t\t{l.port}\t{l.name}")

    def setup(self):
        os.makedirs("data", exist_ok=True)

        printlog("Connecting to database")
        self.con = sqlite3.connect('data/crystalc2.db')

        printlog("Creating database schema")
        with api.app_context():
            db.create_all()
            db.session.commit()

        printlog("Getting available agent and listener modules")
        load_modules()
        printinfo(f"Loaded {len(available_agents)} agent modules")
        printinfo(f"Loaded {len(available_listeners)} listener modules")
        printinfo(f"Loaded {len(available_post_modules)} post-exploitation modules")

        with api.app_context():
            listeners = ListenerModel.query.order_by(ListenerModel.id).all()
            if listeners:
                success("Recreating listeners registered in database")
                for l in ListenerModel.query.order_by(ListenerModel.id).all():
                    HttpListener(l.name, l.ip_address, l.port).run_as_daemon()

        printlog("Starting server")
        t = threading.Thread(target = socketio.run, args=[api], kwargs={"host":"0.0.0.0","port":9292,"debug":False})
        t.start()

        success(f"Server running on port {self.port}")

# =======================================================================
# API

@socketio.on('connect')
def connected():
    # success("Socket connection received.", newline=True)
    pass

# HTTP
@api.errorhandler(werkzeug.exceptions.InternalServerError)
def handle_bad_request(e):
    return 'InternalServerError', 500

@api.route("/api/broadcast", methods=['POST'])
def broadcast():
    """
    Broadcast a message to all connected clients
    """
    if flask.request.method == "POST":
        msg = flask.request.form.get('msg')
        socketio.emit('message', msg, broadcast=True)
        return flask.jsonify({
            'success': True
        })

@api.route("/api/tasks/<agent_name>", methods=['GET', 'POST'])
def get_task(agent_name):
    """
    GET: get all unexecuted tasks for this agent
    POST: add a task to this agent to the db
    """
    if flask.request.method == "GET":

        task = TaskModel.query.filter(TaskModel.executing_agent == agent_name, TaskModel.executed == False).first()
        if task:
            task.executed = True
            db.session.commit()
            return flask.jsonify({
                'data': task.serialized
            })
        else:
            return flask.jsonify({
                'data': {
                    'task': ''  # no task queued
                }
            })

    if flask.request.method == "POST":
        task = flask.request.form.get('task')

        db.session.add(TaskModel(
            agent_name,
            task
        ))
        db.session.commit()

        return flask.jsonify({
            'success': True
        })

@api.route("/api/agents/modules", methods=["GET"])
def available_agents():
    """
    Get a list of all available agent modules
    """
    return flask.jsonify({
        'data': [a.serialized for a in available_agents]
    })

@api.route("/api/agents", methods=["GET", "POST", "PUT"])
def active_agents():
    """
    GET: Get all active agents
    POST: Add a registered agent to the db
    PUT: rename an agent
    """
    if flask.request.method == "GET":
        agents = AgentModel.query.order_by(AgentModel.id).all()
        return flask.jsonify({
            'data': [a.serialized for a in agents]
        })

    elif flask.request.method == "POST":
        name = flask.request.form.get('name')
        ip_address = flask.request.form.get('ip_address')
        username = flask.request.form.get('username')
        hostname = flask.request.form.get('hostname')

        db.session.add(AgentModel(
            name,
            ip_address,
            username,
            hostname
        ))
        db.session.commit()

        socketio.emit('message', f"Agent {name} checked in: {Color.B}{username}@{hostname}", broadcast=True)

        created = AgentModel.query.filter_by(name=name).first()

        return created.serialized

    elif flask.request.method == "PUT":
        old_name = flask.request.form.get('old_name')
        new_name = flask.request.form.get('new_name')

        agent: AgentModel = AgentModel.query.filter_by(name=old_name).first()

        agent.name = new_name
        db.session.commit()

        socketio.emit('message', f"Agent renamed to {Color.B}{new_name}", broadcast=True)
        return flask.jsonify({
            'success': True
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

@api.route("/api/dl/<script_id>", methods=["GET"])
def get_script(script_id):
    """
    download script, where id is the index of the available post modules array
    """
    script: ScriptModule = available_post_modules[int(script_id)]
    with open(script.file_path, "r") as f:
        script_string = f.read()

    return (script_string, 200)

@api.route("/api/post/modules", methods=["GET"])
def get_available_post_modules():
    """
    Get a list of all available post exploitation modules
    """
    return flask.jsonify({
        'data': [a.serialized for a in available_post_modules]
    })