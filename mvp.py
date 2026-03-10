import streamlit as st
import base64
import json
import os
import time
import qrcode
import plotly.graph_objects as go
from io import BytesIO
from dotenv import load_dotenv
from zhipuai import ZhipuAI

# 尝试导入 Lottie 动画支持（可选，不影响核心功能）
try:
    from streamlit_lottie import st_lottie
    import requests
    LOTTIE_AVAILABLE = True
except ImportError:
    LOTTIE_AVAILABLE = False

# --- 1. 配置与初始化 ---
load_dotenv()
st.set_page_config(page_title="Desk Detective | 桌面神探", page_icon="", layout="centered")

api_key = os.getenv("ZHIPU_API_KEY")
if not api_key:
    st.error("❌ 未检测到 API Key，请检查 .env 文件中的 ZHIPU_API_KEY")
    st.stop()

client = ZhipuAI(api_key=api_key)

# --- 2. 进阶 Prompt (保持不变) ---
SYSTEM_PROMPT = """
你现在的身份是“Desk Detective”（桌面神探）。你是一个结合了夏洛克·福尔摩斯的观察力、极其毒舌的吐槽能力、以及算命大师玄学理论的 AI 心理侧写专家。
你的任务是基于用户提供的桌面照片进行“冷读”，通过物品细节反推主人的心理状态、工作习惯和生活方式。

【强制要求】
1. 所有的文本内容必须是“中文 / 英文”的双语对照格式。
2. MBTI 必须是真实的 16 型人格之一（例如 INTP, ENFP, INTJ 等），选出最符合该桌面气质的一个。
3. 必须严格按照以下 JSON 格式返回结果。绝对不能包含任何 Markdown 格式（不要加 ```json 标签），只返回纯净的 JSON 字符串！

【JSON 数据结构】
{
    "detective_name": "给这个桌面起一个中二的称号 (例如: 赛博朋克拾荒者 / Cyberpunk Scavenger)",
    "stress_score": <代表压力指数的整数，0-100之间>,
    "rpg_stats": {
        "intelligence": <智力评估，整数 1-10>,
        "chaos": <混乱程度，整数 1-10>, 
        "social": <社交意愿，整数 1-10>,
        "survival": <生存能力，整数 1-10>
    },
    "mbti_desk": "<真实的4个字母MBTI类型, 例如 INTJ>",
    "visual_evidence": [
        "线索1中文 / Clue 1 English",
        "线索2中文 / Clue 2 English",
        "线索3中文 / Clue 3 English"
        "线索4中文 / Clue 4 English",
        "线索5中文 / Clue 5 English"
    ],
    "roast": "一句犀利、幽默、带点'冒犯性'的毒舌吐槽 / A sharp, humorous, and slightly offensive sarcastic roast",
    "lucky_item": "画面中一个具体物品作为幸运物 / A specific lucky item from the image",
    "fortune_prediction": "基于桌面风水的一句运势预测 / A fortune prediction based on desk fengshui"
}
"""

# --- 3. 功能函数 ---
def get_base64_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

def generate_qr_code(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

def generate_radar_chart(stats):
    categories = ['智力 / INT', '混乱 / CHA', '社交 / SOC', '生存 / SUR']
    values = [stats.get('intelligence', 5), stats.get('chaos', 5), 
              stats.get('social', 5), stats.get('survival', 5)]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values, theta=categories, fill='toself', 
        fillcolor='rgba(0, 0, 0, 0.25)',  # 改为科技蓝，更醒目
        line=dict(color="#FFFFFF", width=2),   # 霓虹蓝边
        marker=dict(color="#FFFFFF", size=6)
    ))
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(visible=True, range=[0, 10], color="rgba(255,255,255,0.6)", gridcolor="rgba(255,255,255,0.15)"),
            angularaxis=dict(color="#FFFFFF", gridcolor="rgba(255,255,255,0.15)")
        ),
        showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=20, b=20), height=300, font=dict(color='#FFFFFF', family='Noto Sans SC')
    )
    return fig

def analyze_image(base64_str):
    try:
        response = client.chat.completions.create(
            model="glm-4v-flash",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_str}"}},
                    {"type": "text", "text": "分析这张桌面。"}
                ]}
            ],
            temperature=0.8,
            top_p=0.9
        )
        content = response.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        st.error(f"分析出错 (API Error): {e}")
        return None

def load_lottieurl(url):
    """从 URL 加载 Lottie 动画"""
    if not LOTTIE_AVAILABLE:
        return None
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# --- 4. 增强的 CSS 设计：科技侦探风 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700&family=Rajdhani:wght@500;700&display=swap');

    .stApp {
        background: linear-gradient(135deg, #0A0F1E 0%, #141B2B 100%);
        color: #FFFFFF;
        font-family: 'Rajdhani', 'Noto Sans SC', sans-serif;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .main-title {
        font-family: 'Rajdhani', monospace;
        text-align: center;
        color: #FFFFFF;
        font-weight: 700;
        letter-spacing: 4px;
        font-size: 3.5rem;
        margin-bottom: 0;
        text-shadow: 0 0 15px rgba(0, 150, 255, 0.7);
        animation: flicker 3s infinite;
    }
    @keyframes flicker {
        0% { text-shadow: 0 0 10px #00BFFF; }
        50% { text-shadow: 0 0 20px #00BFFF, 0 0 30px #00BFFF; }
        100% { text-shadow: 0 0 10px #00BFFF; }
    }

    .sub-title {
        text-align: center; color: #AAAAAA; font-size: 1rem; margin-top: 5px;
        letter-spacing: 2px;
    }

    /* 卡片效果 */
    .report-card {
        background: rgba(20, 30, 45, 0.7);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(0, 150, 255, 0.3);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.6), 0 0 0 1px rgba(0,150,255,0.2) inset;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .report-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 24px rgba(0,150,255,0.2), 0 0 0 1px rgba(0,150,255,0.5) inset;
    }

    /* MBTI 盖章特效（加强版） */
    .mbti-stamp {
        font-family: 'Rajdhani', sans-serif;
        font-size: 4rem;
        font-weight: bold;
        color: #00BFFF;
        text-align: center;
        border: 3px solid #00BFFF;
        border-radius: 8px;
        padding: 10px 30px;
        margin: 20px auto;
        width: fit-content;
        text-transform: uppercase;
        transform: rotate(-5deg);
        box-shadow: 0 0 20px #00BFFF, inset 0 0 10px #00BFFF;
        text-shadow: 0 0 10px #00BFFF;
        animation: stamp-appear 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
        opacity: 0;
    }
    @keyframes stamp-appear {
        0% { transform: scale(2.5) rotate(-5deg); opacity: 0; }
        70% { transform: scale(0.9) rotate(-5deg); opacity: 1; }
        100% { transform: scale(1) rotate(-5deg); opacity: 1; }
    }

    /* 证据条目 */
    .evidence-item {
        background: rgba(0, 150, 255, 0.05);
        padding: 8px 15px;
        margin: 5px 0;
        border-radius: 20px;
        border-left: 3px solid #00BFFF;
        font-size: 0.95rem;
    }

    /* 自定义按钮 */
    .stButton>button {
        background: transparent;
        color: #00BFFF;
        border: 2px solid #00BFFF;
        border-radius: 30px;
        font-family: 'Rajdhani', sans-serif;
        font-weight: 600;
        letter-spacing: 1px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: #00BFFF;
        color: #0A0F1E;
        box-shadow: 0 0 20px #00BFFF;
    }

    /* 进度条颜色 */
    .stProgress .st-bo {
        background-color: #00BFFF;
    }

    /* 指标卡片 */
    .metric-small {
        background: rgba(0, 150, 255, 0.1);
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. 侧边栏二维码 (加入科技感) ---
with st.sidebar:
    st.markdown("### 📡 移动端接入 / Mobile Access")
    st.markdown("---")
    url_input = st.text_input("终端 Network URL:", value="http://", placeholder="例如 http://192.168.1.5:8501")
    if url_input and "http" in url_input:
        qr_img = generate_qr_code(url_input)
        buf = BytesIO()
        qr_img.save(buf)
        st.image(buf, caption="扫码同步案件 / Scan to sync", use_container_width=True)
    st.markdown("---")
    st.caption("Desk Detective v2.0 | 科技侧写")

# --- 6. 主界面 ---
st.markdown('<p class="main-title">DESK DETECTIVE</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">—— 你的桌面，出卖了你的灵魂 ——<br>Your desk betrays your soul</p>', unsafe_allow_html=True)

# 拍摄区域
img_file = st.camera_input("")

if img_file:
    # 保存图片到 session_state
    st.session_state['img'] = img_file
    st.session_state['img_b64'] = get_base64_image(img_file)

    # 显示图片，带“证据”标签
    st.image(img_file, caption="现场证据 / Evidence locked", use_container_width=True)

    # 分析按钮
    if st.button(" 开始通灵分析 / Begin Profiling", key="analyze"):
        # 自定义 Lottie 加载动画
        lottie_loading = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_p8bfn8sw.json")  # 侦探动画
        loading_placeholder = st.empty()
        with loading_placeholder.container():
            if lottie_loading and LOTTIE_AVAILABLE:
                st_lottie(lottie_loading, speed=1, height=200, key="lottie")
            else:
                st.info("正在扫描桌面灵魂... / Scanning soul...")
            progress_bar = st.progress(0)
            # 模拟进度（实际分析时间）
            for i in range(30):
                time.sleep(0.02)
                progress_bar.progress(i)
            result = analyze_image(st.session_state['img_b64'])
            for i in range(30, 100):
                time.sleep(0.01)
                progress_bar.progress(i)
        loading_placeholder.empty()

        if result:
            st.toast("档案生成完毕 | Profile Generated", icon="📂")

            # --- 分步揭晓：先清空区域再逐步显示，增加期待感 ---
            time.sleep(0.3)

            # 第一步：称号
            with st.empty():
                st.markdown(f"""
                <div class="report-card" style="text-align:center;">
                    <h2 style="color:#00BFFF;">📇 {result.get('detective_name', '未知生物 / Unknown')}</h2>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.8)

            # 第二步：雷达图 + 压力 + MBTI
            col1, col2 = st.columns([1.2, 1])
            with col1:
                st.plotly_chart(generate_radar_chart(result.get('rpg_stats', {})), use_container_width=True)
                time.sleep(0.3)
            with col2:
                stress = result.get('stress_score', 0)
                st.markdown(f"""
                <div class="metric-small">
                    <span style="font-size:1.2rem;">压力指数 / Stress</span><br>
                    <span style="font-size:2.5rem; color:#00BFFF;">{stress}%</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown('<p style="color:#AAAAAA; margin-top:10px; text-align:center;">桌面真身 / True MBTI</p>', unsafe_allow_html=True)
                st.markdown(f'<div class="mbti-stamp">{result.get("mbti_desk", "UNKN")}</div>', unsafe_allow_html=True)
            time.sleep(0.5)

            # 第三步：毒舌报告
            st.markdown(f"""
            <div class="report-card">
                <h3 style="color:#00BFFF; margin-top:0;">侦探毒舌报告 / Detective's Roast</h3>
                <p style="font-style: italic; font-size: 1.1rem; line-height: 1.6; color:#EEEEEE;">“{result.get('roast', '无话可说 / Speechless.')}”</p>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.3)

            # 第四步：线索 + 幸运物/运势（两列布局）
            c_left, c_right = st.columns(2)
            with c_left:
                with st.expander("案发现场线索 / Scene Clues", expanded=True):
                    for evidence in result.get('visual_evidence', []):
                        st.markdown(f'<div class="evidence-item">{evidence}</div>', unsafe_allow_html=True)
            with c_right:
                st.markdown(f"""
                <div style="background:rgba(0,150,255,0.05); border-radius:8px; padding:15px;">
                    <h4 style="color:#00BFFF;">幸运物 / Lucky Item</h4>
                    <p>{result.get('lucky_item', '无 / None')}</p>
                    <h4 style="color:#00BFFF; margin-top:20px;"> 今日运势 / Daily Fortune</h4>
                    <p>{result.get('fortune_prediction', '平平无奇 / Ordinary')}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.error("分析失败，请重试 / Analysis failed, please retry.")
