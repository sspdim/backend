from operator import and_
import requests
import json
from flask import Flask, request, jsonify
from db import userinfo, servers, tokens, pending_friend_requests, pending_messages, connection
import sqlalchemy as db
from flask_bcrypt import Bcrypt
import firebase_admin
from firebase_admin import messaging

app = Flask(__name__)
bcrypt = Bcrypt(app)

DOMAIN_NAME = 'capstoneX.devmashru.tech'
FRIEND_REQUEST_PENDING = 3
FRIEND_REQUEST_ACCEPTED = 2

cred_obj = firebase_admin.credentials.Certificate('sspdim-firebase-adminsdk-5jn4m-fb95747ef9.json')
default_app = firebase_admin.initialize_app(cred_obj)

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
    query = db.delete(tokens).where(and_(tokens.columns.username == request.json['username'], tokens.columns.token == request.json['token']))
    res = connection.execute(query)
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
    friend_username, domain_name = request.json['friend_username'].split('@')
    response = {}
    domain_name.strip()

    if domain_name == DOMAIN_NAME:
        query = db.select([userinfo]).where(userinfo.columns.username == friend_username)
        res = connection.execute(query)
        result = res.fetchall()
        if result:
            query = db.select([tokens]).where(tokens.columns.username == friend_username)
            to_token = connection.execute(query).fetchall()
            res = messaging.Message(
                notification = messaging.Notification(
                    title = 'Friend Request',
                    body = 'You have a new friend request!',
                ),
                data = {
                        'action': 'add-friend',
                        'data': request.json['username']
                    },
                    token = to_token[0][0]
                )
            try:
                resp = messaging.send(res)
                response = jsonify({
                    'status': 200,
                    'message': 'Request sent'
                })
            except:
                response = jsonify({
                    'status': 500,
                    'message': 'Error sending request'
                })
            try:
                query = db.insert(pending_friend_requests).values(
                    from_username = request.json['username'],
                    to_username = request.json['friend_username'],
                    request_status = FRIEND_REQUEST_PENDING)
                connection.execute(query)
            except:
                pass
        else:
            response = jsonify({
                'status': 400,
                'message': 'Did not find user'
            })
    else:
        body = {
            'username': request.json['username'],
            'friend_username': request.json['friend_username']
        }
        try:
            r = requests.post('http://' + domain_name + '/receive-add-friend', json = body, headers = {'Content-type': 'application/json'})
            res = json.loads(r.text)
            if res['status'] == 200:
                response = jsonify({
                    'status': 200,
                    'message': f'Request sent to {domain_name}'
                })
            else:
                return jsonify(res)
        except:
            response = jsonify({
                'status': 500,
                'message': 'Error sending request'
            })
    return response

@app.route('/receive-add-friend', methods = ['POST'])
def receive_add_friend():
    friend_username = request.json['friend_username'].split('@')[0]
    query = db.select([userinfo]).where(userinfo.columns.username == friend_username)
    res = connection.execute(query)
    result = res.fetchall()
    response = {}
    if result:
        query = db.select([tokens]).where(tokens.columns.username == friend_username)
        to_token = connection.execute(query).fetchall()
        res = messaging.Message(
            notification = messaging.Notification(
                title = 'Friend Request',
                body = 'You have a new friend request!',
            ),
            data = {
                    'action': 'add-friend',
                    'data': request.json['username']
                },
                token = to_token[0][0]
            )
        try:
            resp = messaging.send(res)
            response = jsonify({
                'status': 200,
                'message': 'Request sent'
            })
        except:
            response = jsonify({
                'status': 500,
                'message': 'Error sending request'
             })
        try:
            query = db.insert(pending_friend_requests).values(
                from_username = request.json['username'],
                to_username = request.json['friend_username'],
                request_status = FRIEND_REQUEST_PENDING)
            connection.execute(query)
        except:
            pass
    else:
        response = jsonify({
            'status': 400,
            'message': 'Did not find user'
        })
    return response

@app.route('/send-message', methods = ['POST'])
def send_message():
    to, domain_name = request.json['to'].split('@')
    response = {}
    domain_name.strip()

    if domain_name == DOMAIN_NAME:
        query = db.select([userinfo]).where(userinfo.columns.username == to)
        res = connection.execute(query)
        result = res.fetchall()
        if result:
            query = db.select([tokens]).where(tokens.columns.username == to)
            to_token = connection.execute(query).fetchall()
            res = messaging.Message(
                notification = messaging.Notification(
                    title = 'Message',
                    body = 'You have a new message!',
                ),
                data = {
                        'action': 'message',
                        'data': request.json['from'],
                        'message': request.json['message'],
                        'message_id': request.json['message_id']
                    },
                    token = to_token[0][0]
                )
            try:
                resp = messaging.send(res)
                response = jsonify({
                    'status': 200,
                    'message': 'Message sent'
                })
            except:
                response = jsonify({
                    'status': 500,
                    'message': 'Error sending message'
                })
            try:
                query = db.insert(pending_messages).values(
                    from_username = request.json['from'],
                    to_username = request.json['to'],
                    message_content = request.json['message'],
                    message_id = request.json['message_id'])
                connection.execute(query)
            except:
                pass
        else:
            response = jsonify({
                'status': 400,
                'message': 'Did not find user'
            })
    else:
        body = {
            'from': request.json['from'],
            'to': request.json['to'],
            'message': request.json['message'],
            'message_id': request.json['message_id']
        }
        try:
            r = requests.post('http://' + domain_name + '/receive-message', json = body, headers = {'Content-type': 'application/json'})
            res = json.loads(r.text)
            if res['status'] == 200:
                response = jsonify({
                    'status': 200,
                    'message': f'Message sent to {domain_name}'
                })
            else:
                response = jsonify(res)
        except:
            response = jsonify({
                'status': 500,
                'message': 'Error sending message'
            })
    return response

@app.route('/receive-message', methods = ['POST'])
def receive_message():
    to = request.json['to'].split('@')[0]
    query = db.select([userinfo]).where(userinfo.columns.username == to)
    res = connection.execute(query)
    result = res.fetchall()
    response = {}
    if result:
        query = db.select([tokens]).where(tokens.columns.username == to)
        to_token = connection.execute(query).fetchall()
        res = messaging.Message(
            notification = messaging.Notification(
                title = 'New message',
                body = 'You have a new message!',
            ),
            data = {
                    'action': 'message',
                    'data': request.json['from'],
                    'message': request.json['message'],
                    'message_id': request.json['message_id']
                },
                token = to_token[0][0]
            )
        try:
            resp = messaging.send(res)
            response = jsonify({
                'status': 200,
                'message': 'Message sent'
            })
        except:
            response = jsonify({
                'status': 500,
                'message': 'Error sending message'
             })
        try:
            query = db.insert(pending_messages).values(
                from_username = request.json['from'],
                to_username = request.json['to'],
                message_content = request.json['message'],
                message_id = request.json['message_id'])
            connection.execute(query)
        except:
            pass
    else:
        response = jsonify({
            'status': 400,
            'message': 'Did not find user'
        })
    return response

@app.route('/accept-friend', methods = ['POST'])
def accept_friend():
    friend_username, domain_name = request.json['friend_username'].split('@')
    domain_name.strip()

    if domain_name == DOMAIN_NAME:
        query = db.select([userinfo]).where(userinfo.columns.username == friend_username)
        res = connection.execute(query)
        result = res.fetchall()
        response = {}
        if result:
            query = db.select([tokens]).where(tokens.columns.username == friend_username)
            to_token = connection.execute(query).fetchall()
            res = messaging.Message(
                notification = messaging.Notification(
                    title = 'Friend Request Accepted',
                    body = 'Your friend request was accepted!',
                ),
                data = {
                        'action': 'accept-friend',
                        'data': request.json['username']
                    },
                    token = to_token[0][0]
                )
            try:
                resp = messaging.send(res)
                response = jsonify({
                    'status': 200,
                    'message': 'Request sent'
                })
            except:
                response = jsonify({
                    'status': 500,
                    'message': 'Error sending request'
                })
            try:
                query = db.insert(pending_friend_requests).values(
                    from_username = request.json['username'],
                    to_username = request.json['friend_username'],
                    request_status = FRIEND_REQUEST_ACCEPTED)
                connection.execute(query)
            except:
                pass
        else:
            response = jsonify({
                'status': 400,
                'message': 'Did not find user'
            })
    else:
        body = {
            'username': request.json['username'],
            'friend_username': request.json['friend_username']
        }
        try:
            r = requests.post('http://' + domain_name + '/receive-accept-friend', json = body, headers = {'Content-type': 'application/json'})
            res = json.loads(r.text)
            if res['status'] == 200:
                response = jsonify({
                    'status': 200,
                    'message': f'Request sent to {domain_name}'
                })
            else:
                response = jsonify(res)
        except:
            response = jsonify({
                'status': 500,
                'message': 'Error sending request'
            })
    return response

@app.route('/receive-accept-friend', methods = ['POST'])
def receive_accept_friend():
    friend_username = request.json['friend_username'].split('@')[0]
    query = db.select([userinfo]).where(userinfo.columns.username == friend_username)
    res = connection.execute(query)
    result = res.fetchall()
    response = {}
    if result:
        query = db.select([tokens]).where(tokens.columns.username == friend_username)
        to_token = connection.execute(query).fetchall()
        res = messaging.Message(
            notification = messaging.Notification(
                title = 'Friend Request Accepted',
                body = 'Your friend request was accepted!',
            ),
            data = {
                    'action': 'accept-friend',
                    'data': request.json['username']
                },
                token = to_token[0][0]
            )
        try:
            resp = messaging.send(res)
            response =  jsonify({
                'status': 200,
                'message': 'Request sent'
            })
        except:
            response =  jsonify({
                'status': 500,
                'message': 'Error sending request'
             })
        try:
            query = db.insert(pending_friend_requests).values(
                from_username = request.json['username'],
                to_username = request.json['friend_username'],
                request_status = FRIEND_REQUEST_ACCEPTED)
            connection.execute(query)
        except:
            pass
    else:
        response =  jsonify({
            'status': 400,
            'message': 'Did not find user'
        })
    return response

@app.route('/pending-friend-requests', methods = ['POST'])
def get_pending_friend_requests():
    to_username = request.json['username']
    query = db.select([pending_friend_requests]).where(
        pending_friend_requests.columns.to_username == to_username)
    result = connection.execute(query).fetchall()
    response = [{'from_username': row[0], 'status': row[2]} for row in result]
    query = db.delete(pending_friend_requests).where(
        pending_friend_requests.columns.to_username == to_username)
    result = connection.execute(query)
    return response

@app.route('/pending-messages', methods = ['POST'])
def get_pending_messages():
    to_username = request.json['username']
    query = db.select([pending_messages]).where(
        pending_messages.columns.to_username == to_username)
    result = connection.execute(query).fetchall()
    response = [{'from_username': row[0], 'message_content': row[2], 'message_id': row[3]} for row in result]
    query = db.delete(pending_messages).where(
        pending_messages.columns.to_username == to_username)
    result = connection.execute(query)
    return response

if __name__ == '__main__':
    app.run(debug = True)
