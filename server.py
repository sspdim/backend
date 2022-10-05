from flask import Flask, request, jsonify
from db import userinfo, servers, tokens, connection
import sqlalchemy as db
from flask_bcrypt import Bcrypt
import firebase_admin
from firebase_admin import messaging


app = Flask(__name__)
bcrypt = Bcrypt(app)

@app.route('/login', methods=['POST'])
def login():
    query = db.select([userinfo]).where(userinfo.columns.username == request.json['username'])
    res = connection.execute(query)
    result = res.fetchall()
    if result and bcrypt.check_password_hash(result[0][1], request.json['password']):
        return jsonify({
            'status': 200,
            'message': 'Login Successful!'
        })
    else:
        return jsonify({
            'status': 400,
            'message': 'User not found!'
        })

@app.route('/register', methods=['POST'])
def register():
    query = db.select([userinfo]).where(userinfo.columns.username == request.json['username'])
    res = connection.execute(query)
    result = res.fetchall()
    if result:
        return jsonify({
            'status': 400,
            'message': 'Username already taken!'
        })
    else:
        hashedpwd = bcrypt.generate_password_hash(request.json['password']).decode('utf-8')
        query = db.insert(userinfo).values(username = request.json['username'], password = hashedpwd)
        try:
            res = connection.execute(query)
            return jsonify({
                'status': 200,
                'message': 'Registration successful!'
            })
        except:
            return jsonify({
                'status': 500,
                'message': 'Registration unsuccessful!'
            })

@app.route('/message', methods=['POST'])
def send_message():
    f = request.json['f']
    to = request.json['to']
    message = request.json['message']
    print(' Sending ' + message + ' from ' + f + ' to ' + to)
    print(request.json)

    # Check if device is online

    # push_message(to, from, message) # GCM? JSON? 

    # from_token = db.select([tokens]).where(tokens.coulmns.username == f)
    to_token = db.select([tokens]).where(tokens.columns.username == to)

    cred_obj = firebase_admin.credentials.Certificate('path/to/json')
    default_app = firebase_admin.initialize_app(cred_obj)

    res = messaging.Message(
            data = {
                f : f,
                message : message
            },
            token = to_token
        )
    try:
        resp = messaging.send(res)
        return jsonify({
            'status': 200
            })
    except:
        return jsonify({
            'status': 406
            })


@app.route('/', methods=['GET'])
def home():
    return "Hello World"

@app.route('/get-servers-list', methods=['GET'])
def get_servers():
    query = db.select([servers]).where(servers.columns.status == 'active')
    res = connection.execute(query)
    result = res.fetchall()
    json_objects = [{"ip_address": row[0], "domain_name": row[1]} for row in result]
    return jsonify(json_objects)

@app.route('/add-token', methods = ['POST'])
def add_token():
    query = db.insert(tokens).values(username = request.json['username'], token = request.json['token'])
    try:
        res = connection.execute(query)
        return jsonify({
            'status': 200,
            'message': 'Token added!'
        })
    except:
        return jsonify({
            'status': 500,
            'message': 'Token not added!'
        })

@app.route('/add-friend', methods = ['POST'])
def add_friend():
    domain_name = request.json['friend_username'].split('@')[1]
    if domain_name == 'capstone1.devmashru.tech':
        return jsonify({
            'status': 200,
            'message': f'Request sent to {domain_name}'
        })
    else:
        return jsonify({
            'status': 400,
            'message': f'Did not find user'
        })

if __name__ == '__main__':
    app.run(debug = True)
