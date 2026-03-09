---
theme: default
title: 本地 LLM 推理探索
info: |
  Ollama / LM Studio / mlx-vlm 安装、性能对比与视频理解实验
  MacBook Pro M3 Pro 36GB
highlighter: shiki
transition: slide-left
mdc: true
---

# 本地 LLM 推理探索

Ollama · LM Studio · mlx-vlm

<div class="pt-12 text-gray-400">
  MacBook Pro M3 Pro · 36GB 内存 · macOS Darwin 25.3.0
</div>

---

# 目标

在本地 Mac 上跑大语言模型，探索：

<v-clicks>

- 🚀 **速度**：本地推理能跑多快？
- 🔧 **工具对比**：Ollama vs LM Studio vs mlx-vlm
- 🖼️ **多模态**：本地模型能理解图片和视频吗？
- ☁️ **云端对比**：本地 vs 云端（kimi-code）差距有多大？

</v-clicks>

---
layout: two-cols
---

# 环境信息

**硬件**

- MacBook Pro M3 Pro
- 36GB 统一内存
- GPU 6 核，内存带宽 ~150 GB/s

**软件**

- macOS Darwin 25.3.0
- Ollama 0.17.7
- LM Studio（MLX 后端）
- mlx-vlm 0.4.0

::right::

# 模型

**本地模型**

| 模型 | 参数 | 量化 | 大小 |
|------|------|------|------|
| qwen3.5:9b | 9.7B | Q4_K_M | 6.1 GB |
| Qwen3.5-9B-MLX-4bit | 9.7B | 4bit | ~5 GB |

**云端模型（通过 LiteLLM）**

- kimi-code (Kimi K2 系列)
- deepseek-chat / deepseek-reasoner
- tencent-kimi-k2.5

---

# 第一步：安装 Ollama

```bash
brew install ollama
brew services start ollama
```

服务监听 `http://127.0.0.1:11434`

<div class="mt-6">

**带优化参数启动（推荐）**

```bash
OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 ollama serve
```

| 参数 | 效果 |
|------|------|
| `OLLAMA_FLASH_ATTENTION=1` | Prefill 速度 38 → **120 tokens/s** |
| `OLLAMA_KV_CACHE_TYPE=q8_0` | KV Cache 量化，节省内存带宽 |

</div>

---

# Ollama 性能基准

测试模型：`qwen3.5:9b`（Q4_K_M，M3 Pro）

<div class="grid grid-cols-2 gap-8 mt-6">
<div>

**生成速度**

| 配置 | 速度 |
|------|------|
| 默认 | 15.62 tokens/s |
| 优化后 | 15.72 tokens/s |

生成速度提升不明显 😐

</div>
<div>

**Prefill 速度**

| 配置 | 速度 |
|------|------|
| 默认 | 38.39 tokens/s |
| 优化后 | **120.02 tokens/s** |

Prefill 提升显著 🚀

</div>
</div>

<div class="mt-6 text-gray-400 text-sm">

> M3 不支持 Metal Tensor API（M5/A19 才支持），llama.cpp 受此限制，生成速度约 15 tokens/s 为正常水平

</div>

---
layout: two-cols
---

# LM Studio (MLX) 对比

同一模型，同一 Prompt，不同后端：

| | Ollama | LM Studio |
|---|---|---|
| 推理引擎 | llama.cpp + Metal | **MLX** |
| 生成速度 | 15.62 t/s | **24.81 t/s** |
| 提升 | 基准 | **+59%** |

<div class="mt-4">

**为什么 MLX 更快？**

- M3 不支持 Metal Tensor API
- llama.cpp 受此限制
- MLX 是 Apple 专为 Apple Silicon 设计，有独立计算内核，不依赖 Metal Tensor API

</div>

::right::

<div class="pl-8">

# 工具选择建议

**Ollama**
- ✅ 安装简单，一行命令
- ✅ 系统服务，后台常驻
- ✅ 丰富的模型库
- ❌ M3 上速度受限

**LM Studio**
- ✅ MLX 后端，速度 +59%
- ✅ 图形界面直观
- ❌ 依赖 GUI，关窗即停
- ❌ 多模态有 bug

**mlx-vlm**
- ✅ 纯命令行，后台运行
- ✅ 原生多模态支持
- ✅ 速度与 LM Studio 相当

</div>

---

# 云端模型测试：kimi-code

通过 **LiteLLM** 代理统一访问云端模型

```bash
# LiteLLM 运行在 Podman 容器中
podman ps  # → litellm  Up  0.0.0.0:4000->4000/tcp
```

<div class="grid grid-cols-2 gap-8 mt-6">
<div>

**速度测试**

| 方式 | 速度 |
|------|------|
| 非流式 | ~22.8 tokens/s |
| 流式首 token | 极快（<1s） |
| 流式总耗时 | ~12s |

</div>
<div>

**结论**

速度与本地 9B 模型相近（~22 t/s）

但**能力不在一个量级** ⬇️

</div>
</div>

---

# 本地 vs 云端：能力对比

速度相近，但质量差距巨大

| 维度 | qwen3.5:9b（本地） | kimi-code（云端） |
|------|-------------------|-----------------|
| 参数规模 | 9.7B | 千亿级 MoE（激活 ~32B+） |
| 上下文窗口 | 8k～32k | **128k+** |
| 写简单算法 | ✅ 能完成 | ✅ 更完整 |
| 理解大型代码库 | ❌ 容易丢失上下文 | ✅ 轻松处理 |
| 复杂架构设计 | ❌ 经常出错 | ✅ 明显更可靠 |

<div class="mt-6 text-center text-lg">

> 速度是**"量"**，能力是**"质"**
> 本地 9B 模型 ≈ 初级工程师，kimi-code ≈ 高级工程师

</div>

---

# LM Studio 多模态踩坑

遇到两个问题：

<v-clicks>

**问题一：Context Overflow 报错**
```
Context overflow policy error: TruncateMiddle context overflow policy
is not currently supported for prompts with images.
```
原因：`TruncateMiddle` 策略不支持含图片的输入

**问题二：Metal 内存超限崩溃**
```
RuntimeError: [metal::malloc] Attempting to allocate 24454103552 bytes
which is greater than the maximum allowed buffer size of 22613000192 bytes.
```
原因：Context Length 设为 100000，KV Cache 占用 ~14GB，加上模型权重超出 Metal 22.6GB 上限

**解决方案：改用 mlx-vlm 独立部署** ✅

</v-clicks>

---

# 解决方案：mlx-vlm

用 conda 隔离环境，脱离 LM Studio GUI：

```bash
# 创建环境
conda create -n mlx-vlm python=3.11 -y
conda activate mlx-vlm
pip install mlx-vlm torch torchvision

# 启动服务（直接复用 LM Studio 已下载的模型）
python -m mlx_vlm.server --port 8080
```

<div class="grid grid-cols-2 gap-8 mt-4">
<div>

**关键参数**

```json
{
  "model": "~/.lmstudio/models/mlx-community/...",
  "enable_thinking": false,
  "stream": true
}
```

`enable_thinking: false` 可关闭 Qwen3 思考模式，避免输出冗长推理过程

</div>
<div>

**性能**

- 生成速度：**~24 tokens/s**
- 峰值内存：**~6 GB**
- 首 token 延迟：极低
- 多模态：原生支持 ✅

</div>
</div>

---

# 视频内容理解实验

用 `mlx-vlm` 分析视频内容，三步流程：

```
抽帧 → 逐帧分析 → 生成完整描述 + 故事
```

<div class="mt-4">

**测试视频**：Pizza Party - A Command Line Program (133s, 30fps, 192×144)

**脚本流程（analyze_video.py）**

```python
frames = extract_frames(video, interval=5)   # 每 5s 抽一帧，共 27 帧
for frame in frames:
    desc = analyze_frame(frame)              # mlx-vlm 分析画面
summary = summarize(frame_descriptions)      # 生成视频摘要
story   = tell_story(frame_descriptions, summary)  # 串成故事
```

</div>

---

# 视频分析：逐帧结果

| 时间 | 画面 |
|------|------|
| 0s | 标题页："Pizza Party / Example Video!" |
| 5s | 男子坐在电脑前，专注看屏幕 |
| 10s~15s | 终端执行 `./pizza_party` 和 `-help` |
| 20s~40s | 命令行帮助文档，参数说明（username/password...） |
| 45s~70s | 配料选择菜单（洋葱、青椒、培根、牛肉、烤鸡...） |
| 85s | 订单确认："medium thin pizza with mushrooms $12.48" |
| 90s~100s | 用户 fruminator 成功下单，订单处理日志 |
| 105s~110s | 场景切换，昏暗房间，男子走下楼梯 |
| 115s | 红衣男子抱着黑色物体走廊中 |
| 120s~130s | 保鲜膜包裹的食物，双手拿老式相机 |

---

# 视频分析：AI 生成的故事

<div class="text-sm leading-relaxed">

"披萨派对"的序幕在一片死寂的黑暗中拉开，只有两行刺眼的白色英文标题——"Pizza Party"与"Example Video!"，像是一份来自旧时代的邀请函，突兀地宣告着今晚的特别仪式。

屏幕前的男子屏住了呼吸。随着他指尖在键盘上轻轻敲击，一行绿色的终端命令如闪电般划出：`./pizza_party -help`。这不仅仅是一条指令，更是他向那个神秘系统发出的第一声问候。

程序读懂了他的意图。配料菜单徐徐展开——洋葱的辛辣、青椒的清脆、蘑菇的鲜香。终于，屏幕中央弹出一行文字：**中号薄底披萨，$12.48**。订单生成，虚拟世界的交易完美闭环。

然而，高潮不在屏幕之中，而在屏幕之外。男子站起身，沿着狭窄的楼梯走向现实。透明塑料膜包裹的外卖盒赫然出现——那是刚才那行绿色代码具象化的产物，是数字世界对物理世界的一次深情拥抱。

他拿起老式相机，按下快门。**孤独的代码化作了温暖的相聚。**"

</div>

---
layout: two-cols
---

# 总结

**速度排名（M3 Pro）**

| 方案 | 速度 |
|------|------|
| mlx-vlm / LM Studio | **~24 t/s** |
| kimi-code 云端 | ~22 t/s |
| Ollama（优化） | ~15 t/s |

**能力排名**

kimi-code >>> 本地 9B 模型

::right::

<div class="pl-8">

**关键结论**

<v-clicks>

- M3 Pro 上 **MLX 比 llama.cpp 快 59%**
- `enable_thinking: false` 可关闭 Qwen3 思考模式
- mlx-vlm 可直接复用 LM Studio 模型，无需重新下载
- 本地模型适合**隐私场景**，云端模型适合**复杂任务**
- 视频理解：抽帧 + VLM 逐帧分析，效果出乎意料地好

</v-clicks>

</div>

---
layout: center
---

# 代码和笔记

GitHub 仓库：

**https://github.com/leavingme/local-llm-notes**

<div class="mt-8 text-gray-400">

包含：README · benchmark.py · analyze_video.py

</div>
