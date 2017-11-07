import flask
from flask import render_template
from sqlalchemy import func, tuple_
from sqlalchemy.exc import SQLAlchemyError

from app import app
from functools import wraps
from flask import request, Response

from app.constants import *
from config import AUTH_LOGIN, AUTH_PASS, CASTLE
from app.types import *


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == AUTH_LOGIN and password == AUTH_PASS


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/robots.txt')
def robots():
    return render_template('robots.txt')


def get_squads():
    try:
        squads = Session().query(Squad).all()
        return squads
    except SQLAlchemyError:
        Session.rollback()
        return flask.Response(status=400)


@app.route('/users')
def get_usernames():
    try:
        session = Session()
        sub_query = session.query(Character.user_id, func.max(Character.date)).group_by(Character.user_id).subquery()
        characters = session.query(Character, User).filter(tuple_(Character.user_id, Character.date)
                                                           .in_(sub_query))\
            .join(User, User.id == Character.user_id)

        if CASTLE:
            characters = characters.filter(Character.castle == CASTLE)
        characters = characters.all()
        return render_template('users.html', characters=characters)
    except SQLAlchemyError:
        Session.rollback()
        return flask.Response(status=400)


@app.route('/player/<int:id>', methods=['GET'])
def get_user(id):
    session = Session()
    try:
        user = session.query(User).filter_by(id=id).first()
        return render_template('player.html', output=user)
    except SQLAlchemyError:
        Session.rollback()
        return flask.Response(status=400)


@app.route('/member-equip/<int:squad_id>', methods=['GET'])
@requires_auth
def get_member_equip(squad_id):
    session = Session()
    try:
        sub_query_1 = session.query(Character.user_id, func.max(Character.date)).group_by(Character.user_id).subquery()
        sub_query_2 = session.query(Equip.user_id, func.max(Equip.date)).group_by(Equip.user_id).subquery()
        members = session.query(Character, User, Equip.equip) \
            .filter(tuple_(Character.user_id, Character.date).in_(sub_query_1)) \
            .join(User, User.id == Character.user_id) \
            .outerjoin(Equip, User.id == Equip.user_id) \
            .join(SquadMember, SquadMember.user_id == Character.user_id) \
            .filter((tuple_(Equip.user_id, Equip.date).in_(sub_query_2)) | (Equip.user_id.is_(None))) \
            .filter(SquadMember.squad_id == squad_id) \
            .order_by(Character.level.desc())

        if CASTLE:
            members = members.filter(Character.castle == CASTLE)
        members = members.all()

        members_new = []
        total_attack = 0
        total_defence = 0
        total_lvl = 0
        for character, user, equip in members:
            member_equip = []
            total_attack += character.attack
            total_defence += character.defence
            total_lvl += character.level
            if equip:
                for part in EQUIP_PARTS:
                    flag = False
                    for item, grade in STUFF[part]:
                        if item in equip:
                            member_equip.append([item, COLORS[grade]])
                            flag = True
                            break
                    if not flag:
                        member_equip.append([' ', None])
            else:
                member_equip = [[' ', None], [' ', None], [' ', None], [' ', None], [' ', None], [' ', None]]
            members_new.append([character, user, member_equip])
        avg_lvl = total_lvl/len(members)
        squad = session.query(Squad).filter(Squad.chat_id == squad_id)
        squad = squad.first()
        return render_template('squad_member_equip.html', members=members_new, squad=squad, avg_lvl=round(avg_lvl,1),
                               total_attack=total_attack, total_defence=total_defence)
    except SQLAlchemyError:
        Session.rollback()
        return flask.Response(status=400)


@app.route('/squads')
def squads_function():
    return render_template('squads.html', output=get_squads())


@app.route('/top')
def top():
    return render_template('top.html', output=MSG_UNDER_CONSTRUCTION)


@app.route('/build')
def build():
    return render_template('build.html', output=MSG_UNDER_CONSTRUCTION)


@app.route('/reports')
def reports():
    return render_template('reports.html', output=MSG_UNDER_CONSTRUCTION)


@app.route('/squad_craft')
def squad_craft():
    return render_template('squad_craft.html', output=MSG_UNDER_CONSTRUCTION)