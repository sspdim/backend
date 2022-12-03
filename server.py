from operator import or_
import requests
import json
from flask import Flask, request, jsonify
from db import userinfo, servers, tokens, pending_friend_requests, pending_messages, connection, Keys
import sqlalchemy as db
from flask_bcrypt import Bcrypt
import firebase_admin
from firebase_admin import messaging
import random

import subprocess, os

app = Flask(__name__)
bcrypt = Bcrypt(app)

DOMAIN_NAME = os.environ['DOMAIN_NAME']
FRIEND_REQUEST_PENDING = 3
FRIEND_REQUEST_ACCEPTED = 2

cred_obj = firebase_admin.credentials.Certificate(os.environ['FB_CREDENTIALS'])
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

@app.route('/get-servers-list', methods=['GET'])
def get_servers():
    query = db.select([servers]).where(servers.columns.status == 'active')
    res = connection.execute(query)
    result = res.fetchall()
    json_objects = [{"ip_address": row[0], "domain_name": row[1]} for row in result]
    return jsonify(json_objects)

@app.route('/add-token', methods = ['POST'])
def add_token():
    query = db.delete(tokens).where(or_(tokens.columns.username == request.json['username'], tokens.columns.token == request.json['token']))
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
                data = {
                        'action': 'message',
                        'data': request.json['from'],
                        'message': request.json['message'],
                        'message_id': request.json['message_id'],
                        'timestamp': request.json['timestamp']
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
                    message_id = request.json['message_id'],
                    time_stamp = request.json['timestamp'])
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
            data = {
                    'action': 'message',
                    'data': request.json['from'],
                    'message': request.json['message'],
                    'message_id': request.json['message_id'],
                    'timestamp': request.json['timestamp']
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
                message_id = request.json['message_id'],
                time_stamp = request.json['timestamp'])
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
    response = [{'from_username': row[0], 'message_content': row[2], 'message_id': row[3], 'timestamp': row[4]} for row in result]
    query = db.delete(pending_messages).where(
        pending_messages.columns.to_username == to_username)
    result = connection.execute(query)
    return response

@app.route('/insertkeys', methods = ['POST'])
def insertkeys():
    username = request.json['username']
    identitykeypair = request.json['identitykeypair']
    registrationid = request.json['registrationid']
    signedprekey = request.json['signedprekey']
    prekeys = request.json['prekeys']
    
    try:
        query = db.select([Keys.columns.username])
        result = connection.execute(query).fetchall()
        if username in [r[0] for r in result]:
            query = db.delete(Keys).where(
                Keys.columns.username == username
            )
            connection.execute(query)

        query = db.insert(Keys).values(
            username = username,
            identitykeypair = identitykeypair,
            registrationid = registrationid,
            signedprekey = signedprekey,
            prekeys = prekeys
        )
        connection.execute(query)
    
        response =  jsonify({
                'status': 200,
                'message': 'Success'
            })
    except:
        response =  jsonify({
                'status': 400,
                'message': 'Error'
            })
    return response

@app.route('/getkeys', methods = ['POST'])
def getkeys():
    username, domain_name = request.json['username'].split("@")
    
    if domain_name == DOMAIN_NAME:

        try:
            query = db.select([Keys]).where(
                Keys.columns.username == username
            )
            result = connection.execute(query).fetchall()
            number_of_prekeys = len(result[0][3])
            ran = random.randint(0, number_of_prekeys - 1)
            prekey = result[0][3].pop(ran)
            prekeys = result[0][3]
            query = db.update(Keys).where(
                Keys.columns.username == username
            ).values(
                prekeys = prekeys
            )
            connection.execute(query)
            response = jsonify({
                'status': 200,
                'registrationid': result[0][2],
                'identitykeypair': result[0][1],
                'signedprekey': result[0][4],
                'prekey': prekey,
                'number_of_prekeys': number_of_prekeys
            })
        except Exception as e:
            response = jsonify({
                'status': 400,
            })
            print(e)

    else:
        body = {
            'username': request.json['username']
        }
        try:
            r = requests.post('http://' + domain_name + '/getkeys', json = body, headers = {'Content-type': 'application/json'})
            res = json.loads(r.text)
            if res['status'] == 200:
                response = res
            else:
                response = jsonify(res)
        except:
            response = jsonify({
                'status': 500
            })
    return response

@app.route('/insertprekeys', methods = ['POST'])
def insertprekeys():
    username = request.json['username'].split('@')[0]
    prekeys = request.json['prekeys']

    try:
        query = db.select([Keys]).where(
            Keys.columns.username == username
        )
        result = connection.execute(query).fetchall()
        try:
            pre_keys = result[0][3]
            for key in pre_keys:
                prekeys.append(key)
        except Exception as e:
            print(e)
        query = db.update(Keys).where(
            Keys.columns.username == username
        ).values(
            prekeys = prekeys
        )
        connection.execute(query)

        response =  jsonify({
                'status': 200,
                'message': 'Success'
            })
    except:
        response =  jsonify({
                'status': 400,
                'message': 'Error'
            })
    return response

@app.route('/webhook', methods = ['POST'])
def webhook():
    home = os.environ["HOME"]
    subprocess.call(['bash', home + '/backend/scripts/pull.sh'])
    return jsonify({ 'status': 200 })

@app.route('/', methods=['GET'])
def home():
    return "Hello World"

if __name__ == '__main__':
    app.run(debug = True)
