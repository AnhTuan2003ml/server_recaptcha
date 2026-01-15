from flask import Blueprint, jsonify, request
from app.models.user import Session, User
from app.extensions import db
import time
import random
import string

user_bp = Blueprint('user', __name__)

@user_bp.route('/me', methods=['GET'])
def get_me():
    token = request.headers.get('Authorization')
    session = Session.query.filter_by(token=token).first()

    if session and session.expires_at > time.time():
        user = User.query.get(session.user_id)
        return jsonify({
            "id": user.id,
            "email": user.email,
            "credit": user.credit,
            "key": user.key  # Include API key in response
        })
    return jsonify({"error": "Unauthorized"}), 401

@user_bp.route('/regenerate-key', methods=['POST'])
def regenerate_key():
    """Regenerate API key for user"""
    token = request.headers.get('Authorization')
    session = Session.query.filter_by(token=token).first()

    if not session or session.expires_at <= time.time():
        return jsonify({"error": "Unauthorized"}), 401

    user = User.query.get(session.user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Generate new unique key
    max_attempts = 10
    new_key = None
    for _ in range(max_attempts):
        candidate_key = ''.join(random.choices(string.ascii_letters + string.digits, k=18))
        if not User.query.filter_by(key=candidate_key).first():
            new_key = candidate_key
            break

    if not new_key:
        return jsonify({"error": "Could not generate unique key"}), 500

    # Update user key
    user.key = new_key
    db.session.commit()

    print(f"✅ User {user.email} regenerated API key")

    return jsonify({
        "success": True,
        "message": "API key regenerated successfully",
        "new_key": new_key
    })