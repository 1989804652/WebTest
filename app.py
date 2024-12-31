import streamlit as st
import requests
from bs4 import BeautifulSoup
import jieba
from collections import Counter
import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import WordCloud, Bar, Pie, Line, Scatter, Funnel, Radar
from pyecharts.globals import SymbolType, ThemeType
from streamlit_echarts import st_pyecharts
import re
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pyecharts import options as opts
from pyecharts.charts import WordCloud, Bar, Pie, Line

def get_text_content(url):
    """获取网页文本内容"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 移除script、style等标签
        for tag in soup.find_all(['script', 'style', 'iframe']):
            tag.decompose()
            
        return soup.get_text()
        
    except Exception as e:
        st.error(f"获取内容失败: {str(e)}")
        return ""

def process_text(text, min_freq=2):
    """文本分词和统计"""
    # 加载停用词
    stop_words = set([line.strip() for line in open('stop_words.txt', encoding='utf-8')])
    
    # 分词并过滤
    words = jieba.cut(text)
    words = [w for w in words if w not in stop_words and len(w) > 1]
    
    # 统计词频
    word_freq = Counter(words)
    
    # 过滤低频词
    word_freq = {k:v for k,v in word_freq.items() if v >= min_freq}
    
    return word_freq

def create_charts(word_freq, chart_lib="Pyecharts"):
    """创建各种图表"""
    if not word_freq:
        st.error("没有找到任何词频数据")
        return {}
        
    # 准备数据
    items = list(word_freq.items())
    words, freqs = zip(*sorted(items, key=lambda x: x[1], reverse=True)[:20])
    
    if chart_lib == "Pyecharts":
        return create_pyecharts(words, freqs)
    elif chart_lib == "Plotly":
        return create_plotly(words, freqs)
    else:  # Matplotlib
        return create_matplotlib(words, freqs)

def create_pyecharts(words, freqs):
    """使用Pyecharts创建图表"""
    charts = {}
    
    # 词云图
    word_freq_list = list(zip(words, freqs))
    charts["词云图"] = (
        WordCloud()
        .add(
            series_name="",
            data_pair=word_freq_list,
            word_size_range=[20, 100]
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="词云图"),
            tooltip_opts=opts.TooltipOpts(is_show=True),
        )
    )

    # 柱状图
    charts["柱状图"] = (
        Bar()
        .add_xaxis(list(words))
        .add_yaxis(
            series_name="词频",
            y_axis=list(freqs),
            label_opts=opts.LabelOpts(is_show=True)
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="词频柱状图"),
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(rotate=45)
            )
        )
    )

    # 折线图
    charts["折线图"] = (
        Line()
        .add_xaxis(list(words))
        .add_yaxis(
            series_name="词频",
            y_axis=list(freqs),
            label_opts=opts.LabelOpts(is_show=True)
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="词频趋势图"),
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(rotate=45)
            )
        )
    )
    
    return charts

def create_plotly(words, freqs):
    """使用Plotly创建图表"""
    df = pd.DataFrame({"词语": words, "频次": freqs})
    
    charts = {
        "柱状图": px.bar(df, x="词语", y="频次", title="词频柱状图"),
        "折线图": px.line(df, x="词语", y="频次", title="词频趋势图"),
        "散点图": px.scatter(df, x="词语", y="频次", title="词频散点图")
    }
    
    # 调整x轴标签角度
    for chart in charts.values():
        chart.update_layout(xaxis_tickangle=45)
    
    return charts

def create_matplotlib(words, freqs):
    """使用Matplotlib创建图表"""
    # 删除 seaborn 样式设置，使用默认样式或其他可用样式
    plt.style.use('default')  # 或使用其他内置样式如 'classic', 'ggplot'
    
    # 设置中文字体支持
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
    
    charts = {}
    
    # 柱状图
    fig_bar, ax_bar = plt.subplots(figsize=(12, 6))
    ax_bar.bar(words, freqs)
    ax_bar.set_xticklabels(words, rotation=45, ha='right')
    ax_bar.set_title("词频柱状图")
    plt.tight_layout()  # 自动调整布局
    charts["柱状图"] = fig_bar
    
    # 折线图
    fig_line, ax_line = plt.subplots(figsize=(12, 6))
    ax_line.plot(words, freqs, marker='o')
    ax_line.set_xticklabels(words, rotation=45, ha='right')
    ax_line.set_title("词频趋势图")
    plt.tight_layout()
    charts["折线图"] = fig_line
    
    # 散点图
    fig_scatter, ax_scatter = plt.subplots(figsize=(12, 6))
    ax_scatter.scatter(words, freqs)
    ax_scatter.set_xticklabels(words, rotation=45, ha='right')
    ax_scatter.set_title("词频散点图")
    plt.tight_layout()
    charts["散点图"] = fig_scatter
    
    return charts

def main():
    st.title("文本分析可视化工具")
    
    # 侧边栏配置
    st.sidebar.header("配置")
    url = st.sidebar.text_input("输入文章URL")
    min_freq = st.sidebar.slider("最小词频", 1, 10, 2)
    
    # 选择可视化库
    chart_lib = st.sidebar.selectbox("选择可视化库", ["Pyecharts", "Plotly", "Matplotlib"])
    
    # 根据所选库显示对应的图表类型
    chart_types = {
        "Pyecharts": ["词云图", "柱状图", "折线图"],
        "Plotly": ["柱状图", "折线图", "散点图"],
        "Matplotlib": ["柱状图", "折线图", "散点图"]
    }
    
    chart_type = st.sidebar.selectbox("选择图表类型", chart_types[chart_lib])
    
    if url:
        text = get_text_content(url)
        if text:
            word_freq = process_text(text, min_freq)
            if word_freq:
                # 展示词频统计
                st.subheader("词频统计 (Top 20)")
                df = pd.DataFrame(
                    sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20],
                    columns=["词语", "频次"]
                )
                st.dataframe(df)
                
                # 展示选中的图表
                st.subheader(f"可视化图表 - {chart_type}")
                charts = create_charts(word_freq, chart_lib)
                
                if chart_lib == "Pyecharts":
                    try:
                        st_pyecharts(
                            charts[chart_type],
                            height=400
                        )
                    except Exception as e:
                        st.error(f"图表渲染失败: {str(e)}")
                        st.write("Debug info:", str(charts[chart_type]))
                elif chart_lib == "Plotly":
                    st.plotly_chart(charts[chart_type])
                else:  # Matplotlib
                    st.pyplot(charts[chart_type])

if __name__ == "__main__":
    main()
