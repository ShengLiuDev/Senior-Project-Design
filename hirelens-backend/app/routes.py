from flask import Flask, Blueprint, jsonify, request
from app.sheets_api import get_static_sheet_data

routes = Blueprint('routes', __name__)

@routes.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to HireLens API!"})

@routes.route('/api/static-sheet-data', methods=['GET'])
def static_sheet():
    """API route to return data from the specific hardcoded sheet."""
    data, status_code = get_static_sheet_data()
    return jsonify(data), status_code