# bp_backend/services/paligemma_service.py

import sys
import os
import functools

import numpy as np
import sentencepiece
import jax
import ml_collections
# ----------------------------------------------------------------
# 1) Set BASE_DIR = services/ folder, then go two levels up
#    to reach project_root/, where big_vision_repo/ is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))      # .../project_root/bp_backend/services
PROJECT_APP_DIR = os.path.dirname(BASE_DIR)                 # .../project_root/bp_backend
PROJECT_ROOT = os.path.dirname(PROJECT_APP_DIR)             # .../project_root

# 2) Build path to big_vision_repo/ and append to sys.path
BIG_VISION_PATH = os.path.join(PROJECT_ROOT, "big_vision_repo")
sys.path.append(BIG_VISION_PATH)

# Now we can import Paligemma:
from big_vision.models.proj.paligemma import paligemma
from big_vision.trainers.proj.paligemma import predict_fns
# ----------------------------------------------------------------

# Paths to model and tokenizer files (assuming models/ is in project_root)
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "paligemma-3b-mix-448.f16.npz")
TOKENIZER_PATH = os.path.join(PROJECT_ROOT, "models", "paligemma_tokenizer.model")

model_config = ml_collections.FrozenConfigDict({
    "llm": {"vocab_size": 257_152},
    "img": {"variant": "So400m/14", "pool_type": "none", "scan": True, "dtype_mm": "float16"}
})

# Initialization (will be done once on first import of this module):
model_pg = paligemma.Model(**model_config)
params_pg = paligemma.load(None, MODEL_PATH, model_config)
tokenizer_pg = sentencepiece.SentencePieceProcessor(TOKENIZER_PATH)
decode_fn_pg = predict_fns.get_all(model_pg)["decode"]
decode_pg = functools.partial(
    decode_fn_pg,
    devices=jax.devices(),
    eos_token=tokenizer_pg.eos_id()
)


def run_example(image_pil, prompt, max_decode_len=128):
    # Exactly the same method code you had in views.py, unmodified:
    image = image_pil.resize((448, 448)).convert("RGB")
    image_arr = np.array(image).astype(np.float32)
    image_arr = image_arr / 127.5 - 1.0
    image_arr = np.expand_dims(image_arr, axis=0)
    tokens_list = tokenizer_pg.encode(prompt, add_bos=True) + [tokenizer_pg.eos_id()]
    tokens = np.array(tokens_list)[None, :]
    mask_ar = np.zeros_like(tokens)
    mask_input = np.ones_like(tokens)
    batch = {
        "image": image_arr,
        "text": tokens,
        "mask_input": mask_input,
        "mask_ar": mask_ar,
        "_mask": np.array([True])
    }
    output_tokens = decode_pg(
        {"params": params_pg},
        batch=batch,
        max_decode_len=max_decode_len,
        sampler="greedy"
    )
    tokens_out = np.array(output_tokens)[0].tolist()
    try:
        eos_index = tokens_out.index(tokenizer_pg.eos_id())
        tokens_out = tokens_out[:eos_index]
    except ValueError:
        pass
    return tokenizer_pg.decode(tokens_out)
