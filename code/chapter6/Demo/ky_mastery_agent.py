"""
408-MasteryGraph: 考研408智能攻防审题与动态卡片自省教练
基于 LangGraph 状态图与本地 408 知识卡片库 (all_cards_data.json) 构建的自适应学习闭环智能体。
"""

import os
import sys
import json
import random
from typing import TypedDict, Optional, List, Dict, Any
from dotenv import load_dotenv

# 加载环境变量
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, ".env"), override=True)
load_dotenv(override=False)

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

# 卡片数据库路径
CARD_DB_PATH = os.path.abspath(
    os.path.join(
        current_dir,
        r"..\..\..\..\GenericAgent\GenericAgent\temp\projects\工具开发\ky_cards_rebuild\all_cards_data.json"
    )
)
OUTPUT_CARD_PATH = os.path.join(current_dir, "my_generated_cards.json")


class ExamState(TypedDict):
    """LangGraph 全局状态定义"""
    subject: str                    # 科目: os / co / net / ds / all
    query_topic: str                # 指定知识点/考点关键词
    selected_card: Dict[str, Any]   # 从库中检索到的底座知识卡片
    question: str                   # 命题器生成的变式攻防试题
    rubric: str                     # 采分点与命题暗雷解析
    user_answer: str                # 考生作答
    score: int                      # 得分 (0-100)
    critique: str                   # 漏洞归因与扣分详评
    reflection_card: Optional[Dict[str, Any]]  # 若失分，反思合成的新卡片
    completed: bool                 # 是否完成全部流程


import requests

def call_llm(messages: List[Dict[str, str]], temperature: float = 0.3) -> str:
    """使用 requests 稳定轻量调用模型接口，秒级载入且彻底规避 SDK 重载与代理冲突"""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:8317/v1").rstrip("/")
    model_name = os.getenv("MODEL_NAME", "gemini-3.8-flash-high")

    if not api_key:
        raise ValueError("请检查 .env 中是否配置了 OPENAI_API_KEY")

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

    # 显式禁止 requests 走系统冲突代理以保障直连 127.0.0.1
    session = requests.Session()
    session.trust_env = False
    
    print(f"      📡 [LLM Request] 正在请求 {model_name} (URL: {url})...")
    resp = session.post(url, headers=headers, json=payload, timeout=45.0)
    print(f"      ✅ [LLM Response] HTTP {resp.status_code}")
    if resp.status_code != 200:
        raise RuntimeError(f"LLM API 调用失败: HTTP {resp.status_code} - {resp.text}")

    res_json = resp.json()
    choices = res_json.get("choices", [])
    if not choices:
        raise RuntimeError(f"LLM API 未返回有效内容: {res_json}")

    return choices[0]["message"]["content"] or ""


# ==================== 状态机节点定义 ====================

def retrieve_card_node(state: ExamState) -> Dict[str, Any]:
    """节点 1: 知识库检索节点 - 从 406 张 408 卡片库中抽选核心考点"""
    print("\n🔍 [Node 1: CardRetriever] 正在检索 408 核心考点库...")
    
    if not os.path.exists(CARD_DB_PATH):
        print(f"⚠️ 未找到本地卡片库: {CARD_DB_PATH}，使用内置经典备选卡片")
        card = {
            "id": "co-pipeline-hazard-demo",
            "subject": "co",
            "chapter": "中央处理器-指令流水线",
            "kp": "流水线冒险与数据相关",
            "front": "简述指令流水线中的三种冒险类型及解决 RAW 相关的方法。",
            "back": "结构冒险（资源冲突）、数据冒险（RAW/WAR/WAW相关）、控制冒险（分支预测失败）。解决RAW：转发/旁路技术、插入NOP指令/流水线气泡、编译器指令调度优化。"
        }
        return {"selected_card": card}

    with open(CARD_DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    cards = data.get("cards", [])
    subject = state.get("subject", "all").lower()
    query = state.get("query_topic", "").strip().lower()

    # 过滤科目与关键词
    candidates = []
    for c in cards:
        match_subj = (subject == "all" or c.get("subject", "").lower() == subject)
        match_query = True
        if query:
            match_query = (query in c.get("kp", "").lower() or 
                           query in c.get("front", "").lower() or 
                           query in c.get("chapter", "").lower())
        if match_subj and match_query:
            candidates.append(c)

    if not candidates:
        print(f"⚠️ 未匹配到具体考点，从全量库中随机挑选优质考点卡片")
        candidates = cards

    chosen = random.choice(candidates)
    print(f"📌 已命中卡片: [{chosen.get('subject', '').upper()}] 《{chosen.get('chapter', '')}》")
    print(f"   考点 (kp): {chosen.get('kp', 'N/A')}")
    print(f"   原始题面: {chosen.get('front', '')[:60]}...")
    
    return {"selected_card": chosen}


def adversarial_examiner_node(state: ExamState) -> Dict[str, Any]:
    """节点 2: 攻防出题器 - 依托原卡片，设计含有命题人陷阱的攻防试题"""
    print("\n⚔️ [Node 2: AdversarialExaminer] 攻防命题官正在构思高难度辨析陷阱...")
    card = state["selected_card"]

    prompt = f"""你是一名极其严谨、刁钻的计算机考研 408 命题组骨干。
请基于以下底座知识卡片，原创一道具有针对性的变式考查题。

【底座知识卡片】
学科: {card.get('subject')} | 章节: {card.get('chapter')}
核心考点: {card.get('kp')}
考点正面(Front): {card.get('front')}
考点背面解析(Back): {card.get('back')}

【命题规范】
1. 绝对不要直接照抄原卡片题面，要改为情境设问、概念陷阱辨析题或带边界条件的计算题。
2. 必须包含一个命题人常见的挖坑暗雷（如：容易混淆的单位、主频与周期的倒数关系、逻辑块与物理块、前序后序与栈溢出边界等）。
3. 请以 JSON 格式输出两个字段：
   - "question": 给考生的试题文本（清晰严谨，排版清晰）。
   - "rubric": 采分点标准、标准答案及暗雷拆解（此部分暂不展示给考生）。

仅输出合法 JSON，格式为：
{{
  "question": "试题内容...",
  "rubric": "采分标准与暗雷分析..."
}}
"""
    content = call_llm([
        {"role": "system", "content": "你是考研408命题教授，严格输出JSON"},
        {"role": "user", "content": prompt}
    ]).strip()
    
    # 提取 JSON
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        data = json.loads(content)
        question = data.get("question", "")
        rubric = data.get("rubric", "")
    except Exception:
        question = content
        rubric = "严格依照卡片知识要点评判。"

    print(f"\n==================== [今日 408 攻防挑战试题] ====================")
    print(question)
    print(f"=================================================================\n")

    return {"question": question, "rubric": rubric}


def wait_for_answer_node(state: ExamState) -> Dict[str, Any]:
    """节点 3: 交互/答题节点 - 采集考生作答"""
    # 如果状态中已有预置答题（用于自动化评估测试），直接使用
    existing_ans = state.get("user_answer", "")
    if existing_ans:
        print(f"📝 [Node 3: CandidateAnswer] 监测到自动注入作答: {existing_ans}")
        return {"user_answer": existing_ans}

    print("📝 [Node 3: CandidateAnswer] 请在下方输入你的作答（支持单行/回车提交，输入 exit 退出）：")
    try:
        user_input = input(">> ").strip()
    except EOFError:
        user_input = "略知一二，但细节不太肯定。"

    if not user_input or user_input.lower() == "exit":
        user_input = "考生弃权未作答。"

    return {"user_answer": user_input}


def evaluate_node(state: ExamState) -> Dict[str, Any]:
    """节点 4: 采分裁判节点 - 严格按采分点核验，挖掘漏题漏洞与暗雷掉坑情况"""
    print("\n⚖️ [Node 4: AnswerJudge] 阅卷裁判正在依照踩分点细目严审答案...")

    prompt = f"""你是一名无情的 408 统考阅卷组长。请对照标准和采分点，对考生的作答进行逐点核验。

【原题与考点暗雷】
{state['question']}

【命题人标准解析与采分点】
{state['rubric']}

【考生实际作答】
{state['user_answer']}

【阅卷任务】
1. 给出百分制综合得分 score（0 到 100 整数）。如果考生踩中暗雷陷阱或核心概念含糊，必须扣分！
2. 给出 critique：指出答对的踩分点、遗漏的致命盲区、以及命题暗雷的辨析。

请严格输出 JSON：
{{
  "score": 75,
  "critique": "详细的阅卷点评与失分诊断..."
}}
"""
    content = call_llm([
        {"role": "system", "content": "你是408严格阅卷老师，严格输出JSON"},
        {"role": "user", "content": prompt}
    ]).strip()
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        data = json.loads(content)
        score = int(data.get("score", 60))
        critique = data.get("critique", "")
    except Exception:
        score = 60
        critique = content

    print(f"📊 得分评定: {score} 分")
    print(f"📝 裁判点评: {critique}\n")

    return {"score": score, "critique": critique}


def reflect_and_synthesize_node(state: ExamState) -> Dict[str, Any]:
    """节点 5: 反思与新卡片合成节点 - 针对失分漏洞，生成高质量结构化避坑新卡片"""
    print("\n💡 [Node 5: CardSynthesizer] 检测到作答未达满分，触发反思闭环！正在合成专属避坑卡片...")
    base_card = state["selected_card"]

    prompt = f"""请根据考生的失分漏洞，生成一张 408 核心考点避坑新闪卡（Flashcard）。

科目: {base_card.get('subject')} | 考点: {base_card.get('kp')}
考题简述: {state['question'][:150]}...
考生误区: {state['user_answer']}
漏洞分析: {state['critique'][:300]}...

请严格输出合法的 JSON 对象，字段如下：
{{
  "id": "{base_card.get('subject')}-trap-card",
  "type": "trap_guide",
  "kp": "{base_card.get('kp')}-防坑卡",
  "subject": "{base_card.get('subject')}",
  "chapter": "{base_card.get('chapter')}",
  "tags": ["攻防反思", "命题暗雷", "原创避坑"],
  "front": "【核心辨析提问】（1句话）",
  "back": "【避坑核心结论、关系公式与速记口诀】（Markdown 格式，200字以内，干货精炼）"
}}"""
    content = call_llm([
        {"role": "system", "content": "严格输出规范JSON闪卡对象"},
        {"role": "user", "content": prompt}
    ]).strip()
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        card_obj = json.loads(content)
    except Exception:
        card_obj = {
            "id": f"{base_card.get('subject')}-trap-{random.randint(100, 999)}",
            "type": "trap_guide",
            "kp": f"{base_card.get('kp')}-防坑总结",
            "subject": base_card.get("subject"),
            "chapter": base_card.get("chapter"),
            "tags": ["攻防反思", "命题暗雷"],
            "front": "本次攻防测验暴露的核心误区？",
            "back": state["critique"]
        }

    # 沉淀保存到本地
    save_generated_card(card_obj)
    print("✅ 专属反思卡片已生成并持久化沉淀到: my_generated_cards.json")
    print(f"   [新卡片正面]: {card_obj.get('front')}")

    return {"reflection_card": card_obj, "completed": True}


def pass_mastery_node(state: ExamState) -> Dict[str, Any]:
    """节点 6: 高分掌握节点"""
    print("\n🏆 [Node 6: MasteryAchieved] 恭喜！本考点攻防测试达成高分（>=85分）！已具备极高辨析防御力！")
    return {"reflection_card": None, "completed": True}


def save_generated_card(card_obj: Dict[str, Any]):
    """持久化保存动态合成的卡片"""
    data = []
    if os.path.exists(OUTPUT_CARD_PATH):
        try:
            with open(OUTPUT_CARD_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []
    data.append(card_obj)
    with open(OUTPUT_CARD_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==================== 状态机路由条件 ====================

def route_after_evaluation(state: ExamState) -> str:
    """条件边：如果分数 < 85 则进入反思与卡片合成，否则直接进入掌握通关"""
    score = state.get("score", 0)
    if score < 85:
        return "reflect_and_synthesize"
    return "pass_mastery"


# ==================== 构建 LangGraph 图 ====================

def build_exam_graph():
    """构建状态流转图"""
    workflow = StateGraph(ExamState)

    # 注册节点
    workflow.add_node("retrieve_card", retrieve_card_node)
    workflow.add_node("adversarial_examiner", adversarial_examiner_node)
    workflow.add_node("wait_for_answer", wait_for_answer_node)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("reflect_and_synthesize", reflect_and_synthesize_node)
    workflow.add_node("pass_mastery", pass_mastery_node)

    # 添加边
    workflow.add_edge(START, "retrieve_card")
    workflow.add_edge("retrieve_card", "adversarial_examiner")
    workflow.add_edge("adversarial_examiner", "wait_for_answer")
    workflow.add_edge("wait_for_answer", "evaluate")

    # 条件分支
    workflow.add_conditional_edges(
        "evaluate",
        route_after_evaluation,
        {
            "reflect_and_synthesize": "reflect_and_synthesize",
            "pass_mastery": "pass_mastery"
        }
    )

    workflow.add_edge("reflect_and_synthesize", END)
    workflow.add_edge("pass_mastery", END)

    app = workflow.compile()
    return app


# ==================== 运行入口 ====================

def run_exam(subject: str = "co", topic: str = "", mock_answer: Optional[str] = None):
    app = build_exam_graph()

    # 导出并保存 Mermaid 拓扑图，方便打卡报告展示
    mermaid_code = app.get_graph().draw_mermaid()
    mermaid_path = os.path.join(current_dir, "graph_topology.mmd")
    with open(mermaid_path, "w", encoding="utf-8") as f:
        f.write(mermaid_code)
    print(f"📊 已导出 LangGraph 状态拓扑图: {mermaid_path}")

    initial_state: ExamState = {
        "subject": subject,
        "query_topic": topic,
        "selected_card": {},
        "question": "",
        "rubric": "",
        "user_answer": mock_answer or "",
        "score": 0,
        "critique": "",
        "reflection_card": None,
        "completed": False
    }

    final_state = app.invoke(initial_state)
    return final_state


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="408-MasteryGraph: 考研408智能攻防审题与动态卡片自省教练")
    parser.add_argument("--subject", default="co", choices=["co", "os", "net", "ds", "all"], help="考研科目代码")
    parser.add_argument("--topic", default="", help="指定核心考点关键词，如: metrics, 分页, TCP")
    parser.add_argument("--mock-answer", default="", help="非交互模式下的模拟回答（用于CI/自动测试）")
    args = parser.parse_args()

    print("=" * 65)
    print("🎓 408-MasteryGraph: 考研408攻防审题与自省闭环教练启动")
    print(f"   目标科目: {args.subject} | 指定考点: {args.topic or '随机精选'}")
    print("=" * 65)

    run_exam(subject=args.subject, topic=args.topic, mock_answer=args.mock_answer)
