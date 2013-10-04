import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.options
import logging
import tornado.auth
import tornado.escape
import os.path
import uuid
from uuid import uuid4
import json


from tornado import gen
from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_json = self.get_secure_cookie("chat_user")
        if not user_json: return None
        return tornado.escape.json_decode(user_json)

class Room(object):
    def __init__(self):
        self.messageLog = []
        self.log_size = 250
        self.users = []
        self.callbacks = []

    def new_message(self, message):
        print self.users
        for callback in self.callbacks:
            try:
                callback(message)
            except:
                print "error in waiting user"
        self.messageLog.extend(message)
        if len(self.messageLog) > self.log_size:
            self.messageLog = self.messageLog[-self.log_size:]
        self.callbacks = []
        self.users = []


    def addUser(self, callback, user):
        if user not in self.users:
            self.users.append(user)
        self.callbacks.append(callback)

    def removeUser(self, callback, user):
        self.users.remove(user)
        self.callbacks.remove(callback)

        
chatRoom = Room()

class NewHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        message = {
                "id": str(uuid.uuid4()),
                "from": self.current_user["name"],
                "body": self.get_argument("body"),
                }
         
        message["html"] = tornado.escape.to_basestring(self.render_string("message.html", message=message))
        self.write(message)
        chatRoom.new_message([message])


class UpdateHandler(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def post(self):
        chatRoom.addUser(self.sendUpdates, self.current_user)

    def sendUpdates(self,messages):
        if self.request.connection.stream.closed():
            return
        self.finish(dict(messages=messages))

    def on_connection_close(self):
        chatRoom.removeUser(self.sendUpdates, self.current_user)


class AuthLoginHandler(BaseHandler, tornado.auth.GoogleMixin):
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        if self.get_argument("openid.mode", None):
            user = yield self.get_authenticated_user()
            self.set_secure_cookie("chat_user",
                                   tornado.escape.json_encode(user))
            self.redirect("/")
            return
        self.authenticate_redirect(ax_attrs=["name"])


class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("chat_user")
        self.write("You are now logged out")

class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        session = uuid4()
        self.render("index.html", room=chatRoom)


def main():
    parse_command_line()
    app = tornado.web.Application(
        [  (r"/auth/login", AuthLoginHandler),
          
            (r"/", MainHandler),
            (r"/auth/login", AuthLoginHandler),
            (r"/auth/logout", AuthLogoutHandler),
            (r"/new", NewHandler),
            (r"/updates", UpdateHandler),
            ],
        cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        login_url="/auth/login",
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        xsrf_cookies=True,
        )
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()

