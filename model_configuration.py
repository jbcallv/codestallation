import os
from metagpt.config2 import Config
from dotenv import load_dotenv

load_dotenv()

# for quantized models, simply host on huggingface

def get_tinyllama():
    llm_config = {"api_type": "codestallation", "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"}
    tinyllama = Config.from_llm_config(llm_config)
    return tinyllama

def get_phi4():
    llm_config = {"api_type": "codestallation", "model": "microsoft/Phi-4-mini-instruct"}
    phi4 = Config.from_llm_config(llm_config)
    return phi4

def get_claude():
    llm_config = {
        "api_type": "claude",
        "base_url": "https://api.anthropic.com",
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "model": "claude-3-5-haiku-20241022"
    }

    haiku = Config.from_llm_config(llm_config)
    return haiku

def get_chatgpt():
    llm_config = {
        "api_type": "openai",
        "base_url": "https://api.openai.com/v1",
        "api_key": "",
        "model": "gpt-4.1-mini-2025-04-14"# "gpt-4o-mini-2024-07-18" 2048 max input tokens ??
    }

def get_no_model():
    config = {"api_type": "codestallation", "model": "no_model"}
    no_model = Config.from_llm_config(config)
    return no_model
