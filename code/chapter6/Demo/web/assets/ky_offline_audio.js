// 考研408记忆卡片离线引擎与MP3知识点伴学语音系统
(function () {
  console.log('[ky-rebuild] 离线伴学与MP3系统注入中...');

  const STORAGE_KEY_CARDS = 'ky_local_cards';
  const STORAGE_KEY_REVIEWS = 'ky_local_reviews';
  const STORAGE_KEY_USER = 'ky_local_user';

  // 1. 初始化本地用户与卡片库
  let localUser = {
    id: 'local_ky_master',
    username: '408考研学者',
    email: 'scholar@408.ky',
    createdAt: new Date().toISOString()
  };

  try {
    const savedUser = localStorage.getItem(STORAGE_KEY_USER);
    if (savedUser) localUser = JSON.parse(savedUser);
  } catch (e) {}

  let cardsDb = null;
  let statsDb = null;

  async function loadInitialDb() {
    if (cardsDb) return;
    try {
      const resp = await fetch('/assets/cards_db.json');
      const data = await resp.json();
      cardsDb = data.cards;
      statsDb = data.stats;
      
      const localCustom = localStorage.getItem(STORAGE_KEY_CARDS);
      if (localCustom) {
        const customCards = JSON.parse(localCustom);
        // 合并
        cardsDb = [...cardsDb, ...customCards];
      }
    } catch (err) {
      console.error('加载卡片库失败', err);
    }
  }

  // 2. 劫持 window.fetch 实现脱机 API
  const originalFetch = window.fetch;
  window.fetch = async function (url, options = {}) {
    const urlStr = typeof url === 'string' ? url : url.url || '';
    
    if (urlStr.startsWith('/api')) {
      await loadInitialDb();
      const path = urlStr.replace('/api', '').split('?')[0];

      // 路由处理
      if (path === '/auth/me') {
        return new Response(JSON.stringify(localUser), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      if (path === '/auth/login' || path === '/auth/register') {
        return new Response(JSON.stringify(localUser), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      if (path === '/auth/logout') {
        return new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      if (path === '/stats') {
        return new Response(JSON.stringify(statsDb || []), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      if (path === '/cards') {
        if (options.method === 'POST') {
          const newCard = JSON.parse(options.body);
          newCard.id = newCard.id || ('card-' + Date.now());
          cardsDb.push(newCard);
          let localArr = JSON.parse(localStorage.getItem(STORAGE_KEY_CARDS) || '[]');
          localArr.push(newCard);
          localStorage.setItem(STORAGE_KEY_CARDS, JSON.stringify(localArr));
          return new Response(JSON.stringify(newCard), {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
          });
        }
        return new Response(JSON.stringify(cardsDb || []), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      if (path.startsWith('/cards/') && options.method === 'PUT') {
        const id = path.replace('/cards/', '');
        const updated = JSON.parse(options.body);
        const idx = cardsDb.findIndex(c => c.id === id);
        if (idx >= 0) cardsDb[idx] = { ...cardsDb[idx], ...updated };
        return new Response(JSON.stringify(updated), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      if (path === '/queue') {
        const urlObj = new URL('http://dummy' + urlStr);
        const sub = urlObj.searchParams.get('subject');
        let queue = cardsDb || [];
        if (sub) {
          queue = queue.filter(c => c.subject === sub);
        }
        return new Response(JSON.stringify(queue), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      if (path === '/reviews') {
        return new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      if (path === '/export/anki.tsv') {
        let tsv = 'front\tback\tsubject\ttags\n';
        for (const c of (cardsDb || [])) {
          const f = (c.front || '').replace(/\t|\n/g, ' ');
          const b = (c.back || '').replace(/\t|\n/g, ' ');
          tsv += `${f}\t${b}\t${c.subject || ''}\t${(c.tags || []).join(',')}\n`;
        }
        return new Response(tsv, {
          status: 200,
          headers: { 'Content-Type': 'text/tab-separated-values; charset=utf-8' }
        });
      }
    }

    return originalFetch.apply(this, arguments);
  };

  // 3. 构建「知识点语音 MP3 播放模式」悬浮与常驻控制器
  function initAudioPlayerUI() {
    const container = document.createElement('div');
    container.id = 'ky-audio-companion';
    container.innerHTML = `
      <style>
        #ky-audio-companion {
          position: fixed;
          bottom: 24px;
          right: 24px;
          z-index: 9999;
          font-family: ui-sans-serif, system-ui, sans-serif;
        }
        .ky-audio-panel {
          background: rgba(30, 41, 59, 0.95);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          border: 1px solid rgba(148, 163, 184, 0.2);
          box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5);
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(12px);
          border: 1px solid rgba(229, 231, 235, 1);
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
          border-radius: 16px;
          padding: 14px 18px;
          width: 320px;
          transition: all 0.25s ease;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .dark .ky-audio-panel {
          background: rgba(30, 41, 59, 0.95);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          border: 1px solid rgba(148, 163, 184, 0.2);
          box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5);
          background: rgba(23, 23, 23, 0.95);
          border-color: rgba(64, 64, 64, 1);
          color: #f3f4f6;
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
        }
        .ky-panel-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .ky-panel-title {
          font-size: 13px;
          font-weight: 700;
          display: flex;
          align-items: center;
          gap: 6px;
          color: #2563eb;
        }
        .dark .ky-panel-title {
          color: #60a5fa;
        }
        .ky-panel-badge {
          font-size: 10px;
          padding: 2px 6px;
          border-radius: 9999px;
          background: #eff6ff;
          color: #2563eb;
          font-weight: 600;
        }
        .dark .ky-panel-badge {
          background: #1e3a8a;
          color: #93c5fd;
        }
        .ky-current-text {
          font-size: 12px;
          line-height: 1.4;
          color: #4b5563;
          max-height: 38px;
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
        }
        .dark .ky-current-text {
          color: #9ca3af;
        }
        .ky-controls-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          margin-top: 4px;
        }
        .ky-btn {
          border: none;
          outline: none;
          cursor: pointer;
          background: #f3f4f6;
          color: #374151;
          padding: 6px 12px;
          border-radius: 8px;
          font-size: 12px;
          font-weight: 500;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 4px;
          transition: background 0.15s;
        }
        .ky-btn:hover {
          background: #e5e7eb;
        }
        .dark .ky-btn {
          background: #262626;
          color: #e5e5e5;
        }
        .dark .ky-btn:hover {
          background: #404040;
        }
        .ky-btn.primary {
          background: #2563eb;
          color: #fff;
        }
        .ky-btn.primary:hover {
          background: #1d4ed8;
        }
        .ky-settings-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          font-size: 11px;
          color: #6b7280;
          border-top: 1px solid #f3f4f6;
          padding-top: 8px;
        }
        .dark .ky-settings-row {
          border-color: #262626;
          color: #a3a3a3;
        }
        .ky-toggle-label {
          display: flex;
          align-items: center;
          gap: 5px;
          cursor: pointer;
        }
        .ky-minimized {
          width: 44px;
          height: 44px;
          border-radius: 50%;
          padding: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          background: #2563eb;
          color: #fff;
          box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
        }
      </style>
      <div class="ky-audio-panel" id="ky-panel-body">
        <div class="ky-panel-header">
          <div class="ky-panel-title">
            <span>🎧 408 知识点 MP3 伴学模式</span>
            <span class="ky-panel-badge" id="ky-audio-status">空闲</span>
          </div>
          <button class="ky-btn" id="ky-minimize-btn" style="padding: 2px 6px; font-size: 11px;">✕</button>
        </div>
        <div class="ky-current-text" id="ky-playing-title">
          等待点播或开启自动连播...
        </div>
        <div class="ky-controls-row">
          <button class="ky-btn" id="ky-prev-btn" title="上一个知识点">⏮️ 上一条</button>
          <button class="ky-btn primary" id="ky-play-toggle-btn">▶️ 开始连播</button>
          <button class="ky-btn" id="ky-next-btn" title="下一个知识点">⏭️ 下一条</button>
        </div>
        <div class="ky-settings-row">
          <label class="ky-toggle-label">
            <input type="checkbox" id="ky-auto-next" checked> 自动连续播放
          </label>
          <label class="ky-toggle-label">
            <input type="checkbox" id="ky-include-back" checked> 朗读解析
          </label>
          <select id="ky-rate-select" style="background:transparent;border:none;font-size:11px;color:inherit;outline:none;cursor:pointer;">
            <option value="1">1.0x</option>
            <option value="1.2" selected>1.2x</option>
            <option value="1.5">1.5x</option>
          </select>
        </div>
      </div>
      <div class="ky-minimized" id="ky-panel-mini" style="display:none;" title="展开知识点伴学语音">
        🎧
      </div>
    `;

    document.body.appendChild(container);
    
    // 伴学浮窗拖动手柄辅助函数
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

    const panelHeader = container.querySelector('.ky-panel-header');
    if (panelHeader) {
      makeDraggable(panelHeader, container);
    }
    

    // 音频合成与播发核心
    let currentIndex = 0;
    let isPlaying = false;
    let isContinuous = false;
    const synth = window.speechSynthesis;
    let currentUtterance = null;

    const statusBadge = document.getElementById('ky-audio-status');
    const titleEl = document.getElementById('ky-playing-title');
    const playToggleBtn = document.getElementById('ky-play-toggle-btn');
    const autoNextCheckbox = document.getElementById('ky-auto-next');
    const includeBackCheckbox = document.getElementById('ky-include-back');
    const rateSelect = document.getElementById('ky-rate-select');
    const minimizeBtn = document.getElementById('ky-minimize-btn');
    const miniPanel = document.getElementById('ky-panel-mini');
    const bodyPanel = document.getElementById('ky-panel-body');

    minimizeBtn.onclick = () => {
      bodyPanel.style.display = 'none';
      miniPanel.style.display = 'flex';
    };
    miniPanel.onclick = () => {
      miniPanel.style.display = 'none';
      bodyPanel.style.display = 'flex';
    };

    function cleanTextForSpeech(md) {
      if (!md) return '';
      return md
        .replace(/`{1,3}[^`]*`{1,3}/g, '') // 去除代码块
        .replace(/\$[^$]+\$/g, '公式')      // LaTeX 公式转读
        .replace(/[#*|_-]/g, ' ')           // 去除排版符号
        .replace(/\s+/g, ' ')
        .trim();
    }

    function playCardAtIndex(index) {
      if (!cardsDb || cardsDb.length === 0) return;
      if (index < 0) index = 0;
      if (index >= cardsDb.length) index = 0;
      currentIndex = index;

      const card = cardsDb[currentIndex];
      const subName = { ds: '数据结构', co: '计组', os: '操作系统', net: '计网' }[card.subject] || '408';
      titleEl.innerText = `[${subName}] ${card.front}`;

      synth.cancel();

      let textToRead = `${subName}知识点：${card.front}。`;
      if (includeBackCheckbox.checked && card.back) {
        textToRead += ` 解析如下：${cleanTextForSpeech(card.back)}`;
      }

      currentUtterance = new SpeechSynthesisUtterance(textToRead);
      currentUtterance.lang = 'zh-CN';
      currentUtterance.rate = parseFloat(rateSelect.value);

      currentUtterance.onstart = () => {
        isPlaying = true;
        statusBadge.innerText = '播放中';
        statusBadge.style.color = '#16a34a';
        playToggleBtn.innerText = '⏸️ 暂停';
      };

      currentUtterance.onend = () => {
        isPlaying = false;
        statusBadge.innerText = '完成';
        if (isContinuous && autoNextCheckbox.checked) {
          setTimeout(() => {
            playCardAtIndex(currentIndex + 1);
          }, 1200);
        } else {
          statusBadge.innerText = '空闲';
          playToggleBtn.innerText = '▶️ 继续播放';
        }
      };

      currentUtterance.onerror = (e) => {
        console.warn('Speech error', e);
        isPlaying = false;
        statusBadge.innerText = '已就绪';
        playToggleBtn.innerText = '▶️ 开始';
      };

      synth.speak(currentUtterance);
    }

    playToggleBtn.onclick = () => {
      if (isPlaying) {
        synth.cancel();
        isPlaying = false;
        isContinuous = false;
        statusBadge.innerText = '暂停';
        playToggleBtn.innerText = '▶️ 继续连播';
      } else {
        isContinuous = true;
        playCardAtIndex(currentIndex);
      }
    };

    document.getElementById('ky-prev-btn').onclick = () => {
      playCardAtIndex(currentIndex - 1);
    };

    document.getElementById('ky-next-btn').onclick = () => {
      playCardAtIndex(currentIndex + 1);
    };

    // 暴露全局快速点播方法，供页面单张卡片点击点播
    window.playSingleCardAudio = function (cardId) {
      if (!cardsDb) return;
      const idx = cardsDb.findIndex(c => c.id === cardId);
      if (idx >= 0) {
        bodyPanel.style.display = 'flex';
        miniPanel.style.display = 'none';
        isContinuous = false;
        playCardAtIndex(idx);
      }
    };

    // 观察DOM变化，自动为卡片库列表中的每张卡片追加点播按钮
    setInterval(() => {
      if (!cardsDb) return;
      const cardElements = document.querySelectorAll('li, div.rounded-2xl, div.rounded-xl');
      cardElements.forEach(el => {
        if (el.dataset.kyAudioAttached) return;
        // 查找卡片中的文字判断是否匹配题目
        const text = el.innerText || '';
        const matched = cardsDb.find(c => text.includes(c.front.slice(0, 20)));
        if (matched) {
          el.dataset.kyAudioAttached = 'true';
          const btn = document.createElement('button');
          btn.innerHTML = '🔊 语音朗读';
          btn.title = '手动点播该知识点语音';
          btn.style.cssText = 'margin-top:6px;padding:3px 8px;font-size:12px;border-radius:6px;border:1px solid #d1d5db;background:#f9fafb;color:#374151;cursor:pointer;display:inline-flex;align-items:center;gap:4px;';
          btn.onclick = (e) => {
            e.stopPropagation();
            window.playSingleCardAudio(matched.id);
          };
          el.appendChild(btn);
        }
      });
    }, 1500);
  }

  // 页面加载完成后注入伴学组件
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAudioPlayerUI);
  } else {
    initAudioPlayerUI();
  }
})();
