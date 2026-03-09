import urllib.request
import json

url = "http://localhost:1234/v1/models"

try:
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read())
        models = data.get("data", [])
        if models:
            print(f"共 {len(models)} 个模型：\n")
            for m in models:
                print(f"  - {m['id']}")
        else:
            print("没有已加载的模型")
except Exception as e:
    print(f"连接失败：{e}")
    print("请确认 LM Studio 已启动本地服务器（Developer → Start Server）")
