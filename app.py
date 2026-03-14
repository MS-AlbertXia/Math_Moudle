import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import pandas as pd
from io import BytesIO

# -------------------------- 1. 页面配置 --------------------------
st.set_page_config(page_title="开罐头方法实验数据可视化", layout="wide")
st.title("📊 开罐头方法实验数据可视化与导出工具")

# -------------------------- 2. 侧边栏：数据配置（匹配实验数据） --------------------------
st.sidebar.header("🔧 实验数据配置")

# 替换为开罐头三种方法的实际实验数据
default_data = {
    "开罐头方法": ["橡皮筋法", "水浴法", "敲击法"],
    "扭矩降低幅度(%)": [50, 65, 55],  # 取之前实验数据的中间值
    "操作时间(秒)": [8, 90, 20]        # 取之前实验数据的中间值
}
df = pd.DataFrame(default_data)

# 交互式编辑数据表格（匹配实验数据名称）
st.sidebar.subheader("实验数据编辑")
edited_df = st.sidebar.data_editor(
    df, 
    num_rows="dynamic", 
    key="data_editor"
)  # 支持增删行，比如添加其他开罐头方法

# 图表类型选择（保持语义化，适配实验数据）
chart_type = st.sidebar.selectbox(
    "图表类型选择", 
    ["折线图", "柱状图", "散点图", "饼图"], 
    key="chart_selector"
)

# 数值微调（针对“扭矩降低幅度(%)”列，匹配实验指标）
if "扭矩降低幅度(%)" in edited_df.columns:
    st.sidebar.subheader("实验数值微调")
    # 按行生成滑块，匹配“开罐头方法+扭矩降低幅度”的组合
    for idx, row in edited_df.iterrows():
        new_value = st.sidebar.slider(
            label=f"{row['开罐头方法']} - 扭矩降低幅度(%)",  # 精准匹配实验指标
            min_value=0,
            max_value=100,  # 百分比范围0-100
            value=int(row["扭矩降低幅度(%)"]),
            key=f"slider_{idx}"  # 唯一key避免交互冲突
        )
        edited_df.loc[idx, "扭矩降低幅度(%)"] = new_value

# -------------------------- 3. 主界面：图表显示（适配实验数据） --------------------------
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📈 开罐头方法实验数据图表")
    
    # 根据选择生成图表（适配新的列名）
    if chart_type == "折线图":
        fig = px.line(
            edited_df, 
            x="开罐头方法", 
            y=["扭矩降低幅度(%)", "操作时间(秒)"], 
            markers=True,
            title="不同开罐头方法的扭矩降低幅度与操作时间对比"
        )
    elif chart_type == "柱状图":
        fig = px.bar(
            edited_df, 
            x="开罐头方法", 
            y=["扭矩降低幅度(%)", "操作时间(秒)"], 
            barmode="group",
            title="不同开罐头方法的扭矩降低幅度与操作时间对比"
        )
    elif chart_type == "散点图":
        fig = px.scatter(
            edited_df, 
            x="扭矩降低幅度(%)", 
            y="操作时间(秒)", 
            color="开罐头方法", 
            size="扭矩降低幅度(%)",
            title="扭矩降低幅度 vs 操作时间"
        )
    elif chart_type == "饼图":
        fig = px.pie(
            edited_df, 
            names="开罐头方法", 
            values="扭矩降低幅度(%)",
            title="各方法扭矩降低幅度占比"
        )
    
    # 优化图表样式，适配实验数据展示
    fig.update_layout(
        xaxis_title="开罐头方法",
        yaxis_title="数值",
        font=dict(size=12)
    )
    st.plotly_chart(fig, use_container_width=True)  # 自适应宽度

with col2:
    st.subheader("📋 实验数据预览")
    st.dataframe(edited_df, use_container_width=True)

# -------------------------- 4. 导出与打印功能（匹配实验数据命名） --------------------------
st.divider()
st.subheader("💾 实验数据导出与打印")

# 1. 导出数据为CSV（命名匹配实验数据）
def to_csv(df):
    return df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="📥 导出实验数据为CSV文件",
    data=to_csv(edited_df),
    file_name="开罐头方法实验数据.csv",  # 文件名匹配实验主题
    mime="text/csv",
    key="csv_download"
)

# 2. 导出图表为PNG（命名匹配实验数据）
def to_png(fig):
    img_buffer = BytesIO()
    fig.write_image(img_buffer, format="png", width=1200, height=600)
    return img_buffer.getvalue()

st.download_button(
    label="📸 导出实验图表为PNG图片",
    data=to_png(fig),
    file_name="开罐头方法实验数据图表.png",  # 文件名匹配实验主题
    mime="image/png",
    key="png_download"
)

# 3. 打印功能（仅打印图表）
st.markdown("🖨️ **打印实验图表**：点击下方按钮打印当前生成的实验数据图表")
if st.button("打印当前实验图表", key="print_button"):
    # 将 Plotly 图表转换为 HTML
    chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    # 使用 Base64 编码 HTML 内容，防止特殊字符干扰 JavaScript 字符串
    import base64
    encoded_html = base64.b64encode(chart_html.encode('utf-8')).decode('utf-8')
    
    print_js = f"""
        <script>
            function printChart() {{
                var chartHtml = atob('{encoded_html}');
                var printWindow = window.open('', '_blank');
                printWindow.document.write('<html lang="zh"><head><meta charset="UTF-8"><title>开罐头方法实验数据图表</title>');
                printWindow.document.write('<style>body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }} #print-area {{ width: 100%; }} @media print {{ body {{ margin: 0; }} }}</style>');
                printWindow.document.write('</head><body>');
                printWindow.document.write('<div id="print-area">' + chartHtml + '</div>');
                printWindow.document.close();
                
                // 等待 Plotly 在新窗口中渲染完成
                setTimeout(function() {{
                    printWindow.print();
                    printWindow.close();
                }}, 1000);
            }}
            printChart();
        </script>
    """
    components.html(print_js, height=0)