"""
cosmos_minicpm_agency_skills.py - OpenBMB/MiniCPM-V Multimodal Skills Engine for COSMOS
Architected exclusively for Sri Charan Tirumaladasu ("Boss" / "Charan" / "Sir")
Execution Mode: Pure RAM (0 MB Disk Bloat) with Local Ollama Auto-Detection & Groq Vision Fallback
"""

import base64
import collections
import io
import os
import re
import threading
import time
from typing import Any, Deque, Dict, List, Optional, Tuple

import requests

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# Optional Windows screen grabber for UI Grounding & OCR (RAM-only)
try:
    from PIL import ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

OLLAMA_ENDPOINT = os.environ.get("LLM_ENDPOINT", "http://localhost:11434")


# =====================================================================
# 1. MINICPM-V 4 CORE MULTIMODAL SKILLS (RAM-ONLY + OLLAMA AUTO-DETECT)
# =====================================================================
class CosmosMiniCPMVSkillsEngine:
    """
    Implements OpenBMB/MiniCPM-V's 4 flagship multimodal skills in RAM:
    Skill 1: High-Density OCR & Document/Table-to-Markdown Extraction
    Skill 2: Desktop & Browser UI Coordinate Grounding ([x, y] target locator)
    Skill 3: Multi-Frame Temporal Video Understanding (3-frame RAM ring buffer)
    Skill 4: Live Webcam Affective & Micro-Expression Resonance
    """

    VISION_MODEL_CANDIDATES = (
        "minicpm-v",
        "llava",
        "llama3.2-vision",
        "qwen2.5vl",
        "bakllava",
        "moondream",
    )

    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        # Rolling 3-frame RAM ring buffer for temporal video skill (0 MB disk)
        self.frame_ring_buffer: Deque[str] = collections.deque(maxlen=3)
        self._lock = threading.Lock()
        self.detected_ollama_vision_model: Optional[str] = self._detect_installed_ollama_vision_model()
        threading.Thread(target=self._ram_camera_daemon, daemon=True).start()

    def _detect_installed_ollama_vision_model(self) -> Optional[str]:
        """Queries local Ollama /api/tags without downloading anything (0 MB disk)."""
        try:
            r = requests.get(f"{OLLAMA_ENDPOINT}/api/tags", timeout=3)
            if r.status_code == 200:
                models = [m.get("name", "").lower() for m in r.json().get("models", [])]
                for candidate in self.VISION_MODEL_CANDIDATES:
                    for installed in models:
                        if candidate in installed:
                            return installed
        except Exception:
            pass
        return None

    def _ram_camera_daemon(self):
        """Captures 640x360 JPEG frames into the 3-frame RAM ring buffer, bridging browser feed if active."""
        while True:
            # First check if the browser has sent a live frame to COSMOS_UNIFIED_STATE
            try:
                import cosmos_unified_mega_suite
                b64_relay = cosmos_unified_mega_suite.COSMOS_UNIFIED_STATE.get("camera_frame_b64", "")
                ts = cosmos_unified_mega_suite.COSMOS_UNIFIED_STATE.get("camera_frame_timestamp", 0)
                if b64_relay and (time.monotonic() - ts < 15 or ts == 0):
                    with self._lock:
                        if not self.frame_ring_buffer or self.frame_ring_buffer[-1] != b64_relay:
                            self.frame_ring_buffer.append(b64_relay)
                    time.sleep(2.0)
                    continue
            except Exception:
                pass

            # Otherwise attempt local OpenCV webcam capture if available
            if CV2_AVAILABLE:
                cap = None
                try:
                    if hasattr(cv2, "setLogLevel"):
                        cv2.setLogLevel(0)
                    cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
                    if not cap.isOpened():
                        cap = cv2.VideoCapture(self.camera_index)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret:
                            small = cv2.resize(frame, (640, 360))
                            _, buf = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 75])
                            b64_frame = base64.b64encode(buf).decode("utf-8")
                            with self._lock:
                                self.frame_ring_buffer.append(b64_frame)
                except Exception:
                    pass
                finally:
                    if cap is not None:
                        try:
                            cap.release()
                        except Exception:
                            pass
            time.sleep(2.0)

    def capture_desktop_ram_b64(self) -> str:
        """Captures the active Windows screen strictly in RAM for OCR / UI Grounding."""
        if not PIL_AVAILABLE:
            return ""
        try:
            img = ImageGrab.grab()
            img.thumbnail((1280, 720))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=80)
            return base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception:
            return ""

    def get_latest_webcam_frames(self, count: int = 1) -> List[str]:
        with self._lock:
            frames = list(self.frame_ring_buffer)
        if not frames:
            try:
                import cosmos_unified_mega_suite
                b64 = cosmos_unified_mega_suite.COSMOS_UNIFIED_STATE.get("camera_frame_b64", "")
                if b64:
                    return [b64]
            except Exception:
                pass
        return frames[-count:] if frames else []

    def _dispatch_multimodal(self, skill_prompt: str, b64_images: List[str]) -> str:
        """Routes vision skills to local Ollama vision model -> Groq Vision -> Zero Disk Fallback."""
        if not b64_images:
            return "[Visual Skill Notice]: No camera or screen frame available in RAM."

        # Route 1: Installed Local Ollama Vision Model (e.g., minicpm-v, llava, qwen2.5vl)
        if self.detected_ollama_vision_model:
            try:
                r = requests.post(
                    f"{OLLAMA_ENDPOINT}/api/chat",
                    json={
                        "model": self.detected_ollama_vision_model,
                        "messages": [{
                            "role": "user",
                            "content": skill_prompt,
                            "images": b64_images,
                        }],
                        "stream": False,
                    },
                    timeout=45,
                )
                if r.status_code == 200:
                    ans = r.json().get("message", {}).get("content", "")
                    if ans:
                        return ans
            except Exception:
                pass

        # Route 2: Zero-Storage Groq Vision Fallback (llama-3.2-11b-vision-preview)
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if groq_key:
            content_payload: List[Dict[str, Any]] = [{"type": "text", "text": skill_prompt}]
            for img_b64 in b64_images[:2]:
                content_payload.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                })
            try:
                r = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}"},
                    json={
                        "model": "llama-3.2-11b-vision-preview",
                        "messages": [{"role": "user", "content": content_payload}],
                    },
                    timeout=20,
                )
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"]
            except Exception:
                pass

        return (
            "[MiniCPM-V Router]: No local vision weight detected in Ollama (`/api/tags`) "
            "and `GROQ_API_KEY` not set. Ready for local vision model when pulled by Boss Charan."
        )

    # --- SKILL 1: HIGH-DENSITY OCR & DOCUMENT TABLE PARSER ---
    def skill_scene_ocr_and_table(self, user_query: str, source: str = "screen") -> str:
        img = (
            self.capture_desktop_ram_b64()
            if source == "screen"
            else (self.get_latest_webcam_frames(1) or [""])[0]
        )
        prompt = (
            f"Execute MiniCPM-V High-Density OCR Skill for Boss Sri Charan Tirumaladasu: "
            f"Extract all visible text, code, error tracebacks, or tables into clean Markdown with 100% fidelity. "
            f"User request: {user_query}"
        )
        return self._dispatch_multimodal(prompt, [img] if img else [])

    # --- SKILL 2: UI ELEMENT COORDINATE GROUNDING ---
    def skill_ground_ui_element(self, target_description: str) -> str:
        img = self.capture_desktop_ram_b64()
        prompt = (
            f"Execute MiniCPM-V UI Grounding Skill: Locate the UI element '{target_description}' on screen "
            f"and return its normalized coordinates as JSON: "
            f'`{{"element": "...", "x_pct": 0.0-1.0, "y_pct": 0.0-1.0, "confidence": 0.0-1.0}}`.'
        )
        return self._dispatch_multimodal(prompt, [img] if img else [])

    # --- SKILL 3: MULTI-FRAME TEMPORAL VIDEO & GESTURE UNDERSTANDING ---
    def skill_temporal_video_analysis(self, user_query: str) -> str:
        frames = self.get_latest_webcam_frames(count=3)
        prompt = (
            f"Execute MiniCPM-V Temporal Video Skill across these sequential webcam frames: "
            f"Describe motion, gestures, or physical objects Boss Charan is showing over time. "
            f"Request: {user_query}"
        )
        return self._dispatch_multimodal(prompt, frames)

    # --- SKILL 4: WEBCAM AFFECT & POSTURE CHECK ---
    def skill_detect_boss_visual_affect(self) -> str:
        frames = self.get_latest_webcam_frames(count=1)
        prompt = (
            "Briefly classify Boss Charan's current desk posture and facial focus in 1 short sentence "
            "(e.g., 'deeply focused', 'smiling', 'tired', or 'holding hardware')."
        )
        return self._dispatch_multimodal(prompt, frames)


minicpm_skills = CosmosMiniCPMVSkillsEngine()

