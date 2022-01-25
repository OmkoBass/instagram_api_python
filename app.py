import os
import instaloader

from functools import wraps
from flask import Flask, abort, jsonify, request

from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager

from utils.functions import search_profile, get_posts, get_highlight_stories_single, get_all_highlights, get_all_stories, try_load_session
from utils.auth import login_standard, login_2fa

app = Flask(__name__)


app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
# Token lasts just like a session, 90 days
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 60 * 60 * 24 * 90
# Header should only contain the JWT
app.config["JWT_HEADER_TYPE"] = ""

jwt = JWTManager(app)

loader_accessed = instaloader.Instaloader(
    compress_json=False,
    download_pictures=False,
    download_video_thumbnails=False,
    download_videos=False)

# We need one instaloader for
# unautenticated users
# cause there's no function to
# remove a session
# alternative is declaring an instance
# of instaloader inside of every route
loader_anonymous = instaloader.Instaloader(
    compress_json=False,
    download_pictures=False,
    download_video_thumbnails=False,
    download_videos=False)


def debug_only(f):
    @wraps(f)
    def wrapped(**kwargs):
        if not app.debug:
            abort(404)

        return f(**kwargs)

    return wrapped


# Returns a message when user sends
# an expired jwt
@jwt.expired_token_loader
def my_expired_token_callback(jwt_header, jwt_payload):
    return jsonify(message="You must login again."), 401


@app.route("/alive")
def alive():
    return jsonify(message="alive")


# For testing only, generate a jwt
# without logging in
@app.route("/generate/<username>")
@debug_only
def generate(username):
    access_token = create_access_token(identity=username)
    return jsonify(token=access_token)


@app.route("/login", methods=["POST"])
@jwt_required(optional=True)
def login():
    user = get_jwt_identity()

    if user:
        return jsonify(message="You're already logged in.")

    body = request.json

    username = body['username']
    password = body['password']

    code = ""
    if 'code' in body:
        code = body['code']

    if code:
        # If we recieved a code we should call 2fa
        login = login_2fa(loader_accessed, username, code)

        if isinstance(login, list):
            return jsonify(message=login[0]), login[1]
    else:
        # If we recieved no code we should call standard login
        login = login_standard(loader_accessed, username, password)

        if isinstance(login, list):
            return jsonify(message=login[0]), login[1]

    access_token = create_access_token(identity=username)
    return jsonify({'token': access_token, 'message': 'Logged in.'})


@app.route("/story/<username>", methods=["GET"])
@jwt_required()
def get_story(username):
    # To access stories we need to login first
    current_user = get_jwt_identity()

    # Get the profile you want
    profile = search_profile(loader_accessed.context, username)

    if isinstance(profile, list):
        return jsonify(message=profile[0]), profile[1]

    try:
        loader_accessed.load_session_from_file(
            current_user, f"{os.path.dirname(__file__)}/sessions/{current_user}"
        )
    except FileNotFoundError:
        return jsonify(message="You need to log in first."), 401

    generator_stories = loader_accessed.get_stories([profile.userid])

    stories = get_all_stories(generator_stories)

    return jsonify(stories)


@app.route('/highlights/<username>', methods=["GET"])
@jwt_required()
def get_highlights(username):
    # To access highlights we need to login first
    current_user = get_jwt_identity()

    # Get the profile you want
    profile = search_profile(loader_accessed.context, username)

    if isinstance(profile, list):
        return jsonify(message=profile[0]), profile[1]

    try:
        loader_accessed.load_session_from_file(
            current_user, f"{os.path.dirname(__file__)}/sessions/{current_user}"
        )
    except FileNotFoundError:
        return jsonify(message="You need to log in first."), 401

    generator_highlights = loader_accessed.get_highlights(profile.userid)

    highlights = get_all_highlights(generator_highlights)

    return jsonify(highlights)


@app.route('/highlights/<username>/<int:id>/<int:page_number>', methods=["GET"])
@jwt_required()
def get_highlight_stories(username, id, page_number):
    # To access highlight stories we need to login first
    current_user = get_jwt_identity()

    # Get the profile you want
    profile = search_profile(loader_accessed.context, username)

    if isinstance(profile, list):
        return jsonify(message=profile[0]), profile[1]

    try:
        loader_accessed.load_session_from_file(
            current_user, f"{os.path.dirname(__file__)}/sessions/{current_user}"
        )
    except FileNotFoundError:
        return jsonify(message="You need to log in first."), 401

    generator_highlights = loader_accessed.get_highlights(profile.userid)

    stories = get_highlight_stories_single(
        generator_highlights, id, page_number)

    return jsonify(stories)


@app.route("/profile/<username>/<int:page_number>", methods=["GET"])
@jwt_required(optional=True)
def get_profile(username, page_number):
    # We can search some posts if we're not logged in
    # so we don't care, but we can provide added functionality
    # if a user is logged in
    user = get_jwt_identity()

    is_accessed = try_load_session(loader_accessed, user)

    # Get the profile you want
    profile = search_profile(
        loader_accessed.context if is_accessed else loader_anonymous.context, username)

    if isinstance(profile, list):
        return jsonify(message=profile[0]), profile[1]

    generator_posts = profile.get_posts()

    posts = get_posts(generator_posts, page_number)

    return jsonify(posts)


@app.route("/profilePicture/<username>", methods=["GET"])
@jwt_required(optional=True)
def get_profile_picture(username):
    # If we're not logged in a lower quality
    # profile picture will be returned
    user = get_jwt_identity()

    is_accessed = try_load_session(loader_accessed, user)

    # Get the profile you want
    profile = search_profile(
        loader_accessed.context if is_accessed else loader_anonymous.context, username)

    if isinstance(profile, list):
        return jsonify(message=profile[0]), profile[1]

    return jsonify(url=profile.profile_pic_url)
