# Dots TTS ComfyUI

[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](https://www.apache.org/licenses/LICENSE-2.0)
[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Models-yellow)](https://huggingface.co/collections/rednote-hilab/dotstts)

[English](./README.md) | **中文**

[rednote-hilab/dots.tts](https://github.com/rednote-hilab/dots.tts) 的 ComfyUI 自定义节点。

<img width="1555" height="1146" alt="Screenshot 2026-06-06 054154" src="https://github.com/user-attachments/assets/ffbcd3be-fe89-4d38-85eb-5872635f34f2" />

## 节点

- Dots TTS 加载模型
- Dots TTS 生成
- Dots TTS 语音克隆
- Dots TTS Whisper 转录

## 模型

加载器目录首先显示官方小红书检查点，然后是 drbaph 的 BF16 转换版本：

1. `dots.tts Base FP32 (auto-download)` - [rednote-hilab/dots.tts-base][hf-base]
2. `dots.tts SOAR FP32 (auto-download)` - [rednote-hilab/dots.tts-soar][hf-soar]
3. `dots.tts MF FP32 (auto-download)` - [rednote-hilab/dots.tts-mf][hf-mf]
4. `dots.tts Base BF16 (auto-download)` - [drbaph/dots.tts-base-bf16][hf-base-bf16]
5. `dots.tts SOAR BF16 (auto-download)` - [drbaph/dots.tts-soar-bf16][hf-soar-bf16]
6. `dots.tts MF BF16 (auto-download)` - [drbaph/dots.tts-mf-bf16][hf-mf-bf16]

## dots.tts 模型速查

| 模型 | 推荐步数 (NFE) | CFG / 引导系数 | 主要用途 |
|------|--------------|---------------|---------|
| **dots.tts-base** | 10–32 | 1.2（可调） | 微调、研究、完全的质量/延迟控制 |
| **dots.tts-soar** | 10–32 | 1.2（可调） | 最高质量的零样本语音克隆，最佳说话人相似度 |
| **dots.tts-mf** | 4 | 0 | 低延迟生产推理 |

### 简单建议

- **优先质量** → `dots.tts-soar`
- **优先速度** → `dots.tts-mf`
- **训练 / 微调** → `dots.tts-base`

下载的模型文件放置如下：

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

小型分词器/配置资源文件打包在此自定义节点中，按源模型分类存放：

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
            │   └── 相同的小文件集
            └── dots.tts-mf/
                └── 相同的小文件集
```

BF16 条目使用匹配的源模型资源文件。例如，[drbaph/dots.tts-base-bf16][hf-base-bf16] 使用 `assets/dots.tts-base/`。

共享的大型资源文件来自 [drbaph/dots.tts-common][hf-common]，存储在 `ComfyUI/models/dotstts/common/` 下。公共仓库文件位于仓库根目录：

```text
drbaph/dots.tts-common/speaker_encoder.safetensors
drbaph/dots.tts-common/vocoder.safetensors
```
加载时，节点使用来自节点资源、共享大型资源和所选模型权重的链接/副本，在 `runtime/` 下组装一个与上游兼容的运行时缓存。加载器直接使用 Hugging Face，不使用 HF 镜像。

## 生成限制

"生成"和"语音克隆"上的 `max_audio_patches` 是该次生成的最大音频补丁预算，而不是文本标记限制。默认值为 `500`。使用捆绑的配置，一个补丁大约是 `0.32` 秒，因此 `500` 大约是 `160` 秒的音频预算。模型在达到 EOS 时可以提前停止；非常长的文本可能会达到上限并提前结束。与 `reference_text` 配对的语音克隆提示音频也会消耗此预算的一部分。

## 语言

官方基准测试覆盖：24 种语言 — 中文、英语、粤语、日语、韩语、阿拉伯语、西班牙语、土耳其语、印尼语、葡萄牙语、法语、意大利语、荷兰语、越南语、德语、俄语、乌克兰语、泰语、波兰语、罗马尼亚语、希腊语、捷克语、芬兰语和印地语。它可能支持更多语言，但这些是官方进行过基准测试的语言。并非所有语言都能产生高质量的结果 — 您可能需要自行实验来确认。

语言下拉菜单保留这 24 种语言，加上 `auto` 和 `none`：`AR`、`YUE`、`ZH`、`CS`、`NL`、`EN`、`FI`、`FR`、`DE`、`EL`、`HI`、`ID`、`IT`、`JA`、`KO`、`PL`、`PT`、`RO`、`RU`、`ES`、`TH`、`TR`、`UK`、`VI`。

## 安装

**ComfyUI-Manager（推荐）：** 打开 ComfyUI-Manager，搜索 **Dots TTS**，然后点击安装。ComfyUI-Manager 会自动处理一切。

使用 uv 手动安装依赖：

```bash
python -m uv pip install -r requirements.txt
```

使用 pip 手动安装依赖：

```bash
python -m pip install -r requirements.txt
```

安装程序会保护 ComfyUI 的核心运行时包，不会自动升级 `torch`、`torchaudio`、`torchvision`、`transformers` 或 `pydantic`。

## 备注

Dots 上游推荐使用较新版本的 `transformers` 和 pydantic v2。此节点会就这些版本发出警告，而不是自动更改它们，因为意外升级可能会破坏其他 ComfyUI 节点。

音频文件 I/O 优先使用 `soundfile`。Dots 的说话人特征路径针对损坏的 torchaudio 安装提供了无 torchaudio 的回退方案，但在可用时会使用原始的 torchaudio/Kaldi fbank 路径。

## 参考

- [Dots TTS 上游仓库][dots-repo]
- [官方 Dots TTS Base 模型][hf-base]
- [官方 Dots TTS SOAR 模型][hf-soar]
- [官方 Dots TTS MF 模型][hf-mf]
- [drbaph Dots TTS Base BF16 模型][hf-base-bf16]
- [drbaph Dots TTS SOAR BF16 模型][hf-soar-bf16]
- [drbaph Dots TTS MF BF16 模型][hf-mf-bf16]
- [drbaph Dots TTS 共享公共文件][hf-common]
- [OpenAI Whisper large-v3-turbo][hf-whisper-turbo]

[dots-repo]: https://github.com/rednote-hilab/dots.tts
[hf-base]: https://huggingface.co/rednote-hilab/dots.tts-base
[hf-soar]: https://huggingface.co/rednote-hilab/dots.tts-soar
[hf-mf]: https://huggingface.co/rednote-hilab/dots.tts-mf
[hf-base-bf16]: https://huggingface.co/drbaph/dots.tts-base-bf16
[hf-soar-bf16]: https://huggingface.co/drbaph/dots.tts-soar-bf16
[hf-mf-bf16]: https://huggingface.co/drbaph/dots.tts-mf-bf16
[hf-common]: https://huggingface.co/drbaph/dots.tts-common
[hf-whisper-turbo]: https://huggingface.co/openai/whisper-large-v3-turbo

## 引用

```bibtex
@article{dotstts2026,
  title   = {dots.tts Technical Report},
  author  = {dots.tts Team},
  journal = {arXiv preprint},
  year    = {2026},
}
```

## 许可证

基于 [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) 发布。
