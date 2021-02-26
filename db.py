import motor

client = motor.motor_asyncio.AsyncIOMotorClient()

db = client.test_database
collection = db['test_collection']



