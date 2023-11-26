import os, gridfs, pika, json # pika for rabbitmq
from flask import Flask, request
from flask_pymongo import PyMongo # store files (with gridfs to store large files)
from auth import validate
from auth_svc import access
from storage import util

server = Flask(__name__)
server.config['MONGO_URI'] = "mongodb://host.minikube.internal:27017/videos"

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