# jwt = JSON Web Token
import jwt, datetime, os
# Flask = Python microservice framework
from flask import Flask, request
from flask_mysqldb import MySQL

server = Flask(__name__)
mysql = MySQL(server)

# 