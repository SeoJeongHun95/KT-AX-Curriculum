# -*- coding: utf-8 -*-
"""samples.json 의 입력을 순서대로 서비스에 보내고 결과를 출력합니다.

먼저 다른 터미널에서 `fastapi dev app.py` 로 서비스를 띄운 뒤 실행합니다.
실행: python run_samples.py          (포트를 바꾸려면 python run_samples.py 8011)
"""

import json
import sys
from pathlib import Path

import httpx

PORT = sys.argv[1] if len(sys.argv) > 1 else "8000"
BASE = f"http://127.0.0.1:{PORT}"

samples = json.loads(Path(__file__).with_name("samples.json").read_text(encoding="utf-8"))

health = httpx.get(f"{BASE}/healthz", timeout=10)
print(f"[healthz] {health.status_code} {health.text}")

for i, payload in enumerate(samples, 1):
    response = httpx.post(f"{BASE}/ask", json=payload, timeout=120)
    print(f"\n[{i}] 요청: {payload['question']}")
    print(f"[{i}] 상태: {response.status_code}")
    print(f"[{i}] 응답: {response.json()}")
