// 考研408智能攻防教练 · LangGraph Agent 交互面板注入脚本
(function () {
  console.log('[ky-agent] 初始化 408-MasteryGraph 攻防面板 (Markdown & 可拖动增强版)...');

  // 轻量级安全标准 Markdown 转换器
  function parseMarkdown(md) {
    if (!md) return '';
    let html = md
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // 代码块 ```lang ... ```
    html = html.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, function(match, lang, code) {
      return `<pre style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 12px; overflow-x: auto; margin: 10px 0; font-family: Consolas, Monaco, monospace; font-size: 13px; color: #38bdf8; line-height: 1.5;"><code>${code.trim()}</code></pre>`;
    });

    // 行内代码 `code`
    html = html.replace(/`([^`]+)`/g, '<code style="background: rgba(99, 102, 241, 0.2); color: #c7d2fe; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px;">$1</code>');

    // 标题 ###, ##, #
    html = html.replace(/^### (.*$)/gim, '<h4 style="color:#e2e8f0;margin:12px 0 6px 0;font-size:15px;font-weight:700;">$1</h4>');
    html = html.replace(/^## (.*$)/gim, '<h3 style="color:#f1f5f9;margin:14px 0 8px 0;font-size:16px;font-weight:700;">$1</h3>');
    html = html.replace(/^# (.*$)/gim, '<h2 style="color:#f8fafc;margin:16px 0 10px 0;font-size:18px;font-weight:800;">$1</h2>');

    // 粗体 **bold**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong style="color: #fde047; font-weight: 700;">$1</strong>');
    // 斜体 *italic*
    html = html.replace(/\*(.*?)\*/g, '<em style="color: #cbd5e1;">$1</em>');

    // 引用块 > text
    html = html.replace(/^> (.*$)/gim, '<blockquote style="border-left: 3px solid #6366f1; background: rgba(99, 102, 241, 0.12); padding: 8px 12px; margin: 8px 0; border-radius: 0 6px 6px 0; color: #cbd5e1;">$1</blockquote>');

    // 无序列表 - item 或 * item
    html = html.replace(/^[\*\-] (.*$)/gim, '<li style="margin-left: 20px; list-style-type: disc; margin-bottom: 4px; color: #e2e8f0;">$1</li>');
    // 有序列表 1. item
    html = html.replace(/^\d+\. (.*$)/gim, '<li style="margin-left: 20px; list-style-type: decimal; margin-bottom: 4px; color: #e2e8f0;">$1</li>');

    // 换行
    html = html.replace(/\n/g, '<br/>');

    // 清理连续多余换行
    html = html.replace(/(<br\/>){3,}/g, '<br/><br/>');
    return html;
  }

  // 窗口拖动手柄辅助函数
  function makeDraggable(handleEl, targetEl) {
    let isDragging = false;
    let startX = 0, startY = 0;
    let origLeft = 0, origTop = 0;

    handleEl.style.cursor = 'move';
    handleEl.style.userSelect = 'none';

    handleEl.addEventListener('mousedown', function (e) {
      if (e.target.tagName === 'BUTTON' || e.target.tagName === 'SELECT' || e.target.tagName === 'INPUT') return;
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;

      const rect = targetEl.getBoundingClientRect();
      origLeft = rect.left;
      origTop = rect.top;

      targetEl.style.position = 'fixed';
      targetEl.style.left = origLeft + 'px';
      targetEl.style.top = origTop + 'px';
      targetEl.style.right = 'auto';
      targetEl.style.bottom = 'auto';
      targetEl.style.transform = 'none';
      targetEl.style.margin = '0';

      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
      e.preventDefault();
    });

    function onMouseMove(e) {
      if (!isDragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;

      let newLeft = origLeft + dx;
      let newTop = origTop + dy;

      // 限制在可视区域内
      const maxLeft = window.innerWidth - targetEl.offsetWidth - 10;
      const maxTop = window.innerHeight - targetEl.offsetHeight - 10;
      newLeft = Math.max(10, Math.min(maxLeft, newLeft));
      newTop = Math.max(10, Math.min(maxTop, newTop));

      targetEl.style.left = newLeft + 'px';
      targetEl.style.top = newTop + 'px';
    }

    function onMouseUp() {
      isDragging = false;
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    }
  }

  function createFloatingCoachButton() {
    if (document.getElementById('ky-agent-fab')) return;

    // 悬浮教练按钮
    const fab = document.createElement('button');
    fab.id = 'ky-agent-fab';
    fab.innerHTML = '⚔️ 攻防教练';
    fab.title = '打开 408 暗雷特训与避坑教练面板';
    Object.assign(fab.style, {
      position: 'fixed',
      bottom: '24px',
      right: '24px',
      zIndex: '9999',
      padding: '12px 20px',
      background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
      color: '#ffffff',
      fontWeight: '700',
      fontSize: '14px',
      border: 'none',
      borderRadius: '30px',
      boxShadow: '0 8px 24px rgba(124, 58, 237, 0.45)',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
      backdropFilter: 'blur(8px)'
    });

    fab.onmouseenter = () => {
      fab.style.transform = 'translateY(-3px) scale(1.03)';
      fab.style.boxShadow = '0 12px 28px rgba(124, 58, 237, 0.6)';
    };
    fab.onmouseleave = () => {
      fab.style.transform = 'translateY(0) scale(1)';
      fab.style.boxShadow = '0 8px 24px rgba(124, 58, 237, 0.45)';
    };

    document.body.appendChild(fab);

    // 模态弹窗容器
    const modal = document.createElement('div');
    modal.id = 'ky-agent-modal';
    Object.assign(modal.style, {
      position: 'fixed',
      top: '0',
      left: '0',
      width: '100vw',
      height: '100vh',
      backgroundColor: 'rgba(15, 23, 42, 0.65)',
      backdropFilter: 'blur(10px)',
      webkitBackdropFilter: 'blur(10px)',
      zIndex: '10000',
      display: 'none',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '20px'
    });

    // 弹窗主卡片 (优雅暗夜蓝灰毛玻璃风格)
    const card = document.createElement('div');
    card.id = 'ky-agent-card';
    Object.assign(card.style, {
      width: '100%',
      maxWidth: '680px',
      maxHeight: '90vh',
      backgroundColor: '#1e293b',
      backgroundImage: 'linear-gradient(180deg, rgba(30, 41, 59, 0.98) 0%, rgba(15, 23, 42, 0.98) 100%)',
      borderRadius: '16px',
      border: '1px solid rgba(148, 163, 184, 0.2)',
      boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.05)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      color: '#f8fafc',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    });

    card.innerHTML = `
      <!-- 弹窗顶栏 (支持拖动) -->
      <div id="ky-agent-card-header" style="padding: 16px 20px; border-bottom: 1px solid rgba(148, 163, 184, 0.15); display: flex; justify-content: space-between; align-items: center; background: rgba(15, 23, 42, 0.7); cursor: move;">
        <div style="display: flex; align-items: center; gap: 10px; pointer-events: none;">
          <div style="width: 32px; height: 32px; border-radius: 8px; background: linear-gradient(135deg, #4f46e5, #7c3aed); display: flex; align-items: center; justify-content: center; font-size: 16px;">⚔️</div>
          <div>
            <div style="font-weight: 700; font-size: 16px; color: #f8fafc; letter-spacing: -0.01em;">408 智能攻防教练</div>
            <div style="font-size: 12px; color: #94a3b8;">LangGraph 自适应命题 · 审题避坑 · 错因反思</div>
          </div>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="font-size: 11px; color: #64748b; background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 12px;">可按住顶栏拖动</span>
          <button id="ky-agent-btn-close" style="background: transparent; border: none; color: #94a3b8; font-size: 20px; cursor: pointer; padding: 4px 8px; border-radius: 6px; transition: all 0.2s;">✕</button>
        </div>
      </div>

      <!-- 弹窗主体滚动区 -->
      <div style="padding: 20px; overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 18px;">
        
        <!-- 操作栏：科目选择与出题 -->
        <div style="display: flex; gap: 10px; align-items: center; background: rgba(15, 23, 42, 0.4); padding: 12px 14px; border-radius: 10px; border: 1px solid rgba(148, 163, 184, 0.12);">
          <span style="font-size: 13px; color: #94a3b8; font-weight: 500;">特训科目:</span>
          <select id="ky-agent-subject" style="background: #0f172a; color: #f8fafc; border: 1px solid rgba(148, 163, 184, 0.25); border-radius: 6px; padding: 6px 12px; font-size: 13px; outline: none; cursor: pointer;">
            <option value="ds">数据结构 (DS)</option>
            <option value="co">计算机组成原理 (CO)</option>
            <option value="os">操作系统 (OS)</option>
            <option value="cn">计算机网络 (CN)</option>
          </select>
          <button id="ky-agent-btn-gen" style="flex: 1; background: #4f46e5; hover:background: #4338ca; color: #ffffff; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 600; font-size: 13px; cursor: pointer; transition: background 0.2s; box-shadow: 0 2px 8px rgba(79, 70, 229, 0.3);">
            🎯 抽取考点命制暗雷题
          </button>
        </div>

        <!-- 题目区域 (Markdown 渲染) -->
        <div id="ky-agent-q-box" style="display: none; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 12px; padding: 16px 18px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <span id="ky-agent-q-meta" style="color: #818cf8; font-size: 12px; font-weight: 700; background: rgba(99, 102, 241, 0.15); padding: 3px 8px; border-radius: 6px;"></span>
            <span id="ky-agent-q-card-title" style="color: #64748b; font-size: 12px;"></span>
          </div>
          <div id="ky-agent-q-text" style="font-size: 14px; line-height: 1.7; color: #f1f5f9;"></div>
        </div>

        <!-- 答题输入区 -->
        <div id="ky-agent-a-box" style="display: none; flex-direction: column; gap: 10px;">
          <textarea id="ky-agent-input-ans" placeholder="请输入你的思路或判断理由（教练会重点考察是否有踩入概念陷阱或混淆细节）..." style="width: 100%; min-height: 90px; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 10px; padding: 12px 14px; color: #f8fafc; font-size: 13px; line-height: 1.6; resize: vertical; outline: none;"></textarea>
          <button id="ky-agent-btn-submit" style="align-self: flex-end; background: #10b981; color: #ffffff; border: none; padding: 8px 22px; border-radius: 6px; font-weight: 600; font-size: 13px; cursor: pointer; transition: background 0.2s; box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);">
            🚀 提交阅卷裁判
          </button>
        </div>

        <!-- 评语与避坑卡片区 (Markdown 渲染) -->
        <div id="ky-agent-res-box" style="display: none; flex-direction: column; gap: 12px;"></div>

      </div>
    `;

    modal.appendChild(card);
    document.body.appendChild(modal);

    // 绑定顶栏拖动
    const cardHeader = document.getElementById('ky-agent-card-header');
    makeDraggable(cardHeader, card);

    // 交互逻辑
    let currentCard = null;
    let currentQuestion = null;

    fab.onclick = () => {
      modal.style.display = 'flex';
    };

    const btnClose = document.getElementById('ky-agent-btn-close');
    btnClose.onclick = () => {
      modal.style.display = 'none';
    };
    btnClose.onmouseenter = () => btnClose.style.color = '#fff';
    btnClose.onmouseleave = () => btnClose.style.color = '#94a3b8';

    modal.onclick = (e) => {
      if (e.target === modal) modal.style.display = 'none';
    };

    const btnGen = document.getElementById('ky-agent-btn-gen');
    const qBox = document.getElementById('ky-agent-q-box');
    const qMeta = document.getElementById('ky-agent-q-meta');
    const qCardTitle = document.getElementById('ky-agent-q-card-title');
    const qText = document.getElementById('ky-agent-q-text');
    const aBox = document.getElementById('ky-agent-a-box');
    const resBox = document.getElementById('ky-agent-res-box');
    const inputAns = document.getElementById('ky-agent-input-ans');
    const btnSubmit = document.getElementById('ky-agent-btn-submit');

    btnGen.onclick = async () => {
      btnGen.disabled = true;
      btnGen.textContent = '⏳ Agent 正在分析考点并命题...';
      resBox.style.display = 'none';
      resBox.innerHTML = '';
      inputAns.value = '';

      try {
        const subject = document.getElementById('ky-agent-subject').value;
        const resp = await fetch('/api/agent/challenge', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ subject: subject })
        });
        const data = await resp.json();
        if (data.status === 'success') {
          currentCard = data.card;
          currentQuestion = data.question;

          qMeta.textContent = `【${(currentCard.subject || '').toUpperCase()}】 ${currentCard.kp || ''}`;
          qCardTitle.textContent = `原卡ID: ${currentCard.id || ''}`;
          // 使用 Markdown 格式化渲染题目
          qText.innerHTML = parseMarkdown(currentQuestion);

          qBox.style.display = 'block';
          aBox.style.display = 'flex';
        } else {
          alert('出题失败: ' + (data.message || '未知错误'));
        }
      } catch (err) {
        alert('网络请求失败: ' + err.message);
      } finally {
        btnGen.disabled = false;
        btnGen.textContent = '🎯 抽取考点命制暗雷题';
      }
    };

    btnSubmit.onclick = async () => {
      const ans = inputAns.value.trim();
      if (!ans) {
        alert('请输入你的作答内容！');
        return;
      }
      btnSubmit.disabled = true;
      btnSubmit.textContent = '⚖️ 裁判阅卷中...';

      try {
        const resp = await fetch('/api/agent/evaluate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            card: currentCard,
            question: currentQuestion,
            user_answer: ans
          })
        });
        const res = await resp.json();

        resBox.style.display = 'flex';
        const isPass = res.passed;
        const color = isPass ? '#10b981' : '#f43f5e';
        const tag = isPass ? '✅ 考核通过' : '❌ 踩坑失分 · 触发自愈避坑合成';

        let html = `
          <div style="background: rgba(15, 23, 42, 0.7); border-left: 4px solid ${color}; border-top: 1px solid rgba(148, 163, 184, 0.15); border-right: 1px solid rgba(148, 163, 184, 0.15); border-bottom: 1px solid rgba(148, 163, 184, 0.15); padding: 14px 18px; border-radius: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
              <span style="font-size: 15px; font-weight: 700; color: ${color};">${tag}</span>
              <span style="font-size: 16px; font-weight: 800; color: #f8fafc;">得分: ${res.score} / 100</span>
            </div>
            <div style="font-size: 13.5px; line-height: 1.7; color: #cbd5e1;">${parseMarkdown(res.critique || '')}</div>
          </div>
        `;

        if (res.generated_card) {
          const gc = res.generated_card;
          html += `
            <div style="background: rgba(88, 28, 135, 0.25); border: 1px solid rgba(147, 51, 234, 0.45); border-radius: 10px; padding: 14px 18px; margin-top: 6px;">
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span style="background: #7c3aed; color: #fff; font-size: 11px; padding: 2px 7px; border-radius: 4px; font-weight: bold;">增生避坑卡片</span>
                <span style="font-weight: 700; color: #e9d5ff; font-size: 14px;">${gc.kp || ''}</span>
              </div>
              <div style="font-size: 13.5px; color: #ddd6fe; margin-bottom: 8px;"><strong>辨析问:</strong> ${parseMarkdown(gc.front || '')}</div>
              <div style="font-size: 13px; color: #c4b5fd; background: rgba(15, 23, 42, 0.6); padding: 10px 14px; border-radius: 6px; border: 1px solid rgba(168, 85, 247, 0.2);">${parseMarkdown(gc.back || '')}</div>
            </div>
          `;

          // 同步动态注入前端内存的 local cards，实现无需刷新卡片库即更新
          try {
            const raw = localStorage.getItem('ky_local_cards');
            let list = raw ? JSON.parse(raw) : [];
            list.unshift(gc);
            localStorage.setItem('ky_local_cards', JSON.stringify(list));
            console.log('✅ 已同步将增生闪卡加入前端本地缓存');
          } catch (e) {}
        }

        resBox.innerHTML = html;
      } catch (err) {
        alert('阅卷请求失败: ' + err.message);
      } finally {
        btnSubmit.disabled = false;
        btnSubmit.textContent = '🚀 提交阅卷裁判';
      }
    };
  }

  // 彻底移除页面中可能残存的登录注册按钮
  function purgeLoginUI() {
    try {
      const buttons = document.querySelectorAll('button, a');
      buttons.forEach(btn => {
        const txt = btn.textContent.trim();
        if (txt.includes('登录') || txt.includes('注册') || txt === 'Login' || txt === 'Sign in') {
          btn.style.display = 'none';
        }
      });
    } catch (e) {}
  }

  setInterval(purgeLoginUI, 1000);

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      createFloatingCoachButton();
      purgeLoginUI();
    });
  } else {
    createFloatingCoachButton();
    purgeLoginUI();
  }
})();
