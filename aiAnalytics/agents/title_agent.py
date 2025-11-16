"""
Title Generation Agent
标题生成Agent - 生成吸引人且信息量丰富的标题
"""

from ..base_agent import BaseAgent
from typing import Dict, List, Any

class TitleAgent(BaseAgent):
    """标题生成Agent"""
    
    def __init__(self):
        super().__init__(
            name="TitleGenerator",
            role="Generate compelling and informative titles for daily tech news",
            max_iterations=5
        )
    
    def get_system_prompt(self) -> str:
        return """You are a professional tech news editor and headline writer. Your expertise lies in creating compelling, informative, and engaging titles that capture attention while accurately representing the content.

Key skills:
- Create headlines that are both click-worthy and informative
- Balance between being catchy and being accurate
- Use power words and emotional triggers appropriately
- Keep titles concise but impactful
- Understand what makes tech news titles viral and shareable

Your goal is to create the perfect headline that will make people want to read and share the content."""
    
    def get_task_prompt(self, posts_data: Dict[str, Any], other_agents_results: Dict[str, Any] = None) -> str:
        if other_agents_results is None:
            other_agents_results = {}
        
        total_posts = posts_data.get('total_posts', 0)
        keywords = posts_data.get('keywords', [])
        platform_posts = posts_data.get('platform_posts', {})
        
        prompt = f"""Based on today's tech news data, create a compelling headline that captures the essence of the most important developments.

Data Overview:
- Total hot posts: {total_posts}
- Keywords: {', '.join(keywords)}

Top Posts by Platform:"""

        for platform, posts in platform_posts.items():
            prompt += f"\n\n{platform.upper()} ({len(posts)} posts):"
            for i, post in enumerate(posts[:3], 1):  # Top 3 from each platform
                prompt += f"\n{i}. {post['title']} (Heat: {post['heat_score']:.1f})"
        
        # Include other agents' insights if available
        if other_agents_results:
            prompt += "\n\nOther Analysis Results:"
            for agent_name, result in other_agents_results.items():
                if result and 'summary' in result:
                    prompt += f"\n- {agent_name}: {result['summary']}"
        
        prompt += """

Requirements:
1. Create a headline that is 8-15 words long
2. Make it attention-grabbing but accurate
3. Include the most important keyword or trend
4. Use action words and emotional appeal
5. Make it suitable for social media sharing

IMPORTANT: If you are satisfied with your previous results and don't need to make changes, respond with "NA" and explain why you're satisfied. Otherwise, provide your new headline.

Format your response as:
SATISFACTION: [SATISFIED/NEEDS_IMPROVEMENT]
HEADLINE: [Your headline here or "NA" if satisfied]
REASONING: [Brief explanation of why this headline works or why you're satisfied]
KEYWORDS: [Main keywords/topics covered]
"""
        
        return prompt
    
    def process_result(self, result: str) -> Dict[str, Any]:
        """处理标题生成结果"""
        lines = result.strip().split('\n')
        satisfaction = ""
        headline = ""
        reasoning = ""
        keywords = ""
        agent_satisfied = False
        
        for line in lines:
            if line.startswith('SATISFACTION:'):
                satisfaction = line.replace('SATISFACTION:', '').strip()
                agent_satisfied = satisfaction.upper() == 'SATISFIED'
            elif line.startswith('HEADLINE:'):
                headline = line.replace('HEADLINE:', '').strip()
            elif line.startswith('REASONING:'):
                reasoning = line.replace('REASONING:', '').strip()
            elif line.startswith('KEYWORDS:'):
                keywords = line.replace('KEYWORDS:', '').strip()
        
        return {
            "satisfaction": satisfaction,
            "headline": headline,
            "reasoning": reasoning,
            "keywords": keywords,
            "agent_satisfied": agent_satisfied,
            "summary": f"Generated headline: {headline}" if not agent_satisfied else f"Satisfied with previous results: {reasoning}",
            "type": "title_generation"
        }
