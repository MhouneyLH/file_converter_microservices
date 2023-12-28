import os
import gridfs
import pika  # for rabbitmq
import json
from flask import Flask, request
from flask_pymongo import PyMongo  # store files (with gridfs to store large files)
from auth import validate
from auth_svc import access
from storage import util
from bson.objectid import ObjectId

server = Flask(__name__)

# multiple PyMongo instances for different databases are possible
mongo_video = PyMongo(
    server,
    uri="mongodb://mongodb-service:27017/videos",
)
mongo_mp3 = PyMongo(
    server,
    uri="mongodb://mongodb-service:27017/mp3s",
)

fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

# the string "rabbitmq" is the name of host
connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
channel = connection.channel()


@server.route("/login", methods=["POST"])
def login():
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
    if err:
        return err

    # json string to python object
    access = json.loads(access)
    if not access["admin"]:
        return "Unauthorized", 401

    if len(request.files) != 1:
        return "Exactly one file must be uploaded", 400

    # key (_), value (f)
    for _, file in request.files.items():
        err = util.upload(file, fs_videos, channel, access)
        if err:
            return err

    return "Success: File uploaded!", 200


@server.route("/download", methods=["GET"])
def download():
    access, err = validate.token(request)
    if err:
        return err

    # json string to python object
    access = json.loads(access)
    if not access["admin"]:
        return "Unauthorized", 401

    # shows if this parameter is set in the request
    file_id_string = request.args.get("fid")
    if file_id_string == None:
        return "No file id specified", 400

    try:
        out = fs_mp3s.get(ObjectId(file_id_string))
        return send_file(out, download_name=f"{file_id_string}.mp3")
    except Exception as err:
        return "Internal server error: " + str(err), 500


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)
