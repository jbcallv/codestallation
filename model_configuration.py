from metagpt.config2 import Config

# for quantized models, simply host on huggingface

def get_tinyllama():
    llm_config = {"api_type": "codestallation", "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"}
    tinyllama = Config.from_llm_config(llm_config)
    return tinyllama

def get_phi4():
    llm_config = {"api_type": "codestallation", "model": "microsoft/Phi-4-mini-instruct"}
    phi4 = Config.from_llm_config(llm_config)
    return phi4

def get_no_model():
    config = {"api_type": "", "model": ""}
    no_model = Config.from_llm_config(config)
    return no_model

