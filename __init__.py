"""ComfyUI custom nodes for Dots TTS."""

from __future__ import annotations

__version__ = "0.1.2"

import importlib.metadata as _metadata
import importlib.util
import logging
import sys
import types
from pathlib import Path
from typing import Any

logger = logging.getLogger("Dots-TTS-ComfyUI")
logger.propagate = False
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("[Dots-TTS-ComfyUI] %(message)s"))
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))


def _quiet_third_party_logging() -> None:
    try:
        from loguru import logger as _loguru_logger

        for _module_name in (
            "dots_tts",
            f"{__name__}.dots_tts",
            f"{_HERE}.dots_tts",
            f"{_HERE.as_posix()}.dots_tts",
            "Dots-TTS-ComfyUI.dots_tts",
            "Dots_TTS_ComfyUI.dots_tts",
        ):
            _loguru_logger.disable(_module_name)
    except Exception:
        pass
    try:
        from transformers.utils import logging as _transformers_logging

        _transformers_logging.set_verbosity_error()
        if hasattr(_transformers_logging, "disable_progress_bar"):
            _transformers_logging.disable_progress_bar()
    except Exception:
        pass
    try:
        from huggingface_hub.utils import disable_progress_bars

        disable_progress_bars()
    except Exception:
        pass


def _block_broken_torchcodec() -> None:
    broken = False
    if "torchcodec" not in sys.modules:
        try:
            import torchcodec  # noqa: F401
        except Exception:
            broken = True

    tc = sys.modules.get("torchcodec")
    if not broken and tc is not None and getattr(tc, "__spec__", None) is not None:
        return

    stub = types.ModuleType("torchcodec")
    stub.__path__ = []
    stub.__package__ = "torchcodec"
    stub.__spec__ = importlib.util.spec_from_loader("torchcodec", loader=None, origin="torchcodec")
    for sub in ("decoders", "encoders", "samplers", "transforms", "_core"):
        sub_mod = types.ModuleType(f"torchcodec.{sub}")
        sub_mod.__spec__ = importlib.util.spec_from_loader(f"torchcodec.{sub}", loader=None)
        if sub == "decoders":
            class _AudioDecoder:
                pass

            sub_mod.AudioDecoder = _AudioDecoder
        setattr(stub, sub, sub_mod)
        sys.modules[f"torchcodec.{sub}"] = sub_mod
    sys.modules["torchcodec"] = stub

    original_version = _metadata.version

    def patched_version(name: str) -> str:
        if name == "torchcodec":
            return "0.0.0"
        return original_version(name)

    _metadata.version = patched_version
    logger.info("torchcodec is unavailable or incompatible; using audio fallback paths.")


_quiet_third_party_logging()
_block_broken_torchcodec()

NODE_CLASS_MAPPINGS: dict[str, Any] = {}
NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {}

try:
    from .loader import install_comfy_unload_hook, register_model_folder

    register_model_folder()
    install_comfy_unload_hook()
    from .nodes import NODE_CLASS_MAPPINGS as _NODE_CLASS_MAPPINGS
    from .nodes import NODE_DISPLAY_NAME_MAPPINGS as _NODE_DISPLAY_NAME_MAPPINGS

    NODE_CLASS_MAPPINGS.update(_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(_NODE_DISPLAY_NAME_MAPPINGS)
    logger.info("Registered %d node(s).", len(NODE_CLASS_MAPPINGS))
except Exception as exc:
    logger.error("Failed to register Dots TTS nodes: %s", exc, exc_info=True)

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "__version__"]
