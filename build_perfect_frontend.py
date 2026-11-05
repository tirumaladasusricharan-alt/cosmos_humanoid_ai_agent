import base64
import os

print("Building perfected COSMOS 3D Humanoid single-file frontend...")

# Read original base assets
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

# 1. SF: Always open 3D humanoid directly without any landing/ENTER page
sf_target = '[e,t]=Te.useState(()=>!!i.get("auto")||i.has("t"))'
sf_repl = '[e,t]=Te.useState(()=>!0)'
assert sf_target in js, "sf_target not found"
js = js.replace(sf_target, sf_repl)

# 2. xF: Initial speed 3x and expose window.__cosmos_restart_anim
xf_target = '[m,g]=Te.useState(1),v=Te.useRef({start:performance.now(),speed:1,pin:o})'
xf_repl = '[m,g]=Te.useState(3),v=Te.useRef({start:performance.now(),speed:3,pin:o});window.__cosmos_restart_anim=()=>{v.current.start=performance.now();v.current.speed=3;try{p(c=>c+1)}catch(e){}}'
assert xf_target in js, "xf_target not found"
js = js.replace(xf_target, xf_repl)

# 3. Shader: Radiant Face Spindle & Head Glowing Light (matching media_1793386683938_0feaf08e.jpg)
shader_target = 'if (vKind < 0.5) c += faceColor(tile) * faceGlow(tile) * 0.8;'
shader_repl = 'if (vKind < 0.5) c += 0.0;'
assert shader_target in js, "shader_target not found"
js = js.replace(shader_target, shader_repl)

# 4. qk: Face Glow flaring intensely when talking
qk_target = 'function qk(i,e,t,n){const r=Math.max(0,Math.min(1,i.talk||0)),o=Math.max(0,Math.min(1,i.voice||0)),a=Math.max(0,Math.min(.1,t)),c=e+(r-e)*Math.min(1,a*(r>e?.9:1.6)),h=c<.002?0:c;return{warm:h,glow:n.glow*h*(.55+.65*o),move:n.move*9*(.25*r+.75*o)}}'
qk_repl = 'function qk(i,e,t,n){const isSpk=(window.__cosmos_state==="talking");const r=isSpk?1:Math.max(0,Math.min(1,i.talk||0)),o=isSpk?(0.95+0.35*Math.sin(performance.now()*0.015)):Math.max(0,Math.min(1,i.voice||0)),a=Math.max(0,Math.min(.1,t)),c=e+(r-e)*Math.min(1,a*(r>e?.9:1.6)),h=c<.002?0:c;const gl=isSpk?(n.glow*1.9*(0.85+0.35*o)):(n.glow*h*(.55+.65*o));return{warm:isSpk?1:h,glow:gl,move:n.move*9*(.25*r+.75*o)}}'
assert qk_target in js, "qk_target not found"
js = js.replace(qk_target, qk_repl)

# 5. gF: Reactively feed speech energy pulse to YU
gf_target = 'function gF({state:i}){return nh((e,t)=>{const n=i==="talking"||i==="speaking";YU(t,{energy:M_("output"),speaking:n,listening:i==="listening"})}),null}'
gf_repl = 'function gF({state:i}){return nh((e,t)=>{const n=i==="talking"||i==="speaking"||window.__cosmos_state==="talking";const eng=n?(0.95+0.35*Math.sin(performance.now()*0.015)):M_("output");YU(t,{energy:eng,speaking:n,listening:i==="listening"})}),null}'
assert gf_target in js, "gf_target not found"
js = js.replace(gf_target, gf_repl)

# Escape </script>
js_safe = js.replace('</script>', '<\\/script>')

# Build the complete HTML
full_html = f"""<!doctype html>
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

<!-- COSMOS HUD Glassmorphism Chat & Single Bottom-Left MIC Button -->
<style>
/* 1. Filter template UI: keep ONLY the bottom-left MIC ON/OFF button */
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
  background: rgba(10, 12, 18, 0.85) !important;
  border: 1px solid rgba(255, 255, 255, 0.45) !important;
  color: #ffffff !important;
  border-radius: 9px !important;
  padding: 10px 22px !important;
  font-size: 13px !important;
  font-family: 'Share Tech Mono', monospace !important;
  letter-spacing: 0.16em !important;
  box-shadow: 0 0 18px rgba(255, 255, 255, 0.22) !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
}}
.mira-page-row button:hover {{
  background: rgba(25, 30, 44, 0.92) !important;
  box-shadow: 0 0 25px rgba(255, 255, 255, 0.45) !important;
}}

/* 2. Sleek Glassmorphism Chat Card (Right-Side, matching User Mockup) */
#cosmos-chat-card {{
  position: fixed;
  right: 24px;
  top: 50px;
  bottom: 50px;
  width: 360px;
  max-width: calc(100vw - 48px);
  background: rgba(12, 15, 22, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.32);
  border-radius: 18px;
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7), 0 0 28px rgba(255, 255, 255, 0.18);
  z-index: 9999;
  font-family: 'Segoe UI', 'Share Tech Mono', sans-serif;
  color: #ffffff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1), opacity 0.3s;
}}

#cosmos-chat-header {{
  padding: 14px 18px;
  background: rgba(16, 20, 30, 0.88);
  border-bottom: 1px solid rgba(255, 255, 255, 0.22);
  display: flex;
  justify-content: space-between;
  align-items: center;
  user-select: none;
}}
.cosmos-header-left {{
  display: flex;
  align-items: center;
  gap: 10px;
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
  background: #ffffff;
  box-shadow: 0 0 15px #ffffff;
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
  background: rgba(255, 255, 255, 0.25);
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
  background: rgba(20, 24, 36, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.35);
  color: #ffffff;
  border-radius: 14px 14px 14px 3px;
  padding: 10px 14px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
}}
.cosmos-bubble.cosmos-user {{
  align-self: flex-end;
  background: rgba(35, 45, 65, 0.90);
  border: 1px solid rgba(255, 255, 255, 0.5);
  color: #ffffff;
  border-radius: 14px 14px 3px 14px;
  padding: 10px 14px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
}}

#cosmos-input-bar {{
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background: rgba(12, 15, 22, 0.92);
  border-top: 1px solid rgba(255, 255, 255, 0.25);
  gap: 8px;
}}
#cosmos-query-field {{
  flex: 1;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.28);
  border-radius: 10px;
  padding: 10px 14px;
  color: #ffffff;
  font-family: inherit;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s, background 0.2s;
}}
#cosmos-query-field:focus {{
  border-color: #ffffff;
  background: rgba(255, 255, 255, 0.1);
}}
#cosmos-send-button {{
  background: rgba(255, 255, 255, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.45);
  color: #ffffff;
  border-radius: 10px;
  width: 40px;
  height: 40px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  transition: all 0.2s;
}}
#cosmos-send-button:hover {{
  background: rgba(255, 255, 255, 0.4);
  color: #ffffff;
  box-shadow: 0 0 12px rgba(255, 255, 255, 0.35);
}}
</style>

<div id="cosmos-chat-card">
  <div id="cosmos-chat-header">
    <div class="cosmos-header-left">
      <span class="cosmos-brand-title">COSMOS</span>
    </div>
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

  let lastTranscript = '';
  let lastResponse = '';
  let lastWakeCounter = -1;

  function addMsg(content, isUser) {{
    if (!content || !content.trim()) return;
    const div = document.createElement('div');
    div.className = 'cosmos-bubble ' + (isUser ? 'cosmos-user' : 'cosmos-bot');
    div.textContent = content;
    scroll.appendChild(div);
    scroll.scrollTop = scroll.scrollHeight;
  }}

  // Initialize Web Audio on first interaction/load
  function unlockAudio() {{
    try {{
      if (typeof window.bg === 'function') window.bg();
    }} catch(e) {{}}
  }}
  window.addEventListener('click', unlockAudio, {{ once: true }});
  window.addEventListener('keydown', unlockAudio, {{ once: true }});

  // Poll state every 250ms
  setInterval(() => {{
    fetch('/api/state')
      .then(res => res.ok ? res.json() : null)
      .then(d => {{
        if (!d) return;

        window.__cosmos_state = d.state;

        // Auto restart humanoid dust-to-model animation at 3x speed on wake word
        if (typeof d.wake_counter === 'number' && d.wake_counter !== lastWakeCounter) {{
          if (lastWakeCounter !== -1 && typeof window.__cosmos_restart_anim === 'function') {{
            window.__cosmos_restart_anim();
          }}
          lastWakeCounter = d.wake_counter;
        }}

        // Update single bottom-left button text
        const micBtn = document.querySelector('.mira-page-row button:last-child');
        if (micBtn) {{
          micBtn.textContent = 'MIC ' + (d.mic_enabled ? 'ON' : 'OFF');
        }}

        if (d.state === 'talking') {{
          dot.className = 'cosmos-status-dot talking';
          text.textContent = 'SPEAKING';
          badge.style.color = '#ffffff';
          badge.style.borderColor = 'rgba(255,255,255,0.45)';
          badge.style.background = 'rgba(255,255,255,0.18)';
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

        if (d.last_transcript && d.last_transcript !== lastTranscript) {{
          lastTranscript = d.last_transcript;
          addMsg(d.last_transcript, true);
        }}

        if (d.last_response && d.last_response !== lastResponse) {{
          lastResponse = d.last_response;
          addMsg(d.last_response, false);
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
      addMsg(q, true);
      lastTranscript = q;

      fetch('/api/query', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ query: q }})
      }})
      .then(res => res.ok ? res.json() : null)
      .then(d => {{
        if (d && d.response) {{
          lastResponse = d.response;
          addMsg(d.response, false);
        }}
      }})
      .catch(() => {{}});
    }});
  }}
}})();
</script>

  </body>
</html>
"""

# Write to both frontend locations
target_paths = [
    'cosmos frontend/index.html',
    'Jarvis_Setup_Package/cosmos frontend/index.html'
]

for p in target_paths:
    with open(p, 'w', encoding='utf-8') as f:
        f.write(full_html)
    size = os.path.getsize(p)
    print(f"[OK] Generated {p}: {size:,} bytes")

