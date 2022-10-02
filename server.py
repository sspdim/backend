from flask import Flask, request, jsonify
from db import userinfo, servers, tokens, connection
import sqlalchemy as db
from flask_bcrypt import Bcrypt

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

if __name__ == '__main__':
    app.run(debug = True)