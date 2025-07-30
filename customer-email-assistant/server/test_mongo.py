from pymongo.mongo_client import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
load_dotenv('../.env')

# If still None, set it directly for testing
if not os.getenv("MONGODB_URI"):
    os.environ["MONGODB_URI"] = "mongodb+srv://ghgh2753:dydy1011%21%40@hohyeonkim.zwkkdyu.mongodb.net/?retryWrites=true&w=majority&appName=HOHYEONKIM"

uri = os.getenv("MONGODB_URI")
print(f"MongoDB URI: {uri}")

# Create a new client and connect to the server
client = MongoClient(uri)

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    
    # Test database operations
    db = client.emails
    collection = db.test
    
    # Insert a test document
    test_doc = {"test": "connection", "status": "success"}
    result = collection.insert_one(test_doc)
    print(f"Test document inserted with ID: {result.inserted_id}")
    
    # Read the document back
    found_doc = collection.find_one({"test": "connection"})
    print(f"Found document: {found_doc}")
    
    # Clean up
    collection.delete_one({"test": "connection"})
    print("Test document deleted")
    
except Exception as e:
    print(f"MongoDB connection error: {e}")