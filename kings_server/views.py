import asyncio
import base64
import os
import pprint

import aiohttp_jinja2
import bcrypt
import jinja2
from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient
from db import car
from bson import ObjectId

WEBAPP_HOST = 'localhost'  # or ip
WEBAPP_PORT = 8000


def generate_password_hash(password, salt_rounds=10):
    password_bin = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bin, bcrypt.gensalt(salt_rounds))
    encoded = base64.b64encode(hashed)
    return encoded.decode('utf-8')


def check_password_hash(encoded, password):
    password = password.encode('utf-8')
    encoded = encoded.encode('utf-8')
    hashed = base64.b64decode(encoded)
    is_correct = bcrypt.hashpw(password, hashed) == hashed
    return is_correct


async def setup_db():
    """base db setup f-n"""
    client = AsyncIOMotorClient()
    db = client['kings_db']
    return db


async def db_fetch_all():
    """return list of all cars from db"""
    cursor = db.cars.find().sort('timestamp')
    return [x for x in await cursor.to_list(length=100)]


async def new_user(username, password):
    """make new user in db with encrypted password"""
    result = await db.user.insert_one(
        {'username': username,
         'password': generate_password_hash(password)}
    )
    return result


async def check_login(username, password):
    """return Error if user is not register / False if password is incorrect / True if ok"""
    user = await db.user.find_one(
        {'username': username}
    )
    if not user:
        return {'status': 'User not match'}
    elif user:
        return {'status': 'Nice'} if check_password_hash(user['password'], password) else {'status': 'Incorrect pass'}


@aiohttp_jinja2.template('new.html')
async def new(request):
    """create new car page"""
    return {}


@aiohttp_jinja2.template('main.html')
async def main(request):
    """main handler with list of all cars"""
    print(request.method)
    if request.method == 'POST':
        post = await request.post()
        document = car.check(post)   # validate form
        print(document)
        result = await db.cars.insert_one(document)

    elif request.method == 'GET':
        pass

    context = {'cars': await db_fetch_all()}
    print(context)
    return context


@aiohttp_jinja2.template('login.html')
async def login(request):
    print(request.method)
    if request.method == 'GET':
        return {}
    elif request.method == 'POST':
        data = await request.post()
        username = data['login']
        password = data['password']
        print(username, password)
        status = await check_login(username, password)
        print(status)
        if status['status'] == 'User not match':
            return web.json_response(data={'error': status['status']})
        elif status['status'] == 'Nice':
            return web.HTTPFound('/main')
        elif status['status'] == 'Incorrect pass':
            return web.HTTPUnauthorized()


@aiohttp_jinja2.template('register.html')
async def register(request):
    """make new user and redirect to main"""
    if request.method == 'POST':
        data = await request.post()
        result = await new_user(data['login'], data['password'])
        if result:
            return web.HTTPFound('/main')
        else:
            return web.json_response(data={'error': 'something wrong / try again later'})
    elif request.method == 'GET':
        return {}


@aiohttp_jinja2.template('main.html')
async def delete_car(request):
    """handler that delete car from main list and from db"""
    print(request)
    if request.method == 'POST':
        data = await request.post()
        result = await db.cars.delete_one({'_id': ObjectId(data["car_id"])})
        return web.HTTPFound('/main')


@aiohttp_jinja2.template('edit.html')
async def edit_car(request):
    """handler that render edit car page with db values"""
    print(request)
    if request.method == 'POST':
        data = await request.post()
        context = {'car': await db.cars.find_one({'_id': ObjectId(data['car_id'])})}
        print(context)
        return context


async def save_edit(request):
    """save edited car data to db"""
    print(request)
    if request.method == 'POST':
        data = await request.post()
        result = await db.cars.update_one({'_id': ObjectId(data['car_id'])}, {'$set': data})
        return web.HTTPFound('/main')


loop = asyncio.get_event_loop()
db = loop.run_until_complete(setup_db())

app = web.Application()
app['db'] = db
app.add_routes([web.post('/login', login, name='login'),
                web.get('/', login),
                web.get('/main', main),
                web.post('/main', main),
                web.post('/new', new),
                web.get('/new', new),
                web.post('/register', register),
                web.get('/register', register),
                web.post('/edit_car', edit_car),
                web.post('/delete_car', delete_car),
                web.post('/save_edit', save_edit),
                ])
aiohttp_jinja2.setup(app,
                     loader=jinja2.FileSystemLoader(os.path.join(os.getcwd(), 'template')))
web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
