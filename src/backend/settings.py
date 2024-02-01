from dotenv import load_dotenv
import os
import logging

load_dotenv()


class Settings:
    def __init__(self):
        self.api_endpoint = os.getenv("OPENAI_URI")
        self.api_key = os.getenv("OPENAI_KEY")
        self.api_version = os.getenv("OPENAI_VERSION")
        self.api_deployment_name = os.getenv("OPENAI_GPT_DEPLOYMENT")
        self.email_URI = os.getenv("EMAIL_URI")
        self.deploy_spa = os.getenv("DEPLOY_SPA")


settings = None


def Instance() -> Settings:
    global settings
    if settings is None:
        settings = Settings()
        if settings.api_endpoint is None or settings.api_key is None or settings.api_version is None or settings.api_deployment_name is None or settings.email_URI is None:
            logging.error(
                "Missing environment variables. Please ensure that OPENAI_URI, OPENAI_KEY, OPENAI_VERSION, OPENAI_GPT_DEPLOYMENT, and EMAIL_URI are set.")
            os._exit(1)
    return settings
