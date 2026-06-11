from flask import jsonify


def success(data=None, message="Success", status=200):
    resp = {"success": True, "message": message}
    if data is not None:
        resp["data"] = data
    return jsonify(resp), status


def error(message="An error occurred", status=400, details=None):
    resp = {"success": False, "message": message}
    if details:
        resp["details"] = details
    return jsonify(resp), status


def validate_required(data: dict, fields: list) -> list:
    return [f for f in fields if not data.get(f)]
