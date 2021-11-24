from flask_login import UserMixin
import math


class User(UserMixin):
    def __init__(self, _id, name, email, handle) -> None:
        self.id = _id
        self._name = name
        self._email = email
        self.handle = handle
    
    @staticmethod
    def get(userid, _db):
        cursor = _db.get_db()
        cursor.execute("SELECT * FROM userdata where id='{}'".format(userid))
        result = cursor.fetchone()
        if not result:
            return None
        return User(result[0], result[1], result[2], result[3])        
    

    @staticmethod
    def create(userid, name, email, handle, _db):
        cursor = _db.get_db()
        if not handle:
            handle = 'NULL'
        cursor.execute("INSERT INTO userdata values('{0}', '{1}', '{2}', '{3}')".format(userid, \
        name, email, handle))
        cursor.execute("commit")

        return User(userid, name, email, handle)

    @staticmethod
    def create_no_handle(userid, name, email, _db):
        cursor = _db.get_db()
        cursor.execute("INSERT INTO userdata values('{0}', '{1}', '{2}', NULL)".format(userid, \
            name, email))
        cursor.execute("commit")

        return User(userid, name, email, None)
    @staticmethod
    def get_handle(userid, _db):
        cursor = _db.get_db()
        cursor.execute("SELECT handle FROM userdata where id='{}'".format(userid))
        result = cursor.fetchone()
        if not result:
            return None
        return result[0]
    
    @staticmethod
    def add_handle(userid, handle, _db):
        cursor = _db.get_db()
        cursor.execute("UPDATE userdata SET handle='{0}' WHERE id='{1}'".format(handle, userid))
        cursor.execute("commit")
    
    @staticmethod
    def update(userid, name, email, handle, _db):
        cursor = _db.get_db()
        cursor.execute("UPDATE userdata SET name='{0}', email='{1}', handle='{2}' \
        where id='{3}'".format(name, email, handle, userid))
        cursor.execute("commit")

        return User.get(userid, _db)

    @staticmethod
    def get_xp(userid, _db):
        cursor = _db.get_db()
        cursor.execute("SELECT xp FROM userdata WHERE id='{}'".format(userid))
        res = cursor.fetchone()[0]
        return res

    @staticmethod
    def get_level(userid, _db):
        xp = User.get_xp(userid, _db)
        level = xp / 100
        level = math.pow(level, 1/3)
        return int(level)
    
    @staticmethod
    def get_league(userid, _db):
        lev = User.get_level(userid, _db)
        lev -= 1
        lev //= 5
        if (lev == 0):
            return "Bronze"
        elif (lev == 1):
            return "Silver"
        elif (lev == 2):
            return "Gold"
        else:
            return "Platinum"
