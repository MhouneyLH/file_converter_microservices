# jwt = JSON Web Token
import jwt, datetime, os
# Flask = Python microservice framework
from flask import Flask, request
# interact with the MySQL database
from flask_mysqldb import MySQL

server = Flask(__name__)
mysql = MySQL(server)

# config
# use env variables -> we could set it via `export MYSQL_HOST=...`
server.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
server.config["MYSQL_USER"] = os.environ.get("MYSQL_USER")
server.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD")
server.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")
server.config["MYSQL_PORT"] = os.environ.get("MYSQL_PORT")

@server.route("/login", methods=["POST"])
def login():
    auth = request.authorization
    if not auth:
        return "Missing credentials", 401
    
    ### check db for username and password
    cursor = mysql.connection.cursor()
    # query something
    # %s = whatever it is
    # email is used for username
    result = cursor.execute(
        "SELECT email, password FROM user WHERE email=%s",
        (auth.username,)
    )
 
    # result holds the rows of the query
    # no users in database
    if result <= 0:
        return "Invalid credentials: No users found", 401

    # will return a tuple
    user_row = cursor.fetchOne()

    email = user_row[0]
    password = user_row[1]

    if auth.username != email or auth.password != password:
        return "Invalid credentials", 401

    return createJWT(auth.username, os.environ.get("JWT_SECRET"), True)

def createJWT():