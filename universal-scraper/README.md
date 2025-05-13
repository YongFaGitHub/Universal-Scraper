# Universal Scraper | 通用网页爬虫框架

一个功能强大、高度可配置的网页数据采集和 AI 分析框架，专为研究和数据分析项目设计。

## 功能特点

- 🔍 **高度可配置** - 通过 YAML 配置文件轻松定义爬取目标和规则，无需编写代码
- 🤖 **AI 驱动分析** - 使用 LLM 模型（Gemini 或 OpenAI）自动分析和结构化网页数据
- 📊 **结构化输出** - 支持多种输出格式（JSON, CSV, TSV 等）
- 🔄 **自动化工作流** - 集成 GitHub Actions，实现定时爬取和分析
- 📱 **多渠道通知** - 支持钉钉、飞书、企业微信等通知渠道
- 🛡️ **稳定可靠** - 内置错误处理和重试机制，确保数据采集可靠性
- 🌐 **多引擎支持** - 支持常规 HTTP 请求、Playwright 和 Firecrawl 等多种爬取引擎
- 🚀 **页面交互支持** - 支持页面点击、滚动、表单填写等交互操作获取动态内容

## 项目结构

```
universal-scraper/
├── config/                   # 配置文件目录
│   ├── sites/                # 站点配置文件
│   │   ├── example.yaml      # 示例站点配置
│   │   ├── firecrawl_example.yaml # Firecrawl示例配置
│   │   ├── heimao.yaml       # 黑猫投诉站点配置
│   │   └── ...
│   ├── analysis/             # AI分析配置
│   │   ├── prompts/          # 分析提示词模板
│   │   │   ├── general_prompt.txt    # 通用提示词
│   │   │   ├── heimao_prompt.txt     # 黑猫投诉分析提示词
│   │   │   └── ...
│   ├── workflow/             # 工作流模板
│   │   ├── crawler.yml.template     # 爬虫工作流模板
│   │   ├── analyzer.yml.template    # 分析工作流模板
│   │   └── ...
│   └── settings.yaml         # 全局设置
├── scripts/                  # 脚本目录
│   ├── scraper.py            # 爬虫脚本
│   ├── ai_analyzer.py        # AI分析脚本
│   ├── notify.py             # 通知脚本
│   ├── playwright_test.py    # Playwright测试脚本
│   └── workflow_generator.py # 工作流生成器
├── .github/                  # GitHub相关文件
│   └── workflows/            # GitHub Actions工作流
│       ├── heimao_crawler.yml # 黑猫投诉爬虫工作流
│       └── ...
├── data/                     # 数据存储目录
│   └── daily/                # 按日期存储的数据
├── analysis/                 # 分析结果目录
│   └── daily/                # 按日期存储的分析结果
├── docs/                     # 文档目录
│   ├── firecrawl_usage.md    # Firecrawl使用文档
│   ├── heimao_usage.md       # 黑猫投诉使用文档
│   └── ...                   # 其他文档
├── status/                   # 状态文件目录
├── src/                      # 源代码目录
│   ├── scrapers/             # 爬虫实现
│   │   ├── firecrawl_integration.py  # Firecrawl集成
│   │   ├── heimao_scraper.py         # 黑猫投诉爬虫
│   │   └── ...
│   ├── analyzers/            # 分析器实现
│   ├── parsers/              # 解析器实现
│   ├── notifiers/            # 通知器实现
│   ├── storage/              # 存储实现
│   └── utils/                # 工具函数
├── requirements.txt          # 项目依赖
└── README.md                 # 项目说明
```

## 快速开始

### 安装

1. 克隆仓库

   ```bash
   git clone https://github.com/yourusername/universal-scraper.git
   cd universal-scraper
   ```

2. 安装依赖

   ```bash
   pip install -r requirements.txt
   ```

3. 安装 Playwright 浏览器

   ```bash
   playwright install --with-deps
   ```

4. 设置环境变量
   ```bash
   # 根据您使用的AI提供商设置API密钥
   export OPENAI_API_KEY=your_openai_api_key
   # 或
   export GEMINI_API_KEY=your_gemini_api_key
   # Firecrawl API密钥（如果使用Firecrawl）
   export FIRECRAWL_API_KEY=your_firecrawl_api_key
   ```

### 创建站点配置

1. 在`config/sites/`目录下创建新的 YAML 配置文件（例如`mysite.yaml`）
2. 参考`example.yaml`模板填写配置

### 运行爬虫

```bash
python scripts/scraper.py --site mysite
```

### 使用 Firecrawl 增强版爬虫

```bash
python src/scrapers/firecrawl_integration.py --site firecrawl_example --extract
```

### 运行 AI 分析

```bash
python scripts/ai_analyzer.py --file data/daily/2023-01-01/mysite_data.json --site mysite
```

### 生成工作流

```bash
python scripts/workflow_generator.py --site mysite
```

### 运行 Playwright 测试

```bash
# 运行单个浏览器测试
python scripts/playwright_test.py --browser chromium

# 运行所有浏览器测试
python scripts/playwright_test.py --browser all
```

## 配置说明

### 站点配置

站点配置文件（`config/sites/mysite.yaml`）包含爬取特定网站所需的所有参数：

```yaml
site_info:
  name: "网站名称"
  base_url: "https://example.com"
  description: "网站描述"

scraping:
  targets:
    - url: "/path"
      method: "GET"
  schedule: "0 0 * * *" # 每天午夜执行

parsing:
  selector_type: "css" # 或 "xpath"
  field_selectors:
    title: "h1.title"
    content: "div.content"
    date: "span.date"

output:
  format: "json" # 或 "csv", "tsv"
  filename: "mysite_data.json"
```

### 全局设置

全局设置文件（`config/settings.yaml`）配置框架的整体行为：

```yaml
# 一般设置
default_site: "example"
run_mode: "local" # 本地运行或GitHub Actions
data_dir: "data"
analysis_dir: "analysis"
status_dir: "status"

# AI分析设置
ai_analysis:
  provider: "gemini" # 或 "openai"
  api_key_env: "GEMINI_API_KEY"
  output_format: "tsv"
```

## 高级使用

### 使用 Firecrawl 增强爬取能力

本框架集成了 Firecrawl，这是一个强大的爬虫工具，特别适合处理复杂的、JavaScript 渲染的网站。

1. 配置 Firecrawl

   在站点配置中添加 Firecrawl 特定配置：

   ```yaml
   scraping:
     engine: "firecrawl" # 使用Firecrawl引擎
     firecrawl_options: # Firecrawl特定选项
       formats: ["markdown", "html", "json", "screenshot"]
       onlyMainContent: true # 只提取主要内容
       enableWebSearch: true # 启用Web搜索增强提取
       # 页面交互操作
       actions:
         - { type: "wait", milliseconds: 2000 } # 等待2秒
         - { type: "click", selector: "button.show-more" } # 点击按钮
         - { type: "screenshot" } # 截图
     extract_prompt: "提取API名称、描述和参数" # 提取提示词
   ```

2. 运行 Firecrawl 爬虫

   ```bash
   python src/scrapers/firecrawl_integration.py --site firecrawl_example --extract
   ```

详细使用说明请参考[Firecrawl 使用指南](docs/firecrawl_usage.md)。

### 自定义分析提示词

1. 在`config/analysis/prompts/`目录下创建新的提示词文件
2. 文件名应为`{site_id}_prompt.txt`格式

### 使用 GitHub Actions 自动化

1. 生成工作流文件

   ```bash
   python scripts/workflow_generator.py --all
   ```

2. 在 GitHub 仓库设置中添加密钥:

   - `OPENAI_API_KEY` 或 `GEMINI_API_KEY`
   - `FIRECRAWL_API_KEY`（如果使用 Firecrawl）

3. 推送代码到 GitHub，工作流将按照配置的计划自动运行

### 使用 Playwright 进行自动化测试

本项目集成了 Playwright 进行浏览器自动化测试，支持在 GitHub Actions 中运行。

1. 安装 Playwright 浏览器

   ```bash
   playwright install --with-deps
   ```

2. 运行测试脚本

   ```bash
   python scripts/playwright_test.py --browser chromium
   ```

3. 查看测试报告

   测试报告将生成在 `playwright-report` 目录下，包括截图和 HTML 报告文件。

4. GitHub Actions 自动化测试

   项目在 GitHub Actions 中使用矩阵策略，自动在多种浏览器上运行测试。
   可以在 Actions 标签页中查看测试结果和下载测试报告。

### 黑猫投诉数据采集

本框架集成了黑猫投诉数据采集功能，可以自动获取黑猫投诉平台上的投诉信息。

1. 配置黑猫投诉爬虫

   ```yaml
   site_info:
     name: "黑猫投诉"
     base_url: "https://tousu.sina.com.cn"
     description: "黑猫投诉数据采集"

   scraping:
     engine: "custom" # 使用自定义引擎
     targets:
       - type: "latest" # 最新投诉列表
       - type: "keyword" # 关键词搜索
         keywords: ["${HEIMAO_KEYWORDS}"] # 从环境变量获取关键词
   ```

2. 设置必要的环境变量

   ```bash
   export HEIMAO_COOKIE="your_cookie_here"  # 获取Cookie方法见文档
   export HEIMAO_KEYWORDS="关键词1,关键词2"
   ```

3. 运行黑猫投诉爬虫

   ```bash
   python scripts/scraper.py --site heimao
   ```

4. 使用 GitHub Actions 自动化

   在仓库的 Secrets 中添加必要的环境变量，GitHub Actions 将按计划自动运行爬虫并分析数据。

详细使用说明请参考[黑猫投诉使用指南](docs/heimao_usage.md)。

## 贡献

欢迎提交问题和贡献代码!

## 许可证

MIT License
