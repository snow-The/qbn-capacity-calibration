"""環境探測：WSL2 內可用的套件與版本（DIM1 用）。"""
import importlib
import platform
import sys

print("python", sys.version.split()[0])
print("platform", platform.platform())

for name in ("numpy", "matplotlib", "sklearn", "scipy", "model2vec", "sentence_transformers",
             "torch", "transformers", "huggingface_hub"):
    try:
        m = importlib.import_module(name)
        print(f"OK   {name:24s} {getattr(m, '__version__', '?')}")
    except Exception as e:  # noqa: BLE001
        print(f"FAIL {name:24s} {type(e).__name__}: {e}")

try:
    import torch
    print("torch.cuda.is_available() =", torch.cuda.is_available())
except Exception:
    pass
