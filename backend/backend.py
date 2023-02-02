import uuid

import redis
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_jwt_extended import create_access_token
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin

from flask import request
import json
import pika
import datetime

import configparser
cfg = configparser.ConfigParser()

cfg.read("./config_file.ini")


DB_CONNECTION_STRING = cfg.get("hosts", "db_connection", fallback="172.17.0.6")
RABBITMQ_HOST = cfg.get("hosts", "rabbitmq", fallback="172.17.0.5")
REDIS_HOST = cfg.get("hosts", "redis", fallback="172.17.0.4")
JWT_SECRET = cfg.get("jwt", "secret")

app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config["JWT_SECRET_KEY"] = JWT_SECRET
app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONNECTION_STRING
jwt = JWTManager(app)

db = SQLAlchemy(app)
redis_client = redis.Redis(host=REDIS_HOST)

class User(db.Model):
    __tablename__ = "user_table"

    id = db.Column('user_id', db.Integer, primary_key = True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(256))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class TrustSearch(db.Model):
    __tablename__ = "trust_search"

    id = db.Column('search_id', db.String(512), primary_key = True)
    user_id = db.Column("user_id", db.Integer, db.ForeignKey("user_table.user_id"))
    processed = db.Column(db.Boolean)
    subreddits = db.Column(db.String(512))
    target = db.Column(db.String(256))
    trust_percentage = db.Column(db.Float)

    def as_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "processed": self.processed,
            "subreddits": ",".join(self.subreddits.split(";")),
            "target": self.target,
            "trust_percentage": self.trust_percentage
        }

@app.route("/login", methods=["POST"])
@cross_origin()
def create_token():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    user = User.query.filter_by(username=username, password=password).first()
    if user is None:
        return json.dumps({"msg": "Bad username or password"}), 401

    # create a new token with the user id inside
    access_token = create_access_token(identity=user.id, expires_delta=datetime.timedelta(minutes=10))
    return json.dumps({"token": access_token, "user_id": user.id})

@app.route("/register", methods=["POST"])
@cross_origin()
def create_user():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    if not username or not password:
        return json.dumps({"msg": "Invalid input given."}), 400

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()

    return json.dumps({"msg": "User successfully added.."}), 200

@app.route("/search", methods=["GET"])
@jwt_required()
@cross_origin()
def list_all_searches():
    # Access the identity of the current user with get_jwt_identity
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(id=current_user_id)

    all_searches = TrustSearch.query.filter(TrustSearch.user_id == current_user_id).all()

    all_searches_dict = [x.as_dict() for x in all_searches]
    return json.dumps(all_searches_dict), 200

@app.route("/search/processed", methods=["GET"])
@jwt_required()
@cross_origin()
def list_searches_processed():
    # Access the identity of the current user with get_jwt_identity
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(id=current_user_id)

    all_searches = TrustSearch.query.filter(TrustSearch.processed == True).filter(TrustSearch.user_id == current_user_id).all()

    all_searches_dict = [x.as_dict() for x in all_searches]
    return json.dumps(all_searches_dict), 200


@app.route("/search/pending", methods=["GET"])
@jwt_required()
def list_searches_pending():
    # Access the identity of the current user with get_jwt_identity
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(id=current_user_id)

    all_searches = TrustSearch.query.filter(TrustSearch.processed == False).all()

    return json.dumps(all_searches), 200


@app.route("/search/<given_id>", methods=["GET"])
@jwt_required()
def list_searches(given_id):
    # Access the identity of the current user with get_jwt_identity
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(id=current_user_id)

    search = TrustSearch.query.filter_by(id=given_id).first()

    if not search:
        return json.dumps({"msg": "No search with this ID exists.."}), 404

    return json.dumps(search), 200


@app.route("/search", methods=["POST"])
@jwt_required()
@cross_origin()
def make_search():
    # Access the identity of the current user with get_jwt_identity
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(id=current_user_id)

    subreddits = request.json.get("subreddits", None)
    target_term = request.json.get("target", None)

    print(request.json)
    if not subreddits or not target_term:
        return json.dumps({"msg": "Invalid input given."}), 400

    request_id = uuid.uuid4()

    search_info = {
        "request_identifier": str(request_id),
        "subreddits": subreddits,
        "target": target_term
    }

    new_search = TrustSearch(id=str(request_id), user_id=current_user_id, processed=False, subreddits=subreddits, target=target_term, trust_percentage=None)
    db.session.add(new_search)
    db.session.commit()

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue='flow_request')
    channel.basic_publish(exchange='',
                          routing_key='flow_request',
                          body=json.dumps(search_info),
                          properties=pika.BasicProperties(delivery_mode = 2))
    connection.close()

    return json.dumps({"msg": "Search request was successfully sent,"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082)
