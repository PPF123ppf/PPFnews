# Daily News Push — 每日国内外十大消息推送

## 概述

每日自动抓取国内外主流新闻源，聚合后取国内/国际各 TOP 10，通过 Server酱 / PushPlus 推送到微信。

## 推送方式

- **Server酱 / PushPlus**：用户配置其一即可。通过第三方 API 绑定个人微信，实现消息推送。
- **定时触发**：GitHub Actions 每天早上 8:00（北京时间）自动运行。

## 技术栈

- Python 3.11+
- GitHub Actions（定时调度）
- requests + BeautifulSoup（爬虫）
- feedparser（RSS 解析）

## 数据模型

```python
@dataclass
class NewsItem:
    title: str          # 标题
    source: str         # 来源名称（如"新华社"）
    url: str            # 链接
    summary: str        # 摘要（自动截取前 100 字）
    category: str       # "domestic" | "international"
    hot_score: int      # 热度分（排序用）
```

## 新闻来源

### 国内
| 来源 | 方式 | 说明 |
|------|------|------|
| 百度热搜 | 爬虫 | 百度首页热搜榜 |
| 微博热搜 | 爬虫/API | 微博热搜榜 |
| 新华社 | RSS | 新华网 RSS feed |
| 央视新闻 | RSS | 央视网 RSS feed |
| 腾讯新闻 | 爬虫 | 腾讯新闻热点 |
| 新浪新闻 | 爬虫 | 新浪新闻头条 |

### 国际
| 来源 | 方式 | 说明 |
|------|------|------|
| Reuters | RSS | 路透社 RSS |
| BBC | RSS | BBC News RSS |
| CNN | RSS | CNN Top Stories RSS |
| AP | RSS | Associated Press RSS |
| 环球网 | 爬虫 | 环球网国际新闻 |

## 项目结构

```
daily-news/
├── .github/workflows/daily.yml     # GitHub Actions 配置
├── src/
│   ├── __init__.py
│   ├── main.py                     # 入口：抓取→聚合→排序→推送
│   ├── config.py                   # 配置（API Keys、URL 等）
│   ├── models.py                   # NewsItem 数据类
│   ├── collectors/                 # 各来源采集器
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseCollector 抽象基类
│   │   ├── baidu.py
│   │   ├── weibo.py
│   │   ├── xinhua.py
│   │   ├── cctv.py
│   │   ├── tencent.py
│   │   ├── sina.py
│   │   ├── reuters.py
│   │   ├── bbc.py
│   │   ├── cnn.py
│   │   ├── ap.py
│   │   └── global_times.py
│   └── pusher.py                   # Server酱 / PushPlus 推送
├── requirements.txt
└── README.md
```

## 数据流

```
各采集器 fetch() → NewsItem 列表
         ↓
聚合去重（按标题相似度）
         ↓
国内按热度分排序取 TOP 10
国际按热度分排序取 TOP 10
         ↓
格式化为 Markdown 消息模板
         ↓
Server酱 / PushPlus API → 微信推送
```

## 错误处理

- 每个采集器独立 try/except，单个源失败不影响其他源
- 推送失败重试 2 次
- GitHub Actions 运行失败会发邮件通知（GitHub 内置功能）

## 配置项

（通过 GitHub Actions Secrets 或环境变量传入）

```
SERVERCHAN_KEY=xxx        # Server酱 SendKey（可选）
PUSHPLUS_TOKEN=xxx        # PushPlus Token（可选）
# 至少配置一个
```
