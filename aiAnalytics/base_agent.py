"""
Base Agent Class for Multi-Agent System
多Agent系统的基础Agent类
"""

import os
import json
import openai
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class BaseAgent(ABC):
    """基础Agent类"""
    
    def __init__(self, name: str, role: str, max_iterations: int = 5):
        self.name = name
        self.role = role
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.results_history = []
        self.is_satisfied = False
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Clear proxy settings
        for key in list(os.environ.keys()):
            if 'proxy' in key.lower():
                del os.environ[key]
        
        self.client = openai.OpenAI(api_key=api_key)
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        pass
    
    @abstractmethod
    def get_task_prompt(self, posts_data: Dict[str, Any], other_agents_results: Dict[str, Any]) -> str:
        """获取任务提示词"""
        pass
    
    @abstractmethod
    def process_result(self, result: str) -> Dict[str, Any]:
        """处理AI返回的结果"""
        pass
    
    def execute(self, posts_data: Dict[str, Any], other_agents_results: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行Agent任务"""
        if other_agents_results is None:
            other_agents_results = {}
        
        self.current_iteration += 1
        
        # 构建动态提示词
        system_prompt = self.get_system_prompt()
        task_prompt = self.get_task_prompt(posts_data, other_agents_results)
        
        # 添加历史结果到提示词
        if self.results_history:
            history_context = "\n\nPrevious Results:\n"
            for i, result in enumerate(self.results_history, 1):
                history_context += f"Iteration {i}: {result.get('summary', '')}\n"
            task_prompt += history_context
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task_prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            ai_result = response.choices[0].message.content
            
            # 处理结果
            processed_result = self.process_result(ai_result)
            processed_result.update({
                "iteration": self.current_iteration,
                "timestamp": datetime.now().isoformat(),
                "agent_name": self.name,
                "raw_result": ai_result
            })
            
            # 保存到历史
            self.results_history.append(processed_result)
            
            # 检查是否满意
            self.is_satisfied = self._check_satisfaction(processed_result)
            
            return processed_result
            
        except Exception as e:
            return {
                "error": f"Agent {self.name} execution failed: {str(e)}",
                "iteration": self.current_iteration,
                "timestamp": datetime.now().isoformat(),
                "agent_name": self.name
            }
    
    def _check_satisfaction(self, result: Dict[str, Any]) -> bool:
        """检查Agent是否对当前结果满意"""
        # 如果达到最大迭代次数，强制满意
        if self.current_iteration >= self.max_iterations:
            return True
        
        # 检查Agent是否返回了"NA"（表示满意，不需要更新）
        if result.get('agent_satisfied', False):
            return True
        
        return False
    
    def get_latest_result(self) -> Optional[Dict[str, Any]]:
        """获取最新结果"""
        if self.results_history:
            return self.results_history[-1]
        return None
    
    def get_all_results(self) -> List[Dict[str, Any]]:
        """获取所有历史结果"""
        return self.results_history
    
    def reset(self):
        """重置Agent状态"""
        self.current_iteration = 0
        self.results_history = []
        self.is_satisfied = False
