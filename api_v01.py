import asyncio
import os
import aiohttp_jinja2
import jinja2
from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient

WEBAPP_HOST = 'localhost'  # or ip
WEBAPP_PORT = 8000


async def setup_db():
    db = AsyncIOMotorClient().test
    await db.pages.drop()
    html = '<html><body>{}</body></html>'
    await db.pages.insert_one({'_id': 'page-one',
                                    'body': html.format('Hello!')})

    await db.pages.insert_one({'_id': 'page-two',
                                    'body': html.format('Goodbye.')})

    return db


async def admin(request):
    """main admin site"""
    # db = await setup_db()
    # name = request.match_info.get('name', "Anonymous")
    txt = "Hello, {}".format(db)
    return web.Response(text=txt)


async def new(request):
    """create new car page"""
    context = dict()
    response = aiohttp_jinja2.render_template('new.html',
                                              request,
                                              context
                                            )
    return response


async def main(request):
    """main handler with list of all cars"""
    print(0)
    print(request.method)
    if request.method == 'POST':
        print(11)
        form = await request.post()
        print(form)
        context = form
    elif request.method == 'GET':
        print(22)
        context = dict()
    response = aiohttp_jinja2.render_template('main.html',
                                              request, context
                                            )
    response.headers['Content-Language'] = 'ru'
    return response


async def login(request):
    if request.method == 'GET':
        context = dict()
        response = aiohttp_jinja2.render_template('login.html',
                                                  request, context
                                                  )
        response.headers['Content-Language'] = 'ru'
        return response
    elif request.method == 'POST':
        data = await request.post()
        login = data['login']
        password = data['password']
        print(login, password)
        # error = validate_login(form)  #TODO
        error = False
        if error:
            return {'error': error}
        else:
            return web.HTTPFound('/main')


loop = asyncio.get_event_loop()
db = loop.run_until_complete(setup_db())

app = web.Application()
app['db'] = db
app.add_routes([web.get('/admin', admin, name='admin'),
                web.post('/login', login, name='login'),
                web.get('/', login),
                web.get('/main', main),
                web.post('/main', main),
                web.post('/new', new),
                web.get('/new', new),
                ])
aiohttp_jinja2.setup(app,
                     loader=jinja2.FileSystemLoader(os.path.join(os.getcwd(), 'template')))
web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
