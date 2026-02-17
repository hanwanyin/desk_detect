import streamlit as st
import base64
import json
import os
import qrcode
from io import BytesIO
from dotenv import load_dotenv
from zai import ZhipuAiClient

# --- 1. 配置与初始化 ---
load_dotenv()
st.set_page_config(page_title="Desk Detective Pro", page_icon="🕵️‍♂️", layout="centered")

api_key = os.getenv("ZHIPU_API_KEY")
if not api_key:
    st.error("❌ 请检查 .env 文件中的 ZHIPU_API_KEY")
    st.stop()

client = ZhipuAiClient(api_key=api_key)

# --- 2. 进阶 Prompt (复制上面的) ---
SYSTEM_PROMPT = """
你现在的身份是“Desk Detective”（桌面神探）。你是一个结合了夏洛克·福尔摩斯的观察力、罗永浩的吐槽能力、以及算命大师玄学理论的 AI。
你的任务是基于照片进行“冷读”，通过物品细节反推主人的心理状态。

请必须严格按照以下 JSON 格式返回结果（纯 JSON，无 Markdown）：
{
    "detective_name": "给这个桌面起一个中二的称号 (e.g., '赛博朋克拾荒者')",
    "stress_score": 整数(0-100),
    "rpg_stats": {
        "intelligence": 整数(0-10),
        "chaos": 整数(0-10), 
        "social": 整数(0-10),
        "survival": 整数(0-10)
    },
    "mbti_desk": "创造一个由4个字母组成的虚构MBTI (e.g. 'LAZY')",
    "visual_evidence": ["线索1", "线索2", "线索3"],
    "roast": "一句犀利、幽默、带点'冒犯性'的吐槽。",
    "lucky_item": "画面中一个具体物品",
    "fortune_prediction": "基于桌面风水的一句运势预测"
}
"""

# --- 3. 功能函数 ---
def get_base64_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

def generate_qr_code(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

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
            temperature=0.8, # 稍微调高一点，让吐槽更骚
            top_p=0.9
        )
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        st.error(f"分析出错: {e}")
        return None

# --- 4. 侧边栏：二维码生成器 ---
with st.sidebar:
    st.header("📱 手机扫码体验")
    st.caption("请查看你的终端(Terminal)，找到 'Network URL' (例如 http://192.168.1.5:8501)")
    
    # 获取用户输入的 URL (因为自动获取本地 IP 在不同路由器下不稳定，手动输入最稳)
    url_input = st.text_input("输入终端里的 Network URL:", value="http://")
    
    if url_input and "http" in url_input:
        qr_img = generate_qr_code(url_input)
        # 将 PIL 图片转为字节流以在 Streamlit 显示
        buf = BytesIO()
        qr_img.save(buf)
        st.image(buf, caption="让朋友扫这个码（需在同一WiFi下）", use_container_width=True)

# --- 5. 主界面 ---
st.title("🕵️‍♂️ Desk Detective | Pro")
st.markdown("*“你的桌面，出卖了你的灵魂。”*")

img_file = st.camera_input("📸 拍摄案发现场")

if img_file:
    with st.spinner('🕵️‍♂️ 正在进行通灵...'):
        result = analyze_image(get_base64_image(img_file))

    if result:
        st.balloons()
        
        # 结果头部
        st.header(f"📇 鉴定称号：{result.get('detective_name')}")
        
        # 核心指标区
        c1, c2, c3 = st.columns(3)
        c1.metric("压力指数", result.get('stress_score'), delta_color="inverse")
        c2.metric("桌面 MBTI", result.get('mbti_desk'))
        c3.metric("幸运物", result.get('lucky_item'))

        st.divider()

        # 雷达能力值 (用进度条模拟)
        st.subheader("📊 玩家属性")
        stats = result.get('rpg_stats', {})
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("🧠 智力 (INT)")
            st.progress(stats.get('intelligence', 5) / 10)
            st.write("🌪️ 混乱 (CHA)")
            st.progress(stats.get('chaos', 5) / 10)
        with col_b:
            st.write("🤝 社交 (SOC)")
            st.progress(stats.get('social', 5) / 10)
            st.write("🏕️ 生存 (SUR)")
            st.progress(stats.get('survival', 5) / 10)

        st.divider()
        
        # 毒舌吐槽区 (重点！)
        st.markdown("### 💬 侦探毒舌报告")
        st.info(result.get('roast'))
        
        # 证据展示
        with st.expander("🔎 查看定罪证据"):
            for evidence in result.get('visual_evidence', []):
                st.write(f"- {evidence}")
        
        # 运势
        st.success(f"🔮 **今日运势：** {result.get('fortune_prediction')}")
