from cmd import Cmd
import os
import threading, werkzeug

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

class CrystalServer(Cmd):
    prompt = f"({Color.B}crystal{Color.NC}) {Color.G}server{Color.NC} > "
    port = 9292 # TODO read from config file

    def __init__(self):
        super().__init__()
        self.setup()

    def setup(self):
        os.makedirs("data", exist_ok=True)

        success("Connecting to database")
        self.con = sqlite3.connect('data/crystalc2.db')

        success("Creating database schema")
        with api.app_context():
            db.create_all()
            db.session.commit()

        success("Starting server")
        t = threading.Thread(target = api.run, kwargs={"port":9292})
        t.start() 
        
        printinfo(f"Server running on port {self.port}")

        # TODO: recreate listener in db

    # =======================================================================
    # API

    @api.errorhandler(werkzeug.exceptions.InternalServerError)
    def handle_bad_request(e):
        return 'InternalServerError', 500

    @api.route("/api/listeners", methods=["GET", "POST"])
    def projects():
        """
        GET: Get all listeners
        POST: Add a listener to the db
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
                return flask.jsonify({
                    ListenerModel.serialized
                })
            except:
                raise InternalServerError