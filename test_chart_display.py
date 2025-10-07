#!/usr/bin/env python3
"""
测试图表显示功能
"""

import streamlit as st
import json
import os

def test_chart_display():
    """测试图表显示"""
    st.title("📊 图表显示测试")
    
    # 加载一个图表文件
    chart_file = "data/cache/charts/reddit_ai_trend.json"
    
    if os.path.exists(chart_file):
        with open(chart_file, 'r', encoding='utf-8') as f:
            chart_data = json.load(f)
        
        st.write("### 图表数据:")
        st.json(chart_data['statistics'])
        
        st.write("### 图表显示:")
        chart_html = chart_data['chart_html']
        
        # 添加Plotly.js库
        if 'plotly.js' not in chart_html.lower():
            plotly_js = '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'
            chart_html = chart_html.replace('<head>', f'<head>{plotly_js}')
        
        st.components.v1.html(chart_html, height=450)
        
    else:
        st.error(f"图表文件不存在: {chart_file}")

if __name__ == "__main__":
    test_chart_display()
