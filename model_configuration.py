from metagpt.config2 import Config

# for quantized models, simply host on huggingface

def get_tinyllama():
    llm_config = {"api_type": "codestallation", "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"}
    tinyllama = Config.from_llm_config(llm_config)
    return tinyllama

def get_codet5():
    llm_config = {"api_type": "codestallation", "model": "microsoft/Phi-4-mini-instruct"}
    codet5 = Config.from_llm_config(llm_config)
    return codet5

