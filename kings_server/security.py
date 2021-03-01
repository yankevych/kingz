import bcrypt
import base64
import functools
from aiohttp import web
from aiohttp_security import authorized_userid
from aiohttp_security.abc import AbstractAuthorizationPolicy
from bson import ObjectId


def generate_password_hash(password, salt_rounds=10):
    """convert pass to store in hash in db"""
    password_bin = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bin, bcrypt.gensalt(salt_rounds))
    encoded = base64.b64encode(hashed)
    return encoded.decode('utf-8')


def check_password_hash(encoded, password):
    """check if hash in db is equal to user login password"""
    password = password.encode('utf-8')
    encoded = encoded.encode('utf-8')
    hashed = base64.b64decode(encoded)
    is_correct = bcrypt.hashpw(password, hashed) == hashed
    return is_correct


class AuthorizationPolicy(AbstractAuthorizationPolicy):
    def __init__(self, mongo):
        self.mongo = mongo

    async def authorized_userid(self, identity):
        user = await self.mongo.user.find_one({'_id': ObjectId(identity)})
        if user:
            return identity
        return None

    async def permits(self, identity, permission, context=None):
        if identity is None:
            return False
        return True


def auth_required(f):
    @functools.wraps(f)
    async def wrapped(request):
        user_id = await authorized_userid(request)
        if not user_id:
            raise web.HTTPUnauthorized()
        return (await f(request))
    return wrapped
