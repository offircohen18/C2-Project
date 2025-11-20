import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("C2_SECRET_KEY").encode()
