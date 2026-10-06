import os
import sys
import json
import uuid
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# 引入核心 agent 逻辑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ky_mastery_agent import (
    load_all_cards,
    adversarial_examiner_node,
    evaluate_node,
    reflect_and_synthesize_node,
    save_generated_card,
    GENERATED_CARDS_FILE
)

app = FastAPI(title="408-MasteryGraph Web Coach", description="408攻防审题与自省闭环教练")

# 全局缓存考点卡片
ALL_CARDS = load_all_cards()

class StartExamRequest(BaseModel):
    subject: str = "co"
    query: str = ""

class SubmitAnswerRequest(BaseModel):
    selected_card: Dict[str, Any]
    question: str
    rubric: str
    user_answer: str

@app.get("/api/cards/summary")
def get_cards_summary():
    """获取所有科目及考点卡片概况"""
    subjects = {"co": "计算机组成原理", "os": "操作系统", "ds": "数据结构", "net": "计算机网络"}
    counts = {k: 0 for k in subjects}
    for c in ALL_CARDS:
        s = c.get("subject", "").lower()
        if s in counts:
            counts[s] += 1
    return {
        "total": len(ALL_CARDS),
        "subjects": [{"id": k, "name": v, "count": counts[k]} for k, v in subjects.items()]
    }

@app.get("/api/my-cards")
def get_my_generated_cards():
    """获取生成的防坑反思卡片列表"""
    if os.path.exists(GENERATED_CARDS_FILE):
        try:
            with open(GENERATED_CARDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

@app.post("/api/exam/start")
def start_exam(req: StartExamRequest):
    """阶段一：检索考点卡片并由 AdversarialExaminer 生成攻防题目"""
    subj = req.subject.lower().strip()
    query = req.query.strip().lower()

    candidates = []
    for c in ALL_CARDS:
        match_subj = (c.get("subject", "").lower() == subj) if subj else True
        match_query = True
        if query:
            match_query = (
                query in c.get("kp", "").lower() or
                query in c.get("front", "").lower() or
                query in c.get("chapter", "").lower()
            )
        if match_subj and match_query:
            candidates.append(c)

    if not candidates:
        # 回退
        candidates = [c for c in ALL_CARDS if c.get("subject", "").lower() == subj] or ALL_CARDS

    import random
    selected_card = random.choice(candidates)

    state = {
        "subject": subj,
        "query": query,
        "selected_card": selected_card,
        "question": "",
        "rubric": "",
        "user_answer": "",
        "score": 0,
        "critique": "",
        "reflection_card": None,
        "completed": False
    }

    try:
        exam_res = adversarial_examiner_node(state)
        return {
            "selected_card": selected_card,
            "question": exam_res["question"],
            "rubric": exam_res["rubric"],
            "node_status": "wait_for_answer"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"出题节点执行失败: {str(e)}")

@app.post("/api/exam/evaluate")
def evaluate_exam(req: SubmitAnswerRequest):
    """阶段二：裁判阅卷与反思闭环生成"""
    state = {
        "selected_card": req.selected_card,
        "question": req.question,
        "rubric": req.rubric,
        "user_answer": req.user_answer,
        "score": 0,
        "critique": "",
        "reflection_card": None,
        "completed": False
    }

    try:
        # 1. 评分节点
        eval_res = evaluate_node(state)
        state.update(eval_res)

        reflection_card = None
        route = "pass_mastery"

        # 2. 条件路由
        if eval_res["score"] < 80:
            route = "reflect_and_synthesize"
            reflect_res = reflect_and_synthesize_node(state)
            reflection_card = reflect_res.get("reflection_card")
        else:
            state["completed"] = True

        return {
            "score": state["score"],
            "critique": state["critique"],
            "route_taken": route,
            "reflection_card": reflection_card,
            "completed": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"判分及反思节点失败: {str(e)}")


INDEX_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>408-MasteryGraph · 考研攻防教练</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({ startOnLoad: true, theme: 'neutral' });
    window.mermaid = mermaid;
  </script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&family=Noto+Sans+SC:wght@300;400;600;700&display=swap');
    body { font-family: 'Noto Sans SC', sans-serif; background-color: #0f172a; color: #f8fafc; }
    .code-font { font-family: 'Fira Code', monospace; }
    .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
    .active-node { stroke: #38bdf8 !important; stroke-width: 3px !important; fill: #1e293b !important; }
    .pulse-glow { box-shadow: 0 0 20px rgba(56, 189, 248, 0.35); }
    /* markdown 样式 */
    .prose h1, .prose h2, .prose h3 { color: #38bdf8; font-weight: 700; margin-top: 1rem; margin-bottom: 0.5rem; }
    .prose p { margin-bottom: 0.75rem; line-height: 1.6; }
    .prose table { width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.9rem; }
    .prose th, .prose td { border: 1px solid #334155; padding: 6px 12px; text-align: left; }
    .prose th { background: #1e293b; color: #94a3b8; }
    .prose code { background: #1e293b; padding: 2px 6px; border-radius: 4px; color: #f43f5e; font-family: 'Fira Code', monospace; }
  </style>
</head>
<body class="min-h-screen flex flex-col">

  <!-- 顶部导航 -->
  <header class="border-b border-slate-800 glass sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
    <div class="flex items-center space-x-3">
      <span class="text-2xl">🎓</span>
      <div>
        <h1 class="text-lg font-bold bg-gradient-to-r from-sky-400 via-indigo-300 to-emerald-400 bg-clip-text text-transparent">
          408-MasteryGraph Coach
        </h1>
        <p class="text-xs text-slate-400">基于 LangGraph 状态机驱动的 408 考研攻防辨析与自愈闭环</p>
      </div>
    </div>
    <div class="flex items-center space-x-4">
      <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-sky-950/60 text-sky-400 border border-sky-800/50">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse mr-2"></span>
        LangGraph Flow Engine Active
      </span>
      <button onclick="switchTab('cards')" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-700 transition">
        📚 查看已沉淀防坑卡片 (<span id="saved-cards-count">0</span>)
      </button>
    </div>
  </header>

  <!-- 主体区域 -->
  <main class="flex-1 max-w-7xl w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">

    <!-- 左侧：LangGraph 状态机拓扑监控 -->
    <section class="lg:col-span-4 flex flex-col space-y-4">
      <div class="glass rounded-xl p-5 border border-slate-800">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-sm font-semibold text-slate-200 flex items-center">
            <span class="mr-2 text-sky-400">⚡</span> 状态机工作流 (LangGraph)
          </h2>
          <span id="workflow-badge" class="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400">待命就绪</span>
        </div>
        
        <!-- 工作流图解 -->
        <div class="space-y-2 text-xs">
          <div id="step-retrieve" class="p-2.5 rounded-lg border border-slate-800 bg-slate-900/60 transition flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <span class="w-5 h-5 rounded-full bg-slate-800 flex items-center justify-center text-slate-300 font-mono">1</span>
              <span>考点底座检索 (CardRetriever)</span>
            </div>
            <span class="status-indicator text-slate-500">⚪</span>
          </div>

          <div id="step-adversarial" class="p-2.5 rounded-lg border border-slate-800 bg-slate-900/60 transition flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <span class="w-5 h-5 rounded-full bg-slate-800 flex items-center justify-center text-slate-300 font-mono">2</span>
              <span>攻防命题官挖坑 (Examiner)</span>
            </div>
            <span class="status-indicator text-slate-500">⚪</span>
          </div>

          <div id="step-answer" class="p-2.5 rounded-lg border border-slate-800 bg-slate-900/60 transition flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <span class="w-5 h-5 rounded-full bg-slate-800 flex items-center justify-center text-slate-300 font-mono">3</span>
              <span>考生作答交互 (Candidate)</span>
            </div>
            <span class="status-indicator text-slate-500">⚪</span>
          </div>

          <div id="step-evaluate" class="p-2.5 rounded-lg border border-slate-800 bg-slate-900/60 transition flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <span class="w-5 h-5 rounded-full bg-slate-800 flex items-center justify-center text-slate-300 font-mono">4</span>
              <span>严苛采分判官 (AnswerJudge)</span>
            </div>
            <span class="status-indicator text-slate-500">⚪</span>
          </div>

          <!-- 条件分支 -->
          <div class="pl-6 border-l-2 border-dashed border-slate-700 ml-3 my-1 space-y-2">
            <div id="step-pass" class="p-2 rounded-lg border border-slate-800 bg-slate-900/40 text-emerald-400 flex items-center justify-between">
              <span>分支 A: ≥80分 掌握直通</span>
              <span class="status-indicator text-slate-500">⚪</span>
            </div>
            <div id="step-reflect" class="p-2 rounded-lg border border-slate-800 bg-slate-900/40 text-amber-400 flex items-center justify-between">
              <span>分支 B: &lt;80分 触发反思自愈</span>
              <span class="status-indicator text-slate-500">⚪</span>
            </div>
          </div>

          <div id="step-synthesize" class="p-2.5 rounded-lg border border-slate-800 bg-slate-900/60 transition flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <span class="w-5 h-5 rounded-full bg-slate-800 flex items-center justify-center text-slate-300 font-mono">5</span>
              <span>避坑新卡片沉淀 (Synthesizer)</span>
            </div>
            <span class="status-indicator text-slate-500">⚪</span>
          </div>
        </div>
      </div>

      <!-- 命中的底座卡片信息 -->
      <div id="card-panel" class="glass rounded-xl p-5 border border-slate-800 hidden">
        <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">命中考点底座 (Grounding Card)</h3>
        <div class="bg-slate-900/80 rounded-lg p-3 border border-slate-700 text-xs space-y-1.5">
          <div class="flex justify-between items-center text-sky-400 font-mono">
            <span id="card-subject-tag">[CO]</span>
            <span id="card-chapter-tag" class="text-slate-400">计算机系统概述</span>
          </div>
          <div id="card-front-text" class="text-slate-200 font-medium"></div>
        </div>
      </div>
    </section>

    <!-- 右侧：工作主面板 -->
    <section class="lg:col-span-8 flex flex-col space-y-6">

      <!-- 标签页 1: 攻防审题主界面 -->
      <div id="tab-exam" class="space-y-6">
        
        <!-- 控制卡片：抽考配置 -->
        <div class="glass rounded-xl p-5 border border-slate-800">
          <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
            <div class="md:col-span-4">
              <label class="block text-xs font-semibold text-slate-400 mb-1">选择 408 科目</label>
              <select id="select-subject" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-sky-500">
                <option value="co">计算机组成原理 (CO)</option>
                <option value="os">操作系统 (OS)</option>
                <option value="ds">数据结构 (DS)</option>
                <option value="net">计算机网络 (NET)</option>
              </select>
            </div>
            <div class="md:col-span-5">
              <label class="block text-xs font-semibold text-slate-400 mb-1">指定检索考点 (选填)</label>
              <input id="input-query" type="text" placeholder="例: metrics / 虚拟内存 / 快速排序" value="metrics"
                class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-sky-500 placeholder-slate-600">
            </div>
            <div class="md:col-span-3">
              <button id="btn-start" onclick="startExamChallenge()"
                class="w-full bg-sky-600 hover:bg-sky-500 text-white font-medium px-4 py-2 rounded-lg text-sm transition shadow-lg shadow-sky-600/30 flex items-center justify-center space-x-2">
                <span>⚔️ 发起攻防出题</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 试题区 (出题完毕后显示) -->
        <div id="question-panel" class="glass rounded-xl p-6 border border-slate-800 hidden space-y-4">
          <div class="flex items-center justify-between border-b border-slate-800 pb-3">
            <span class="inline-flex items-center text-xs font-semibold text-amber-400 bg-amber-950/40 px-2.5 py-1 rounded border border-amber-800/40">
              ⚡ 命题组骨干刁钻变式题 (含有隐蔽暗雷)
            </span>
            <span class="text-xs text-slate-500">满分：100分</span>
          </div>

          <div id="question-content" class="text-slate-100 text-sm leading-relaxed whitespace-pre-line bg-slate-900/60 p-4 rounded-lg border border-slate-800 code-font"></div>

          <!-- 作答输入区 -->
          <div class="space-y-2 pt-2">
            <div class="flex justify-between items-center">
              <label class="text-xs font-semibold text-slate-300">✍️ 你的回答与推导：</label>
              <button onclick="fillMockAnswer()" class="text-xs text-sky-400 hover:underline">一键注入典型易错回答 (用于测试反思闭环)</button>
            </div>
            <textarea id="user-answer-input" rows="4" placeholder="在此输入你的辨析分析、结论及公式计算推导..."
              class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-sm text-slate-200 focus:outline-none focus:border-sky-500 placeholder-slate-600"></textarea>
            
            <div class="flex justify-end">
              <button id="btn-submit" onclick="submitUserAnswer()"
                class="bg-emerald-600 hover:bg-emerald-500 text-white font-medium px-5 py-2.5 rounded-lg text-sm transition shadow-lg shadow-emerald-600/30 flex items-center space-x-2">
                <span>⚖️ 提交给阅卷裁判核验</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 裁判评估诊断区 -->
        <div id="eval-panel" class="glass rounded-xl p-6 border border-slate-800 hidden space-y-4">
          <div class="flex items-center justify-between border-b border-slate-800 pb-3">
            <div class="flex items-center space-x-3">
              <span class="text-xl">⚖️</span>
              <h3 class="font-bold text-slate-100">阅卷裁判裁决书</h3>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-xs text-slate-400">核定得分:</span>
              <span id="eval-score" class="text-2xl font-black font-mono">--</span>
            </div>
          </div>

          <div class="bg-slate-900/60 p-4 rounded-lg border border-slate-800 text-sm leading-relaxed text-slate-300 whitespace-pre-line" id="eval-critique"></div>

          <!-- 触发反思闭环生成的新卡片 -->
          <div id="reflection-card-box" class="hidden border border-amber-500/30 bg-amber-950/20 rounded-xl p-5 space-y-3">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-2">
                <span class="text-lg">💡</span>
                <span class="font-bold text-amber-400 text-sm">反思闭环激活：已为你自动炼制专属 408 防坑闪卡</span>
              </div>
              <span class="text-xs px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">已存入本地闪卡库</span>
            </div>
            
            <div class="bg-slate-900/90 rounded-lg p-4 border border-slate-700 text-xs space-y-2">
              <div class="text-sky-400 font-bold" id="reflect-card-front"></div>
              <div class="prose text-slate-300 border-t border-slate-800 pt-2" id="reflect-card-back"></div>
            </div>
          </div>
        </div>

      </div>

      <!-- 标签页 2: 我的防坑卡片库 -->
      <div id="tab-cards" class="hidden space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-base font-bold text-slate-100">我的专属防坑卡片库 (Personal Trap Guides)</h2>
            <p class="text-xs text-slate-400">由智能体在日常答题暗雷诊断中自动沉淀积累，可随时回顾复习</p>
          </div>
          <button onclick="switchTab('exam')" class="text-xs bg-slate-800 hover:bg-slate-700 text-sky-400 px-3 py-1.5 rounded-lg border border-slate-700">
            ← 返回攻防答题
          </button>
        </div>

        <div id="cards-container" class="grid grid-cols-1 gap-4">
          <!-- 动态渲染卡片列表 -->
        </div>
      </div>

    </section>

  </main>

  <footer class="border-t border-slate-800 text-center py-4 text-xs text-slate-500">
    408-MasteryGraph · 《Hello Agents》第六章 原创框架实战 Demo · Powered by LangGraph
  </footer>

  <script>
    let currentExamData = null;

    // 步骤指示灯更新
    function setStep(stepId, state) { // 'active', 'success', 'waiting'
      const el = document.getElementById(stepId);
      if (!el) return;
      const indicator = el.querySelector('.status-indicator');
      if (state === 'active') {
        el.className = el.className.replace(/border-slate-800/g, 'border-sky-500 bg-sky-950/40 pulse-glow');
        if (indicator) indicator.innerHTML = '🔄';
      } else if (state === 'success') {
        el.className = el.className.split('border-sky-500')[0] + 'border-emerald-600/50 bg-emerald-950/20';
        if (indicator) indicator.innerHTML = '✅';
      } else {
        if (indicator) indicator.innerHTML = '⚪';
      }
    }

    function resetWorkflow() {
      ['step-retrieve', 'step-adversarial', 'step-answer', 'step-evaluate', 'step-pass', 'step-reflect', 'step-synthesize'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
          el.className = el.className.replace(/border-sky-500 bg-sky-950\/40 pulse-glow/g, 'border-slate-800 bg-slate-900/60');
          el.className = el.className.replace(/border-emerald-600\/50 bg-emerald-950\/20/g, 'border-slate-800 bg-slate-900/60');
          const ind = el.querySelector('.status-indicator');
          if (ind) ind.innerHTML = '⚪';
        }
      });
      document.getElementById('workflow-badge').innerText = '进行中';
      document.getElementById('workflow-badge').className = 'text-xs px-2 py-0.5 rounded bg-sky-900 text-sky-200';
    }

    async function startExamChallenge() {
      const subject = document.getElementById('select-subject').value;
      const query = document.getElementById('input-query').value;
      const btn = document.getElementById('btn-start');

      btn.disabled = true;
      btn.innerHTML = '<span class="animate-spin mr-2">⏳</span> 检索出题中...';

      resetWorkflow();
      setStep('step-retrieve', 'active');
      document.getElementById('question-panel').classList.add('hidden');
      document.getElementById('eval-panel').classList.add('hidden');

      try {
        setStep('step-adversarial', 'active');
        const res = await fetch('/api/exam/start', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ subject, query })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || '请求失败');

        currentExamData = data;
        setStep('step-retrieve', 'success');
        setStep('step-adversarial', 'success');
        setStep('step-answer', 'active');

        // 展示卡片与题目
        document.getElementById('card-panel').classList.remove('hidden');
        document.getElementById('card-subject-tag').innerText = `[${data.selected_card.subject.toUpperCase()}]`;
        document.getElementById('card-chapter-tag').innerText = data.selected_card.chapter || '';
        document.getElementById('card-front-text').innerText = data.selected_card.front || '';

        document.getElementById('question-content').innerText = data.question;
        document.getElementById('user-answer-input').value = '';
        document.getElementById('question-panel').classList.remove('hidden');

      } catch (err) {
        alert('出题失败: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>⚔️ 发起攻防出题</span>';
      }
    }

    function fillMockAnswer() {
      document.getElementById('user-answer-input').value = 
        'CPU时间由主频决定。主频越高速度一定越快，MIPS越高说明计算机性能一定更强，因为每秒执行的百万指令数更多。';
    }

    async function submitUserAnswer() {
      const answer = document.getElementById('user-answer-input').value.trim();
      if (!answer) {
        alert('请先输入你的作答！');
        return;
      }

      const btn = document.getElementById('btn-submit');
      btn.disabled = true;
      btn.innerHTML = '<span class="animate-spin mr-2">⏳</span> 裁判核验中...';

      setStep('step-answer', 'success');
      setStep('step-evaluate', 'active');

      try {
        const res = await fetch('/api/exam/evaluate', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            selected_card: currentExamData.selected_card,
            question: currentExamData.question,
            rubric: currentExamData.rubric,
            user_answer: answer
          })
        });
        const evalData = await res.json();
        if (!res.ok) throw new Error(evalData.detail || '阅卷失败');

        setStep('step-evaluate', 'success');

        // 展示裁判得分
        document.getElementById('eval-panel').classList.remove('hidden');
        const scoreEl = document.getElementById('eval-score');
        scoreEl.innerText = `${evalData.score} 分`;
        scoreEl.className = evalData.score >= 80 ? 'text-2xl font-black font-mono text-emerald-400' : 'text-2xl font-black font-mono text-rose-400';

        document.getElementById('eval-critique').innerText = evalData.critique;

        if (evalData.score >= 80) {
          setStep('step-pass', 'success');
          document.getElementById('reflection-card-box').classList.add('hidden');
          document.getElementById('workflow-badge').innerText = '考核通关';
          document.getElementById('workflow-badge').className = 'text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-300';
        } else {
          setStep('step-reflect', 'success');
          setStep('step-synthesize', 'success');
          document.getElementById('reflection-card-box').classList.remove('hidden');
          if (evalData.reflection_card) {
            document.getElementById('reflect-card-front').innerText = evalData.reflection_card.front;
            document.getElementById('reflect-card-back').innerHTML = marked.parse(evalData.reflection_card.back);
          }
          document.getElementById('workflow-badge').innerText = '已生成防坑闭环';
          document.getElementById('workflow-badge').className = 'text-xs px-2 py-0.5 rounded bg-amber-950 text-amber-300';
        }

        refreshCardsCount();

      } catch (err) {
        alert('阅卷失败: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>⚖️ 提交给阅卷裁判核验</span>';
      }
    }

    function switchTab(tab) {
      if (tab === 'cards') {
        document.getElementById('tab-exam').classList.add('hidden');
        document.getElementById('tab-cards').classList.remove('hidden');
        loadSavedCards();
      } else {
        document.getElementById('tab-cards').classList.add('hidden');
        document.getElementById('tab-exam').classList.remove('hidden');
      }
    }

    async function refreshCardsCount() {
      try {
        const res = await fetch('/api/my-cards');
        const cards = await res.json();
        document.getElementById('saved-cards-count').innerText = cards.length;
      } catch (e) {}
    }

    async function loadSavedCards() {
      const container = document.getElementById('cards-container');
      container.innerHTML = '<div class="text-xs text-slate-500 py-4 text-center">正在加载防坑卡片...</div>';
      try {
        const res = await fetch('/api/my-cards');
        const cards = await res.json();
        if (!cards.length) {
          container.innerHTML = '<div class="text-sm text-slate-400 py-8 text-center">暂未沉淀错题防坑卡片，去答题试试吧！</div>';
          return;
        }
        container.innerHTML = cards.map(c => `
          <div class="glass p-5 rounded-xl border border-slate-800 space-y-3">
            <div class="flex items-center justify-between text-xs text-slate-400">
              <span class="font-mono text-sky-400 font-bold">[${(c.subject || '408').toUpperCase()}] ${c.kp || ''}</span>
              <span class="bg-slate-800 px-2 py-0.5 rounded text-amber-400 border border-amber-900/50">${c.chapter || '原创避坑卡'}</span>
            </div>
            <div class="text-sm font-semibold text-slate-100">${c.front}</div>
            <div class="prose text-xs text-slate-300 bg-slate-900/80 p-4 rounded-lg border border-slate-800/80">
              ${marked.parse(c.back || '')}
            </div>
          </div>
        `).join('');
      } catch (e) {
        container.innerHTML = '<div class="text-xs text-rose-400 py-4 text-center">加载失败</div>';
      }
    }

    // 初始化
    refreshCardsCount();
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index_page():
    return HTMLResponse(content=INDEX_HTML)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8088)
