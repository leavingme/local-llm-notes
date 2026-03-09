import json
import time
import urllib.request

MODEL = "qwen3.5-9b-mlx"
PROMPT = "请详细介绍一下量子计算的原理和应用场景，尽量写得详细一些。"

def benchmark():
    url = "http://localhost:1234/v1/chat/completions"
    data = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT}],
        "stream": True
    }).encode()

    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    print(f"模型: {MODEL}")
    print(f"Prompt: {PROMPT}\n")
    print("-" * 50)

    token_count = 0
    start_time = None

    with urllib.request.urlopen(req) as resp:
        for line in resp:
            line = line.decode().strip()
            if not line.startswith("data:"):
                continue
            line = line[5:].strip()
            if line == "[DONE]":
                break
            try:
                chunk = json.loads(line)
            except:
                continue

            delta = chunk.get("choices", [{}])[0].get("delta", {})
            token = delta.get("content", "")
            if token:
                if start_time is None:
                    start_time = time.time()
                token_count += 1
                print(token, end="", flush=True)

    end_time = time.time()
    elapsed = end_time - (start_time or end_time)
    tps = token_count / elapsed if elapsed > 0 else 0

    print("\n" + "-" * 50)
    print(f"\n【性能统计】")
    print(f"  输出 tokens:    {token_count}")
    print(f"  生成速度:       {tps:.2f} tokens/s")
    print(f"  总耗时:         {elapsed:.2f}s")

if __name__ == "__main__":
    benchmark()
