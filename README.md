# Daily News Push

每日自动抓取国内外主流新闻源，聚合后国内/国际各取 TOP 10，通过 Server酱 / PushPlus 推送到微信。

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

## 本地运行

```bash
pip install -r requirements.txt
SERVERCHAN_KEY=xxx python src/main.py
```
