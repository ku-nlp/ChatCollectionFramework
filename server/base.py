from datetime import date, datetime
from flask import Flask, render_template, request, send_from_directory, session
from flask_session import Session
from jinja2.exceptions import TemplateNotFound
import pytz
import threading
import uuid


tz = pytz.timezone('Asia/Tokyo')

def utc_to_local(utc_timestamp):
    return datetime.fromisoformat("{}+00:00".format(utc_timestamp)).astimezone(tz).isoformat() if utc_timestamp else ""

def convert_chatroom_to_dict(chatroom):
    return {
        "id": chatroom.id,
        "experimentId": chatroom.experiment_id,
        "users": chatroom.users,
        "created": chatroom.created,
        "modified": chatroom.modified,
        "initiator": chatroom.initiator,
        "closed": chatroom.closed,
        "events": len(chatroom.events),
        "poll_requests": chatroom.poll_requests
    }


class BaseUser(object):

    def __init__(self, id_, attribs=dict()):
        self.id = id_
        self.attribs = attribs

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.id == other.id

    def has_matching_attribs(self, other):
        # This should be overridden by the superclass.
        # True should be returned when the other user has matching attributes with the self user
        # so that they can be matched together for a chat.  Otherwise, False is returned.
        # In this default implementation, any user is considered ok to chat with.
        return True


class BaseChatroom(object):

    def __init__(self, id_=None, experiment_id=None, initiator=None):
        self.id = id_
        self.created = datetime.utcnow().isoformat()
        self.modified = self.created
        self.events = []
        self.users = []
        self.experiment_id = experiment_id
        self.initiator = initiator
        self.partner = None
        self.closed = False
        self.poll_requests = {}
        if initiator is not None:
            self.add_user(initiator)

    def add_event(self, event):
        timestamp = datetime.utcnow()
        self.events.append(event)
        self.modified = timestamp.isoformat()
        # print("add_event modified={0}".format(self.modified))
        if 'from' in event:
            self.poll_requests[event['from']].append(self.modified)

    def add_user(self, user):
        timestamp = datetime.utcnow()
        self.users.append(user)
        if len(self.users) == 2:
            self.closed = True
            self.partner = user
        self.modified = timestamp.isoformat()
        self.poll_requests[user] = [self.modified]

    def remove_user(self, user):
        if user in self.users:
            self.users.remove(user)
            self.modified = datetime.utcnow().isoformat()
            if user in self.poll_requests:
                del self.poll_requests[user]

    def has_changed(self, timestamp):
        return self.modified > timestamp

    def has_polled(self, user, timestamp):
        self.poll_requests[user].append(timestamp)


class BaseApi:

    def __init__(self, cfg, logger, user_class=BaseUser, chatroom_class=BaseChatroom):
        self.cfg = cfg
        self.logger = logger
        self.user_class = user_class
        self.chatroom_class = chatroom_class

        self.mutex = threading.Lock()

        self.users = {}

        # Dictionaries organized by chatroom ids.
        self.chatrooms = {}
        self.chatroom_locks = {}
        self.released_chatrooms = {}

    def version(self):
        return "1.0"

    def get_chatrooms(self):
        return {
            "chatrooms": list(self.chatrooms.values()),
            "released_chatrooms": list(self.released_chatrooms.values())
        }

    def join(self, user_id, attribs=dict()):
        self.logger.debug("join user={0}".format(user_id))
        self.mutex.acquire()
        try:
            user = self.user_class(user_id, attribs)
            self.users[user_id] = user

            # Try to find an available partner.
            # If none is found, assign the user to a new chatroom.
            available_chatrooms = [self.chatrooms[id_] for id_ in self.chatrooms if
                                    len(self.chatrooms[id_].users) == 1 and
                                    not self.chatrooms[id_].closed and
                                    user_id not in self.chatrooms[id_] and
                                    user.has_matching_attribs(self.chatrooms[id_].users[0])]

            if len(available_chatrooms) > 0:
                chatroom = sorted(available_chatrooms, key=lambda x: x.created, reverse=False)[0]
                if chatroom.id in self.chatroom_locks:
                    self.chatroom_locks[chatroom.id].acquire()
                    try:
                        chatroom.add_user(user_id)
                    finally:
                        self.chatroom_locks[chatroom.id].release()
            else:
                experiment_id = self.cfg['experiment_id']
                chatroom = self.chatroom_class(id_=str(uuid.uuid4()), experiment_id=experiment_id, initiator=user_id)
                self.chatrooms[chatroom.id] = chatroom
                self.chatroom_locks[chatroom.id] = threading.Lock()

            self.logger.debug("User {0} is assigned to chatroom {1}.".format(user_id, chatroom.id))

            data = self._get_chatroom_data(chatroom.id)
            return data
        except:
            self.logger.info('data is None!')
            return None
        finally:
            self.mutex.release()

    def _get_chatroom_data(self, chatroom_id):
        chatroom = self.chatrooms[chatroom_id]

        data = {
            'chatroom': chatroom,
            'msg_count_low': self.cfg['msg_count_low'],
            'msg_count_high': self.cfg['msg_count_high'],
            'poll_interval': self.cfg['poll_interval'],
            'delay_for_partner': self.cfg['delay_for_partner']
        }
        return data


class BaseApp(Flask):

    def __init__(self, import_name, api):
        Flask.__init__(self, import_name)
        self.api = api
        self.cfg = api.cfg
        self.logger = api.logger

        self.SESSION_TYPE = 'filesystem'
        self.SESSION_COOKIE_NAME = 'CGISESSID'
        self.SESSION_FILE_DIR = self.cfg['sessions']
        self.SESSION_COOKIE_PATH = self.cfg['cookiePath']
        self.SESSION_COOKIE_SECURE = True

        self.config.from_object(self)
        Session(self)

        @self.route('/{}/static/<path:path>'.format(self.cfg['web_context']))
        def get_static(path):
            return self.get_static(path)

        @self.route('/{}/version'.format(self.cfg['web_context']))
        def version():
            return self.version()

        @self.route('/{}/index'.format(self.cfg['web_context']))
        def index():
            return self.index()

        @self.route('/{}/admin'.format(self.cfg['web_context']))
        def admin():
            return self.admin()

        @self.route('/{}/join'.format(self.cfg['web_context']), methods=['POST'])
        def join():
            return self.join(session, request)

    def get_static(self, path):
        return send_from_directory('static', path)

    def version(self):
        version = self.api.version()
        try:
            return render_template('version.html', version=version)
        except TemplateNotFound:
            return render_template('default_version.html', version=version)

    def index(self):
        try:
            return render_template('index.html')
        except TemplateNotFound:
            return render_template('default_index.html')

    def admin(self):
        data = self.api.get_chatrooms()
        chatrooms = [convert_chatroom_to_dict(chatroom) for chatroom in data['chatrooms']]
        released_chatrooms = [convert_chatroom_to_dict(released_chatrooms)
                                for released_chatrooms in data['released_chatrooms']]
        try:
            return render_template(
                'admin.html',
                chatrooms=chatrooms,
                released_chatrooms=released_chatrooms,
                experiment_id=self.cfg['experiment_id'],
                utc_to_local=utc_to_local)
        except TemplateNotFound:
            return render_template(
                'default_admin.html',
                chatrooms=chatrooms,
                released_chatrooms=released_chatrooms,
                experiment_id=self.cfg['experiment_id'],
                utc_to_local=utc_to_local)

    def join(self, session, request):
        if 'clientTabId' not in request.form:
            return '', 400

        client_tab_id = request.form['clientTabId']
        user_id = session.sid + '_' + client_tab_id
        data = self.api.join(user_id)
        try:
            return render_template(
                'chatroom.html',
                client_tab_id=client_tab_id,
                msg_count_low=data['msg_count_low'],
                msg_count_high=data['msg_count_high'],
                poll_interval=data['poll_interval'],
                delay_for_partner=0 if data['chatroom'].closed else data['delay_for_partner'],
                experiment_id=data['chatroom'].experiment_id,
                chatroom_id=data['chatroom'].id,
                is_first_user=(data['chatroom'].initiator == user_id),
                server_url=''
            )
        except TemplateNotFound:
            return render_template(
                'default_chatroom.html',
                client_tab_id=client_tab_id,
                msg_count_low=data['msg_count_low'],
                msg_count_high=data['msg_count_high'],
                poll_interval=data['poll_interval'],
                delay_for_partner=0 if data['chatroom'].closed else data['delay_for_partner'],
                experiment_id=data['chatroom'].experiment_id,
                chatroom_id=data['chatroom'].id,
                is_first_user=(data['chatroom'].initiator == user_id)
            )
