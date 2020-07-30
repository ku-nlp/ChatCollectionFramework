from datetime import date, datetime
import dateutil.parser
from flask import Flask, jsonify, render_template, request, send_from_directory, session
from flask_session import Session
from jinja2.exceptions import TemplateNotFound
import json
from pathlib import Path
import pytz
import threading
import time
import uuid


tz = pytz.timezone('Asia/Tokyo')

def events_for_user(evt, user_id):
    event_for_user = {
        'from': 'self' if evt['from'] == user_id else 'other',
        'timestamp': evt['timestamp'],
        'type': evt['type']
    }
    if 'body' in evt:
        event_for_user['body'] = evt['body']
    return event_for_user

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
                                    user_id not in self.chatrooms[id_].users and
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

    def get_chatroom(self, chatroom_id, user_id, client_timestamp):
        self.logger.debug("get_chatroom chatroom={0} user={1} client_timestamp={2}".format(chatroom_id,
                                                                                           user_id,
                                                                                           client_timestamp)
                          )

        request_time = datetime.utcnow()
        while True:

            if chatroom_id in self.chatroom_locks:
                chatroom_lock = self.chatroom_locks[chatroom_id]

                chatroom_lock.acquire()
                try:
                    if chatroom_id not in self.chatrooms:
                        return None
                    chatroom = self.chatrooms[chatroom_id]
                    if user_id not in chatroom.users:
                        return None
                    chatroom.has_polled(user_id, request_time.isoformat())
                    chatroom_has_changed = not client_timestamp or chatroom.has_changed(client_timestamp)
                    self.logger.debug("user {0} checks if the chatroom has changed={1} "
                                      "modified={2} vs client_timestamp={3}".format(user_id,
                                                                                    chatroom_has_changed,
                                                                                    chatroom.modified,
                                                                                    client_timestamp)
                                      )
                    if chatroom_has_changed:
                        data = self._get_chatroom_data(chatroom_id)
                        return data

                finally:
                    chatroom_lock.release()

            # Make sure that the function terminates after a certain delay.
            # Otherwise, the poll requests will accumulate and make the web server crash.
            waiting_period = (datetime.utcnow() - request_time).total_seconds()
            if waiting_period >= (self.cfg['poll_interval']):
                # self.logger.debug("Waiting period has expired: {0}".format(waiting_period))
                return "expired"

            time.sleep(1.0)

    def post_message(self, user_id, chatroom_id, message):
        self.logger.debug("post_message user_id={0} chatroom_id={1} message={2}".format(user_id, chatroom_id, message))
        if chatroom_id not in self.chatroom_locks:
            return

        chatroom_lock = self.chatroom_locks[chatroom_id]
        chatroom_lock.acquire()
        try:
            if chatroom_id not in self.chatrooms:
                return
            chatroom = self.chatrooms[chatroom_id]
            if user_id not in chatroom.users:
                return
            evt = {'type': 'msg', 'from': user_id, 'body': message, 'timestamp': datetime.utcnow().isoformat()}
            chatroom.add_event(evt)

            data = self._get_chatroom_data(chatroom_id)
            return data
        finally:
            chatroom_lock.release()

    def leave_chatroom(self, user_id, chatroom_id):
        self.logger.debug("leave_chatroom user_id={0} chatroom_id={1}".format(user_id, chatroom_id))
        self.mutex.acquire()
        try:
            data = self._leave_chatroom(user_id, chatroom_id)
            return data
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

    def _leave_chatroom(self, user_id, chatroom_id):
        if chatroom_id not in self.chatrooms:
            return
        chatroom = self.chatrooms[chatroom_id]
        if user_id not in chatroom.users:
            return

        chatroom.remove_user(user_id)
        if len(chatroom.users) == 0:
            self._archive_dialog(chatroom_id)
            self.released_chatrooms[chatroom_id] = self.chatrooms[chatroom_id]
            self.chatrooms.pop(chatroom_id)
            self.chatroom_locks.pop(chatroom_id)
            return

        data = self._get_chatroom_data(chatroom_id)
        return data

    def _archive_dialog(self, chatroom_id):
        self.logger.debug("Archiving dialog from chatroom {0}...".format(chatroom_id))

        creation_date = dateutil.parser.parse(self.chatrooms[chatroom_id].created)

        tz = pytz.timezone('Asia/Tokyo')

        dialog_dir = "{0}/{1}/{2:0>2d}/{3:0>2d}".format(self.cfg['archives'], creation_date.year,
                                                        creation_date.month, creation_date.day)
        Path(dialog_dir).mkdir(parents=True, exist_ok=True)
        dialog_filename = '{0}.txt'.format(chatroom_id)
        with open("{0}/{1}".format(dialog_dir, dialog_filename), "w") as output_file:
            if self.chatrooms[chatroom_id].experiment_id:
                output_file.write("Experiment: {0}\n".format(self.chatrooms[chatroom_id].experiment_id))
            self.logger.debug("initiator={0} exists? {1}".format(
                self.chatrooms[chatroom_id].initiator,
                self.chatrooms[chatroom_id].initiator in self.users)
            )
            initiator = self.users[self.chatrooms[chatroom_id].initiator]
            output_file.write(
                "Params(U1): attribs: {0}\n".format(initiator.attribs)
            )
            self.logger.debug("partner={0} exists? {1}".format(
                self.chatrooms[chatroom_id].partner,
                self.chatrooms[chatroom_id].partner in self.users)
            )
            if self.chatrooms[chatroom_id].partner:
                partner = self.users[self.chatrooms[chatroom_id].partner]
                output_file.write(
                    "Params(U2): attribs: {0}\n".format(partner.attribs)
                )
            for evt in self.chatrooms[chatroom_id].events:
                str_from = "U{0}".format(1 if evt['from'] == self.chatrooms[chatroom_id].initiator else 2)
                timestamp = datetime.fromisoformat("{}+00:00".format(evt['timestamp'])).astimezone(tz).isoformat()
                output_file.write("{0}|{1}: {2}\n".format(timestamp, str_from, evt['body']))
                if 'checked' in evt and (evt['checked']):
                    output_file.write("checked: {0}\n".format(evt['checked']))
        self.logger.debug("Dialog has been archived in {0}/{1}".format(dialog_dir, dialog_filename))


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

        @self.route('/{}/chatroom'.format(self.cfg['web_context']))
        def get_chatroom():
            return self.get_chatroom(session, request)

        @self.route('/{}/post'.format(self.cfg['web_context']), methods=['POST'])
        def post_message():
            return self.post_message(session, request)

        @self.route('/{}/leave'.format(self.cfg['web_context']))
        def leave_chatroom():
            return self.leave_chatroom(session, request)

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

    def get_chatroom(self, session, request):
        params = request.args.to_dict()
        if 'clientTabId' not in params or 'id' not in params or 'timestamp' not in params:
            return '', 400
        client_tab_id = params.get('clientTabId')
        chatroom_id = params.get('id')
        client_timestamp = params.get('timestamp')
        user_id = session.sid + '_' + client_tab_id
        data = self.api.get_chatroom(chatroom_id, user_id, client_timestamp if client_timestamp != '' else None)
        response = "{}"
        if data is not None:
            if data == "expired":
                response = '{"msg": "poll expired"}'
            else:
                response = self._get_chatroom_response(user_id, data)
        return jsonify(response)

    def post_message(self, session, request):
        if 'clientTabId' not in request.form or 'chatroom' not in request.form or 'message' not in request.form:
            return '', 400
        client_tab_id = request.form['clientTabId']
        chatroom_id = request.form['chatroom']
        message = request.form['message']
        user_id = session.sid + '_' + client_tab_id
        data = self.api.post_message(user_id, chatroom_id, message)
        response = "{}"
        if data is not None:
            response = self._get_chatroom_response(user_id, data)
        return jsonify(response)

    def leave_chatroom(self, session, request):
        params = request.args.to_dict()
        if 'clientTabId' not in params or 'chatroom' not in params:
            return '', 400
        client_tab_id = params.get('clientTabId')
        chatroom_id = params.get('chatroom')
        user_id = session.sid + '_' + client_tab_id
        data = self.api.leave_chatroom(user_id, chatroom_id)
        response = "{}"
        if data is not None:
            response = self._get_chatroom_response(user_id, data)
        return jsonify(response)

    def _get_chatroom_response(self, user_id, data):
        formatted_events = [events_for_user(evt, user_id) for evt in data['chatroom'].events]
        try:
            response = render_template(
                'chatroom.json',
                chatroom_id=data['chatroom'].id,
                experiment_id=data['chatroom'].experiment_id,
                users=json.dumps(data['chatroom'].users),
                created=data['chatroom'].created,
                modified=data['chatroom'].modified,
                initiator="self" if data['chatroom'].initiator == user_id else "other",
                closed="true" if data['chatroom'].closed else "false",
                events=json.dumps(formatted_events, ensure_ascii=False),
                msg_count_low=data['msg_count_low'],
                msg_count_high=data['msg_count_high'],
                poll_interval=data['poll_interval'],
                delay_for_partner=data['delay_for_partner']
            )
        except TemplateNotFound:
            response = render_template(
                'default_chatroom.json',
                chatroom_id=data['chatroom'].id,
                experiment_id=data['chatroom'].experiment_id,
                users=json.dumps(data['chatroom'].users),
                created=data['chatroom'].created,
                modified=data['chatroom'].modified,
                initiator="self" if data['chatroom'].initiator == user_id else "other",
                closed="true" if data['chatroom'].closed else "false",
                events=json.dumps(formatted_events, ensure_ascii=False),
                msg_count_low=data['msg_count_low'],
                msg_count_high=data['msg_count_high'],
                poll_interval=data['poll_interval'],
                delay_for_partner=data['delay_for_partner']
            )
        return response
