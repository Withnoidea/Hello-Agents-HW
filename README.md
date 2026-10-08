<div align="center">

# 🤖 Hello Agents HW

### *《Hello Agents》从原理、范式手搓到框架全栈实战与配套习题*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Frameworks](https://img.shields.io/badge/Frameworks-LangGraph%20%7C%20AutoGen%20%7C%20AgentScope%20%7C%20CAMEL-orange)](https://github.com/datawhalechina/hello-agents)
[![Paradigms](https://img.shields.io/badge/Paradigms-ReAct%20%7C%20Plan--and--Solve%20%7C%20Reflection-green)](https://arxiv.org/abs/2210.03629)
[![License](https://img.shields.io/badge/License-MIT-blue?logo=opensourceinitiative&logoColor=white)](LICENSE)

> 📚 本仓库是 **Hello-Agents** 教程的全流程学习实践与作业沉淀。涵盖**第一至六章全套习题精解（hw-001 ~ hw-006）**、**从零手搓的核心范式源码**，以及**四大多智能体主流框架（LangGraph、AutoGen、AgentScope、CAMEL）的工程落地与原创 Web 闭环 Demo**。

</div>

---

## 🧭 仓库导航与章节全景

| 章节 | 对应作业 | 核心实战代码 | 核心涵盖概念 |
| :--- | :--- | :--- | :--- |
| **Ch1 初识智能体** | [`hw-001.md`](./hw-001.md) | [`code/chapter1/FirstAgentTest.py`](./code/chapter1/FirstAgentTest.py) | PEAS 建模、Workflow vs Agent 判定、系统 1/2 神经符号范式、手搓 ReAct 旅行助手 |
| **Ch2 智能体发展史** | [`hw-002.md`](./hw-002.md) | [`code/chapter2/ELIZA.py`](./code/chapter2/ELIZA.py) | 物理符号系统假说 (PSSH)、MYCIN 专家系统、ELIZA 模式匹配、心智社会、代码审查三时代演进 |
| **Ch3 大语言模型基础** | [`hw-003.md`](./hw-003.md) | [`code/chapter3/`](./code/chapter3/) (`Transformer`, `BPE`, `N_gram`, `Qwen`) | N-gram 局限、Transformer 自注意力与并行性、BPE 子词分词、开源模型量化部署与采样、幻觉缓解工程 (RAG/推理) |
| **Ch4 经典范式构建** | [`hw-004.md`](./hw-004.md) | [`code/chapter4/`](./code/chapter4/) (`ReAct`, `Plan_and_solve`, `Reflection`) | 原生手搓 ReAct 闭环、Plan-and-Solve 规划、自我反思自愈机制 (Reflection)、结构化输出与工具检索 |
| **Ch5 低代码平台搭建** | [`hw-005.md`](./hw-005.md) | — | Coze / Dify / n8n / FastGPT 四大平台深度横评、工作流节点设计、持久化与 MCP 协议规范 |
| **Ch6 框架开发实践** | [`hw-006.md`](./hw-006.md) | [`code/chapter6/`](./code/chapter6/) (AutoGen, AgentScope, CAMEL, LangGraph, Demo) | 多智能体框架多维对比、群聊协作、三国杀在线博弈、双智能体角色扮演、LangGraph 原创考研教练闭环 |

---

## 📁 目录结构

```text
hello-agents-hw/
├── hw-001.md                # 📝 第一章《初识智能体》习题 1–6 精解
├── hw-002.md                # 📝 第二章《智能体发展史》习题 1–7 精解
├── hw-003.md                # 📝 第三章《大语言模型基础》习题 1–6 精解
├── hw-004.md                # 📝 第四章《智能体经典范式构建》习题 1–7 精解
├── hw-005.md                # 📝 第五章《基于低代码平台的智能体搭建》习题 1–7 精解
├── hw-006.md                # 📝 第六章《框架开发实践》习题 1–6 精解
├── code/
│   ├── chapter1/
│   │   └── FirstAgentTest.py        # 原生 Python 手搓 ReAct 旅行智能体（不依赖框架）
│   ├── chapter2/
│   │   └── ELIZA.py                 # 经典 ELIZA 心理咨询模式匹配程序
│   ├── chapter3/
│   │   ├── BPE.py                   # BPE 子词分词算法实现
│   │   ├── N_gram.py                # N-gram 语言模型统计计算
│   │   ├── Transformer.py           # Transformer 核心架构与自注意力机制示意
│   │   └── Qwen.py                  # 开源 Qwen 模型调用与推理实验
│   ├── chapter4/
│   │   ├── llm_client.py            # 统一 OpenAI 兼容客户端封装
│   │   ├── tools.py                 # 常用工具库封装（天气、计算、搜索等）
│   │   ├── ReAct.py                 # 手搓 ReAct 经典范式
│   │   ├── Plan_and_solve.py        # 手搓 Plan-and-Solve 分解规划范式
│   │   └── Reflection.py            # 手搓 Reflection 自我反思与评测闭环
│   └── chapter6/
│       ├── AutoGenDemo/             # AutoGen 多智能体软件协作团队（PM + Engineer + Reviewer）
│       ├── AgentScopeDemo/          # AgentScope 三国文化狼人杀多智能体博弈对决
│       ├── CAMEL/                   # CAMEL 角色扮演与多角色图书创作协作系统
│       ├── Langgraph/               # LangGraph 状态图基础问答工作流
│       └── Demo/                    # 🌟 408-MasteryGraph: 考研408攻防审题与自省教练全栈 Demo
├── .env.example             # 环境变量模板
└── README.md                # 本说明文档
```

---

## 🌟 核心亮点：原创全栈 Demo (408-MasteryGraph)

位于 `code/chapter6/Demo/`，针对全国硕士研究生入学考试计算机学科专业基础（408）备考痛点打造。

### 1. 架构与设计哲学
普通问答 Agent 极易在专业理论场景下产生事实性幻觉。本项目采用 **LangGraph 状态机** 实现高可靠认知攻防回路：
- **数据底座锚定（Grounding）**：深度结合考研 408 核心考点卡片库，覆盖计组、操作系统、计网、数据结构四大核心模块；
- **攻防变式命题（Adversarial Formulation）**：针对容易混淆的经典概念（如“主频与 CPU 执行时间倒挂”、“流水线相关判定”）生成情境辨析题；
- **采分裁判与条件路由（Conditional Routing）**：
  - 考生回答 $\ge 80$ 分：判定掌握，直接流转至归档；
  - 考生回答 $< 80$ 分：触发条件分支，定位失分点并生成专属防坑诊断闪卡（Mistake Flashcard）；
- **全栈一体化呈现**：React + Tailwind 前端页面 + 后端一体化服务，并在页面无缝注入悬浮攻防交互看板。

```text
[考点提取 & 状态初始化]
        │
        ▼
[攻防变式出题 (Adversarial Node)]
        │
        ▼
   [考生作答]
        │
        ▼
[采分与诊断裁判 (Evaluate Node)]
        │
   ┌────┴──────────────────────────┐
   ▼ (Score >= 80)                 ▼ (Score < 80)
[判定掌握 (Pass)]           [认知自省与自愈闪卡 (Reflection)]
```

### 2. 一键启动 Demo
```bash
cd code/chapter6/Demo
pip install -r requirements.txt   # 安装依赖
python server.py 8088             # 启动全栈服务，浏览器访问 http://localhost:8088
```

---

## 🚀 快速上手与运行

### 1. 环境准备
```bash
# 克隆仓库
git clone https://github.com/Withnoidea/Hello-Agents-HW.git
cd Hello-Agents-HW

# 推荐使用 Python 3.10+
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 2. 配置环境变量
在项目根目录或各案例子目录下配置 `.env` 文件（兼容 OpenAI 规范）：
```ini
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o-mini
TAVILY_API_KEY=your_tavily_key_here   # 若运行涉及联网检索工具
```

### 3. 运行对应章节实践
- **运行手搓 ReAct 旅行助手**：
  ```bash
  python code/chapter1/FirstAgentTest.py
  ```
- **运行第四章范式实践**：
  ```bash
  python code/chapter4/ReAct.py
  python code/chapter4/Plan_and_solve.py
  python code/chapter4/Reflection.py
  ```
- **运行第六章框架案例**：
  ```bash
  # AutoGen 软件团队
  python code/chapter6/AutoGenDemo/autogen_software_team.py

  # AgentScope 狼人杀
  python code/chapter6/AgentScopeDemo/main_cn.py

  # LangGraph 问答工作流
  python code/chapter6/Langgraph/Dialogue_System.py
  ```

---

## 📝 配套习题精解索引

- 📘 **[hw-001.md · 第一章 初识智能体](./hw-001.md)**：智能体四判定、PEAS 维度、Workflow vs Agent 权衡、双系统思维与神经符号、局限与评估
- 📘 **[hw-002.md · 第二章 智能体发展史](./hw-002.md)**：物理符号系统假说、专家系统、ELIZA 模式匹配、心智社会分布式架构、深度学习与强化学习演进
- 📘 **[hw-003.md · 第三章 大语言模型基础](./hw-003.md)**：N-gram 与马尔可夫链、Transformer 自注意力与并行解码、BPE 算法、模型采样与量化、幻觉缓解三大路径、长文本学术助手
- 📘 **[hw-004.md · 第四章 智能体经典范式构建](./hw-004.md)**：ReAct / Plan-and-Solve / Reflection 对比与混合、JSON 结构化输出解析自愈、大规模工具向量检索、分层规划、电商售后客服架构
- 📘 **[hw-005.md · 第五章 基于低代码平台的智能体搭建](./hw-005.md)**：Coze / Dify / n8n / FastGPT 四大平台横向对比、工作流重构、持久化状态管理、MCP 协议与插件体系、初创企业场景选型矩阵
- 📘 **[hw-006.md · 第六章 框架开发实践](./hw-006.md)**：四大框架哲学（显式控制 vs 涌现式协作）、AutoGen 动态回退与 QA 角色、AgentScope 复杂状态流、CAMEL 角色扮演与 Workforce 拓扑、LangGraph 问答图重构

---

## 📄 许可证

本项目以 [MIT License](LICENSE) 许可证开源，欢迎自由交流与学习。

<div align="center">

**Keep Building & Enjoy Agentic Systems! 🚀**

</div>
