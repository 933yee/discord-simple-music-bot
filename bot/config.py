import os
from dotenv import load_dotenv


def getToken():
    load_dotenv()
    return os.environ.get("DISCORD_BOT_TOKEN")
