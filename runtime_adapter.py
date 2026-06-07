"""ComfyUI-facing generation helpers for Dots TTS."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Callable

import numpy as np
import torch
from tqdm import tqdm

from .loader import DotsTTSBundle, resume_bundle_to_device


def manual_seed_all(seed: int) -> None:
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    if hasattr(torch, "xpu") and torch.xpu.is_available():
        torch.xpu.manual_seed(seed)
    try:
        np.random.seed(seed)
    except Exception:
        pass


def comfy_audio_to_tensor(audio: dict) -> tuple[torch.Tensor, int]:
    waveform = audio["waveform"]
    sample_rate = int(audio["sample_rate"])
    if not isinstance(waveform, torch.Tensor):
        waveform = torch.as_tensor(waveform)
    wav = waveform[0].detach().float().cpu()
    if wav.ndim == 2 and wav.shape[0] > 1:
        wav = wav.mean(dim=0, keepdim=True)
    elif wav.ndim == 1:
        wav = wav.unsqueeze(0)
    return wav.contiguous(), sample_rate


def write_temp_audio(audio: dict, directory: Path, name: str = "reference.wav") -> Path:
    import soundfile as sf

    wav, sample_rate = comfy_audio_to_tensor(audio)
    path = directory / name
    samples = wav.transpose(0, 1).numpy().astype(np.float32, copy=False)
    sf.write(str(path), samples, sample_rate)
    return path


def tensor_to_comfy_audio(audio: torch.Tensor, sample_rate: int) -> dict:
    audio = audio.detach().float().cpu().clamp(-1.0, 1.0)
    if audio.ndim == 1:
        audio = audio.view(1, 1, -1)
    elif audio.ndim == 2:
        audio = audio.unsqueeze(0)
    elif audio.ndim != 3:
        audio = audio.reshape(1, 1, -1)
    return {"waveform": audio.contiguous(), "sample_rate": int(sample_rate)}


def _language_to_runtime(language: str) -> str | None:
    value = (language or "").strip()
    if not value or value.lower() == "none":
        return None
    if value.lower() == "auto":
        return "auto_detect"
    return value


def generate_dotstts(
    bundle: DotsTTSBundle,
    *,
    text: str,
    reference_audio: dict | None,
    reference_text: str,
    steps: int,
    cfg: float,
    seed: int,
    language: str,
    normalize_text: bool,
    max_audio_patches: int,
    progress_callback: Callable[[int, int], None] | None = None,
) -> dict:
    if not text.strip():
        raise ValueError("Text cannot be empty.")
    if bundle.runtime is None or bundle.runtime.model is None:
        raise RuntimeError("Dots TTS model was unloaded. Re-run the Dots TTS Load Model node.")
    if seed:
        manual_seed_all(int(seed))
    resume_bundle_to_device(bundle)
    max_audio_patches = max(1, min(int(max_audio_patches), 4096))
    previous_max_audio_patches = int(bundle.runtime.max_generate_length)
    bundle.runtime.max_generate_length = max_audio_patches

    prompt_text = reference_text.strip() if reference_audio is not None else None
    prompt_path: str | None = None
    temp_dir_obj = None
    if reference_audio is not None:
        temp_dir_obj = tempfile.TemporaryDirectory(prefix="dotstts_ref_")
        prompt_path = str(write_temp_audio(reference_audio, Path(temp_dir_obj.name)))

    chunks: list[torch.Tensor] = []
    total = max_audio_patches
    cli_progress = tqdm(
        total=total,
        desc="[Dots-TTS-ComfyUI] Generating",
        ascii=False,
        dynamic_ncols=True,
        mininterval=0.0,
        miniters=10,
        leave=True,
    )
    generation_completed = False
    try:
        for index, chunk in enumerate(
            bundle.runtime.generate_stream(
                text=text,
                prompt_audio_path=prompt_path,
                prompt_text=prompt_text,
                language=_language_to_runtime(language),
                num_steps=int(steps),
                guidance_scale=float(cfg),
                normalize_text=bool(normalize_text),
            ),
            start=1,
        ):
            chunks.append(chunk.detach().float().cpu())
            cli_progress.update(1)
            if progress_callback is not None:
                progress_callback(min(index, total), total)
        if not chunks:
            raise RuntimeError("Dots TTS generated no audio chunks.")
        generation_completed = True
    finally:
        if generation_completed:
            cli_progress.total = cli_progress.n
        cli_progress.close()
        bundle.runtime.max_generate_length = previous_max_audio_patches
        if temp_dir_obj is not None:
            temp_dir_obj.cleanup()

    if progress_callback is not None:
        progress_callback(total, total)
    audio = torch.cat(chunks, dim=-1)
    return tensor_to_comfy_audio(audio, bundle.runtime.sample_rate)
