import base64
import os

print("Rebuilding COSMOS frontend with 3D Humanoid, docked glassmorphic side chatbot & cleaned HUD...")

with open('cosmos frontend/humanoid/mira-hair-v1.webp', 'rb') as f:
    hair_b64 = 'data:image/webp;base64,' + base64.b64encode(f.read()).decode('utf-8')

with open('cosmos frontend/humanoid/mira-idle-v1.webp', 'rb') as f:
    idle_b64 = 'data:image/webp;base64,' + base64.b64encode(f.read()).decode('utf-8')

with open('cosmos frontend/assets/index-BlszmC9G.css', 'r', encoding='utf-8') as f:
    css = f.read()

with open('cosmos frontend/assets/index-1PiDnpcG.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Replace asset URLs with base64
js = js.replace('"./humanoid/mira-hair-v1.webp"', f'"{hair_b64}"')
js = js.replace('"/humanoid/mira-hair-v1.webp"', f'"{hair_b64}"')
js = js.replace('"./humanoid/mira-idle-v1.webp"', f'"{idle_b64}"')
js = js.replace('"/humanoid/mira-idle-v1.webp"', f'"{idle_b64}"')

# Purge and sanitize template creator branding to COSMOS exclusively
js = js.replace('"MIRA HUMANOID"', '"COSMOS HUMANOID"')
js = js.replace('>MIRA<', '>COSMOS<')

# 1. Remove Enter page and bridge React state to window
old_sf = 'const i=new URLSearchParams(window.location.search),[e,t]=Te.useState(()=>!!i.get("auto")||i.has("t")),[n,r]=Te.useState(()=>Jw.some(([g])=>g===i.get("state"))?i.get("state"):"idle")'
new_sf = 'const i=new URLSearchParams(window.location.search),[e,t]=Te.useState(()=>!0),[n,r]=Te.useState(()=>"idle");window.__cosmos_set_state=r'
assert old_sf in js, "old_sf not found"
js = js.replace(old_sf, new_sf)

# 2. Expose animation restart in xF
old_xf = '[m,g]=Te.useState(1),v=Te.useRef({start:performance.now(),speed:1,pin:o})'
new_xf = '[m,g]=Te.useState(3),v=Te.useRef({start:performance.now(),speed:3,pin:o});window.__cosmos_restart_anim=()=>{v.current.start=performance.now();v.current.speed=3}'
assert old_xf in js, "old_xf not found"
js = js.replace(old_xf, new_xf)

# Escape </script>
js_safe = js.replace('</script>', '<\\/script>')

clean_html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>COSMOS - Humanoid AI | Sri Charan Tirumaladasu</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet" />
    <style>
{css}
    </style>
  </head>
  <body>
    <div id="root"></div>
    <script type="module">
{js_safe}
    </script>

<style>
/* ═══════════════════════════════════════════════════════════════
   1. HUD CLEANUP: REMOVE REPLAY & SPEED BUTTONS, PRESERVE SOUND ON
   ═══════════════════════════════════════════════════════════════ */
.mira-own-row {{
  position: fixed !important;
  right: 18px !important;
  bottom: 18px !important;
  display: flex !important;
  gap: 8px !important;
  z-index: 999 !important;
}}
/* Hide REPLAY and SPEED 0.3x buttons */
.mira-own-row button:not([data-testid="mira-humanoid-sound"]) {{
  display: none !important;
}}
/* Keep SOUND ON button styled and visible */
.mira-own-row button[data-testid="mira-humanoid-sound"] {{
  background: rgba(16, 6, 30, 0.72) !important;
  border: 1px solid rgba(196, 168, 255, 0.45) !important;
  color: #c4a8ff !important;
  border-radius: 9px !important;
  padding: 8px 14px !important;
  font: 12px 'Share Tech Mono', monospace !important;
  letter-spacing: 0.14em !important;
  cursor: pointer !important;
  box-shadow: 0 0 16px rgba(196, 168, 255, 0.18) !important;
  transition: all 0.2s ease !important;
}}
.mira-own-row button[data-testid="mira-humanoid-sound"]:hover {{
  border-color: #ffd27a !important;
  color: #ffd27a !important;
}}

/* ═══════════════════════════════════════════════════════════════
   2. BOTTOM-LEFT HUD PILLS: IDLE, LISTENING, TALKING, MIC ON/OFF
   ═══════════════════════════════════════════════════════════════ */
.mira-page-row {{
  position: fixed !important;
  left: 18px !important;
  bottom: 18px !important;
  z-index: 999 !important;
  display: flex !important;
  gap: 8px !important;
  flex-wrap: wrap !important;
}}
.mira-page-row button {{
  background: rgba(16, 6, 30, 0.72) !important;
  border: 1px solid rgba(196, 168, 255, 0.45) !important;
  color: #c4a8ff !important;
  border-radius: 9px !important;
  padding: 8px 13px !important;
  font: 12px 'Share Tech Mono', monospace !important;
  letter-spacing: 0.14em !important;
  cursor: pointer !important;
  box-shadow: 0 0 16px rgba(196, 168, 255, 0.15) !important;
  transition: all 0.2s ease !important;
}}
.mira-page-row button:hover {{
  border-color: #ffd27a !important;
  box-shadow: 0 0 18px rgba(255, 210, 122, 0.3) !important;
}}
.mira-page-row button.cosmos-active,
.mira-page-row button[aria-pressed="true"] {{
  background: rgba(196, 168, 255, 0.28) !important;
  border-color: #ffd27a !important;
  color: #ffd27a !important;
  box-shadow: 0 0 20px rgba(255, 210, 122, 0.45) !important;
}}

/* ═══════════════════════════════════════════════════════════════
   3. FLOATING GLASSMORPHIC SIDE CHATBOT (#cosmos-side-chat)
   ═══════════════════════════════════════════════════════════════ */
#cosmos-side-chat {{
  position: fixed;
  right: 68px;
  top: 50%;
  transform: translateY(-54%);
  width: 320px;
  height: 410px;
  max-width: calc(100vw - 90px);
  max-height: calc(100vh - 80px);
  background: rgba(18, 9, 34, 0.68);
  border: 1px solid rgba(255, 210, 122, 0.38);
  border-radius: 16px;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.75), 0 0 28px rgba(196, 168, 255, 0.2), inset 0 0 14px rgba(255, 210, 122, 0.08);
  z-index: 9998;
  font-family: 'Segoe UI', 'Share Tech Mono', sans-serif;
  color: #f3ebff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: height 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}}

#cosmos-side-chat.minimized {{
  height: 46px !important;
  overflow: hidden;
}}

#cosmos-chat-header {{
  padding: 10px 14px;
  background: rgba(26, 12, 48, 0.85);
  border-bottom: 1px solid rgba(255, 210, 122, 0.25);
  display: flex;
  justify-content: space-between;
  align-items: center;
  user-select: none;
}}

.cosmos-header-left {{
  display: flex;
  align-items: center;
  gap: 8px;
}}

.cosmos-brand-title {{
  font-family: 'Share Tech Mono', monospace;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: #ffd27a;
  text-shadow: 0 0 10px rgba(255, 210, 122, 0.4);
}}

.cosmos-status-pill {{
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  font-family: 'Share Tech Mono', monospace;
  letter-spacing: 0.12em;
  padding: 2px 7px;
  border-radius: 10px;
  background: rgba(87, 240, 194, 0.15);
  border: 1px solid rgba(87, 240, 194, 0.4);
  color: #57f0c2;
  transition: all 0.3s;
}}

.cosmos-status-dot {{
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #57f0c2;
  box-shadow: 0 0 8px #57f0c2;
}}

.cosmos-status-dot.talking {{
  background: #ffd27a;
  box-shadow: 0 0 12px #ffd27a;
  animation: cosmosPulse 0.9s infinite alternate;
}}

.cosmos-status-dot.listening {{
  background: #49e6f2;
  box-shadow: 0 0 12px #49e6f2;
  animation: cosmosPulse 0.9s infinite alternate;
}}

@keyframes cosmosPulse {{
  from {{ opacity: 0.55; transform: scale(0.85); }}
  to {{ opacity: 1; transform: scale(1.25); }}
}}

.cosmos-header-controls {{
  display: flex;
  align-items: center;
  gap: 6px;
}}

#cosmos-minimize-btn {{
  background: transparent;
  border: 1px solid rgba(196, 168, 255, 0.3);
  color: #c4a8ff;
  border-radius: 6px;
  width: 24px;
  height: 22px;
  font-size: 12px;
  font-family: monospace;
  line-height: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}}

#cosmos-minimize-btn:hover {{
  background: rgba(196, 168, 255, 0.2);
  color: #ffd27a;
  border-color: #ffd27a;
}}

#cosmos-chat-messages,
#cosmos-messages-scroll {{
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}}

#cosmos-chat-messages::-webkit-scrollbar {{
  width: 4px;
}}
#cosmos-chat-messages::-webkit-scrollbar-track {{
  background: transparent;
}}
#cosmos-chat-messages::-webkit-scrollbar-thumb {{
  background: rgba(196, 168, 255, 0.25);
  border-radius: 3px;
}}

.cosmos-bubble {{
  max-width: 88%;
  font-size: 12.5px;
  line-height: 1.45;
  word-break: break-word;
}}

.cosmos-bubble.cosmos-bot {{
  align-self: flex-start;
  background: rgba(45, 18, 72, 0.75);
  border: 1px solid rgba(196, 168, 255, 0.32);
  color: #f7f2ff;
  border-radius: 12px 12px 12px 2px;
  padding: 8px 12px;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.35);
}}

.cosmos-bubble.cosmos-user {{
  align-self: flex-end;
  background: rgba(85, 42, 138, 0.82);
  border: 1px solid rgba(255, 210, 122, 0.45);
  color: #ffffff;
  border-radius: 12px 12px 2px 12px;
  padding: 8px 12px;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.35);
}}

.cosmos-bubble pre {{
  background: rgba(10, 5, 20, 0.85);
  border: 1px solid rgba(196, 168, 255, 0.25);
  border-radius: 6px;
  padding: 8px;
  margin: 6px 0;
  overflow-x: auto;
  font-family: 'Share Tech Mono', monospace;
  font-size: 11px;
}}

#cosmos-input-bar {{
  display: flex;
  align-items: center;
  padding: 8px 10px;
  background: rgba(18, 9, 32, 0.92);
  border-top: 1px solid rgba(255, 210, 122, 0.2);
  gap: 6px;
}}

#cosmos-query-field {{
  flex: 1;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(196, 168, 255, 0.25);
  border-radius: 8px;
  padding: 8px 10px;
  color: #ffffff;
  font-family: inherit;
  font-size: 12px;
  outline: none;
  transition: all 0.2s;
}}

#cosmos-query-field:focus {{
  border-color: #ffd27a;
  background: rgba(255, 255, 255, 0.1);
}}

#cosmos-send-button {{
  background: rgba(255, 210, 122, 0.18);
  border: 1px solid rgba(255, 210, 122, 0.45);
  color: #ffd27a;
  border-radius: 8px;
  width: 34px;
  height: 34px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  transition: all 0.2s;
}}

#cosmos-send-button:hover {{
  background: rgba(255, 210, 122, 0.35);
  box-shadow: 0 0 12px rgba(255, 210, 122, 0.4);
}}
</style>

<!-- Floating Glassmorphic Side Chatbot -->
<div id="cosmos-side-chat" class="cosmos-chat-card">
  <div id="cosmos-chat-header">
    <div class="cosmos-header-left">
      <span class="cosmos-brand-title">COSMOS</span>
      <div class="cosmos-status-pill" id="cosmos-status-badge">
        <span class="cosmos-status-dot" id="cosmos-status-dot"></span>
        <span id="cosmos-status-text">ONLINE</span>
      </div>
    </div>
    <div class="cosmos-header-controls">
      <button id="cosmos-minimize-btn" title="Minimize / Restore">_</button>
    </div>
  </div>
  <div id="cosmos-chat-messages" class="cosmos-messages-scroll">
    <div class="cosmos-bubble cosmos-bot">
      Namaste Boss! Online and ready for your commands.
    </div>
  </div>
  <form id="cosmos-input-bar">
    <input id="cosmos-query-field" type="text" placeholder="Type a message..." autocomplete="off" />
    <button type="submit" id="cosmos-send-button" title="Send to COSMOS">➤</button>
  </form>
</div>

<script>
(function() {{
  const chatPanel = document.getElementById('cosmos-side-chat');
  const badge = document.getElementById('cosmos-status-badge');
  const dot = document.getElementById('cosmos-status-dot');
  const text = document.getElementById('cosmos-status-text');
  const scroll = document.getElementById('cosmos-chat-messages') || document.getElementById('cosmos-messages-scroll');
  const form = document.getElementById('cosmos-input-bar');
  const input = document.getElementById('cosmos-query-field');
  const minBtn = document.getElementById('cosmos-minimize-btn');

  let lastRenderedMsgId = 1;
  let lastWakeCounter = -1;
  let isMinimized = false;

  // Minimize Toggle
  if (minBtn && chatPanel) {{
    minBtn.addEventListener('click', (e) => {{
      e.stopPropagation();
      isMinimized = !isMinimized;
      chatPanel.classList.toggle('minimized', isMinimized);
      minBtn.textContent = isMinimized ? '□' : '_';
    }});
  }}

  function addMsg(content, isUser) {{
    if (!content || !content.trim()) return;
    const div = document.createElement('div');
    div.className = 'cosmos-bubble ' + (isUser ? 'cosmos-user' : 'cosmos-bot');
    
    // Format fenced code blocks if present
    if (content.includes('```')) {{
      const parts = content.split(/```(?:[a-zA-Z0-9_\\-\\.\\+]*\n)?(.*?)```/s);
      div.innerHTML = '';
      for (let i = 0; i < parts.length; i++) {{
        if (i % 2 === 1) {{
          const pre = document.createElement('pre');
          const code = document.createElement('code');
          code.textContent = parts[i];
          pre.appendChild(code);
          div.appendChild(pre);
        }} else if (parts[i]) {{
          const span = document.createElement('span');
          span.textContent = parts[i];
          div.appendChild(span);
        }}
      }}
    }} else {{
      div.textContent = content;
    }}
    
    scroll.appendChild(div);
    scroll.scrollTop = scroll.scrollHeight;
  }}

  // Click on bottom-left MIC button to toggle mic
  document.addEventListener('click', (e) => {{
    const target = e.target;
    if (target && target.matches && target.matches('.mira-page-row button')) {{
      const txt = (target.textContent || '').trim().toLowerCase();
      if (txt.startsWith('mic')) {{
        fetch('/api/mic_toggle', {{ method: 'POST' }}).catch(() => {{}});
      }}
    }}
  }});

  // Poll state every 200ms
  setInterval(() => {{
    fetch('/api/state')
      .then(res => res.ok ? res.json() : null)
      .then(d => {{
        if (!d) return;

        // 1. Sync React 3D Humanoid speaking/listening/idle state (triggers face light glow!)
        if (d.state && typeof window.__cosmos_set_state === 'function') {{
          window.__cosmos_set_state(d.state);
        }}

        // 2. Auto restart particle dust animation at 3x speed on wake word
        if (typeof d.wake_counter === 'number' && d.wake_counter !== lastWakeCounter) {{
          if (lastWakeCounter !== -1 && typeof window.__cosmos_restart_anim === 'function') {{
            window.__cosmos_restart_anim();
          }}
          lastWakeCounter = d.wake_counter;
        }}

        // 3. Render chat messages atomically in sequence
        if (Array.isArray(d.messages)) {{
          d.messages.forEach(m => {{
            if (m.id > lastRenderedMsgId) {{
              addMsg(m.text, m.sender === 'user');
              lastRenderedMsgId = m.id;
            }}
          }});
        }}

        // 4. Update and synchronize all bottom-left pills (IDLE, LISTENING, TALKING, MIC ON/OFF)
        const hudBtns = document.querySelectorAll('.mira-page-row button');
        hudBtns.forEach(btn => {{
          const btxt = (btn.textContent || '').trim().toLowerCase();
          if (btxt === 'idle' || btxt === 'listening' || btxt === 'talking') {{
            if (btxt === d.state) {{
              btn.setAttribute('aria-pressed', 'true');
              btn.classList.add('cosmos-active');
            }} else {{
              btn.setAttribute('aria-pressed', 'false');
              btn.classList.remove('cosmos-active');
            }}
          }} else if (btxt.startsWith('mic')) {{
            btn.textContent = 'MIC ' + (d.mic_enabled ? 'ON' : 'OFF');
            btn.setAttribute('aria-pressed', d.mic_enabled ? 'true' : 'false');
            if (d.mic_enabled) {{
              btn.classList.add('cosmos-active');
            }} else {{
              btn.classList.remove('cosmos-active');
            }}
          }}
        }});

        // 5. Update Floating Side Chatbot live status dot and text
        if (d.state === 'talking') {{
          dot.className = 'cosmos-status-dot talking';
          text.textContent = 'SPEAKING';
          badge.style.color = '#ffd27a';
          badge.style.borderColor = 'rgba(255,210,122,0.5)';
          badge.style.background = 'rgba(255,210,122,0.18)';
        }} else if (d.state === 'listening') {{
          dot.className = 'cosmos-status-dot listening';
          text.textContent = 'LISTENING';
          badge.style.color = '#49e6f2';
          badge.style.borderColor = 'rgba(73,230,242,0.5)';
          badge.style.background = 'rgba(73,230,242,0.18)';
        }} else {{
          dot.className = 'cosmos-status-dot';
          text.textContent = d.mic_enabled ? 'ONLINE' : 'MIC OFF';
          badge.style.color = '#57f0c2';
          badge.style.borderColor = 'rgba(87,240,194,0.45)';
          badge.style.background = 'rgba(87,240,194,0.18)';
        }}
      }})
      .catch(() => {{}});
  }}, 200);

  // Wire input bar to POST /api/command (and fallback /api/query)
  if (form) {{
    form.addEventListener('submit', (e) => {{
      e.preventDefault();
      const q = input.value.trim();
      if (!q) return;
      input.value = '';

      fetch('/api/command', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ command: q, query: q }})
      }}).catch(() => {{
        // Fallback to /api/query
        fetch('/api/query', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ query: q }})
        }}).catch(() => {{}});
      }});
    }});
  }}
}})();
</script>

  </body>
</html>
"""

target_paths = [
    'cosmos frontend/index.html',
    'Jarvis_Setup_Package/cosmos frontend/index.html'
]

for p in target_paths:
    with open(p, 'w', encoding='utf-8') as f:
        f.write(clean_html)
    print(f"[OK] Wrote perfected {p}: {os.path.getsize(p):,} bytes")
