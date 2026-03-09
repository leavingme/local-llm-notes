"""
视频内容理解脚本
- 按间隔抽取关键帧
- 调用本地 mlx-vlm 服务分析每帧内容
- 汇总生成视频摘要
"""

import cv2
import base64
import requests
import json
import os
import tempfile
from pathlib import Path

VIDEO_PATH = "/Users/leavingme/workspace/my-video/public/Pizza Party A Command Line Program for Ordering Pizza.mp4"
MLX_VLM_URL = "http://localhost:8080/v1/chat/completions"
MODEL = "/Users/leavingme/.lmstudio/models/mlx-community/Qwen3.5-9B-MLX-4bit"

# 每隔多少秒抽一帧
INTERVAL_SECONDS = 5


def extract_frames(video_path: str, interval: int) -> list[tuple[float, str]]:
    """按时间间隔抽帧，返回 [(时间戳, base64图片), ...]"""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = total_frames / fps

    print(f"视频时长: {duration:.1f}s，每 {interval}s 抽一帧")

    frames = []
    timestamp = 0.0
    while timestamp < duration:
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        ret, frame = cap.read()
        if not ret:
            break

        # 编码为 base64 JPEG
        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        b64 = base64.b64encode(buf).decode("utf-8")
        frames.append((timestamp, b64))
        print(f"  抽帧: {timestamp:.1f}s")
        timestamp += interval

    cap.release()
    return frames


def analyze_frame(timestamp: float, b64_image: str) -> str:
    """调用 mlx-vlm 分析单帧"""
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是一个简洁的图像描述助手。只输出1-2句中文描述，不输出任何分析过程、思考步骤或多余内容。",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
                    },
                    {
                        "type": "text",
                        "text": "描述这张图片的内容。",
                    },
                ],
            }
        ],
        "max_tokens": 100,
        "stream": False,
        "enable_thinking": False,
    }

    resp = requests.post(MLX_VLM_URL, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def summarize(frame_descriptions: list[tuple[float, str]]) -> str:
    """根据各帧描述生成整体摘要"""
    timeline = "\n".join(
        f"[{t:.0f}s] {desc}" for t, desc in frame_descriptions
    )

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是一个视频内容叙述助手。根据用户提供的逐帧描述，按时间顺序完整还原视频内容，语言流畅自然，不输出分析过程。",
            },
            {
                "role": "user",
                "content": f"以下是一段视频各时间点的画面描述：\n\n{timeline}\n\n请根据以上内容，用中文写一段完整详细的视频描述，按时间顺序叙述视频的全部内容，尽量还原视频的完整过程。",
            }
        ],
        "max_tokens": 800,
        "stream": False,
        "enable_thinking": False,
    }

    resp = requests.post(MLX_VLM_URL, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def tell_story(frame_descriptions: list[tuple[float, str]], summary: str) -> str:
    """基于逐帧描述和摘要，创作一个完整连贯的故事"""
    timeline = "\n".join(
        f"[{t:.0f}s] {desc}" for t, desc in frame_descriptions
    )

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是一个擅长叙事的创意写作助手。根据视频画面信息，将内容串联成一个完整、流畅、有趣的故事，赋予画面生命和情节逻辑。",
            },
            {
                "role": "user",
                "content": (
                    f"以下是一段视频的逐帧画面描述：\n\n{timeline}\n\n"
                    f"视频整体摘要：\n{summary}\n\n"
                    "请将以上内容串联成一个完整的故事，要求：\n"
                    "1. 有起承转合，情节连贯自然\n"
                    "2. 为画面中的人物和动作赋予动机和情感\n"
                    "3. 语言生动，像一篇短篇故事\n"
                    "4. 直接输出故事正文，不需要标题或说明"
                ),
            }
        ],
        "max_tokens": 1000,
        "stream": False,
        "enable_thinking": False,
    }

    resp = requests.post(MLX_VLM_URL, json=payload, timeout=180)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def main():
    print("=" * 60)
    print("视频内容分析")
    print("=" * 60)

    # 1. 抽帧
    frames = extract_frames(VIDEO_PATH, INTERVAL_SECONDS)
    print(f"\n共抽取 {len(frames)} 帧，开始逐帧分析...\n")

    # 2. 逐帧分析
    frame_descriptions = []
    for i, (ts, b64) in enumerate(frames):
        print(f"[{i+1}/{len(frames)}] 分析 {ts:.0f}s 处画面...", end=" ", flush=True)
        desc = analyze_frame(ts, b64)
        frame_descriptions.append((ts, desc))
        print(f"✓ {desc}")

    # 3. 生成摘要
    print("\n生成整体摘要...")
    summary = summarize(frame_descriptions)

    # 4. 串成故事
    print("串联故事...")
    story = tell_story(frame_descriptions, summary)

    # 5. 输出结果
    print("\n" + "=" * 60)
    print("逐帧分析结果：")
    print("=" * 60)
    for ts, desc in frame_descriptions:
        print(f"[{ts:>4.0f}s] {desc}")

    print("\n" + "=" * 60)
    print("视频摘要：")
    print("=" * 60)
    print(summary)

    print("\n" + "=" * 60)
    print("故事：")
    print("=" * 60)
    print(story)

    # 6. 保存结果
    output = {
        "video": VIDEO_PATH,
        "frames": [{"timestamp": ts, "description": desc} for ts, desc in frame_descriptions],
        "summary": summary,
        "story": story,
    }
    output_path = Path(VIDEO_PATH).stem + "_analysis.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {output_path}")


if __name__ == "__main__":
    main()
