import os

class Config:
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://admin:admin@clustereficaz.j4vdwxj.mongodb.net/marketplace")
