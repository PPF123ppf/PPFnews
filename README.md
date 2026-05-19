# Daily News Push

每日自动抓取国内外主流新闻源，聚合后国内/国际各取 TOP 10，通过 Server酱 / PushPlus 推送到微信。推送内容包含标题、中文概括、相关图片和来源链接，不再只发送链接列表。

## 新闻来源

### 国内
| 来源 | 方式 |
|------|------|
| 百度热搜 | HTML 爬取 |
| 微博热搜 | JSON API |
| 新华社 | RSS |
| 央视新闻 | RSS |
| 腾讯新闻 | HTML 爬取 |
| 新浪新闻 | HTML 爬取 |

### 国际
| 来源 | 方式 |
|------|------|
| Reuters | RSS |
| BBC | RSS |
| CNN | RSS |
| AP | RSS |
| 环球网 | RSS |

## 使用方式

### 1. Fork 本仓库

### 2. 配置推送渠道（至少一个）

**Server酱：** 在 https://sct.ftqq.com 获取 SendKey
**PushPlus：** 在 https://www.pushplus.plus 获取 Token

### 3. 配置 GitHub Secrets

在仓库 Settings → Secrets and variables → Actions 中添加：

| Name | Value |
|------|-------|
| `SERVERCHAN_KEY` | Server酱 SendKey |
| `PUSHPLUS_TOKEN` | PushPlus Token |

### 4. 启用 Actions

GitHub Actions 默认启用，每天 UTC 00:00（北京时间 08:00）自动运行。

也可以手动触发：Actions → Daily News Push → Run workflow

## 推送内容

每条新闻会尽量输出：

- 标题和来源
- 更完整的中文内容概括（国际新闻会先翻译成中文；正文过短时会补充来源、热度和后续关注点）
- 相关图片（优先来自 RSS 媒体字段、新闻正文 `og:image` / `twitter:image` 等元数据；GitHub Actions 运行时会缓存为 GitHub Raw 图片链接）
- 原文链接

如果某条新闻源没有提供可靠图片，会明确标注“未获取到可可靠引用的相关图片”。

国内新闻会按来源做均衡筛选，避免百度热搜、微博热搜等单一平台因为原始热度分数口径更大而垄断 TOP 10。

在 GitHub Actions 中运行时，程序会把推送用图片缓存到仓库 `assets/news/日期/`，并优先使用 GitHub Raw 图片链接推送，减少国外媒体图片防盗链导致的微信端不显示问题。

RSS 类来源会过滤 48 小时以前的旧闻；Google News 来源使用 `site:` 和 `when:2d` 限定，减少错源、旧闻和英文国内新闻混入。

## 本地运行

```bash
pip install -r requirements.txt
SERVERCHAN_KEY=xxx python src/main.py
```
