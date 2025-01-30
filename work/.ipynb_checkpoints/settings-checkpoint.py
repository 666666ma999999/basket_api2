import os
from os.path import join
from dotenv import load_dotenv

load_dotenv(verbose=True)
current_directory = os.getcwd()

dotenv_path = join(current_directory, '.env')
load_dotenv(dotenv_path)

SSH_HOST = os.environ.get("SSH_HOST")
SSH_PORT = os.environ.get("SSH_PORT")
SSH_USER = os.environ.get("SSH_USER")
SSH_KEY = os.environ.get("SSH_KEY")

DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
