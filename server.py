from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    if(request.headers.get('Content-Type') == 'application/json'):
        res = {
            "username" : request.json["username"],
            "password" : request.json["password"],
            "response-code": 200
        }
        return jsonify(res)

@app.route('/register', methods=['POST'])
def register():
    if(request.headers.get('Content-Type') == 'application/json'):
        res = {
            "username" : request.json["username"],
            "password" : request.json["password"],
            "response-code": 404
        }
        return jsonify(res)

if __name__ == '__main__':
    app.run(debug = True)