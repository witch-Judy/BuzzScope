"""
Multi-Agent Scheduler
多Agent调度器 - 管理Agent并发执行和协作
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

from .agents.title_agent import TitleAgent
from .agents.trends_agent import TrendsAgent
from .agents.twitter_agent import TwitterAgent
from .agents.linkedin_agent import LinkedInAgent
from .agents.xiaohongshu_agent import XiaohongshuAgent

class AgentScheduler:
    """多Agent调度器"""
    
    def __init__(self):
        self.agents = {
            "title": TitleAgent(),
            "trends": TrendsAgent(),
            "twitter": TwitterAgent(),
            "linkedin": LinkedInAgent(),
            "xiaohongshu": XiaohongshuAgent()
        }
        
        self.execution_log = []
        self.results = {}
        self.is_running = False
        self.max_rounds = 5
        
        # 确保结果目录存在
        self.results_dir = "data/ai_analytics_results"
        os.makedirs(self.results_dir, exist_ok=True)
    
    def log_execution(self, message: str, agent_name: str = None, iteration: int = None):
        """记录执行日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "agent_name": agent_name,
            "iteration": iteration
        }
        self.execution_log.append(log_entry)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def execute_agents_round(self, posts_data: Dict[str, Any], round_number: int) -> Dict[str, Any]:
        """执行一轮Agent任务"""
        self.log_execution(f"Starting round {round_number}")
        
        round_results = {}
        
        # 并发执行所有Agent
        with ThreadPoolExecutor(max_workers=5) as executor:
            # 提交所有任务
            future_to_agent = {}
            for agent_name, agent in self.agents.items():
                if not agent.is_satisfied:
                    future = executor.submit(
                        agent.execute, 
                        posts_data, 
                        self.results
                    )
                    future_to_agent[future] = agent_name
            
            # 收集结果
            for future in as_completed(future_to_agent):
                agent_name = future_to_agent[future]
                try:
                    result = future.result()
                    round_results[agent_name] = result
                    self.log_execution(
                        f"Agent {agent_name} completed iteration {result.get('iteration', 0)}",
                        agent_name,
                        result.get('iteration', 0)
                    )
                except Exception as e:
                    self.log_execution(f"Agent {agent_name} failed: {str(e)}", agent_name)
                    round_results[agent_name] = {"error": str(e)}
        
        # 更新全局结果
        self.results.update(round_results)
        
        # 等待所有Agent完成并更新状态后，再检查满意度
        time.sleep(0.1)  # 短暂延迟确保状态更新完成
        
        # 检查是否所有Agent都满意
        all_satisfied = all(agent.is_satisfied for agent in self.agents.values())
        
        self.log_execution(f"Round {round_number} completed. All satisfied: {all_satisfied}")
        
        return {
            "round_number": round_number,
            "results": round_results,
            "all_satisfied": all_satisfied,
            "timestamp": datetime.now().isoformat()
        }
    
    def execute_multi_agent_analysis(self, posts_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行多Agent分析"""
        self.log_execution("Starting multi-agent analysis")
        self.is_running = True
        
        # 重置所有Agent
        for agent in self.agents.values():
            agent.reset()
        
        self.results = {}
        self.execution_log = []
        
        round_results = []
        
        try:
            for round_num in range(1, self.max_rounds + 1):
                round_result = self.execute_agents_round(posts_data, round_num)
                round_results.append(round_result)
                
                # 如果所有Agent都满意，提前结束
                if round_result["all_satisfied"]:
                    self.log_execution("All agents satisfied, ending early")
                    break
                
                # 短暂延迟，避免API限制
                time.sleep(2)
            
            # 保存结果
            final_results = self._compile_final_results(round_results)
            self._save_results(final_results, posts_data)
            
            self.log_execution("Multi-agent analysis completed successfully")
            return final_results
            
        except Exception as e:
            self.log_execution(f"Multi-agent analysis failed: {str(e)}")
            return {"error": str(e)}
        finally:
            self.is_running = False
    
    def _compile_final_results(self, round_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """编译最终结果"""
        final_results = {
            "analysis_metadata": {
                "total_rounds": len(round_results),
                "completed_at": datetime.now().isoformat(),
                "agents_used": list(self.agents.keys())
            },
            "agent_results": {},
            "execution_log": self.execution_log,
            "round_results": round_results
        }
        
        # 收集每个Agent的最终结果
        for agent_name, agent in self.agents.items():
            final_results["agent_results"][agent_name] = {
                "final_result": agent.get_latest_result(),
                "all_results": agent.get_all_results(),
                "iterations_completed": agent.current_iteration,
                "is_satisfied": agent.is_satisfied
            }
        
        return final_results
    
    def _save_results(self, results: Dict[str, Any], posts_data: Dict[str, Any]):
        """保存结果到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        keywords = "_".join(posts_data.get('keywords', ['unknown']))
        filename = f"multi_agent_analysis_{keywords}_{timestamp}.json"
        filepath = os.path.join(self.results_dir, filename)
        
        # 添加原始数据
        results["original_posts_data"] = posts_data
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            self.log_execution(f"Results saved to {filename}")
        except Exception as e:
            self.log_execution(f"Failed to save results: {str(e)}")
    
    def get_execution_status(self) -> Dict[str, Any]:
        """获取执行状态"""
        return {
            "is_running": self.is_running,
            "current_round": len([r for r in self.execution_log if "Starting round" in r.get("message", "")]),
            "agents_status": {
                name: {
                    "iterations": agent.current_iteration,
                    "is_satisfied": agent.is_satisfied,
                    "has_results": len(agent.results_history) > 0
                }
                for name, agent in self.agents.items()
            },
            "latest_logs": self.execution_log[-10:] if self.execution_log else []
        }
    
    def get_latest_results(self) -> Optional[Dict[str, Any]]:
        """获取最新结果"""
        if not self.results:
            return None
        
        return {
            "agent_results": {
                name: agent.get_latest_result()
                for name, agent in self.agents.items()
                if agent.get_latest_result()
            },
            "timestamp": datetime.now().isoformat()
        }
