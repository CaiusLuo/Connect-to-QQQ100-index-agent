# 更新日志 (Changelog)

## [0.1.0] - 2024-12-21

### ✨ 新增功能

- 🤖 实现基于 CrewAI 的三 Agent 协作系统
  - Market Analyst: 获取 QQQ 实时数据
  - News Researcher: 搜索纳斯达克相关英文新闻
  - Content Creator: 撰写中文盘后总结报告
- 🌐 FastAPI HTTP API 支持
  - POST /invoke: 触发分析任务（SSE 流式输出）
  - POST /webhook: Telegram Bot Webhook
  - GET /health: 健康检查
- 📱 Telegram Bot 集成
  - /start_summary 命令触发分析
  - 实时进度更新
  - 自动推送分析报告
- 🔧 工具集成
  - yfinance: 获取 QQQ ETF 实时行情
  - Tavily: 搜索英文财经新闻（Reuters, Bloomberg, CNBC, WSJ）

### 🐛 Bug 修复

- ✅ 修复任务 Context 传递问题
  - 使用同一个 Task 实例建立依赖关系
  - 确保 Task 3 能正确接收 Task 1 和 Task 2 的输出
- ✅ 修复 Agent Memory 污染问题
  - 禁用 news_researcher 和 content_creator 的 memory 功能
  - 避免历史对话影响当前分析
- ✅ 修复 Windows 平台兼容性问题
  - 添加信号兼容性修复代码
  - 解决 `AttributeError: module 'signal' has no attribute 'SIGHUP'`
- ✅ 修复搜索结果不准确问题
  - 强制使用英文关键词搜索
  - 明确禁止搜索中国 A 股市场
  - 限制搜索域名为英文财经媒体

### 🔧 优化改进

- 📝 强化任务描述
  - 明确要求使用前置任务的输出
  - 要求输出包含具体数字
  - 禁止使用模糊描述
- 🎯 优化 Agent 配置
  - 明确 Agent 只关注美国市场
  - 添加 CRITICAL 警告防止偏离主题
  - 提供具体的搜索关键词示例
- 📊 改进输出格式
  - 结构化的中文报告
  - 包含核心数据、市场驱动力分析、操盘建议
  - 适合 Telegram 推送的 Markdown 格式

### 📚 文档更新

- 📖 完善 README.md
  - 添加详细的工作流程图
  - 补充 API 使用指南
  - 添加项目结构说明
  - 更新开发计划
  - 添加故障排除指南
- 📋 更新 example.env
  - 添加所有必需的环境变量
  - 提供详细的配置说明
- 🧪 添加测试脚本
  - test_stream.py: 测试流式输出
  - test_context.py: 测试任务依赖传递

### 🛠️ 技术栈

- Python 3.11+
- CrewAI 1.7.0+
- FastAPI 0.124.4+
- yfinance 0.2.66+
- Tavily 0.7.17+
- uv (包管理器)

---

## 未来计划

### v0.2.0 (计划中)

- [ ] 添加定时任务支持（每日自动分析）
- [ ] 支持更多指数（SPY, DIA, IWM）
- [ ] 添加历史数据分析
- [ ] 优化报告格式和可视化

### v0.3.0 (计划中)

- [ ] 添加用户偏好设置
- [ ] 支持多语言输出
- [ ] 添加技术指标分析
- [ ] 集成更多数据源

---

**注**: 本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范。
