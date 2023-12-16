import os
import gridfs
import pika  # for rabbitmq
import json
from flask import Flask, request
from flask_pymongo import PyMongo  # store files (with gridfs to store large files)
from auth import validate
from auth_svc import access
from storage import util

server = Flask(__name__)
server.config["MONGO_URI"] = "mongodb://host.minikube.internal:27017/videos"

mongo = PyMongo(server)

fs = gridfs.GridFS(mongo.db)

# the string "rabbitmq" is the name of host
connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
channel = connection.channel()


@server.route("/login", methods=["POST"])
def loginconnection():
    token, err = access.login(request)

    if err:
        return err

    return token


@server.route("/upload", methods=["POST"])
def upload():
    # the user has to be logged in, so we validate the token
    # header is needed and should contain valid information
    # the token gets forward to /validate of the auth service
    access, err = validate.token(request)

    # json string to python object
    access = json.loads(access)
    if not access["admin"]:
        return "Unauthorized", 401

    if len(request.files) != 1:
        return "Exactly one file must be uploaded", 400

    # key (_), value (f)
    for _, f in request.files.items():
        err = util.upload(f, fs, channel, access)
        if err:
            return err

    return "Success: File uploaded!", 200


@server.route("/download", methods=["GET"])
def download():
    # nothing happens for now
    pass


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)
