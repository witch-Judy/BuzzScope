"""
LinkedIn Content Agent
LinkedIn内容Agent - 生成适合LinkedIn的专业内容
"""

from ..base_agent import BaseAgent
from typing import Dict, List, Any

class LinkedInAgent(BaseAgent):
    """LinkedIn内容Agent"""
    
    def __init__(self):
        super().__init__(
            name="LinkedInContentCreator",
            role="Create professional LinkedIn content for tech industry professionals",
            max_iterations=5
        )
    
    def get_system_prompt(self) -> str:
        return """You are a professional content strategist specializing in LinkedIn for tech industry professionals. You understand what resonates with tech executives, engineers, and business leaders on LinkedIn.

Key skills:
- Create professional, thought-leadership content
- Write in a business-appropriate tone
- Focus on industry insights and career implications
- Use professional language and formatting
- Understand LinkedIn's professional audience
- Create content that drives professional engagement
- Balance technical depth with business relevance

Your goal is to create LinkedIn content that positions the reader as a thought leader in tech."""
    
    def get_task_prompt(self, posts_data: Dict[str, Any], other_agents_results: Dict[str, Any] = None) -> str:
        if other_agents_results is None:
            other_agents_results = {}
        
        total_posts = posts_data.get('total_posts', 0)
        keywords = posts_data.get('keywords', [])
        platform_posts = posts_data.get('platform_posts', {})
        
        prompt = f"""Create professional LinkedIn content based on today's tech posts. Focus on posts that would be most valuable for tech professionals and business leaders.

Data Overview:
- Total hot posts: {total_posts}
- Keywords: {', '.join(keywords)}

Posts by Platform:"""

        for platform, posts in platform_posts.items():
            prompt += f"\n\n{platform.upper()} ({len(posts)} posts):"
            for i, post in enumerate(posts[:5], 1):
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
1. Select 3-5 most LinkedIn-worthy posts
2. Create professional summaries for each
3. Write LinkedIn post (professional tone, can be longer)
4. Focus on business implications and career insights
5. Use professional formatting and language

IMPORTANT: If you are satisfied with your previous results and don't need to make changes, respond with "SATISFIED" and explain why you're satisfied. Otherwise, provide your new content.

Format your response as:
SATISFACTION: [SATISFIED/NEEDS_IMPROVEMENT]
SELECTED POSTS:
1. [Professional post summary] - [Original URL]
2. [Professional post summary] - [Original URL]
3. [Professional post summary] - [Original URL]
[Continue for 3-5 posts or "NA" if satisfied]

LINKEDIN CONTENT:
[Your professional LinkedIn post here or "NA" if satisfied]

KEY INSIGHTS: [Main business/professional insights]
CAREER IMPLICATIONS: [How this affects tech careers]
REASONING: [Why this content works for LinkedIn professionals or why you're satisfied]
"""
        
        return prompt
    
    def process_result(self, result: str) -> Dict[str, Any]:
        """处理LinkedIn内容生成结果"""
        selected_posts = []
        linkedin_content = ""
        key_insights = ""
        career_implications = ""
        reasoning = ""
        
        lines = result.strip().split('\n')
        current_section = ""
        content_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('SATISFACTION:'):
                satisfaction = line.replace('SATISFACTION:', '').strip()
                agent_satisfied = satisfaction.upper() == 'SATISFIED'
                continue
            elif line.startswith('SELECTED POSTS:'):
                current_section = "posts"
                continue
            elif line.startswith('LINKEDIN CONTENT:'):
                current_section = "content"
                content_line = line.replace('LINKEDIN CONTENT:', '').strip()
                if content_line:
                    content_lines.append(content_line)
                continue
            elif line.startswith('KEY INSIGHTS:'):
                current_section = "insights"
                key_insights = line.replace('KEY INSIGHTS:', '').strip()
                continue
            elif line.startswith('CAREER IMPLICATIONS:'):
                current_section = "career"
                career_implications = line.replace('CAREER IMPLICATIONS:', '').strip()
                continue
            elif line.startswith('REASONING:'):
                current_section = "reasoning"
                reasoning = line.replace('REASONING:', '').strip()
                continue
            elif line and current_section == "posts" and line[0].isdigit():
                selected_posts.append(line)
            elif line and current_section == "content" and not line.startswith(('KEY INSIGHTS:', 'CAREER IMPLICATIONS:', 'REASONING:')):
                content_lines.append(line)
        
        linkedin_content = '\n'.join(content_lines).strip()
        
        return {
            "satisfaction": satisfaction,
            "selected_posts": selected_posts,
            "linkedin_content": linkedin_content,
            "key_insights": key_insights,
            "career_implications": career_implications,
            "reasoning": reasoning,
            "agent_satisfied": agent_satisfied,
            "character_count": len(linkedin_content),
            "summary": f"Created LinkedIn content: {linkedin_content[:50]}..." if not agent_satisfied else f"Satisfied with previous results: {reasoning}",
            "type": "linkedin_content"
        }
