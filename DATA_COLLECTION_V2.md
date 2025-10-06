# Data Collection V2 - Architecture Overview

## 🏗️ **重构后的数据收集架构**

### **📊 两大收集策略**：

#### **1. 历史数据收集 (Historical Data Collection)**
- **用途**: 声量统计、趋势分析
- **数据源策略**:
  - **Hacker News**: 使用已有历史数据文件
  - **Discord**: 使用已有历史数据文件
  - **Reddit**: 实时搜索 `time=all` 前100个帖子
  - **YouTube**: 实时搜索前100个视频

#### **2. 实时数据收集 (Real-time Data Collection)**
- **用途**: 事件驱动通知
- **数据源**: 当日热门内容
- **平台**: Hacker News, Reddit, YouTube

### **💾 缓存机制**：

#### **智能缓存策略**：
- **检查缓存**: 先检查是否有缓存数据
- **使用缓存**: 有缓存则直接使用，显示"💾 Using cached data"
- **重新收集**: 无缓存或强制刷新时重新收集
- **保存缓存**: 收集后自动保存到缓存

#### **缓存文件结构**：
```
data/cache/
├── hackernews/
│   ├── unified_namespace.json
│   ├── ai.json
│   └── iot.json
├── reddit/
├── youtube/
└── discord/
```

### **🔧 核心服务**：

#### **1. DataCollectionServiceV2**
- **功能**: 历史数据收集和缓存管理
- **特性**: 智能缓存、平台特定策略、错误处理

#### **2. RealtimeCollectionService**
- **功能**: 实时热门内容收集
- **特性**: 多平台同步、关键词搜索、数据持久化

#### **3. EventDrivenService**
- **功能**: 事件驱动通知
- **特性**: MQTT发布、邮件通知、持续监控

### **🚀 使用方法**：

#### **历史数据收集**：
```bash
# 收集单个关键词
python3 collect_keyword_data.py "unified namespace" --exact-match

# 收集多个关键词
python3 collect_multiple_keywords.py "ai" "iot" "mqtt" --exact-match

# 查看缓存统计
python3 collect_keyword_data.py "test" --stats

# 强制刷新缓存
python3 collect_keyword_data.py "ai" --force-refresh
```

#### **实时监控**：
```bash
# 单次监控
python3 monitor_keywords.py "ai" --once

# 持续监控
python3 monitor_keywords.py "ai" --interval 6

# 查看MQTT消息
python3 mqtt_monitor.py
```

### **📈 收集结果示例**：

#### **成功收集**：
```
📈 Collection Results:
------------------------------

📱 HACKERNEWS:
  ✅ Status: success
  📊 Total posts: 0
  📁 Data source: historical

📱 REDDIT:
  ✅ Status: success
  📊 Total posts: 120
  📁 Data source: time_all

📱 YOUTUBE:
  ✅ Status: success
  📊 Total posts: 0
  📁 Data source: time_all

📱 DISCORD:
  ✅ Status: success
  📊 Total posts: 277
  📁 Data source: historical

📊 Summary:
  Total posts found: 397
  Successful platforms: 4/4
```

#### **使用缓存**：
```
📱 HACKERNEWS:
  💾 Using cached data
  📊 Total posts: 0
  📁 Data source: historical
```

### **🔍 关键词匹配**：

#### **精确匹配 (exact_match=True)**：
- 使用正则表达式 `\bkeyword\b`
- 确保关键词作为完整短语出现
- 适用于"unified namespace"等复合术语

#### **模糊匹配 (exact_match=False)**：
- 使用简单的子字符串搜索
- 关键词可以是单词的一部分
- 适用于"ai"等简单术语

### **📊 数据统计**：

#### **收集统计**：
- 总缓存关键词数量
- 各平台缓存文件数量
- 最新收集时间
- 数据源类型

#### **实时统计**：
- 热门内容收集次数
- 各平台帖子数量
- 最新帖子时间
- 关键词提及次数

### **🛠️ 错误处理**：

#### **API错误**：
- YouTube API key无效 → 继续其他平台收集
- Reddit API限制 → 记录错误并继续
- 网络超时 → 自动重试

#### **文件错误**：
- 编码问题 → 跳过问题文件
- 权限问题 → 记录错误
- 磁盘空间 → 清理旧文件

### **⚡ 性能优化**：

#### **缓存策略**：
- 避免重复API调用
- 减少网络请求
- 提高响应速度

#### **并发处理**：
- 多平台并行收集
- 异步数据处理
- 批量操作优化

### **🔒 数据安全**：

#### **API密钥管理**：
- 环境变量存储
- 密钥轮换支持
- 错误日志脱敏

#### **数据持久化**：
- JSON格式存储
- 备份和恢复
- 版本控制支持

## 🎯 **总结**

新的数据收集架构实现了：

1. **智能缓存**: 避免重复收集，提高效率
2. **平台特定策略**: 历史数据 vs 实时搜索
3. **错误容错**: 单个平台失败不影响整体
4. **灵活配置**: 支持精确匹配和模糊匹配
5. **实时监控**: 事件驱动的关键词监控
6. **MQTT集成**: 实时通知和系统集成

这个架构完美支持了你的需求：**历史数据分析** + **实时事件通知**！
