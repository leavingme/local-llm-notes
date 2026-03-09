# Ollama 安装与使用笔记

## 环境信息

- 机器：MacBook Pro M3 Pro，36GB 内存
- 系统：macOS (Darwin 25.3.0)
- Ollama 版本：0.17.7

---

## 安装 Ollama

```bash
brew install ollama
```

安装时会同时安装 `mlx`、`mlx-c`、`python@3.14` 等依赖。

### 启动服务

```bash
brew services start ollama
```

服务启动后会在登录时自动运行，监听 `http://127.0.0.1:11434`。

### 带优化参数启动（推荐）

```bash
brew services stop ollama
OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 ollama serve &>/tmp/ollama.log &
```

- `OLLAMA_FLASH_ATTENTION=1`：启用 Flash Attention，显著提升 Prefill 速度（38 → 120 tokens/s）
- `OLLAMA_KV_CACHE_TYPE=q8_0`：KV Cache 使用 q8_0 量化，节省内存带宽

---

## 模型信息

### 当前模型

| 模型 | 参数量 | 量化 | 文件大小 |
|------|--------|------|---------|
| qwen3.5:9b | 9.7B | Q4_K_M | 6.1 GB |

### 模型存储位置

```
~/.ollama/models/blobs/sha256-dec52a44...  # 模型权重（GGUF 格式）
```

---

## 性能基准测试

测试脚本：`benchmark.py`

### 测试结果（qwen3.5:9b，M3 Pro）

| 指标 | 默认配置 | 优化配置 |
|------|---------|---------|
| 生成速度 | 15.62 tokens/s | 15.72 tokens/s |
| Prefill 速度 | 38.39 tokens/s | 120.02 tokens/s |

### 速度说明

- M3 Pro 的 GPU 为 6 核，统一内存带宽约 150 GB/s
- `ggml_metal_device_init: tensor API disabled for pre-M5 and pre-A19 devices`，M3 不支持 Metal Tensor API，有一定限制
- M3 Pro 跑 9B 模型 ~15 tokens/s 为正常水平

### 提速方案

1. 换更小模型，如 `qwen3.5:4b`，速度约翻倍
2. 换更激进量化，如 Q3_K_M，速度提升约 20%
3. 使用 MLX 后端（见下文），实测提升 59%

---

## LM Studio (MLX) vs Ollama (llama.cpp) 实测对比

测试脚本：`benchmark_lmstudio.py`

### 测试结果（qwen3.5-9b，M3 Pro，相同 Prompt）

| | Ollama (llama.cpp+Metal) | LM Studio (MLX) |
|---|---|---|
| 生成速度 | 15.62 tokens/s | **24.81 tokens/s** |
| 提升幅度 | 基准 | **+59%** |

M3 Pro 上 MLX 推理优势明显，超出预期的 20-40%。

> 原因：M3 不支持 Metal Tensor API（M5/A19 才支持），llama.cpp 受此限制；MLX 是 Apple 专为 Apple Silicon 设计的框架，有独立计算内核，不依赖 Metal Tensor API。

---

## Ollama vs mlx-lm

| | Ollama | mlx-lm / LM Studio |
|---|---|---|
| 开发者 | Ollama 公司 | Apple |
| 推理引擎 | llama.cpp + Metal | MLX 框架 |
| 使用方式 | HTTP API 服务 | Python 库/命令行/LM Studio GUI |
| 模型格式 | GGUF | safetensors |
| Apple Silicon 优化 | 通用 | 深度优化 |
| 速度（M3 Pro 实测） | 15.62 tokens/s | **24.81 tokens/s (+59%)** |

> Ollama 更方便，MLX（LM Studio）在 Mac 上更快。

mlx-lm 命令行安装与使用：

```bash
pip install mlx-lm
mlx_lm.generate --model mlx-community/Qwen2.5-7B-Instruct-4bit --prompt "你好"
```

---

## 与 LM Studio 共用模型

LM Studio 可以直接使用 Ollama 下载的 GGUF 文件，通过软链接共享，不占额外磁盘空间。

```bash
mkdir -p ~/.lmstudio/models/qwen/qwen3.5-9b
ln -s ~/.ollama/models/blobs/sha256-dec52a44569a2a25341c4e4d3fee25846eed4f6f0b936278e3a3c900bb99d37c \
  ~/.lmstudio/models/qwen/qwen3.5-9b/qwen3.5-9b-Q4_K_M.gguf
```

目录结构须为 `作者/模型名/文件.gguf` 三层，LM Studio 才能识别。

> 注意：若执行 `ollama rm qwen3.5:9b` 删除模型，LM Studio 中的软链接也会失效。

---

## 云端模型对比（kimi-code）

通过 LiteLLM 代理测试 kimi-code（Kimi K2 系列）接口速度：

| 测试方式 | 速度 | 备注 |
|---------|------|------|
| 非流式（stream: false） | ~22.8 tokens/s | 需等全部生成完才返回 |
| 流式（stream: true） | 首 token 极快，总耗时 ~12s | 体感流畅，推荐使用 |

### 本地模型 vs kimi-code 能力对比

速度相近（都约 22 tokens/s），但能力不在一个量级：

| 维度 | qwen3.5:9b（本地） | kimi-code（云端） |
|------|-------------------|-----------------|
| 参数规模 | 9.7B | 千亿级 MoE（激活 ~32B+） |
| 上下文窗口 | 8k～32k | 128k+ |
| 写简单算法 | 能完成 | 能完成，且更完整 |
| 理解大型代码库 | 容易丢失上下文 | 轻松处理 |
| 复杂架构设计 | 经常出错 | 明显更可靠 |
| 多文件重构 | 一般 | 较强 |

> 速度是"量"，能力是"质"。本地 9B 模型像初级工程师，kimi-code 像经验丰富的高级工程师。

---

## mlx-vlm 多模态推理服务

### 背景

LM Studio 在处理包含图片的 prompt 时报错：

```
Context overflow policy error: TruncateMiddle context overflow policy is not currently
supported for prompts with images.
```

同时设置 Context Length 过大（如 100000）会导致 Metal 内存超限崩溃：

```
RuntimeError: [metal::malloc] Attempting to allocate 24454103552 bytes which is greater
than the maximum allowed buffer size of 22613000192 bytes.
```

根本原因：LM Studio 的 `TruncateMiddle` 策略不支持含图片的输入；Context Length × KV Cache 占用超过 Metal 单 buffer 上限（~22.6GB）。

解决方案：改用 `mlx-vlm` 独立部署，完全脱离 LM Studio GUI。

---

### 环境准备

使用 conda 隔离环境：

```bash
conda create -n mlx-vlm python=3.11 -y
conda activate mlx-vlm
pip install mlx-vlm torch torchvision
```

### 模型

LM Studio 下载的 MLX 模型可直接复用，无需重新下载：

```
~/.lmstudio/models/mlx-community/Qwen3.5-9B-MLX-4bit/
```

### 启动服务

```bash
conda run -n mlx-vlm python -m mlx_vlm.server --port 8080
```

服务监听 `http://0.0.0.0:8080`，兼容 OpenAI API 格式。

与 LM Studio 不同，mlx-vlm 是纯命令行服务，关闭终端后可保持后台运行，不依赖 GUI。

### 调用方式

模型路径在请求体中指定：

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "~/.lmstudio/models/mlx-community/Qwen3.5-9B-MLX-4bit",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 100,
    "stream": false,
    "enable_thinking": false
  }'
```

### 关键参数

| 参数 | 说明 |
|------|------|
| `enable_thinking` | 控制 Qwen3 思考模式，设为 `false` 可关闭，避免输出冗长推理过程 |
| `--max-kv-size` | 限制 KV Cache 最大 token 数，防止 Metal 内存超限 |
| `--kv-bits` | KV Cache 量化位数，降低内存占用 |
| `--prefill-step-size` | 每步 prefill token 数，遇到 GPU 内存错误可调低（如 512/256） |

### 性能

- **生成速度**：~24 tokens/s（与 LM Studio MLX 一致）
- **峰值内存**：~6 GB（仅模型权重，不含 KV Cache 超限风险）

---

### 视频内容理解示例

脚本：`analyze_video.py`

功能：按时间间隔抽取视频关键帧，逐帧调用 mlx-vlm 分析画面内容，最终生成完整视频描述。

```bash
conda run -n mlx-vlm python analyze_video.py
```

**测试视频**：`Pizza Party - A Command Line Program for Ordering Pizza.mp4`（133s，30fps，192×144）

**逐帧分析结果**（每 10s 抽一帧）：

| 时间 | 画面描述 |
|------|---------|
| 0s | 黑色背景标题页，白字"Pizza Party / Example Video!" |
| 10s | 终端窗口，执行命令 `./pizza_party` |
| 20s~40s | 命令行帮助信息，展示参数选项（用户名、密码等） |
| 50s~70s | 披萨配料选择菜单（洋葱、青椒、培根、牛肉等） |
| 80s~100s | 模拟订购流程，登录、下单、订单处理日志 |
| 110s | 一名男子背对镜头走下昏暗楼梯 |
| 120s~130s | 保鲜膜包裹的食物特写，双手操作纸盒的镜头 |

**完整视频描述**：

视频以"Pizza Party"标题页开场，随后进入电脑终端演示。用户执行 `./pizza_party` 脚本，程序依次展示命令行参数说明、披萨配料选择菜单（含洋葱、青椒、培根、牛肉等），并模拟完整的在线订购流程（登录、下单、处理日志）。视频后半段切换至现实场景：一名男子走下昏暗楼梯，随后镜头对准保鲜膜包裹的食物和手持纸盒的特写，呈现出"披萨派对"命令行程序演示与实际派对现场的交替叙事。

---

## 常用命令

```bash
ollama list              # 查看本地模型
ollama pull <model>      # 下载模型
ollama rm <model>        # 删除模型
ollama ps                # 查看运行中的模型
brew services start ollama   # 启动服务
brew services stop ollama    # 停止服务
```
