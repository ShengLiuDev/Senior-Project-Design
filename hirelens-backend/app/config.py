import os
from dotenv import load_dotenv

# load environment variables from .env file
load_dotenv()

# API keys and config
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
GOOGLE_SHEETS_CREDENTIALS = os.getenv('GOOGLE_SHEETS_CREDENTIALS')

# API endpoints
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# model config using the 33b version of the deepseek coder
DEEPSEEK_MODEL = "deepseek-ai/deepseek-coder-33b-instruct" 