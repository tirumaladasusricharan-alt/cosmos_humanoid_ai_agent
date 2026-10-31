import base64
import os

print("Rebuilding frontend with React state bridge for glowing speech...")

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
/* 1. Only show single MIC button on bottom left */
.mira-own-row {{
  display: none !important;
}}
.mira-page-row button:not(:last-child) {{
  display: none !important;
}}
.mira-page-row {{
  position: fixed !important;
  left: 24px !important;
  bottom: 24px !important;
  z-index: 9999 !important;
  display: flex !important;
}}
.mira-page-row button {{
  background: rgba(18, 8, 36, 0.78) !important;
  border: 1px solid rgba(196, 168, 255, 0.45) !important;
  color: #c4a8ff !important;
  border-radius: 9px !important;
  padding: 10px 22px !important;
  font-size: 13px !important;
  font-family: 'Share Tech Mono', monospace !important;
  letter-spacing: 0.16em !important;
  box-shadow: 0 0 18px rgba(196, 168, 255, 0.22) !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
}}
.mira-page-row button:hover {{
  background: rgba(45, 20, 80, 0.9) !important;
  box-shadow: 0 0 25px rgba(196, 168, 255, 0.45) !important;
}}

/* 2. Glassmorphism Chat Box on Right Side */
#cosmos-chat-card {{
  position: fixed;
  right: 24px;
  top: 50px;
  bottom: 50px;
  width: 360px;
  max-width: calc(100vw - 48px);
  background: rgba(20, 10, 36, 0.65);
  border: 1px solid rgba(196, 168, 255, 0.32);
  border-radius: 18px;
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7), 0 0 28px rgba(196, 168, 255, 0.18);
  z-index: 9999;
  font-family: 'Segoe UI', 'Share Tech Mono', sans-serif;
  color: #f2eaff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}}

#cosmos-chat-header {{
  padding: 14px 18px;
  background: rgba(28, 14, 50, 0.82);
  border-bottom: 1px solid rgba(196, 168, 255, 0.22);
  display: flex;
  justify-content: space-between;
  align-items: center;
  user-select: none;
}}
.cosmos-brand-title {{
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: #ffffff;
}}
.cosmos-status-pill {{
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  letter-spacing: 0.12em;
  padding: 3px 9px;
  border-radius: 12px;
  background: rgba(87, 240, 194, 0.15);
  border: 1px solid rgba(87, 240, 194, 0.45);
  color: #57f0c2;
  transition: all 0.3s;
}}
.cosmos-status-dot {{
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #57f0c2;
  box-shadow: 0 0 10px #57f0c2;
}}
.cosmos-status-dot.talking {{
  background: #c4a8ff;
  box-shadow: 0 0 15px #c4a8ff;
  animation: cosmosPulse 1.1s infinite alternate;
}}
.cosmos-status-dot.listening {{
  background: #49e6f2;
  box-shadow: 0 0 12px #49e6f2;
}}
@keyframes cosmosPulse {{
  from {{ opacity: 0.55; transform: scale(0.85); }}
  to {{ opacity: 1; transform: scale(1.25); }}
}}

#cosmos-messages-scroll {{
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}}
#cosmos-messages-scroll::-webkit-scrollbar {{
  width: 5px;
}}
#cosmos-messages-scroll::-webkit-scrollbar-track {{
  background: transparent;
}}
#cosmos-messages-scroll::-webkit-scrollbar-thumb {{
  background: rgba(196, 168, 255, 0.25);
  border-radius: 4px;
}}

.cosmos-bubble {{
  max-width: 85%;
  font-size: 13px;
  line-height: 1.5;
  word-break: break-word;
}}
.cosmos-bubble.cosmos-bot {{
  align-self: flex-start;
  background: rgba(48, 22, 78, 0.72);
  border: 1px solid rgba(196, 168, 255, 0.35);
  color: #f7f2ff;
  border-radius: 14px 14px 14px 3px;
  padding: 10px 14px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
}}
.cosmos-bubble.cosmos-user {{
  align-self: flex-end;
  background: rgba(85, 42, 138, 0.85);
  border: 1px solid rgba(220, 190, 255, 0.5);
  color: #ffffff;
  border-radius: 14px 14px 3px 14px;
  padding: 10px 14px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
}}

#cosmos-input-bar {{
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background: rgba(20, 10, 36, 0.9);
  border-top: 1px solid rgba(196, 168, 255, 0.2);
  gap: 8px;
}}
#cosmos-query-field {{
  flex: 1;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(196, 168, 255, 0.28);
  border-radius: 10px;
  padding: 10px 14px;
  color: #ffffff;
  font-family: inherit;
  font-size: 13px;
  outline: none;
}}
#cosmos-query-field:focus {{
  border-color: #c4a8ff;
  background: rgba(255, 255, 255, 0.1);
}}
#cosmos-send-button {{
  background: rgba(196, 168, 255, 0.22);
  border: 1px solid rgba(196, 168, 255, 0.45);
  color: #c4a8ff;
  border-radius: 10px;
  width: 40px;
  height: 40px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
}}
</style>

<div id="cosmos-chat-card">
  <div id="cosmos-chat-header">
    <span class="cosmos-brand-title">COSMOS</span>
    <div class="cosmos-status-pill" id="cosmos-status-badge">
      <span class="cosmos-status-dot" id="cosmos-status-dot"></span>
      <span id="cosmos-status-text">ONLINE</span>
    </div>
  </div>
  <div id="cosmos-messages-scroll">
    <div class="cosmos-bubble cosmos-bot">
      Namaste Boss! Online and ready for your commands.
    </div>
  </div>
  <form id="cosmos-input-bar">
    <input id="cosmos-query-field" type="text" placeholder="Type a message..." autocomplete="off" />
    <button type="submit" id="cosmos-send-button" title="Send command">➤</button>
  </form>
</div>

<script>
(function() {{
  const badge = document.getElementById('cosmos-status-badge');
  const dot = document.getElementById('cosmos-status-dot');
  const text = document.getElementById('cosmos-status-text');
  const scroll = document.getElementById('cosmos-messages-scroll');
  const form = document.getElementById('cosmos-input-bar');
  const input = document.getElementById('cosmos-query-field');

  let lastRenderedMsgId = 1;
  let lastWakeCounter = -1;

  function addMsg(content, isUser) {{
    if (!content || !content.trim()) return;
    const div = document.createElement('div');
    div.className = 'cosmos-bubble ' + (isUser ? 'cosmos-user' : 'cosmos-bot');
    div.textContent = content;
    scroll.appendChild(div);
    scroll.scrollTop = scroll.scrollHeight;
  }}

  // Poll state every 250ms
  setInterval(() => {{
    fetch('/api/state')
      .then(res => res.ok ? res.json() : null)
      .then(d => {{
        if (!d) return;

        // Sync React 3D Humanoid speaking/listening/idle state (triggers face light glow!)
        if (d.state && typeof window.__cosmos_set_state === 'function') {{
          window.__cosmos_set_state(d.state);
        }}

        // Auto restart particle dust animation at 3x speed on wake word
        if (typeof d.wake_counter === 'number' && d.wake_counter !== lastWakeCounter) {{
          if (lastWakeCounter !== -1 && typeof window.__cosmos_restart_anim === 'function') {{
            window.__cosmos_restart_anim();
          }}
          lastWakeCounter = d.wake_counter;
        }}

        // Render messages atomically in sequence
        if (Array.isArray(d.messages)) {{
          d.messages.forEach(m => {{
            if (m.id > lastRenderedMsgId) {{
              addMsg(m.text, m.sender === 'user');
              lastRenderedMsgId = m.id;
            }}
          }});
        }}

        // Update single bottom-left button
        const micBtn = document.querySelector('.mira-page-row button:last-child');
        if (micBtn) {{
          micBtn.textContent = 'MIC ' + (d.mic_enabled ? 'ON' : 'OFF');
        }}

        if (d.state === 'talking') {{
          dot.className = 'cosmos-status-dot talking';
          text.textContent = 'SPEAKING';
          badge.style.color = '#c4a8ff';
          badge.style.borderColor = 'rgba(196,168,255,0.45)';
          badge.style.background = 'rgba(196,168,255,0.18)';
        }} else if (d.state === 'listening') {{
          dot.className = 'cosmos-status-dot listening';
          text.textContent = 'LISTENING';
          badge.style.color = '#49e6f2';
          badge.style.borderColor = 'rgba(73,230,242,0.45)';
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
  }}, 250);

  if (form) {{
    form.addEventListener('submit', (e) => {{
      e.preventDefault();
      const q = input.value.trim();
      if (!q) return;
      input.value = '';

      fetch('/api/query', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ query: q }})
      }}).catch(() => {{}});
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
    print(f"[OK] Wrote bridged {p}: {os.path.getsize(p):,} bytes")
