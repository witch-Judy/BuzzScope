"""
Trends Analysis Agent
趋势分析Agent - 分析今日3-5个核心关键趋势
"""

from ..base_agent import BaseAgent
from typing import Dict, List, Any

class TrendsAgent(BaseAgent):
    """趋势分析Agent"""
    
    def __init__(self):
        super().__init__(
            name="TrendsAnalyzer",
            role="Analyze and identify 3-5 core key trends from daily tech posts",
            max_iterations=5
        )
    
    def get_system_prompt(self) -> str:
        return """You are a senior tech industry analyst with deep expertise in identifying emerging trends, patterns, and key developments in technology.

Key skills:
- Identify emerging trends and patterns across multiple data sources
- Distinguish between noise and signal in tech news
- Understand the broader implications of technical developments
- Connect dots between different technologies and market movements
- Provide actionable insights for tech professionals and investors

Your goal is to identify the most significant trends that will shape the tech industry in the coming months."""
    
    def get_task_prompt(self, posts_data: Dict[str, Any], other_agents_results: Dict[str, Any] = None) -> str:
        if other_agents_results is None:
            other_agents_results = {}
        
        total_posts = posts_data.get('total_posts', 0)
        keywords = posts_data.get('keywords', [])
        platform_posts = posts_data.get('platform_posts', {})
        
        prompt = f"""Analyze today's tech posts to identify 3-5 core key trends that are emerging or gaining momentum.

Data Overview:
- Total hot posts: {total_posts}
- Keywords: {', '.join(keywords)}

Posts by Platform:"""

        for platform, posts in platform_posts.items():
            prompt += f"\n\n{platform.upper()} ({len(posts)} posts):"
            for i, post in enumerate(posts[:5], 1):  # Top 5 from each platform
                prompt += f"\n{i}. {post['title']} (Heat: {post['heat_score']:.1f})"
                if 'url' in post:
                    prompt += f" - {post['url']}"
        
        # Include other agents' insights if available
        if other_agents_results:
            prompt += "\n\nOther Analysis Results:"
            for agent_name, result in other_agents_results.items():
                if result and 'summary' in result:
                    prompt += f"\n- {agent_name}: {result['summary']}"
        
        prompt += """

Requirements:
1. Identify 3-5 distinct trends (not just topics)
2. Each trend should be significant and actionable
3. Explain why each trend matters
4. Provide evidence from the posts
5. Consider both technical and business implications

IMPORTANT: If you are satisfied with your previous results and don't need to make changes, respond with "SATISFIED" and explain why you're satisfied. Otherwise, provide your new analysis.

Format your response as:
SATISFACTION: [SATISFIED/NEEDS_IMPROVEMENT]
TREND 1: [Trend name or "NA" if satisfied]
DESCRIPTION: [What this trend is about or satisfaction reason]
EVIDENCE: [Posts that support this trend]
IMPACT: [Why this matters]

[Continue for 3-5 trends or explain satisfaction]

SUMMARY: [Overall trend summary in 2-3 sentences or satisfaction explanation]
"""
        
        return prompt
    
    def process_result(self, result: str) -> Dict[str, Any]:
        """处理趋势分析结果"""
        trends = []
        summary = ""
        satisfaction = ""
        agent_satisfied = False
        
        lines = result.strip().split('\n')
        current_trend = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('SATISFACTION:'):
                satisfaction = line.replace('SATISFACTION:', '').strip()
                agent_satisfied = satisfaction.upper() == 'SATISFIED'
            elif line.startswith('TREND'):
                if current_trend:
                    trends.append(current_trend)
                current_trend = {"name": line}
            elif line.startswith('DESCRIPTION:'):
                current_trend["description"] = line.replace('DESCRIPTION:', '').strip()
            elif line.startswith('EVIDENCE:'):
                current_trend["evidence"] = line.replace('EVIDENCE:', '').strip()
            elif line.startswith('IMPACT:'):
                current_trend["impact"] = line.replace('IMPACT:', '').strip()
            elif line.startswith('SUMMARY:'):
                summary = line.replace('SUMMARY:', '').strip()
        
        if current_trend:
            trends.append(current_trend)
        
        return {
            "satisfaction": satisfaction,
            "trends": trends,
            "summary": summary,
            "trend_count": len(trends),
            "agent_satisfied": agent_satisfied,
            "type": "trends_analysis"
        }
