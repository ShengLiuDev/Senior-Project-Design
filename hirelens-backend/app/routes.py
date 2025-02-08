from flask import Blueprint, jsonify

routes = Blueprint('routes', __name__)

@routes.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to HireLens API!"})
