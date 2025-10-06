"""
Chart factory for creating common chart types
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional

class ChartFactory:
    """Factory for creating common chart types"""
    
    @staticmethod
    def create_metric_cards(metrics: Dict[str, Any], columns: int = 4) -> None:
        """Create metric cards display"""
        if not metrics:
            return
        
        # Create columns
        cols = st.columns(columns)
        
        # Display metrics
        for i, (key, value) in enumerate(metrics.items()):
            with cols[i % columns]:
                if isinstance(value, (int, float)):
                    if value >= 1000:
                        display_value = f"{value:,}"
                    else:
                        display_value = str(value)
                else:
                    display_value = str(value)
                
                st.metric(key, display_value)
    
    @staticmethod
    def create_bar_chart(data: pd.DataFrame, x: str, y: str, title: str, 
                        color: Optional[str] = None) -> go.Figure:
        """Create a bar chart"""
        fig = px.bar(
            data, 
            x=x, 
            y=y, 
            title=title,
            color=color,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_layout(
            xaxis_title=x.title(),
            yaxis_title=y.title(),
            showlegend=True if color else False,
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_line_chart(data: pd.DataFrame, x: str, y: str, title: str,
                         color: Optional[str] = None) -> go.Figure:
        """Create a line chart"""
        fig = px.line(
            data,
            x=x,
            y=y,
            title=title,
            color=color,
            markers=True
        )
        
        fig.update_layout(
            xaxis_title=x.title(),
            yaxis_title=y.title(),
            showlegend=True if color else False,
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_pie_chart(data: pd.DataFrame, names: str, values: str, title: str) -> go.Figure:
        """Create a pie chart"""
        fig = px.pie(
            data,
            names=names,
            values=values,
            title=title,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_layout(height=400)
        
        return fig
    
    @staticmethod
    def create_platform_comparison_chart(platform_data: List[Dict[str, Any]], 
                                       metric: str, title: str) -> go.Figure:
        """Create platform comparison chart"""
        df = pd.DataFrame(platform_data)
        
        fig = px.bar(
            df,
            x='Platform',
            y=metric,
            title=title,
            color='Platform',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_layout(
            xaxis_title="Platform",
            yaxis_title=metric.title(),
            showlegend=False,
            height=400
        )
        
        return fig

