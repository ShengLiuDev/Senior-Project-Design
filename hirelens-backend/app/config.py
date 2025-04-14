import os
from dotenv import load_dotenv

# load environment variables from .env file
load_dotenv()

# API keys and config
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
GOOGLE_SHEETS_CREDENTIALS = os.getenv('GOOGLE_SHEETS_CREDENTIALS')

# API endpoints
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# model config using DeepSeek R1 free version
DEEPSEEK_MODEL = "deepseek/deepseek-r1:free" 