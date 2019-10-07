from app import create_app
from config import LiveConfig


application = create_app(LiveConfig)

if __name__ == "__main__":
    application.run()
