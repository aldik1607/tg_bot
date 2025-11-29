import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:3000")  
API_TIMEOUT = 10