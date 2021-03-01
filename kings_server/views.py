import asyncio

import os
import aiohttp_jinja2

import jinja2
from datetime import datetime
from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient
from db import car
from bson import ObjectId
from loguru import logger
from security import *
import trafaret as t

WEBAPP_HOST = 'localhost'
WEBAPP_PORT = 8000


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
    if request.method == 'POST':
        post = await request.post()
        pre_check = await db.cars.find_one({'vin': post['vin']})    # check if VIN is unique
        if pre_check:
            return web.json_response(data={'error': 'VIN must be unique'})
        else:
            try:
                document = car.check(post)   # validate form
                logger.info(document)
                document.update({"timestamp": datetime.now()})
                await db.cars.insert_one(document)
            except t.DataError as e:
                return web.json_response(data={'error': e.as_dict()})

    elif request.method == 'GET':
        pass

    context = {'cars': await db_fetch_all()}
    logger.info(context)
    return context


@aiohttp_jinja2.template('login.html')
async def login(request):
    """main login page with login checker"""
    if request.method == 'GET':
        return {}
    elif request.method == 'POST':
        data = await request.post()
        username = data['login']
        password = data['password']
        logger.info(username, password)
        status = await check_login(username, password)
        logger.info(status)
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
    if request.method == 'POST':
        data = await request.post()
        await db.cars.delete_one({'_id': ObjectId(data["car_id"])})
        return web.HTTPFound('/main')


@aiohttp_jinja2.template('edit.html')
async def edit_car(request):
    """handler that render edit car page with db values"""
    if request.method == 'POST':
        data = await request.post()
        context = {'car': await db.cars.find_one({'_id': ObjectId(data['car_id'])})}
        logger.info(context)
        return context


async def save_edit(request):
    """save edited car data to db"""
    if request.method == 'POST':
        data = await request.post()
        await db.cars.update_one({'_id': ObjectId(data['car_id'])}, {'$set': data})
        return web.HTTPFound('/main')


@aiohttp_jinja2.template('main.html')
async def search(request):
    """filter car from search method"""
    if request.method == 'POST':
        data = await request.post()
        cursor = db.cars.find({f'{data["method"]}': f'{data["query"]}'}).sort('timestamp')
        context = {'cars': [x for x in await cursor.to_list(length=100)]}
        return context


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
                web.post('/search', search),
                ])
aiohttp_jinja2.setup(app,
                     loader=jinja2.FileSystemLoader(os.path.join(os.getcwd(), 'template')))
web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
