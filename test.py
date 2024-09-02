from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi

ca = certifi.where()

uri = "mongodb+srv://elimranyissam:omaxrvIzqZmZef6c@cluster0.x6xoo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server with increased timeout settings
client = MongoClient(uri, tlsCAFile = ca)

# Send a ping to confirm a successful connection
for db in client.list_database_names() :
    print(db)

