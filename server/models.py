from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class ListenerModel(db.Model):
    __tablename__ = "listeners"
 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    ip_address = db.Column(db.String)
    port = db.Column(db.Integer)

    def __init__(self, name: str, ip_address: str, port: int):
        self.name = name
        self.ip_address = ip_address
        self.port = port   

    @property
    def serialized(self):
        return {
            "name": self.name,
            "ip_address": self.ip_address,
            "port": self.port
        }

class AgentModel(db.Model):
    __tablename__ = "agents"
 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    ip_address = db.Column(db.String)
    username = db.Column(db.String)
    hostname = db.Column(db.String)
    # last_connected = db.Column(db.Date)

    def __init__(self, name: str, ip_address: str, username, hostname: str): #, last_connected):
        self.name = name
        self.ip_address = ip_address
        self.username = username
        self.hostname = hostname
        # self.last_connected = last_connected

    @property
    def serialized(self):
        return {
            "name": self.name,
            "ip_address": self.ip_address,
            "username": self.username,
            "hostname": self.hostname
        }

class TaskModel(db.Model):
    """
    Tasks for agents to execute
    """
    __tablename__ = "tasks"
 
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String)
    executing_agent = db.Column(db.String)
    executed = db.Column(db.Boolean)

    def __init__(self, executing_agent: str, task: str): 
        self.executing_agent = executing_agent
        self.task = task
        self.executed = False

    @property
    def serialized(self):
        return {
            "task": self.task,
            "executing_agent": self.executing_agent,
            "executed": self.executed
        }
