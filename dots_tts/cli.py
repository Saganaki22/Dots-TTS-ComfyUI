from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="dots.tts inference CLI.")
    template_choices = ("tts", "instruction_tts", "text_to_audio", "tts_interleave")
    parser.add_argument(
        "--model-name-or-path",
        required=True,
        help="Local pretrained directory or Hugging Face repo id",
    )
    parser.add_argument(
        "--revision", default=None, help="Optional Hugging Face revision"
    )
    parser.add_argument(
        "--cache-dir", default=None, help="Optional Hugging Face cache dir"
    )
    parser.add_argument("--text", type=str, required=True, help="Input text")
    parser.add_argument("--output", default="output.wav", help="Output wav file path")
    parser.add_argument(
        "--precision", type=str, default="bfloat16", help="Inference precision"
    )
    parser.add_argument(
        "--attention",
        choices=("auto", "sdpa", "flash_attention"),
        default="auto",
        help="Qwen2 attention implementation. flash_attention requires flash_attn.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for inference.",
    )
    parser.add_argument(
        "--prompt-audio", type=str, default=None, help="Path to prompt audio"
    )
    parser.add_argument(
        "--prompt-text", type=str, default=None, help="Transcript of prompt audio"
    )
    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Language tag mode. Default: none. Supported values: none, auto_detect, or a language code/name such as EN/en/english/chinese.",
    )
    parser.add_argument(
        "--template-name",
        choices=template_choices,
        default=None,
        help="Named template preset for generation.",
    )
    parser.add_argument(
        "--ode-method", type=str, default="euler", help="ODE solver method"
    )
    parser.add_argument(
        "--num-steps", type=int, default=10, help="Diffusion sampling steps"
    )
    parser.add_argument(
        "--guidance-scale",
        type=float,
        default=1.2,
        help="Classifier-free guidance scale",
    )
    parser.add_argument(
        "--speaker-scale",
        type=float,
        default=1.5,
        help="Scale applied to the reference speaker embedding",
    )
    parser.add_argument(
        "--max-generate-length",
        type=int,
        default=500,
        help="Maximum audio patch budget. 500 is about 160 seconds at 48 kHz.",
    )
    parser.add_argument(
        "--normalize-text",
        action="store_true",
        help="Whether to normalize text before inference",
    )
    parser.add_argument(
        "--profile-inference",
        action="store_true",
        help="Collect per-module inference timing statistics",
    )
    return parser.parse_args(argv)


def _resolve_attention(attention: str) -> str | None:
    if attention in {"auto", "sdpa"}:
        return "sdpa"
    if attention == "flash_attention":
        if importlib.util.find_spec("flash_attn") is None:
            raise ImportError("flash_attention was selected, but flash_attn is not installed.")
        return "flash_attention_2"
    raise ValueError(f"Unsupported attention mode: {attention}")


def main(argv=None):
    args = parse_args(argv)
    import soundfile as sf
    import torch
    from loguru import logger
    from tqdm import tqdm

    from dots_tts.runtime import DotsTtsRuntime
    from dots_tts.utils.logging import configure_logging
    from dots_tts.utils.util import seed_everything

    configure_logging()
    seed_everything(args.seed)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(
        "CLI command started: model={} output={} seed={}",
        args.model_name_or_path,
        output_path,
        args.seed,
    )

    try:
        runtime = DotsTtsRuntime.from_pretrained(
            args.model_name_or_path,
            revision=args.revision,
            cache_dir=args.cache_dir,
            precision=args.precision,
            attn_implementation=_resolve_attention(args.attention),
            max_generate_length=args.max_generate_length,
        )
        chunks = []
        total = max(1, int(args.max_generate_length))
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
            for chunk in runtime.generate_stream(
                text=args.text,
                prompt_audio_path=args.prompt_audio,
                prompt_text=args.prompt_text,
                language=args.language,
                template_name=args.template_name,
                ode_method=args.ode_method,
                num_steps=args.num_steps,
                guidance_scale=args.guidance_scale,
                speaker_scale=args.speaker_scale,
                normalize_text=args.normalize_text,
                profile_inference=args.profile_inference,
            ):
                chunks.append(chunk.detach().float().cpu())
                cli_progress.update(1)
            if not chunks:
                raise RuntimeError("Generation produced no audio chunks.")
            generation_completed = True
        finally:
            if generation_completed:
                cli_progress.total = cli_progress.n
            cli_progress.close()
        audio = torch.cat(chunks, dim=-1)
        sf.write(
            output_path,
            audio.float().cpu().squeeze().numpy(),
            runtime.sample_rate,
        )
    except Exception:
        logger.exception(
            "CLI inference failed: model={} output={}",
            args.model_name_or_path,
            output_path,
        )
        raise

    logger.info(
        "CLI output written: output={} sample_rate={} samples={}",
        output_path,
        runtime.sample_rate,
        int(audio.shape[-1]),
    )


if __name__ == "__main__":
    raise SystemExit(main())
