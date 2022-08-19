from flask import Flask, request, jsonify
from db import userinfo, connection
import sqlalchemy as db

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    query = db.select([userinfo]).where(userinfo.columns.username == request.json['username'])
    res = connection.execute(query)
    result = res.fetchall()
    if result and result[0][1] == request.json['password']:
        return jsonify({
            'status': 200,
            'message': 'Found user'
        })
    else:
        return jsonify({
            'status': 400,
            'message': 'Did not find user'
        })

@app.route('/register', methods=['POST'])
def register():
    query = db.select([userinfo]).where(userinfo.columns.username == request.json['username'])
    res = connection.execute(query)
    result = res.fetchall()
    if result:
        return jsonify({
            'status': 400,
            'message': 'Username already taken'
        })
    else:
        query = db.insert(userinfo).values(username = request.json['username'], password = request.json['password'])
        try:
            res = connection.execute(query)
            return jsonify({
                'status': 200,
                'message': 'Registration successful'
            })
        except:
            return jsonify({
                'status': 400,
                'message': 'Registration unsuccessful'
            })

if __name__ == '__main__':
    app.run(debug = True)