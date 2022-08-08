from flask_login import UserMixin

class User:
    def __init__(self, id, username, password):
        self.username = username
        self.id = id
        self.password = password

