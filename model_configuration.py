from metagpt.config2 import Config

# for quantized models, simply host on huggingface

def get_deepseek():
    llm_config = {"api_type": "codestallation", "model": "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct"}
    deepseek = Config.from_llm_config(llm_config)
    return deepseek

def get_tinyllama():
    llm_config = {"api_type": "codestallation", "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"}
    tinyllama = Config.from_llm_config(llm_config)
    return tinyllama