# 📧 快速邮件设置指南

## 🎯 目标
设置Gmail邮件通知，当检测到热门帖子时自动发送邮件到你的邮箱

## 📋 步骤

### 1. 获取Gmail应用密码

1. **访问Google账户安全设置**：
   - 打开 [Google账户安全](https://myaccount.google.com/security)
   - 登录你的Gmail账户

2. **启用两步验证**（如果还没启用）：
   - 点击"两步验证"
   - 按照提示完成设置

3. **生成应用密码**：
   - 在安全设置中找到"应用密码"
   - 选择"邮件" → "其他（自定义名称）"
   - 输入名称：`BuzzScope Monitor`
   - 点击"生成"
   - **复制16位密码**（格式：`abcd efgh ijkl mnop`）

### 2. 配置环境变量

创建或编辑 `.env` 文件，添加以下内容：

```env
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_16_digit_app_password
FROM_EMAIL=your_email@gmail.com
TO_EMAIL=your_notification_email@gmail.com
```

**重要**：将 `你的16位应用密码` 替换为步骤1中生成的实际密码。

### 3. 测试邮件功能

运行测试脚本：

```bash
python test_email_notification.py
```

如果成功，你会收到一封测试邮件。

### 4. 运行监控系统

#### 测试一次监控：
```bash
python monitor_hot_posts.py once
```

#### 持续监控（每30分钟）：
```bash
python monitor_hot_posts.py continuous --interval 30
```

## 🔧 故障排除

### 常见问题

1. **"Authentication failed"错误**：
   - 检查应用密码是否正确
   - 确保使用应用密码，不是常规密码

2. **"Connection refused"错误**：
   - 检查网络连接
   - 确认SMTP设置正确

3. **"Permission denied"错误**：
   - 确保已启用两步验证
   - 重新生成应用密码

### 验证设置

运行以下命令检查配置：

```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Email config check:')
print(f'Username: {os.getenv(\"EMAIL_USERNAME\")}')
print(f'Password: {\"*\" * len(os.getenv(\"EMAIL_PASSWORD\", \"\"))}')
print(f'From: {os.getenv(\"FROM_EMAIL\")}')
print(f'To: {os.getenv(\"TO_EMAIL\")}')
"
```

## 📱 邮件示例

成功设置后，你会收到类似这样的邮件：

```
主题: 🔥 3 Hot Posts Detected!

内容:
- Hacker News: AI Breakthrough in Machine Learning (Score: 150, Comments: 75)
- Reddit: IoT Security Best Practices (Score: 500, Comments: 120)  
- YouTube: MQTT Protocol Tutorial (Views: 10000, Likes: 1000)
```

## ⚡ 快速命令

```bash
# 测试邮件
python test_email_notification.py

# 运行一次监控
python monitor_hot_posts.py once

# 持续监控
python monitor_hot_posts.py continuous --interval 30

# 停止监控
Ctrl+C
```

## 🆘 需要帮助？

如果遇到问题：
1. 检查 `.env` 文件配置
2. 验证Gmail应用密码
3. 运行测试脚本查看错误信息
4. 检查网络连接和防火墙设置


