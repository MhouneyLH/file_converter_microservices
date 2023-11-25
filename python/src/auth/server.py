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
    # %s = whatever it is that gets passed in
    # email is used for username
    # result is array of rows
    result = cursor.execute(
        "SELECT email, password FROM user WHERE email=%s",
        (auth.username,)
    )
 
    # result holds the rows of the query
    # no users in database
    if result <= 0:
        return "Invalid credentials: No users could be found / searched for", 401

    # will return a tuple
    user_row = cursor.fetchOne()

    email = user_row[0]
    password = user_row[1]

    if auth.username != email or auth.password != password:
        return "Invalid credentials", 401

    return createJWT(auth.username, os.environ.get("JWT_SECRET"), True)

@server.route("/validate", methods=["POST"])
def validate():
    encoded_jwt = request.headers.get("Authorization")

    if not encoded_jwt:
        return "Missing credentials from token", 401
    
    # Authentification header should look liek this:
    # Authentification: Bearer <token>
    # more information see: https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication#authentication_schemes
    
    authentification_header_content = encoded_jwt.split(" ")
    if len(authentification_header_content) != 2:
        return "Invalid token format in authentification header", 401

    authentification_type = authentification_header_content[0]
    if authentification_type != "Bearer":
        return "Invalid token type", 401
    
    encoded_jwt = authentification_header_content[1]
        
    try:
        decoded_jwt = jwt.decode(encoded_jwt, os.environ.get("JWT_SECRET"), algorithm = "HS256")
    except:
        return "Not authorized", 401
    
    return decoded_jwt, 200

# authz for now = is admin / isn't admin
def createJWT(username, secret, authz):
    return jwt.encode(
        {
            "username": username,
            # exp = expiration
            # timedelta = expires in 1 day
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
            # issued at = when was the token issued (created / generated)
            "iat": datetime.datetime.utcnow(),
            "admin": authz,
        },
        secret,
        algorithm="HS256",
    )

# Variable __name__ wird zu "__main__" wenn das Programm direkt ausgeführt wird
if __name__ == "__main__":
      # any ip address (otherwise only localhost, ...)
      server.run(host="0.0.0.0", port=5000)