# Dots TTS ComfyUI

**English** | [中文](./README_ZH.md)

ComfyUI custom nodes for [rednote-hilab/dots.tts](https://github.com/rednote-hilab/dots.tts).

## Nodes

- Dots TTS Load Model
- Dots TTS Generate
- Dots TTS Voice Clone
- Dots TTS Whisper Transcribe

## Models

The loader catalog shows the official Rednote checkpoints first, then the drbaph BF16 conversions:

1. `dots.tts Base FP32 (auto-download)` - [rednote-hilab/dots.tts-base][hf-base]
2. `dots.tts SOAR FP32 (auto-download)` - [rednote-hilab/dots.tts-soar][hf-soar]
3. `dots.tts MF FP32 (auto-download)` - [rednote-hilab/dots.tts-mf][hf-mf]
4. `dots.tts Base BF16 (auto-download)` - [drbaph/dots.tts-base-bf16][hf-base-bf16]
5. `dots.tts SOAR BF16 (auto-download)` - [drbaph/dots.tts-soar-bf16][hf-soar-bf16]
6. `dots.tts MF BF16 (auto-download)` - [drbaph/dots.tts-mf-bf16][hf-mf-bf16]

Downloaded model files are placed like this:

```text
ComfyUI/
└── models/
    ├── dotstts/
    │   ├── common/
    │   │   ├── speaker_encoder.safetensors
    │   │   └── vocoder.safetensors
    │   ├── dots.tts-base/
    │   │   └── model.safetensors
    │   ├── dots.tts-soar/
    │   │   └── model.safetensors
    │   ├── dots.tts-mf/
    │   │   └── model.safetensors
    │   ├── dots.tts-base-bf16/
    │   │   └── dots.tts-base-bf16.safetensors
    │   ├── dots.tts-soar-bf16/
    │   │   └── dots.tts-soar-bf16.safetensors
    │   └── dots.tts-mf-bf16/
    │       └── dots.tts-mf-bf16.safetensors
    └── audio_encoders/
        ├── openai_whisper-large-v3-turbo/
        ├── openai_whisper-large-v3/
        ├── openai_whisper-medium/
        ├── openai_whisper-small/
        └── openai_whisper-tiny/
```

Small tokenizer/config assets are bundled in this custom node and separated by source model:

```text
ComfyUI/
└── custom_nodes/
    └── Dots-TTS-ComfyUI/
        └── assets/
            ├── dots.tts-base/
            │   ├── added_tokens.json
            │   ├── chat_template.jinja
            │   ├── config.json
            │   ├── latent_stats.pt
            │   ├── llm_config.json
            │   ├── merges.txt
            │   ├── special_tokens_map.json
            │   ├── tokenizer.json
            │   ├── tokenizer_config.json
            │   └── vocab.json
            ├── dots.tts-soar/
            │   └── same small-file set
            └── dots.tts-mf/
                └── same small-file set
```

BF16 entries use the matching source-model assets. For example, [drbaph/dots.tts-base-bf16][hf-base-bf16] uses `assets/dots.tts-base/`.

Shared heavy assets come from [drbaph/dots.tts-common][hf-common] and are stored under `ComfyUI/models/dotstts/common/`. The common repo files live at the repo root:

```text
drbaph/dots.tts-common/speaker_encoder.safetensors
drbaph/dots.tts-common/vocoder.safetensors
```
At load time the node assembles an upstream-compatible runtime cache under `runtime/` using links/copies from node assets, shared heavy assets, and the selected model weight. The loader uses Hugging Face directly and does not use HF mirrors.

## Generation Limits

`max_audio_patches` on both Generate and Voice Clone is the maximum audio patch budget for that generation, not a text-token limit. The default is `500`. With the bundled configs, one patch is about `0.32` seconds, so `500` is about `160` seconds of audio budget. The model can stop earlier when it reaches EOS; very long text can hit the cap and end early. Voice Clone prompt audio paired with `reference_text` also consumes part of this budget.

## Languages

Officially benchmarked: 24 languages — Chinese, English, Cantonese, Japanese, Korean, Arabic, Spanish, Turkish, Indonesian, Portuguese, French, Italian, Dutch, Vietnamese, German, Russian, Ukrainian, Thai, Polish, Romanian, Greek, Czech, Finnish, and Hindi. It may be able to do more languages but those are the ones officially benchmarked. Not all languages produce high quality results — you may need to experiment for yourself to see.

The language dropdown is kept to those 24 languages, plus `auto` and `none`: `AR`, `YUE`, `ZH`, `CS`, `NL`, `EN`, `FI`, `FR`, `DE`, `EL`, `HI`, `ID`, `IT`, `JA`, `KO`, `PL`, `PT`, `RO`, `RU`, `ES`, `TH`, `TR`, `UK`, `VI`.

## Install

**ComfyUI-Manager (recommended):** Open ComfyUI-Manager, search for **Dots TTS**, and click Install. ComfyUI-Manager will handle everything automatically.

Manual helper install with uv:

```bash
python -m uv pip install -r requirements.txt
```

Manual helper install with pip:

```bash
python -m pip install -r requirements.txt
```

The installer protects ComfyUI's core runtime packages and will not automatically upgrade `torch`, `torchaudio`, `torchvision`, `transformers`, or `pydantic`.

## Notes

Dots upstream recommends recent `transformers` and pydantic v2. This node warns about those versions instead of changing them automatically, because surprise upgrades can break other ComfyUI nodes.

Audio file I/O uses `soundfile` first. Dots' speaker feature path has a torchaudio-free fallback for broken torchaudio installs, though the original torchaudio/Kaldi fbank path is used when available.

## References

- [Dots TTS upstream repository][dots-repo]
- [Official Dots TTS Base model][hf-base]
- [Official Dots TTS SOAR model][hf-soar]
- [Official Dots TTS MF model][hf-mf]
- [drbaph Dots TTS Base BF16 model][hf-base-bf16]
- [drbaph Dots TTS SOAR BF16 model][hf-soar-bf16]
- [drbaph Dots TTS MF BF16 model][hf-mf-bf16]
- [drbaph Dots TTS shared common files][hf-common]
- [OpenAI Whisper large-v3-turbo][hf-whisper-turbo]
- [OpenAI Whisper large-v3][hf-whisper-large]
- [OpenAI Whisper medium][hf-whisper-medium]
- [OpenAI Whisper small][hf-whisper-small]
- [OpenAI Whisper tiny][hf-whisper-tiny]

[dots-repo]: https://github.com/rednote-hilab/dots.tts
[hf-base]: https://huggingface.co/rednote-hilab/dots.tts-base
[hf-soar]: https://huggingface.co/rednote-hilab/dots.tts-soar
[hf-mf]: https://huggingface.co/rednote-hilab/dots.tts-mf
[hf-base-bf16]: https://huggingface.co/drbaph/dots.tts-base-bf16
[hf-soar-bf16]: https://huggingface.co/drbaph/dots.tts-soar-bf16
[hf-mf-bf16]: https://huggingface.co/drbaph/dots.tts-mf-bf16
[hf-common]: https://huggingface.co/drbaph/dots.tts-common
[hf-whisper-turbo]: https://huggingface.co/openai/whisper-large-v3-turbo
[hf-whisper-large]: https://huggingface.co/openai/whisper-large-v3
[hf-whisper-medium]: https://huggingface.co/openai/whisper-medium
[hf-whisper-small]: https://huggingface.co/openai/whisper-small
[hf-whisper-tiny]: https://huggingface.co/openai/whisper-tiny
