"""
ExplainIt3D — Interactive 3D Model Viewer with Part Annotations
A modern prototype inspection tool for engineering reports, demos, and presentations.
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import base64
from datetime import datetime
from pathlib import Path
import time

# Persistent storage paths for uploaded custom prototype
APP_DIR = Path(__file__).parent.resolve()
CUSTOM_GLB_PATH = APP_DIR / "custom_prototype.glb"
CUSTOM_META_PATH = APP_DIR / "custom_prototype_meta.json"

# -----------------------------------------------------------------------------
# 1. PAGE SETUP & SPACIOUS 2026 OBSIDIAN/SLATE DESIGN SYSTEM
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Interactive Prototype Inspector",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS: Removes Streamlit clutter and unlocks expansive screen width
st.markdown(
    """
    <style>
    /* Clutter removal: clean uncluttered canvas */
    #MainMenu {visibility: hidden; display: none !important;}
    footer {visibility: hidden; display: none !important;}
    header {visibility: hidden; display: none !important;}
    .stDeployButton {display: none !important;}
    [data-testid="stToolbar"] {visibility: hidden; display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}

    /* Global typography and background */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", "Plus Jakarta Sans", sans-serif;
        color: #f8fafc;
        background-color: #080c14;
    }

    /* Expansive widescreen container with generous breathing room */
    .block-container {
        padding-top: 1.25rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 96% !important;
        width: 96% !important;
    }

    @media (min-width: 1600px) {
        .block-container {
            max-width: 1540px !important;
        }
    }

    /* Clean modern inputs */
    .stSelectbox label {
        font-size: 12px !important;
        font-weight: 600 !important;
        color: #94a3b8 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        margin-bottom: 4px !important;
    }
    .stSelectbox > div > div {
        background-color: #111827 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-size: 14px !important;
    }

    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* Clean modern expander headers with generous padding */
    .streamlit-expanderHeader {
        background-color: #111827 !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #e2e8f0 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 12px 18px !important;
    }
    .streamlit-expanderContent {
        background-color: #0d121f !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-top: none !important;
        border-radius: 0 0 14px 14px !important;
        padding: 20px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Injected parent-level hover delete cross button on model selectbox options
st.html(
    """
    <style>
    [role="option"] {
        position: relative !important;
        padding-right: 44px !important;
        cursor: pointer !important;
    }

    /* Floating overlay delete button that hovers over the active dropdown option */
    #model-hover-del-btn {
        position: fixed !important;
        width: 22px !important;
        height: 22px !important;
        border-radius: 50% !important;
        background: rgba(239, 68, 68, 0.88) !important;
        border: 1.5px solid rgba(255, 255, 255, 0.9) !important;
        color: #ffffff !important;
        font-size: 13px !important;
        font-weight: 800 !important;
        cursor: pointer !important;
        display: none;
        align-items: center !important;
        justify-content: center !important;
        z-index: 2147483647 !important;
        line-height: 1 !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5), 0 0 10px rgba(239, 68, 68, 0.8) !important;
        transition: transform 0.12s ease, background 0.12s ease !important;
        user-select: none !important;
        pointer-events: auto !important;
    }

    #model-hover-del-btn:hover {
        background: #dc2626 !important;
        transform: translateY(-50%) scale(1.22) !important;
        box-shadow: 0 4px 14px rgba(239, 68, 68, 1) !important;
    }
    </style>

    <script>
    (function initModelOptionDeleters() {
        let delBtn = document.getElementById('model-hover-del-btn');
        if (!delBtn) {
            delBtn = document.createElement('div');
            delBtn.id = 'model-hover-del-btn';
            delBtn.innerHTML = '&#10005;';
            document.body.appendChild(delBtn);
        }

        let currentTargetModel = '';
        let hideTimer = null;

        function getOptionModelName(opt) {
            if (!opt) return '';
            let modelName = '';
            for (let i = 0; i < opt.childNodes.length; i++) {
                const node = opt.childNodes[i];
                if (node.nodeType === 3 && node.textContent.trim()) {
                    modelName = node.textContent.trim();
                    break;
                } else if (node.nodeType === 1 && node.id !== 'model-hover-del-btn') {
                    modelName = node.innerText.trim();
                    if (modelName) break;
                }
            }
            if (!modelName) modelName = opt.innerText.trim();
            if (modelName) {
                modelName = modelName.split('\\n')[0].trim();
            }
            return modelName;
        }

        function showBtnForOption(opt) {
            const name = getOptionModelName(opt);
            if (!name) return;
            currentTargetModel = name;
            delBtn.title = 'Remove "' + name + '"';

            const rect = opt.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) return;

            delBtn.style.top = (rect.top + rect.height / 2) + 'px';
            delBtn.style.left = (rect.right - 32) + 'px';
            delBtn.style.transform = 'translateY(-50%)';
            delBtn.style.display = 'flex';
        }

        document.addEventListener('mouseover', function(e) {
            const opt = e.target.closest('[role="option"]');
            if (opt) {
                clearTimeout(hideTimer);
                showBtnForOption(opt);
            } else if (e.target === delBtn) {
                clearTimeout(hideTimer);
            } else {
                hideTimer = setTimeout(() => {
                    delBtn.style.display = 'none';
                }, 150);
            }
        }, true);

        delBtn.addEventListener('mousedown', function(e) {
            e.stopPropagation();
            e.preventDefault();
        }, true);

        delBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            e.preventDefault();
            if (!currentTargetModel) return;
            const target = currentTargetModel;
            delBtn.style.display = 'none';
            const url = new URL(window.location.href);
            url.searchParams.set('delete_model', target);
            window.location.href = url.href;
        }, true);
    })();
    </script>
    """,
    unsafe_allow_javascript=True,
)

# -----------------------------------------------------------------------------
# 2. 3D MODELS CATALOG WITH PRECISE FRAMING & PROTOTYPE METADATA
# -----------------------------------------------------------------------------
SAMPLE_MODELS = {
    "My Laptop": {
        "url": "https://raw.githubusercontent.com/dhruvachitragar9-cmyk/explainit3d/main/laptop.glb",
        "camera_orbit": "28deg 68deg 3.95m",
        "camera_target": "-0.2m 1.0m 0m",
        "field_of_view": "30deg",
        "category": "Student Hardware Prototype",
    },
    "Engine": {
        "url": "https://alteirac.com/models/engine/scene.gltf",
        "camera_orbit": "45deg 70deg auto",
        "camera_target": "auto auto auto",
        "field_of_view": "auto",
        "category": "Mechanical Powertrain Assembly",
    },
    "Helmet": {
        "url": "https://alteirac.com/models/helmet/scene.gltf",
        "camera_orbit": "35deg 75deg auto",
        "camera_target": "auto auto auto",
        "field_of_view": "auto",
        "category": "Protective Equipment Prototype",
    },
    "Turbine": {
        "url": "https://alteirac.com/models/turbine/scene.gltf",
        "camera_orbit": "45deg 65deg auto",
        "camera_target": "auto auto auto",
        "field_of_view": "auto",
        "category": "Aerospace & Energy Prototype",
    },
}

# -----------------------------------------------------------------------------
# 3. ACCURATE PART SPECIFICATIONS (MATERIAL, FUNCTION, NOTES)
# -----------------------------------------------------------------------------
MODEL_DATA = {
    "My Laptop": {
        "Screen": {
            "position": "-1.45 1.50 0.0",
            "normal": "0.98 -0.19 0",
            "material": "IPS / Mini-LED Anti-Glare Glass Panel with Anodized Aluminum Lid",
            "function": "16:10 High-resolution display delivering primary visual output and UI rendering.",
            "notes": "Bezel-less chassis integration, 400-nit peak brightness, 100% sRGB color gamut.",
        },
        "Keyboard": {
            "position": "-0.15 0.10 0.0",
            "normal": "0 1 0",
            "material": "Polycarbonate Keycaps over Scissor-Switch Tactile Membrane with LED Backlighting",
            "function": "Primary alphanumeric input device with ergonomic 1.3mm key travel distance.",
            "notes": "Equipped with ambient light sensing, spill resistance, and low-profile switches.",
        },
        "Trackpad": {
            "position": "1.00 0.08 0.0",
            "normal": "0 1 0",
            "material": "Etched Satin-Finish Tempered Glass with Integrated Capacitive Sensors",
            "function": "Multi-touch gesture navigation, sub-millimeter cursor tracking, and haptic clicks.",
            "notes": "Solid-state non-mechanical design with uniform edge-to-edge response and palm rejection.",
        },
        "HD Camera": {
            "position": "-1.67 2.45 0.0",
            "normal": "0.98 -0.19 0",
            "material": "Multi-Element Optical Glass Lens with 1080p CMOS Image Sensor & Status LED",
            "function": "Captures high-definition video for conferences and facial biometric recognition.",
            "notes": "Housed within the ultra-narrow upper bezel alongside dual beamforming microphones.",
        },
        "Dual-Axle Hinge": {
            "position": "-1.22 0.06 0.0",
            "normal": "0 1 0",
            "material": "High-Tensile Zinc Alloy & Stainless Steel Friction Clutch Mechanism",
            "function": "Provides smooth 145-degree lid articulation and holds display firmly at any tilt angle.",
            "notes": "Cycle-tested for >25,000 openings while safely shielding internal LVDS ribbon cables.",
        },
        "Thunderbolt / USB-C": {
            "position": "-0.40 0.02 -2.00",
            "normal": "0 0 -1",
            "material": "Reinforced Nickel-Plated Copper Alloy with Grounded EMI Shielding",
            "function": "High-speed data transfer (up to 40 Gbps), 100W Power Delivery, and external 4K video.",
            "notes": "Dual reversible ports supporting universal docking, eGPU arrays, and fast NVMe storage.",
        },
    },
    "Engine": {
        "Engine Block": {
            "position": "0.05 0.35 0.15",
            "normal": "0 0 1",
            "material": "Cast Aluminum-Silicon Alloy (A356-T6)",
            "function": "Houses the cylinders, coolant passages, and core reciprocating components.",
            "notes": "Engineered for optimal strength-to-weight ratio and efficient thermal dissipation.",
        },
        "Exhaust Manifold": {
            "position": "-0.25 0.20 0.05",
            "normal": "-1 0 0",
            "material": "Austenitic Stainless Steel (AISI 304)",
            "function": "Collects hot exhaust gases from cylinders and routes them smoothly to the catalytic converter.",
            "notes": "Engineered to withstand extreme thermal cycles up to 850°C without warping or oxidation.",
        },
        "Intake Valve Assembly": {
            "position": "0.15 0.45 -0.10",
            "normal": "0 1 0",
            "material": "Forged Chrome-Silicon Alloy Steel (Silchrome)",
            "function": "Regulates high-velocity air-fuel mixture entry into combustion chambers.",
            "notes": "Features precision-ground stems and stellite-hardened faces for high-RPM endurance.",
        },
    },
    "Helmet": {
        "Visor Shield": {
            "position": "0 0.10 0.22",
            "normal": "0 0 1",
            "material": "Optical-Grade Injection-Molded Polycarbonate with Anti-Scratch & UV400 Coating",
            "function": "Delivers wide-angle peripheral visibility and high-velocity ballistic impact protection.",
            "notes": "Pinlock-ready inner surface with quick-release ratchet tool-less mechanism.",
        },
        "Composite Outer Shell": {
            "position": "0 0.32 0.0",
            "normal": "0 1 0",
            "material": "Carbon Fiber & Aramid (Kevlar) Reinforced Thermoset Epoxy Matrix",
            "function": "Primary structural defense layer that disperses blunt impact force across the liner.",
            "notes": "Certified to ECE 22.06 and DOT safety standards with an aerodynamic spoiler lip.",
        },
        "Retention Chinstrap": {
            "position": "0 -0.22 0.08",
            "normal": "0 -1 0",
            "material": "High-Tenacity Woven Nylon Webbing with Titanium Double D-Ring Fastener",
            "function": "Firmly anchors the helmet to the head under sudden rotational and deceleration forces.",
            "notes": "Anti-chafing padded comfort sleeve with magnetic quick-snap strap retainer.",
        },
    },
    "Turbine": {
        "Rotor Blades": {
            "position": "0 0.05 0.18",
            "normal": "0 0 1",
            "material": "Single-Crystal Nickel Superalloy (Inconel 718) with Ceramic Thermal Barrier Coating",
            "function": "Extracts thermodynamic energy from high-velocity gas flow to turn the central generator shaft.",
            "notes": "Features internal serpentine cooling passages capable of continuous operation at 1150°C.",
        },
        "Turbine Casing": {
            "position": "0 0.25 -0.15",
            "normal": "0 1 0",
            "material": "Cast Chromium-Molybdenum Heavy-Duty Structural Steel",
            "function": "Contains internal pressures and directs fluid streamline across stator stages.",
            "notes": "Horizontally split casing design allowing direct overhaul inspection without removing the rotor.",
        },
        "Bearing Assembly": {
            "position": "0 -0.15 -0.30",
            "normal": "0 0 -1",
            "material": "Hardened Forged Alloy Steel with Hydrodynamic Babbitt Metal Bearings",
            "function": "Supports rotor mass and absorbs radial and axial thrust loads at high operating RPM.",
            "notes": "Equipped with continuous forced-oil lubrication and proximity vibration sensors.",
        },
    },
}

# -----------------------------------------------------------------------------
# 4. HEADER & TOP CONTROLS
# -----------------------------------------------------------------------------
header_col1, header_col2 = st.columns([7, 3], vertical_alignment="center")

with header_col1:
    st.markdown(
        """
        <p style="margin: 4px 0 10px 0; font-size: 14.5px; color: #94a3b8; font-weight: 400; line-height: 1.5;">
            Rotate the 3D model, tap any hotspot to inspect engineering specifications, or click <strong>➕ Add Hotspot</strong> to place new points directly on the model.
        </p>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# Handle model deletion/removal request from dropdown hover cross button
# -----------------------------------------------------------------------------
if "delete_model" in st.query_params:
    from urllib.parse import unquote
    target_model = unquote(str(st.query_params.get("delete_model", ""))).strip()
    st.query_params.clear()
    
    # Track for 5-second restore popup banner
    st.session_state["just_removed_model"] = target_model
    st.session_state["just_removed_time"] = time.time()
    
    if target_model in SAMPLE_MODELS:
        # Removing a built-in sample model
        if "removed_models" not in st.session_state:
            st.session_state["removed_models"] = []
        if target_model not in st.session_state["removed_models"]:
            st.session_state["removed_models"].append(target_model)
    else:
        # Removing the custom uploaded model (e.g. Razer Basilisk V3 Mouse or any custom prototype)
        # Backup data in memory in case user clicks restore within 5s
        if "uploaded_glb_data" in st.session_state:
            st.session_state["_backup_glb_data"] = st.session_state["uploaded_glb_data"]
            st.session_state["_backup_model_name"] = st.session_state.get("uploaded_model_name", target_model)
            st.session_state["_backup_filename"] = st.session_state.get("_last_uploaded_file", "custom_model.glb")
        elif CUSTOM_GLB_PATH.exists():
            try:
                raw_b = CUSTOM_GLB_PATH.read_bytes()
                b64 = base64.b64encode(raw_b).decode("utf-8")
                st.session_state["_backup_glb_data"] = f"data:model/gltf-binary;base64,{b64}"
                if CUSTOM_META_PATH.exists():
                    meta = json.loads(CUSTOM_META_PATH.read_text(encoding="utf-8"))
                    st.session_state["_backup_model_name"] = meta.get("name", target_model)
                    st.session_state["_backup_filename"] = meta.get("filename", "custom_model.glb")
                else:
                    st.session_state["_backup_model_name"] = target_model
                    st.session_state["_backup_filename"] = "custom_model.glb"
            except Exception:
                pass
        
        # Completely delete from disk and memory
        st.session_state.pop("uploaded_glb_data", None)
        st.session_state.pop("uploaded_model_name", None)
        st.session_state.pop("_last_uploaded_file", None)
        try:
            if CUSTOM_GLB_PATH.exists():
                CUSTOM_GLB_PATH.unlink()
            if CUSTOM_META_PATH.exists():
                CUSTOM_META_PATH.unlink()
        except Exception:
            pass
            
    st.rerun()

# -----------------------------------------------------------------------------
# Handle model restore request from 5-second popup
# -----------------------------------------------------------------------------
if "restore_model" in st.query_params:
    from urllib.parse import unquote
    restore_target = unquote(str(st.query_params.get("restore_model", ""))).strip()
    st.query_params.clear()
    
    if restore_target in SAMPLE_MODELS:
        if "removed_models" in st.session_state and restore_target in st.session_state["removed_models"]:
            st.session_state["removed_models"].remove(restore_target)
    else:
        # Restore custom uploaded model from in-memory backup
        if "_backup_glb_data" in st.session_state:
            b64_data = st.session_state["_backup_glb_data"]
            name = st.session_state.get("_backup_model_name", restore_target)
            st.session_state["uploaded_glb_data"] = b64_data
            st.session_state["uploaded_model_name"] = name
            try:
                raw_bytes = base64.b64decode(b64_data.split(",")[-1])
                CUSTOM_GLB_PATH.write_bytes(raw_bytes)
                meta = {"name": name, "filename": st.session_state.get("_backup_filename", name)}
                CUSTOM_META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            except Exception:
                pass

    st.session_state.pop("just_removed_model", None)
    st.session_state.pop("just_removed_time", None)
    st.rerun()

# Clean up any invalid entries in removed_models (ensure only sample models are tracked there)
if "removed_models" in st.session_state:
    st.session_state["removed_models"] = [m for m in st.session_state["removed_models"] if m in SAMPLE_MODELS]

# Restore custom prototype model from persistent disk storage across page refreshes
if "uploaded_glb_data" not in st.session_state and CUSTOM_GLB_PATH.exists():
    try:
        glb_bytes = CUSTOM_GLB_PATH.read_bytes()
        b64_glb = base64.b64encode(glb_bytes).decode("utf-8")
        st.session_state["uploaded_glb_data"] = f"data:model/gltf-binary;base64,{b64_glb}"
        if CUSTOM_META_PATH.exists():
            meta = json.loads(CUSTOM_META_PATH.read_text(encoding="utf-8"))
            st.session_state["uploaded_model_name"] = meta.get("name", "Custom Prototype")
            st.session_state["_last_uploaded_file"] = meta.get("filename", "custom_model.glb")
        else:
            st.session_state["uploaded_model_name"] = "Custom Prototype"
    except Exception:
        pass

removed_models = st.session_state.get("removed_models", [])
model_options = [m for m in SAMPLE_MODELS.keys() if m not in removed_models]
custom_name = st.session_state.get("uploaded_model_name", "Uploaded Custom Model")
if "uploaded_glb_data" in st.session_state:
    model_options.insert(0, custom_name)

# Ensure at least one model option is always present
if not model_options:
    model_options = list(SAMPLE_MODELS.keys())
    st.session_state["removed_models"] = []

with header_col2:
    model_choice = st.selectbox(
        "Model:",
        options=model_options,
        index=0,
        label_visibility="collapsed",
    )

# 5-Second Floating Restore Popup Banner
just_removed = st.session_state.get("just_removed_model")
just_removed_time = st.session_state.get("just_removed_time", 0)
show_restore_banner = bool(just_removed and (time.time() - just_removed_time < 5.2))

if show_restore_banner:
    import html
    safe_removed_js = str(just_removed).replace("\\", "\\\\").replace("'", "\\'")
    safe_removed_html = html.escape(str(just_removed))
    st.html(
        f"""
        <div id="explainit3d-restore-banner" class="restore-toast-banner">
            <div class="restore-toast-body">
                <span class="restore-toast-msg">🗑️ Removed <strong>{safe_removed_html}</strong></span>
                <button onclick="triggerRestore('{safe_removed_js}')" class="restore-toast-btn">
                    ↺ Restore
                </button>
            </div>
            <div class="restore-toast-bar"></div>
        </div>
        <style>
        .restore-toast-banner {{
            position: fixed;
            top: 24px;
            right: 28px;
            background: rgba(15, 23, 42, 0.96);
            border: 1px solid rgba(239, 68, 68, 0.5);
            box-shadow: 0 16px 42px rgba(0, 0, 0, 0.65), 0 0 18px rgba(239, 68, 68, 0.25);
            border-radius: 14px;
            padding: 12px 18px;
            z-index: 99999999;
            display: flex;
            flex-direction: column;
            gap: 8px;
            backdrop-filter: blur(18px);
            animation: banner-pop 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        @keyframes banner-pop {{
            from {{ transform: translateY(-20px); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
        }}
        .restore-toast-body {{
            display: flex;
            align-items: center;
            gap: 14px;
        }}
        .restore-toast-msg {{
            color: #f1f5f9;
            font-size: 13.5px;
            font-weight: 500;
        }}
        .restore-toast-msg strong {{
            color: #ffffff;
            font-weight: 700;
        }}
        .restore-toast-btn {{
            background: linear-gradient(135deg, #4f46e5, #6366f1);
            border: 1px solid #818cf8;
            color: #ffffff;
            font-size: 12.5px;
            font-weight: 600;
            padding: 5px 13px;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
            transition: all 0.2s ease;
        }}
        .restore-toast-btn:hover {{
            background: linear-gradient(135deg, #4338ca, #4f46e5);
            transform: translateY(-1px);
        }}
        .restore-toast-bar {{
            height: 3px;
            background: #ef4444;
            border-radius: 2px;
            width: 100%;
            animation: toast-timer 5s linear forwards;
        }}
        @keyframes toast-timer {{
            from {{ width: 100%; }}
            to {{ width: 0%; }}
        }}
        </style>
        <script>
        function triggerRestore(name) {{
            const url = new URL(window.location.href);
            url.searchParams.set('restore_model', name);
            window.location.href = url.href;
        }}
        setTimeout(() => {{
            const el = document.getElementById('explainit3d-restore-banner');
            if (el) {{
                el.style.opacity = '0';
                el.style.transform = 'translateY(-16px)';
                el.style.transition = 'all 0.35s ease';
                setTimeout(() => el.remove(), 350);
            }}
        }}, 5000);
        </script>
        """,
        unsafe_allow_javascript=True,
    )

is_custom_model = ("uploaded_glb_data" in st.session_state) and (model_choice == custom_name)

if is_custom_model:
    model_url = st.session_state["uploaded_glb_data"]
    camera_orbit = "auto auto auto"
    camera_target = "auto auto auto"
    field_of_view = "auto"
    active_built_in_parts = {}
else:
    active_meta = SAMPLE_MODELS.get(model_choice, SAMPLE_MODELS["My Laptop"])
    model_url = active_meta["url"]
    camera_orbit = active_meta["camera_orbit"]
    camera_target = active_meta["camera_target"]
    field_of_view = active_meta["field_of_view"]
    active_built_in_parts = MODEL_DATA.get(model_choice, {})

# Base JSON data
base_spec_json = json.dumps(active_built_in_parts)
is_custom_model_str = "true" if is_custom_model else "false"

# -----------------------------------------------------------------------------
# 5. EXPANSIVE & SPACIOUS 3D VIEWER (640px Canvas + Perfectly Sized Spec Card)
# -----------------------------------------------------------------------------
embedded_viewer_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-font-smoothing: antialiased;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", "Plus Jakarta Sans", sans-serif;
      background: transparent;
      color: #f8fafc;
      overflow-x: hidden;
      padding: 4px;
    }}

    /* Expansive 3D Viewer Container (640px Height) */
    .viewer-card {{
      position: relative;
      width: 100%;
      height: 640px;
      border-radius: 22px;
      overflow: hidden;
      background: radial-gradient(circle at 50% 38%, #1f2a40 0%, #0e1526 65%, #070b14 100%);
      border: 1px solid rgba(255, 255, 255, 0.1);
      box-shadow: 0 20px 48px rgba(0, 0, 0, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.12);
    }}

    model-viewer {{
      width: 100%;
      height: 100%;
      background: transparent;
      outline: none;
      --poster-color: transparent;
    }}

    /* Floating Toolbar with generous spacing */
    .floating-toolbar {{
      position: absolute;
      top: 18px;
      left: 18px;
      right: 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      pointer-events: none;
      z-index: 10;
    }}
    .toolbar-left, .toolbar-right {{
      display: flex;
      gap: 10px;
      pointer-events: auto;
    }}
    .model-badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(15, 23, 42, 0.78);
      backdrop-filter: blur(14px);
      border: 1px solid rgba(255, 255, 255, 0.14);
      border-radius: 30px;
      padding: 7px 15px;
      font-size: 12.5px;
      font-weight: 600;
      color: #cbd5e1;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
    }}
    .status-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 10px #10b981;
      display: inline-block;
    }}
    .control-btn {{
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(14px);
      border: 1px solid rgba(255, 255, 255, 0.14);
      color: #e2e8f0;
      font-size: 13px;
      font-weight: 500;
      padding: 7px 16px;
      border-radius: 22px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 7px;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
      transition: all 0.2s ease;
    }}
    .control-btn:hover {{
      background: rgba(30, 41, 59, 0.98);
      border-color: rgba(99, 102, 241, 0.5);
      color: #ffffff;
      transform: translateY(-1px);
    }}
    .control-btn.btn-accent {{
      background: linear-gradient(135deg, #4f46e5, #6366f1);
      border-color: #818cf8;
      color: #ffffff;
      font-weight: 600;
      box-shadow: 0 4px 18px rgba(79, 70, 229, 0.5);
    }}
    .control-btn.btn-accent:hover {{
      background: linear-gradient(135deg, #4338ca, #4f46e5);
      box-shadow: 0 6px 24px rgba(79, 70, 229, 0.65);
    }}
    .control-btn.btn-active-cancel {{
      background: #dc2626 !important;
      border-color: #f87171 !important;
      color: #ffffff !important;
    }}

    /* Top Placement Mode Alert Banner */
    .add-mode-banner {{
      display: none;
      position: absolute;
      top: 72px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(99, 102, 241, 0.96);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.3);
      border-radius: 30px;
      padding: 10px 22px;
      font-size: 13.5px;
      font-weight: 600;
      color: #ffffff;
      box-shadow: 0 8px 28px rgba(79, 70, 229, 0.55);
      z-index: 30;
      align-items: center;
      gap: 12px;
      animation: banner-float 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    @keyframes banner-float {{
      from {{ transform: translate(-50%, -10px); opacity: 0; }}
      to {{ transform: translate(-50%, 0); opacity: 1; }}
    }}

    /* Modern Hotspot Dots */
    .hotspot-dot {{
      background: transparent;
      border: none;
      padding: 0;
      cursor: pointer;
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      outline: none;
      transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .hotspot-core {{
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: #6366f1;
      border: 2px solid #ffffff;
      box-shadow: 0 0 12px rgba(99, 102, 241, 0.95), 0 2px 6px rgba(0,0,0,0.5);
      z-index: 2;
      transition: all 0.2s ease;
    }}

    .hotspot-ring {{
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 28px;
      height: 28px;
      border-radius: 50%;
      border: 1.5px solid rgba(129, 140, 248, 0.75);
      animation: hotspot-pulse 2.2s infinite cubic-bezier(0.215, 0.61, 0.355, 1);
      z-index: 1;
      pointer-events: none;
    }}

    @keyframes hotspot-pulse {{
      0% {{ transform: translate(-50%, -50%) scale(0.6); opacity: 0.9; }}
      70% {{ transform: translate(-50%, -50%) scale(1.6); opacity: 0; }}
      100% {{ transform: translate(-50%, -50%) scale(1.6); opacity: 0; }}
    }}

    .hotspot-pill {{
      position: absolute;
      left: 22px;
      top: 50%;
      transform: translateY(-50%);
      background: rgba(15, 23, 42, 0.9);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.18);
      color: #f8fafc;
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 0.02em;
      padding: 4px 11px;
      border-radius: 18px;
      white-space: nowrap;
      pointer-events: none;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.45);
      opacity: 0.94;
      transition: all 0.2s ease;
    }}

    .hotspot-dot:hover .hotspot-core,
    .hotspot-dot.active .hotspot-core {{
      background: #38bdf8;
      transform: scale(1.25);
      box-shadow: 0 0 18px rgba(56, 189, 248, 1), 0 2px 8px rgba(0,0,0,0.6);
    }}
    .hotspot-dot:hover .hotspot-pill,
    .hotspot-dot.active .hotspot-pill {{
      background: rgba(30, 41, 59, 0.98);
      border-color: rgba(56, 189, 248, 0.6);
      color: #ffffff;
      opacity: 1;
      transform: translateY(-50%) scale(1.05);
    }}

    /* Spacious Part Chips Row */
    .chips-container {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
      margin-bottom: 14px;
      align-items: center;
    }}
    .chips-label {{
      font-size: 11.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #64748b;
      margin-right: 6px;
    }}
    .part-chip {{
      background: rgba(17, 24, 39, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: #cbd5e1;
      font-size: 13px;
      font-weight: 500;
      padding: 7px 16px;
      border-radius: 24px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 7px;
      transition: all 0.2s ease;
    }}
    .chip-dot {{
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #6366f1;
    }}
    .part-chip:hover {{
      background: rgba(30, 41, 59, 0.98);
      border-color: rgba(99, 102, 241, 0.45);
      color: #ffffff;
      transform: translateY(-1px);
    }}
    .part-chip.active {{
      background: rgba(99, 102, 241, 0.22);
      border-color: #6366f1;
      color: #ffffff;
    }}
    .part-chip.active .chip-dot {{
      background: #38bdf8;
      box-shadow: 0 0 8px #38bdf8;
    }}

    /* Modern Product Spec Info Card — Completely Visible & Uncropped */
    .spec-card {{
      background: rgba(15, 23, 42, 0.95);
      backdrop-filter: blur(18px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 18px;
      padding: 18px 24px;
      box-shadow: 0 20px 42px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.1);
      transition: opacity 0.3s cubic-bezier(0.16, 1, 0.3, 1), transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .spec-card.card-hidden {{
      display: none;
      opacity: 0;
      transform: translateY(10px);
    }}
    .spec-card.card-visible {{
      display: block;
      opacity: 1;
      transform: translateY(0);
    }}

    .spec-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      padding-bottom: 10px;
      margin-bottom: 14px;
    }}
    .part-badge {{
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #818cf8;
      background: rgba(99, 102, 241, 0.16);
      border: 1px solid rgba(99, 102, 241, 0.32);
      padding: 3px 10px;
      border-radius: 7px;
      margin-bottom: 6px;
    }}
    .part-title {{
      font-size: 22px;
      font-weight: 700;
      color: #ffffff;
      letter-spacing: -0.01em;
    }}
    .header-btns {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .del-btn {{
      background: rgba(239, 68, 68, 0.16);
      border: 1px solid rgba(239, 68, 68, 0.32);
      color: #fca5a5;
      font-size: 12px;
      font-weight: 600;
      padding: 6px 13px;
      border-radius: 18px;
      cursor: pointer;
      display: none;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
    }}
    .del-btn:hover {{
      background: rgba(239, 68, 68, 0.32);
      color: #ffffff;
      border-color: #ef4444;
    }}
    .close-btn {{
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.14);
      color: #cbd5e1;
      height: 32px;
      padding: 0 14px;
      border-radius: 16px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      font-weight: 600;
      transition: all 0.2s ease;
    }}
    .close-btn:hover {{
      background: rgba(255, 255, 255, 0.18);
      color: #ffffff;
      border-color: rgba(255, 255, 255, 0.3);
    }}

    /* Spacious 3-Column Spec Grid */
    .spec-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
    }}
    .spec-box {{
      background: rgba(30, 41, 59, 0.5);
      border: 1px solid rgba(255, 255, 255, 0.07);
      border-radius: 12px;
      padding: 12px 16px;
    }}
    .spec-label {{
      font-size: 11.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #94a3b8;
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 7px;
    }}
    .spec-val {{
      font-size: 13.5px;
      color: #e2e8f0;
      line-height: 1.55;
      font-weight: 400;
    }}

    /* Hint bar */
    .hint-bar {{
      background: rgba(15, 23, 42, 0.7);
      border: 1px dashed rgba(255, 255, 255, 0.14);
      border-radius: 14px;
      padding: 16px 22px;
      font-size: 13.5px;
      color: #94a3b8;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}

    /* 1-Click Hotspot Modal Dialog */
    .modal-overlay {{
      display: none;
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(3, 7, 18, 0.78);
      backdrop-filter: blur(12px);
      z-index: 100;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}
    .modal-card {{
      background: #0f172a;
      border: 1px solid rgba(255, 255, 255, 0.16);
      border-radius: 18px;
      width: 100%;
      max-width: 480px;
      padding: 24px 28px;
      box-shadow: 0 26px 55px rgba(0, 0, 0, 0.75);
      animation: modal-pop 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    @keyframes modal-pop {{
      from {{ transform: scale(0.92); opacity: 0; }}
      to {{ transform: scale(1); opacity: 1; }}
    }}
    .modal-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }}
    .modal-title {{
      font-size: 19px;
      font-weight: 700;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .modal-subtitle {{
      font-size: 13px;
      color: #94a3b8;
      margin-bottom: 18px;
    }}
    .input-group {{
      margin-bottom: 14px;
    }}
    .input-label {{
      display: block;
      font-size: 11.5px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #cbd5e1;
      margin-bottom: 5px;
    }}
    .modal-input, .modal-textarea {{
      width: 100%;
      background: #1e293b;
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 10px;
      padding: 10px 14px;
      font-size: 14px;
      color: #f8fafc;
      font-family: inherit;
      outline: none;
      transition: border-color 0.2s ease;
    }}
    .modal-input:focus, .modal-textarea:focus {{
      border-color: #6366f1;
      box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25);
    }}
    .modal-footer {{
      display: flex;
      justify-content: flex-end;
      gap: 12px;
      margin-top: 20px;
    }}
    .btn-secondary {{
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #cbd5e1;
      font-size: 13.5px;
      font-weight: 500;
      padding: 9px 18px;
      border-radius: 10px;
      cursor: pointer;
    }}
    .btn-primary {{
      background: linear-gradient(135deg, #4f46e5, #6366f1);
      border: 1px solid #818cf8;
      color: #ffffff;
      font-size: 13.5px;
      font-weight: 600;
      padding: 9px 20px;
      border-radius: 10px;
      cursor: pointer;
      box-shadow: 0 4px 16px rgba(79, 70, 229, 0.45);
    }}

    /* Animated Toast Notification */
    .toast-pill {{
      display: none;
      position: absolute;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(16, 185, 129, 0.96);
      backdrop-filter: blur(12px);
      color: #ffffff;
      font-size: 13.5px;
      font-weight: 600;
      padding: 10px 22px;
      border-radius: 30px;
      box-shadow: 0 8px 26px rgba(0, 0, 0, 0.5);
      z-index: 120;
    }}

    @media (max-width: 768px) {{
      .viewer-card {{ height: 440px; }}
      .spec-grid {{ grid-template-columns: 1fr; }}
    }}

    /* Corner Fullscreen Button */
    .corner-fs-btn {{
      position: absolute;
      bottom: 18px;
      right: 18px;
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(14px);
      border: 1px solid rgba(255, 255, 255, 0.16);
      color: #cbd5e1;
      width: 40px;
      height: 40px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      z-index: 15;
    }}
    .corner-fs-btn:hover {{
      background: rgba(30, 41, 59, 0.98);
      border-color: rgba(99, 102, 241, 0.6);
      color: #ffffff;
      transform: scale(1.08);
      box-shadow: 0 6px 20px rgba(79, 70, 229, 0.45);
    }}
    .corner-fs-btn:active {{
      transform: scale(0.96);
    }}

    /* Fullscreen & Theater Mode Styles */
    .fullscreen-root {{
      width: 100%;
      position: relative;
    }}

    .fullscreen-root:fullscreen,
    .fullscreen-root:-webkit-full-screen,
    .fullscreen-root.theater-mode {{
      width: 100vw !important;
      height: 100vh !important;
      max-width: 100vw !important;
      position: fixed !important;
      inset: 0 !important;
      top: 0 !important;
      left: 0 !important;
      z-index: 999999 !important;
      background: radial-gradient(circle at 50% 38%, #1f2a40 0%, #0e1526 65%, #070b14 100%) !important;
      display: flex !important;
      flex-direction: column !important;
      padding: 16px 24px !important;
      box-sizing: border-box !important;
      overflow: hidden !important;
    }}

    .fullscreen-root:fullscreen .viewer-card,
    .fullscreen-root:-webkit-full-screen .viewer-card,
    .fullscreen-root.theater-mode .viewer-card {{
      flex: 1 1 auto !important;
      height: auto !important;
      min-height: 0 !important;
      border-radius: 18px !important;
    }}

    .fullscreen-root:fullscreen .chips-container,
    .fullscreen-root:-webkit-full-screen .chips-container,
    .fullscreen-root.theater-mode .chips-container {{
      margin-top: 10px !important;
      margin-bottom: 8px !important;
      flex-shrink: 0 !important;
    }}

    .fullscreen-root:fullscreen .spec-card,
    .fullscreen-root:-webkit-full-screen .spec-card,
    .fullscreen-root.theater-mode .spec-card {{
      flex-shrink: 0 !important;
      padding: 14px 20px !important;
      margin-bottom: 4px !important;
    }}

    .fullscreen-root:fullscreen .hint-bar,
    .fullscreen-root:-webkit-full-screen .hint-bar,
    .fullscreen-root.theater-mode .hint-bar {{
      flex-shrink: 0 !important;
      margin-bottom: 4px !important;
      padding: 12px 18px !important;
    }}
  </style>
</head>
<body>

  <!-- Fullscreen Container Wrapper -->
  <div id="fullscreen-root" class="fullscreen-root">

    <!-- Expansive 3D Model Canvas -->
    <div class="viewer-card">
      <!-- Floating Toolbar -->
      <div class="floating-toolbar">
        <div class="toolbar-left">
          <div class="model-badge">
            <span class="status-dot"></span>
            <span>{model_choice}</span>
          </div>
        </div>
        <div class="toolbar-right">
          <button class="control-btn btn-accent" id="btn-add-hotspot" onclick="toggleAddHotspotMode()">
            <span>➕</span> Add Hotspot
          </button>
          <button class="control-btn" id="btn-spin" onclick="toggleSpin()">
            <span>⏸</span> Pause Spin
          </button>
          <button class="control-btn" onclick="resetCamera()">
            <span>🔄</span> Reset View
          </button>
        </div>
      </div>

      <!-- Active Placement Mode Banner -->
      <div id="add-mode-banner" class="add-mode-banner">
        <span>🎯 Click anywhere on the 3D model to place a hotspot</span>
        <button onclick="toggleAddHotspotMode()" style="background:transparent; border:none; color:#fca5a5; font-size:13px; cursor:pointer; font-weight:700;">Cancel ✕</button>
      </div>

      <!-- 1-Click Hotspot Modal Dialog -->
      <div id="add-modal" class="modal-overlay">
        <div class="modal-card">
          <div class="modal-header">
            <div class="modal-title">
              <span>📍</span> New Part Hotspot
            </div>
            <button class="close-btn" onclick="closeAddModal()">✕</button>
          </div>
          <p class="modal-subtitle">Surface point selected! Enter part details:</p>

          <div class="input-group">
            <label class="input-label">Part Name <span style="color:#ef4444;">*</span></label>
            <input type="text" id="input-name" class="modal-input" placeholder="e.g. Battery Cell, Cooling Fan, Hinge..." autocomplete="off">
          </div>

          <div class="input-group">
            <label class="input-label">Material Composition (Optional)</label>
            <input type="text" id="input-material" class="modal-input" placeholder="e.g. Brushed Aluminum, Pure Copper, ABS...">
          </div>

          <div class="input-group">
            <label class="input-label">Primary Function (Optional)</label>
            <input type="text" id="input-function" class="modal-input" placeholder="e.g. Supplies power, exhausts thermal heat...">
          </div>

          <div class="input-group">
            <label class="input-label">Engineering Notes (Optional)</label>
            <textarea id="input-notes" class="modal-textarea" rows="2" placeholder="e.g. Rated at 45W TDP, 1500 RPM quiet profile..."></textarea>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" onclick="closeAddModal()">Cancel</button>
            <button class="btn-primary" onclick="confirmAddHotspot()">➕ Save Hotspot</button>
          </div>
        </div>
      </div>

      <!-- Toast Notification -->
      <div id="toast" class="toast-pill"></div>

      <!-- Corner Option to Make Fullscreen -->
      <button class="corner-fs-btn" id="corner-fs-btn" onclick="toggleFullscreen()" title="Full Screen View (F)">
        <svg id="corner-fs-svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
        </svg>
      </button>

      <model-viewer
        id="mv"
        src="{model_url}"
        camera-controls
        auto-rotate
        rotation-per-second="10deg"
        auto-rotate-delay="2500"
        bounds="tight"
        camera-orbit="{camera_orbit}"
        camera-target="{camera_target}"
        field-of-view="{field_of_view}"
        shadow-intensity="1.2"
        shadow-softness="0.75"
        exposure="1.05"
        environment-image="neutral"
        interaction-prompt="none"
        ar
      >
      </model-viewer>
    </div>

    <!-- Interactive Part Quick Chips -->
    <div class="chips-container" id="chips-container">
      <span class="chips-label">Annotated Parts:</span>
    </div>

    <!-- Product Spec Info Card — Completely Visible & Uncropped -->
    <div id="spec-card" class="spec-card card-hidden">
      <div class="spec-header">
        <div>
          <span class="part-badge">COMPONENT SPECIFICATION</span>
          <h2 id="card-part-title" class="part-title">Part Name</h2>
        </div>
        <div class="header-btns">
          <button id="card-delete-btn" class="del-btn" onclick="deleteActiveHotspot()" title="Delete this custom hotspot">
            <span>🗑️</span> Delete Hotspot
          </button>
          <button class="close-btn" onclick="closeCard()" title="Close details">
            <span>✕</span> Close
          </button>
        </div>
      </div>

      <div class="spec-grid">
        <div class="spec-box">
          <div class="spec-label">
            <span style="color:#818cf8;">🧪</span> Material Composition
          </div>
          <div id="card-material" class="spec-val">—</div>
        </div>

        <div class="spec-box">
          <div class="spec-label">
            <span style="color:#38bdf8;">⚡</span> Primary Function
          </div>
          <div id="card-function" class="spec-val">—</div>
        </div>

        <div class="spec-box">
          <div class="spec-label">
            <span style="color:#34d399;">📝</span> Engineering & Design Notes
          </div>
          <div id="card-notes" class="spec-val">—</div>
        </div>
      </div>
    </div>

    <!-- Hint Bar (Shown when no part is selected) -->
    <div id="hint-bar" class="hint-bar">
      <div style="display: flex; align-items: center; gap: 10px;">
        <span style="font-size: 16px;">💡</span>
        <span>Tap any glowing dot or click <strong>➕ Add Hotspot</strong> in the top toolbar to place a new part directly on the 3D model.</span>
      </div>
      <span style="font-size: 12px; color: #64748b;">Rotate: Drag | Zoom: Scroll</span>
    </div>

  </div><!-- End fullscreen-root -->

  <script>
    const isCustomModel = {is_custom_model_str};
    const currentModel = "{model_choice}";
    // Use stable key for user-uploaded models so renaming never loses custom hotspots
    const storageKey = isCustomModel
      ? 'explainit3d_custom_hotspots_user_uploaded_model'
      : 'explainit3d_custom_hotspots_' + currentModel.split(' ').join('_');
    const deletedKey = isCustomModel
      ? 'explainit3d_deleted_hotspots_user_uploaded_model'
      : 'explainit3d_deleted_hotspots_' + currentModel.split(' ').join('_');
    
    // Load built-in parts
    let partCatalog = {base_spec_json};
    
    // Merge user custom hotspots and respect deletions from localStorage
    try {{
      let saved = localStorage.getItem(storageKey);
      // Migration fallback: check legacy or model-named keys for custom models
      if (!saved && isCustomModel) {{
        saved = localStorage.getItem('explainit3d_custom_hotspots_' + currentModel.split(' ').join('_')) ||
                localStorage.getItem('explainit3d_custom_hotspots_Uploaded_Custom_Model');
        if (saved) {{
          localStorage.setItem(storageKey, saved);
        }}
      }}
      if (saved) {{
        const parsed = JSON.parse(saved);
        partCatalog = Object.assign({{}}, partCatalog, parsed);
      }}
      let delList = JSON.parse(localStorage.getItem(deletedKey) || '[]');
      if (delList.length === 0 && isCustomModel) {{
        delList = JSON.parse(localStorage.getItem('explainit3d_deleted_hotspots_' + currentModel.split(' ').join('_')) || '[]') ||
                  JSON.parse(localStorage.getItem('explainit3d_deleted_hotspots_Uploaded_Custom_Model') || '[]');
        if (delList.length > 0) {{
          localStorage.setItem(deletedKey, JSON.stringify(delList));
        }}
      }}
      delList.forEach(name => delete partCatalog[name]);
    }} catch(e) {{ console.log(e); }}

    const mv = document.getElementById('mv');
    const defaultOrbit = "{camera_orbit}";
    const defaultTarget = "{camera_target}";
    const defaultFov = "{field_of_view}";

    let isAddMode = false;
    let pendingPos = null;
    let pendingNorm = null;
    let activeHotspotName = null;

    // 1. Initial Render of all Hotspot Buttons on <model-viewer>
    function renderAllHotspots() {{
      document.querySelectorAll('.hotspot-dot').forEach(b => b.remove());

      for (const [name, pdata] of Object.entries(partCatalog)) {{
        createHotspotElement(name, pdata);
      }}
      renderChips();
    }}

    function createHotspotElement(name, pdata) {{
      const btn = document.createElement('button');
      btn.className = 'hotspot-dot';
      const safeSlot = 'hotspot-' + name.replace(/[^a-zA-Z0-9]/g, '_');
      btn.setAttribute('slot', safeSlot);
      btn.setAttribute('data-position', pdata.position || '0 0 0');
      btn.setAttribute('data-normal', pdata.normal || '0 1 0');
      btn.setAttribute('data-name', name);
      btn.onclick = (e) => {{
        e.stopPropagation();
        selectHotspot(name);
      }};

      btn.innerHTML = `
        <span class="hotspot-ring"></span>
        <span class="hotspot-core"></span>
        <span class="hotspot-pill">${{name}}</span>
      `;
      mv.appendChild(btn);
    }}

    // 2. Render Part Chips Row Below Viewer
    function renderChips() {{
      const container = document.getElementById('chips-container');
      container.innerHTML = '<span class="chips-label">Annotated Parts:</span>';

      for (const name of Object.keys(partCatalog)) {{
        const chip = document.createElement('button');
        chip.className = 'part-chip';
        chip.setAttribute('data-name', name);
        if (name === activeHotspotName) chip.classList.add('active');
        chip.onclick = () => selectHotspot(name);
        chip.innerHTML = `<span class="chip-dot"></span><span>${{name}}</span>`;
        container.appendChild(chip);
      }}
    }}

    // 3. Select Hotspot & Display Spec Card (Toggles closed if already active)
    function selectHotspot(name) {{
      // Re-clicking the currently active hotspot or chip toggles/closes the card!
      if (activeHotspotName === name) {{
        closeCard();
        return;
      }}

      const data = partCatalog[name];
      if (!data) return;
      activeHotspotName = name;

      // Update active highlight
      document.querySelectorAll('.hotspot-dot').forEach(b => {{
        b.classList.toggle('active', b.getAttribute('data-name') === name);
      }});
      document.querySelectorAll('.part-chip').forEach(c => {{
        c.classList.toggle('active', c.getAttribute('data-name') === name);
      }});

      // Populate spec card
      document.getElementById('card-part-title').innerText = name;
      document.getElementById('card-material').innerText = data.material || 'Standard Prototype Material';
      document.getElementById('card-function').innerText = data.function || 'Component in prototype assembly';
      document.getElementById('card-notes').innerText = data.notes || data.explanation || 'Design spec annotation';

      // Show delete button ONLY for custom hotspots added by user
      const delBtn = document.getElementById('card-delete-btn');
      if (delBtn) {{
        delBtn.style.display = data.isCustom ? 'inline-flex' : 'none';
      }}

      document.getElementById('hint-bar').style.display = 'none';
      const card = document.getElementById('spec-card');
      card.classList.remove('card-hidden');
      card.classList.add('card-visible');

      // Camera pivots gently toward selected part
      if (data.position && mv) {{
        mv.cameraTarget = data.position;
      }}
    }}

    // 4. Close Spec Card
    function closeCard() {{
      activeHotspotName = null;
      const card = document.getElementById('spec-card');
      card.classList.remove('card-visible');
      card.classList.add('card-hidden');
      document.getElementById('hint-bar').style.display = 'flex';
      document.querySelectorAll('.hotspot-dot').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.part-chip').forEach(c => c.classList.remove('active'));
      resetCamera();
    }}

    // 5. Delete Active Hotspot
    function deleteActiveHotspot() {{
      if (!activeHotspotName) return;
      const name = activeHotspotName;
      if (!confirm(`Remove hotspot for "${{name}}"?`)) return;

      delete partCatalog[name];

      // Update localStorage custom hotspots and deletions
      try {{
        let custom = JSON.parse(localStorage.getItem(storageKey) || '{{}}');
        delete custom[name];
        localStorage.setItem(storageKey, JSON.stringify(custom));

        let delList = JSON.parse(localStorage.getItem(deletedKey) || '[]');
        if (!delList.includes(name)) delList.push(name);
        localStorage.setItem(deletedKey, JSON.stringify(delList));
      }} catch(e) {{}}

      // Remove 3D element and chip
      const btn = document.querySelector(`.hotspot-dot[data-name="${{name}}"]`);
      if (btn) btn.remove();

      closeCard();
      renderChips();
      showToast(`Removed "${{name}}"`, '#ef4444');

      // Live broadcast to Spec Sheet
      try {{
        window.parent.postMessage('explainit3d_update', '*');
      }} catch(e) {{}}
    }}

    // 6. Camera Controls
    function resetCamera() {{
      if (!mv) return;
      mv.cameraOrbit = defaultOrbit !== 'auto auto auto' ? defaultOrbit : 'auto auto auto';
      mv.cameraTarget = defaultTarget !== 'auto auto auto' ? defaultTarget : 'auto auto auto';
      if (defaultFov !== 'auto') mv.fieldOfView = defaultFov;
    }}

    function toggleSpin() {{
      if (!mv) return;
      mv.autoRotate = !mv.autoRotate;
      const btn = document.getElementById('btn-spin');
      if (btn) {{
        btn.innerHTML = mv.autoRotate ? '<span>⏸</span> Pause Spin' : '<span>▶</span> Auto Spin';
      }}
    }}

    // 7. Effortless 1-Click Add Hotspot Mode
    function toggleAddHotspotMode() {{
      isAddMode = !isAddMode;
      const btn = document.getElementById('btn-add-hotspot');
      const banner = document.getElementById('add-mode-banner');

      if (isAddMode) {{
        btn.classList.add('btn-active-cancel');
        btn.innerHTML = '<span>✕</span> Cancel';
        banner.style.display = 'flex';
        mv.style.cursor = 'crosshair';
        if (mv.autoRotate) {{
          mv.autoRotate = false;
          document.getElementById('btn-spin').innerHTML = '<span>▶</span> Auto Spin';
        }}
      }} else {{
        btn.classList.remove('btn-active-cancel');
        btn.innerHTML = '<span>➕</span> Add Hotspot';
        banner.style.display = 'none';
        mv.style.cursor = 'default';
      }}
    }}

    // Click on 3D Model in Add Mode
    mv.addEventListener('click', (event) => {{
      if (!isAddMode) return;

      const rect = mv.getBoundingClientRect();
      const hit = mv.positionAndNormalFromPoint(
        event.clientX - rect.left,
        event.clientY - rect.top
      );

      if (!hit) {{
        showToast("⚠️ Tap directly on the model surface", "#f59e0b");
        return;
      }}

      // Capture exact coordinates automatically
      pendingPos = `${{hit.position.x.toFixed(3)}} ${{hit.position.y.toFixed(3)}} ${{hit.position.z.toFixed(3)}}`;
      pendingNorm = `${{hit.normal.x.toFixed(3)}} ${{hit.normal.y.toFixed(3)}} ${{hit.normal.z.toFixed(3)}}`;

      // Open Modal
      openAddModal();
    }});

    function openAddModal() {{
      document.getElementById('input-name').value = '';
      document.getElementById('input-material').value = '';
      document.getElementById('input-function').value = '';
      document.getElementById('input-notes').value = '';
      document.getElementById('add-modal').style.display = 'flex';
      setTimeout(() => document.getElementById('input-name').focus(), 100);
    }}

    function closeAddModal() {{
      document.getElementById('add-modal').style.display = 'none';
      if (isAddMode) toggleAddHotspotMode();
    }}

    function confirmAddHotspot() {{
      const name = document.getElementById('input-name').value.trim();
      if (!name) {{
        alert("Please enter a Part Name.");
        document.getElementById('input-name').focus();
        return;
      }}

      const material = document.getElementById('input-material').value.trim() || 'Standard Engineering Material';
      const func = document.getElementById('input-function').value.trim() || 'Functional component in prototype assembly';
      const notes = document.getElementById('input-notes').value.trim() || 'Custom hotspot annotation';

      const newPart = {{
        position: pendingPos,
        normal: pendingNorm,
        material: material,
        function: func,
        notes: notes,
        isCustom: true
      }};

      // Save to memory
      partCatalog[name] = newPart;

      // Save to browser localStorage
      try {{
        let custom = JSON.parse(localStorage.getItem(storageKey) || '{{}}');
        custom[name] = newPart;
        localStorage.setItem(storageKey, JSON.stringify(custom));

        let delList = JSON.parse(localStorage.getItem(deletedKey) || '[]');
        delList = delList.filter(n => n !== name);
        localStorage.setItem(deletedKey, JSON.stringify(delList));
      }} catch(e) {{}}

      // Add 3D button directly to canvas
      createHotspotElement(name, newPart);
      renderChips();

      // Close modal and exit add mode
      closeAddModal();

      // Immediately select newly added hotspot
      selectHotspot(name);

      showToast(`✓ Added "${{name}}" to model!`, '#10b981');

      // Live broadcast to Spec Sheet
      try {{
        window.parent.postMessage('explainit3d_update', '*');
      }} catch(e) {{}}
    }}

    // Allow Enter key to submit modal
    document.getElementById('input-name').addEventListener('keydown', (e) => {{
      if (e.key === 'Enter') confirmAddHotspot();
    }});

    // Helper Toast
    function showToast(msg, bg) {{
      const t = document.getElementById('toast');
      t.innerText = msg;
      t.style.backgroundColor = bg || '#10b981';
      t.style.display = 'block';
      setTimeout(() => {{ t.style.display = 'none'; }}, 3000);
    }}

    // 8. Fullscreen Mode Controller
    const enterFsSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>`;
    const exitFsSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/></svg>`;

    function isFullscreenActive() {{
      const root = document.getElementById('fullscreen-root');
      return !!(document.fullscreenElement || document.webkitFullscreenElement || (root && root.classList.contains('theater-mode')));
    }}

    function updateFullscreenUI(active) {{
      const label = document.getElementById('fs-label');
      const icon = document.getElementById('fs-icon');
      const cornerBtn = document.getElementById('corner-fs-btn');
      
      if (active) {{
        if (label) label.innerText = 'Exit Fullscreen';
        if (icon) icon.innerText = '⤢';
        if (cornerBtn) {{
          cornerBtn.innerHTML = exitFsSvg;
          cornerBtn.title = 'Exit Fullscreen (Esc)';
        }}
      }} else {{
        if (label) label.innerText = 'Fullscreen';
        if (icon) icon.innerText = '⛶';
        if (cornerBtn) {{
          cornerBtn.innerHTML = enterFsSvg;
          cornerBtn.title = 'Full Screen View (F)';
        }}
      }}
    }}

    function toggleFullscreen() {{
      const root = document.getElementById('fullscreen-root');
      if (!root) return;

      if (isFullscreenActive()) {{
        if (document.exitFullscreen) {{
          document.exitFullscreen().catch(() => {{}});
        }} else if (document.webkitExitFullscreen) {{
          document.webkitExitFullscreen();
        }}
        root.classList.remove('theater-mode');
        updateFullscreenUI(false);
      }} else {{
        const req = root.requestFullscreen || root.webkitRequestFullscreen || root.mozRequestFullScreen || root.msRequestFullscreen;
        if (req) {{
          req.call(root).then(() => {{
            updateFullscreenUI(true);
          }}).catch(() => {{
            root.classList.add('theater-mode');
            updateFullscreenUI(true);
          }});
        }} else {{
          root.classList.add('theater-mode');
          updateFullscreenUI(true);
        }}
      }}
    }}

    document.addEventListener('fullscreenchange', () => {{
      const active = !!(document.fullscreenElement || document.webkitFullscreenElement);
      updateFullscreenUI(active);
      if (!active) {{
        const root = document.getElementById('fullscreen-root');
        if (root) root.classList.remove('theater-mode');
      }}
    }});
    document.addEventListener('webkitfullscreenchange', () => {{
      const active = !!(document.fullscreenElement || document.webkitFullscreenElement);
      updateFullscreenUI(active);
      if (!active) {{
        const root = document.getElementById('fullscreen-root');
        if (root) root.classList.remove('theater-mode');
      }}
    }});

    // Keyboard shortcut: Press "F" to toggle fullscreen, "Esc" to exit
    document.addEventListener('keydown', (e) => {{
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.key === 'f' || e.key === 'F') {{
        toggleFullscreen();
      }} else if (e.key === 'Escape' && isFullscreenActive()) {{
        toggleFullscreen();
      }}
    }});

    // Initial render
    renderAllHotspots();
  </script>
</body>
</html>
"""

# Render embedded 3D viewer component (snug height, uncropped spec card)
components.html(embedded_viewer_html, height=960, scrolling=False)

# -----------------------------------------------------------------------------
# 6. LIVE PROJECT SPEC SHEET & PDF EXPORT (Real-Time Synchronized Table)
# -----------------------------------------------------------------------------
current_date_str = datetime.now().strftime("%B %d, %Y")

spec_sheet_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-font-smoothing: antialiased;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", "Plus Jakarta Sans", sans-serif;
      background: #0d121f;
      color: #f8fafc;
      padding: 22px 24px;
    }}

    .action-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 18px;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .action-btns {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .print-btn {{
      background: linear-gradient(135deg, #4f46e5, #6366f1);
      color: #ffffff;
      border: 1px solid #818cf8;
      padding: 9px 18px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 4px 14px rgba(79, 70, 229, 0.4);
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s ease;
    }}
    .print-btn:hover {{
      background: linear-gradient(135deg, #4338ca, #4f46e5);
      transform: translateY(-1px);
      box-shadow: 0 6px 18px rgba(79, 70, 229, 0.55);
    }}
    .reset-btn {{
      background: rgba(255, 255, 255, 0.08);
      color: #cbd5e1;
      border: 1px solid rgba(255, 255, 255, 0.14);
      padding: 9px 16px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
    }}
    .reset-btn:hover {{
      background: rgba(239, 68, 68, 0.18);
      color: #fca5a5;
      border-color: rgba(239, 68, 68, 0.35);
    }}
    .live-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 600;
      color: #10b981;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.28);
      padding: 4px 12px;
      border-radius: 20px;
    }}
    .live-dot {{
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 8px #10b981;
      animation: live-blink 2s infinite ease-in-out;
    }}
    @keyframes live-blink {{
      0%, 100% {{ opacity: 1; transform: scale(1); }}
      50% {{ opacity: 0.4; transform: scale(0.85); }}
    }}

    .report-header {{
      border-bottom: 2px solid rgba(99, 102, 241, 0.35);
      padding-bottom: 16px;
      margin-bottom: 20px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .report-title {{
      font-size: 22px;
      font-weight: 700;
      color: #ffffff;
      margin: 0 0 4px 0;
      letter-spacing: -0.01em;
    }}
    .report-subtitle {{
      font-size: 13.5px;
      color: #94a3b8;
      margin: 0;
    }}

    .table-card {{
      border-radius: 14px;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.08);
      background: rgba(17, 24, 39, 0.7);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13.5px;
      text-align: left;
    }}
    th {{
      background: #1e293b;
      color: #cbd5e1;
      font-weight: 600;
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.06em;
      padding: 13px 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }}
    td {{
      padding: 13px 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      color: #cbd5e1;
      line-height: 1.5;
    }}
    tr:last-child td {{
      border-bottom: none;
    }}
    tr:hover td {{
      background: rgba(255, 255, 255, 0.03);
    }}
    .badge-custom {{
      background: rgba(99, 102, 241, 0.22);
      color: #a5b4fc;
      border: 1px solid rgba(99, 102, 241, 0.4);
      font-size: 10px;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 8px;
      margin-left: 6px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    /* Print Stylesheet for clean PDF / Paper Export */
    @media print {{
      body {{
        background: #ffffff !important;
        color: #0f172a !important;
        padding: 24px !important;
      }}
      .action-row {{
        display: none !important;
      }}
      .report-title {{
        color: #1e1b4b !important;
      }}
      .report-subtitle {{
        color: #475569 !important;
      }}
      .report-header {{
        border-bottom: 2px solid #4f46e5 !important;
      }}
      .table-card {{
        border: 1px solid #cbd5e1 !important;
        background: #ffffff !important;
        box-shadow: none !important;
      }}
      th {{
        background: #f1f5f9 !important;
        color: #334155 !important;
        border-bottom: 2px solid #cbd5e1 !important;
      }}
      td {{
        color: #334155 !important;
        border-bottom: 1px solid #e2e8f0 !important;
      }}
      .badge-custom {{
        background: #e0e7ff !important;
        color: #3730a3 !important;
        border: 1px solid #c7d2fe !important;
      }}
    }}
  </style>
</head>
<body>
  <div class="action-row">
    <div class="action-btns">
      <button class="print-btn" onclick="window.print()">
        <span>🖨️</span> Save as PDF / Print Document
      </button>
      <button class="reset-btn" onclick="resetToDefaults()" title="Revert to original built-in parts">
        <span>🔄</span> Reset to Defaults
      </button>
    </div>
    <div class="live-badge">
      <span class="live-dot"></span>
      <span>Live Sync Active</span>
    </div>
  </div>

  <div class="report-header">
    <div>
      <h1 class="report-title">
        <span>📄</span> Engineering Part Specification Report
      </h1>
      <p class="report-subtitle">Prototype: <strong>{model_choice}</strong> | Engineering Project Report</p>
    </div>
    <div style="font-size: 12.5px; color: #94a3b8; text-align: right;">
      <div>Generated: {current_date_str}</div>
      <div>Total Parts: <strong id="part-count" style="color: #60a5fa;">0</strong></div>
    </div>
  </div>

  <div class="table-card">
    <table>
      <thead>
        <tr>
          <th style="width: 20%;">Component Part</th>
          <th style="width: 25%;">Material Composition</th>
          <th style="width: 27%;">Primary Function</th>
          <th style="width: 28%;">Engineering Notes</th>
        </tr>
      </thead>
      <tbody id="spec-table-body">
      </tbody>
    </table>
  </div>

  <script>
    const isCustomModel = {is_custom_model_str};
    const currentModel = "{model_choice}";
    // Use stable key for user-uploaded models so renaming never loses custom hotspots
    const storageKey = isCustomModel
      ? 'explainit3d_custom_hotspots_user_uploaded_model'
      : 'explainit3d_custom_hotspots_' + currentModel.split(' ').join('_');
    const deletedKey = isCustomModel
      ? 'explainit3d_deleted_hotspots_user_uploaded_model'
      : 'explainit3d_deleted_hotspots_' + currentModel.split(' ').join('_');
    const baseParts = {base_spec_json};

    function getCatalog() {{
      let catalog = Object.assign({{}}, baseParts);
      try {{
        let saved = localStorage.getItem(storageKey);
        // Migration fallback: check legacy or model-named keys for custom models
        if (!saved && isCustomModel) {{
          saved = localStorage.getItem('explainit3d_custom_hotspots_' + currentModel.split(' ').join('_')) ||
                  localStorage.getItem('explainit3d_custom_hotspots_Uploaded_Custom_Model');
          if (saved) {{
            localStorage.setItem(storageKey, saved);
          }}
        }}
        if (saved) {{
          const custom = JSON.parse(saved);
          catalog = Object.assign({{}}, catalog, custom);
        }}
        let delList = JSON.parse(localStorage.getItem(deletedKey) || '[]');
        if (delList.length === 0 && isCustomModel) {{
          delList = JSON.parse(localStorage.getItem('explainit3d_deleted_hotspots_' + currentModel.split(' ').join('_')) || '[]') ||
                    JSON.parse(localStorage.getItem('explainit3d_deleted_hotspots_Uploaded_Custom_Model') || '[]');
          if (delList.length > 0) {{
            localStorage.setItem(deletedKey, JSON.stringify(delList));
          }}
        }}
        delList.forEach(name => delete catalog[name]);
      }} catch(e) {{
        console.error(e);
      }}
      return catalog;
    }}

    function renderSpecTable() {{
      const catalog = getCatalog();
      const tbody = document.getElementById('spec-table-body');
      const countEl = document.getElementById('part-count');
      const entries = Object.entries(catalog);
      
      if (countEl) countEl.innerText = entries.length;

      if (entries.length === 0) {{
        tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding:32px; color:#64748b;">No parts annotated for this model.</td></tr>`;
        return;
      }}

      let html = '';
      for (const [name, pdata] of entries) {{
        const isCustom = pdata.isCustom ? '<span class="badge-custom">Custom</span>' : '';
        html += `
          <tr>
            <td style="font-weight:600; color:#ffffff;">${{name}} ${{isCustom}}</td>
            <td style="color:#cbd5e1;">${{pdata.material || '—'}}</td>
            <td style="color:#cbd5e1;">${{pdata.function || '—'}}</td>
            <td style="color:#94a3b8; font-size:13px;">${{pdata.notes || pdata.explanation || '—'}}</td>
          </tr>
        `;
      }}
      tbody.innerHTML = html;
    }}

    function resetToDefaults() {{
      if (!confirm("Reset all parts for this model back to original defaults?")) return;
      try {{
        localStorage.removeItem(storageKey);
        localStorage.removeItem(deletedKey);
        window.parent.postMessage('explainit3d_update', '*');
      }} catch(e) {{}}
      renderSpecTable();
    }}

    // Initial render
    renderSpecTable();

    // Listen for live updates from localStorage and message events
    window.addEventListener('storage', renderSpecTable);
    window.addEventListener('message', (e) => {{
      if (e.data === 'explainit3d_update') renderSpecTable();
    }});

    // Continuous polling check so any newly added or removed hotspot updates in real-time
    setInterval(renderSpecTable, 800);
  </script>
</body>
</html>
"""

with st.expander("📄 Project Spec Sheet & PDF Export", expanded=False):
    st.markdown(
        """
        <p style="font-size: 14px; color: #94a3b8; margin-bottom: 14px;">
            Live engineering specification document for your college report. 
            Updates in real-time whenever you add or remove hotspots. Click the button below to print or save directly as a clean PDF.
        </p>
        """,
        unsafe_allow_html=True,
    )
    components.html(spec_sheet_html, height=460, scrolling=True)

# -----------------------------------------------------------------------------
# 7. TEMPORARY CUSTOM GLB UPLOADER
# -----------------------------------------------------------------------------
with st.expander("📁 Temporary Preview: Upload Your Own .glb File", expanded=("uploaded_glb_data" in st.session_state)):
    st.markdown(
        """
        <p style="font-size: 13.5px; color: #94a3b8;">
            Quickly preview a new 3D scan or exported CAD model directly from your computer without uploading to GitHub first.
        </p>
        """,
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader(
        "Choose a .glb file",
        type=["glb"],
        label_visibility="collapsed",
    )
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        b64_glb = base64.b64encode(file_bytes).decode("utf-8")
        st.session_state["uploaded_glb_data"] = f"data:model/gltf-binary;base64,{b64_glb}"
        
        # Derive clean prototype name from file if not set or if a new file was uploaded
        if "uploaded_model_name" not in st.session_state or st.session_state.get("_last_uploaded_file") != uploaded_file.name:
            clean_stem = Path(uploaded_file.name).stem.replace("_", " ").replace("-", " ").strip().title()
            model_name = clean_stem if clean_stem else "Custom Prototype"
            st.session_state["uploaded_model_name"] = model_name
            st.session_state["_last_uploaded_file"] = uploaded_file.name
        else:
            model_name = st.session_state["uploaded_model_name"]

        # Persist to local disk so it permanently survives page refreshes (F5)
        try:
            CUSTOM_GLB_PATH.write_bytes(file_bytes)
            meta = {
                "name": model_name,
                "filename": uploaded_file.name,
            }
            CUSTOM_META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        except Exception:
            pass

        st.rerun()

    if "uploaded_glb_data" in st.session_state:
        current_custom_name = st.session_state.get("uploaded_model_name", "Custom Prototype")
        st.markdown("<hr style='border:none; border-top:1px solid rgba(255,255,255,0.08); margin:14px 0;'>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 13.5px; color: #10b981; font-weight:600;'>✅ Active Preview: <strong>{current_custom_name}</strong></p>", unsafe_allow_html=True)
        
        rename_col1, rename_col2 = st.columns([3, 1], vertical_alignment="bottom")
        with rename_col1:
            name_input_val = st.text_input(
                "Model Prototype Display Name:",
                value=current_custom_name,
                key="custom_model_rename_field",
                help="Change the prototype name shown in the viewer, dropdown, and engineering spec sheet.",
            )
        with rename_col2:
            if st.button("Update Name", use_container_width=True, key="btn_update_uploader_name", type="primary"):
                if name_input_val.strip() and name_input_val.strip() != current_custom_name:
                    new_name = name_input_val.strip()
                    st.session_state["uploaded_model_name"] = new_name
                    # Also update persistent metadata on disk
                    try:
                        meta = {"name": new_name, "filename": st.session_state.get("_last_uploaded_file", "custom_model.glb")}
                        if CUSTOM_META_PATH.exists():
                            meta = json.loads(CUSTOM_META_PATH.read_text(encoding="utf-8"))
                            meta["name"] = new_name
                        CUSTOM_META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
                    except Exception:
                        pass
                    st.rerun()
