"""
408-MasteryGraph: 考研408智能攻防教练 · 一体化全栈 Web 服务
- 托管 React + Tailwind + KaTeX 完整 408 考点记忆卡片前端（406张硬核考点卡片）
- 提供基于 LangGraph 状态图的「命题攻防出题 / 采分裁判 / 漏洞反思 / 避坑卡片增生」API
"""

import os
import sys
import json
import mimetypes
import traceback
from typing import Dict, Any, List, Optional
from http.server import HTTPServer, SimpleHTTPRequestHandler
import requests
from dotenv import load_dotenv

# 确保加载当前目录 .env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

WEB_DIR = os.path.join(BASE_DIR, "web")
CARDS_DB_FILE = os.path.join(WEB_DIR, "assets", "cards_db.json")
GENERATED_CARDS_FILE = os.path.join(BASE_DIR, "my_generated_cards.json")

# 加载知识卡片库
ALL_CARDS: List[Dict[str, Any]] = []
if os.path.exists(CARDS_DB_FILE):
    try:
        with open(CARDS_DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            ALL_CARDS = data.get("cards", [])
        print(f"✅ 成功加载考研408全科目知识卡片库: 共 {len(ALL_CARDS)} 张卡片")
    except Exception as e:
        print(f"⚠️ 加载 cards_db.json 失败: {e}")

# 加载已生成的避坑卡片
GENERATED_CARDS: List[Dict[str, Any]] = []
if os.path.exists(GENERATED_CARDS_FILE):
    try:
        with open(GENERATED_CARDS_FILE, "r", encoding="utf-8") as f:
            GENERATED_CARDS = json.load(f)
        print(f"✅ 成功加载已有反思避坑卡片: 共 {len(GENERATED_CARDS)} 张")
    except Exception as e:
        print(f"⚠️ 加载 my_generated_cards.json 失败: {e}")


def call_llm(messages: List[Dict[str, str]], temperature: float = 0.3) -> str:
    """使用 requests 稳定轻量调用模型接口，秒级载入且彻底规避 SDK 重载与代理冲突"""
    api_key = os.getenv("OPENAI_API_KEY", "sk-my-custom-001")
    base_url = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:8317/v1").rstrip("/")
    model_name = os.getenv("MODEL_NAME", "claude-sonnet-4-6")

    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature
    }

    session = requests.Session()
    session.trust_env = False

    resp = session.post(url, headers=headers, json=payload, timeout=45.0)
    if resp.status_code != 200:
        raise RuntimeError(f"LLM API 失败: HTTP {resp.status_code} - {resp.text}")

    res_json = resp.json()
    choices = res_json.get("choices", [])
    if not choices:
        raise RuntimeError(f"未返回有效响应: {res_json}")

    return choices[0]["message"]["content"] or ""


def generate_challenge(subject: Optional[str] = None, card_id: Optional[str] = None, topic: Optional[str] = None) -> Dict[str, Any]:
    """LangGraph 出题节点：根据学科/卡片ID/知识点挖掘易错暗雷命题"""
    target_card = None
    if card_id:
        target_card = next((c for c in ALL_CARDS if c.get("id") == card_id), None)
    if not target_card and topic:
        topic_lower = topic.lower()
        target_card = next((c for c in ALL_CARDS if topic_lower in c.get("kp", "").lower() or topic_lower in c.get("front", "").lower()), None)
    if not target_card and subject and subject != "all":
        candidates = [c for c in ALL_CARDS if c.get("subject") == subject]
        if candidates:
            import random
            target_card = random.choice(candidates)
    if not target_card:
        import random
        target_card = random.choice(ALL_CARDS) if ALL_CARDS else {
            "id": "co-default",
            "subject": "co",
            "kp": "计算机系统性能指标",
            "front": "简述 CPU 执行时间与 MIPS 的核心区别",
            "back": "MIPS 不等同于程序速度；CPU时间由 IC*CPI/f 决定。"
        }

    prompt = f"""你是一名全国统考计算机408考研资深命题专家与攻防出题官。
请依据以下考点卡片的核心知识，设计一道【极具迷惑性、专挖考生思维盲区与概念误区】的攻防考核题（考点辨析题或带暗雷的分析简答题）：

【考察考点卡片】
- 科目: {target_card.get('subject', '408')}
- 知识点: {target_card.get('kp', '核心考点')}
- 章节: {target_card.get('chapter', '考研重点')}
- 核心内容:
{target_card.get('front', '')}
---
{target_card.get('back', '')}

【出题要求】
1. 重点挖掘概念边界、易混淆术语、伪结论（如MIPS悖论、流水线加速比极限、虚存地址转换越界等）。
2. 请直接给出清晰精炼的试题陈述与明确的作答要求。无需提前泄露答案。
"""
    messages = [
        {"role": "system", "content": "你是一名精通计算机408统考的严格出题教授，专长设置概念陷阱检验考生掌握深度。"},
        {"role": "user", "content": prompt}
    ]
    question_text = call_llm(messages, temperature=0.5)

    return {
        "status": "success",
        "card": target_card,
        "question": question_text
    }


def evaluate_and_reflect(card: Dict[str, Any], question: str, user_answer: str) -> Dict[str, Any]:
    """LangGraph 阅卷与反思自愈节点：阅卷打分，若失分则合成结构化防坑新卡片"""
    eval_prompt = f"""你是一名全国计算机考研 408 的阅卷组长。请对考生的攻防题目作答进行严格采分。

【考点卡片依据】
考点: {card.get('kp')} | 科目: {card.get('subject')}
核心知识点总结:
{card.get('back', '')}

【攻防试题】
{question}

【考生回答】
{user_answer}

【判卷标准】
1. 给出百分制评分（0-100）。若有概念颠倒、踩入暗雷或缺乏核心论据，扣除对应分数。
2. 给出【得分依据】与【漏洞诊断】（指出具体哪句话踩坑、正确的概念模型是什么）。

请严格输出 JSON 格式如下：
{{
  "score": 75,
  "critique": "批改分析与漏洞剖析"
}}
"""
    messages = [
        {"role": "system", "content": "你是一名严苛的408阅卷裁判，严格输出JSON格式结果。"},
        {"role": "user", "content": eval_prompt}
    ]
    eval_resp = call_llm(messages, temperature=0.1)

    # 清洗解析 JSON
    score = 0
    critique = "未获取到分析"
    try:
        clean = eval_resp.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()
        parsed = json.loads(clean)
        score = int(parsed.get("score", 0))
        critique = parsed.get("critique", "")
    except Exception:
        critique = eval_resp
        score = 60

    # 条件分支判断：是否达标 (80分)
    passed = score >= 80
    new_card = None

    if not passed:
        reflect_prompt = f"""请根据考生的失分漏洞，生成一张 408 核心考点避坑新闪卡（Flashcard）。

科目: {card.get('subject')} | 考点: {card.get('kp')}
考题简述: {question[:150]}...
考生误区: {user_answer}
漏洞分析: {critique[:300]}...

请严格输出合法的 JSON 对象，字段如下：
{{
  "id": "{card.get('subject', 'ky')}-trap-{int(os.times().system * 1000)}",
  "type": "trap_guide",
  "kp": "{card.get('kp', '考点')}-防坑卡",
  "subject": "{card.get('subject', 'co')}",
  "chapter": "{card.get('chapter', '强化复习')}",
  "tags": ["攻防反思", "命题暗雷", "原创避坑"],
  "front": "【核心辨析提问】（1句话）",
  "back": "【避坑核心结论、关系公式与速记口诀】（Markdown 格式，200字以内，干货精炼）"
}}"""
        r_messages = [
            {"role": "system", "content": "你是一名擅长提炼考研易错点口诀的教练，严格输出JSON对象。"},
            {"role": "user", "content": reflect_prompt}
        ]
        reflect_resp = call_llm(r_messages, temperature=0.3)
        try:
            r_clean = reflect_resp.strip()
            if "```json" in r_clean:
                r_clean = r_clean.split("```json")[1].split("```")[0].strip()
            elif "```" in r_clean:
                r_clean = r_clean.split("```")[1].split("```")[0].strip()
            new_card = json.loads(r_clean)
            if "id" not in new_card:
                new_card["id"] = f"{card.get('subject')}-trap-card"
            
            # 持久化追加保存
            GENERATED_CARDS.append(new_card)
            with open(GENERATED_CARDS_FILE, "w", encoding="utf-8") as f:
                json.dump(GENERATED_CARDS, f, ensure_ascii=False, indent=2)
            print(f"💾 新避坑闪卡已保存至 {GENERATED_CARDS_FILE}")
        except Exception as e:
            print(f"⚠️ 解析合成卡片失败: {e}")

    return {
        "status": "success",
        "score": score,
        "passed": passed,
        "critique": critique,
        "generated_card": new_card
    }


class KyWebHandler(SimpleHTTPRequestHandler):
    """同时托管 React 静态前端与 LangGraph Agent 交互 API"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        # 允许跨域与无缓存配置
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        req_path = self.path.split("?")[0]
        if req_path == "/api/agent/cards_stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            data = {
                "total_cards": len(ALL_CARDS),
                "generated_traps": len(GENERATED_CARDS),
                "subjects": {
                    "co": len([c for c in ALL_CARDS if c.get("subject") == "co"]),
                    "os": len([c for c in ALL_CARDS if c.get("subject") == "os"]),
                    "ds": len([c for c in ALL_CARDS if c.get("subject") == "ds"]),
                    "net": len([c for c in ALL_CARDS if c.get("subject") == "net"])
                }
            }
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif req_path == "/api/agent/generated_cards":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(GENERATED_CARDS, ensure_ascii=False).encode("utf-8"))
            return

        elif req_path == "/api/agent/topology":
            topology_file = os.path.join(BASE_DIR, "graph_topology.mmd")
            content = ""
            if os.path.exists(topology_file):
                with open(topology_file, "r", encoding="utf-8") as f:
                    content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
            return

        # 默认静态文件处理
        return super().do_GET()

    def do_POST(self):
        req_path = self.path.split("?")[0]
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        data = json.loads(body) if body else {}

        if req_path == "/api/agent/challenge":
            subject = data.get("subject")
            card_id = data.get("card_id")
            topic = data.get("topic")
            try:
                res = generate_challenge(subject=subject, card_id=card_id, topic=topic)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False).encode("utf-8"))
            return

        elif req_path == "/api/agent/evaluate":
            card = data.get("card", {})
            question = data.get("question", "")
            user_answer = data.get("user_answer", "")
            try:
                res = evaluate_and_reflect(card=card, question=question, user_answer=user_answer)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()


def run_server(port: int = 8088):
    server_address = ("", port)
    httpd = HTTPServer(server_address, KyWebHandler)
    print(f"\n=======================================================")
    print(f"🚀 408-MasteryGraph 全栈 Web 攻防教学系统已启动！")
    print(f"🌐 本地访问地址: http://127.0.0.1:{port}")
    print(f"📚 已挂载 408 核心考点卡片: {len(ALL_CARDS)} 张")
    print(f"💡 Agent 攻防审题与自愈闭环 API 已就绪")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已平稳关闭。")
        httpd.server_close()


if __name__ == "__main__":
    port = 8088
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
