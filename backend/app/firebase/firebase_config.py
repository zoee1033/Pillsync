import os
import firebase_admin
from firebase_admin import credentials

# Path of the current folder (app/firebase)
BASE_DIR = os.path.dirname(__file__)

# serviceAccountKey.json is in the same folder
SERVICE_ACCOUNT_PATH = os.path.join(
    BASE_DIR,
    "serviceAccountKey.json"
)

firebase_app = None

if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_app = firebase_admin.initialize_app(cred)
else:
    firebase_app = firebase_admin.get_app()