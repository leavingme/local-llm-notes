import json
import time
import urllib.request

MODEL = "qwen3.5:9b"
PROMPT = "请详细介绍一下量子计算的原理和应用场景，尽量写得详细一些。"

def benchmark():
    url = "http://localhost:11434/api/generate"
    data = json.dumps({
        "model": MODEL,
        "prompt": PROMPT,
        "stream": True
    }).encode()

    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    print(f"模型: {MODEL}")
    print(f"Prompt: {PROMPT}\n")
    print("-" * 50)

    token_count = 0
    start_time = None
    full_response = []

    with urllib.request.urlopen(req) as resp:
        for line in resp:
            line = line.strip()
            if not line:
                continue
            chunk = json.loads(line)

            if chunk.get("done") is False:
                token = chunk.get("response", "")
                if token:
                    if start_time is None:
                        start_time = time.time()
                    full_response.append(token)
                    token_count += 1
                    print(token, end="", flush=True)

            elif chunk.get("done") is True:
                end_time = time.time()
                # 优先使用 ollama 返回的统计数据
                eval_count = chunk.get("eval_count", token_count)
                eval_duration_ns = chunk.get("eval_duration", 0)
                prompt_eval_count = chunk.get("prompt_eval_count", 0)
                prompt_eval_duration_ns = chunk.get("prompt_eval_duration", 0)

                elapsed = end_time - (start_time or end_time)

                print("\n" + "-" * 50)
                print(f"\n【性能统计】")
                print(f"  输入 tokens:    {prompt_eval_count}")
                print(f"  输出 tokens:    {eval_count}")

                if eval_duration_ns > 0:
                    tps = eval_count / (eval_duration_ns / 1e9)
                    print(f"  生成速度:       {tps:.2f} tokens/s  (ollama统计)")
                else:
                    tps = token_count / elapsed if elapsed > 0 else 0
                    print(f"  生成速度:       {tps:.2f} tokens/s  (本地计时)")

                if prompt_eval_duration_ns > 0:
                    prefill_tps = prompt_eval_count / (prompt_eval_duration_ns / 1e9)
                    print(f"  Prefill 速度:   {prefill_tps:.2f} tokens/s")

                total_duration_ns = chunk.get("total_duration", 0)
                if total_duration_ns > 0:
                    print(f"  总耗时:         {total_duration_ns / 1e9:.2f}s")

if __name__ == "__main__":
    benchmark()
