# 小K万能工作台 · XiaoK Workbench

> 面向**云贵川桂**的求职 / 备考 / 计划打卡一体化 AI 工作台。**本地优先、隐私自托管、公开可用**。
> 一套工作台同时备战四大赛道：`找工作（求职）` · `考公考编` · `中药士 / 资格考试` · `考研`，并内置通用「计划打卡」模块。

---

## 一、项目简介

小K万能工作台把分散的招聘平台、人事考试网、备考节点、热门行业信息聚合到一处，帮你：

- 上传简历 → 自动解析专业 / 技能 / 学历
- 关联 **18 个平台**，按**你自己的专业 / 技能**一键生成真实搜索链接
- 智能匹配职位、追踪投递全流程、看板管理
- 内置 **云贵川广西热门行业就业风向标**
- 对任意目标（考研 / 考公 / 教资 / 减肥 / 学技能…）自定义或**智能生成**分阶段计划、每日打卡

**设计理念**：所有数据默认存于本地 / 本浏览器，服务端**中性空白画像**，绝不预置任何用户专业，分享链接也不会泄漏他人信息。

---

## 二、功能特性

| 模块 | 说明 |
|---|---|
| 简历库 | 上传 PDF / Word，本地解析姓名 / 专业 / 技能 / 学历，多版本、可设默认 |
| 平台中心 | 18 个平台分「求职 / 考公考编 / 资格 / 考研」四类切换；一键全网搜（按专业 + 云南省 16 州市打开真实搜索页，BOSS / 58 城市码自动映射）；模板可改 |
| 首页风向标 | 云贵川广西四省重点产业卡片：代表城市 / 企业 / 适合专业 / 薪资 / 趋势 + 一键搜该行业岗位 |
| 四赛道概览 | 仪表盘顶部一眼看清每条赛道备战职位数 |
| 备考时间线 | 四大赛道报名 / 笔试 / 考试关键节点（已核实 2026–2027 周期），带倒计时与优先级，可增删 |
| 职位看板 | 手动添加 / 批量导入，自动算匹配度，Kanban 拖拽改状态，⭐ 收藏、「仅看收藏」视图 |
| 智能匹配 | 默认本地关键词引擎（离线可用）；开启后可调用**本机 Ollama Qwen** 深度分析 |
| 投递追踪 | 每次「去投递」自动记录时间 / 职位 / 公司 / 平台 / 城市 / 简历，可撤回；Kanban 看板 |
| 仪表盘 | 投递漏斗、平台职位分布环图、画像完整度环图、各赛道进度、城市分布、临近节点 |
| 计划打卡 | 自定义或智能生成阶段计划（准备→基础→强化→冲刺→复盘），任务勾选、进度条、🔥 连续打卡天数 |
| 数据 | SQLite 自托管，支持导出 / 导入 JSON；可选用户名 + 密码登录（哈希本机保存）跨设备保存进度 |

### 关于「自动投简历」的诚实说明

各招聘平台**没有公开投递 API**，脚本 / 外挂批量投递违反其用户协议、有封号风险。本工作台采用**合规且真正可用**的方案：

> **一键直达平台投递页 + 自动记录状态**——点「去投递」即在已登录平台打开该职位真实申请页，并自动标记为已投递、记录时间。

如需浏览器级自动化，请参考社区方案（如 `loks666/get_jobs`、八爪鱼 RPA、Tampermonkey 脚本），但**不要在本工作台内硬编码账号密码**，自担账号风险。

---

## 三、技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.10+ · Flask 3 |
| 前端 | 原生 HTML / CSS / JS（零框架，SPA 内联在 `index.html`） |
| 数据 | SQLite（自托管，零外部依赖） |
| 简历解析 | PyMuPDF（`fitz`）/ pdfminer.six（本地，不上传） |
| 可选增强 | 本机 Ollama Qwen（深度匹配，需用户手动开启） |
| 单文件版 | 纯静态 HTML（零后端，数据存 `localStorage`） |

---

## 四、目录结构

```
xiaok-workbench/
├─ README.md                 # 本文件（总览 + 二次开发指南）
├─ LICENSE                   # MIT
├─ .gitignore
├─ docs/
│  └─ design.md              # 个人竞争力分析功能设计方案（早期设计文档）
├─ local/                    # ★ 本地离线版（主可开发版本，Flask 后端）
│  ├─ app.py                 # Flask 后端 + 全部 /api 路由 + 访问口令保护
│  ├─ requirements.txt       # flask>=3.0 / PyMuPDF>=1.23 / pdfminer.six
│  ├─ start.sh               # Linux / macOS 启动
│  ├─ 一键启动.bat            # Windows 启动
│  ├─ 本地运行说明.txt
│  ├─ index.html             # 前端 SPA 入口（Flask 根路由返回此文件）
│  ├─ core/                  # 业务逻辑层（纯 Python，无框架依赖）
│  │  ├─ __init__.py
│  │  ├─ db.py               # 数据层：SQLite 表、四省市州码表、平台注册表、种子数据
│  │  ├─ resume_parser.py    # 简历文本抽取 + 结构化字段提取
│  │  ├─ matcher.py          # 智能匹配（本地关键词 + 领域桥接 / 可选 Ollama）
│  │  ├─ platforms.py        # 平台 deep-link 拼装（{kw}{city}{boss}{58} 占位符）
│  │  ├─ hot_industries.py   # 云贵川广西热门行业内容库
│  │  ├─ planner.py          # 智能计划生成（分阶段任务模板 + 目标识别）
│  │  └─ demo_data.py        # 演示职位（云贵川广西多行业）
│  ├─ static/
│  │  ├─ app.js              # 前端逻辑
│  │  └─ styles.css          # 样式
│  └─ data/                  # 运行时生成（app.db / uploads/），已 gitignore
│     └─ uploads/.gitkeep
└─ single-file/              # 单文件版（纯 HTML，双击即用）
   ├─ index.html             # 全部内联，零外部依赖，约 122KB
   └─ 使用说明.md
```

> 开发以 `local/` 为主；`single-file/` 是面向终端用户的零安装分发包。

---

## 五、快速开始

### 本地离线版（推荐开发版本）

```bash
cd local
pip install -r requirements.txt
python app.py              # 默认 http://localhost:3000
```

- **Windows**：直接双击 `一键启动.bat`
- **Linux / macOS**：`bash start.sh`

环境变量：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `PORT` | `3000` | 监听端口 |
| `WB_PASS` | `<你的访问口令>` | 公网部署时的访问口令（首页弹窗校验），请自行设置强口令 |
| `WB_SECRET` | `kai-workbench-secret` | Flask session 密钥，生产环境请改 |

启动后浏览器打开 **http://localhost:3000**。

### 单文件版

直接双击 `single-file/index.html`（断网也可用，数据存浏览器 `localStorage`）。适合分享给不使用 Python 的朋友。

---

## 六、部署

- **本机 / 内网**：`python app.py` 即可，端口 3000。
- **云服务器**：用 gunicorn / waitress 托管 `app.py`，前置 Nginx；务必设置 `WB_PASS` 与 `WB_SECRET`，数据库文件 `data/app.db` 随服务器走。
- **静态托管（单文件版）**：把 `single-file/index.html` 传到任意静态空间（EdgeOne Pages / CloudStudio / GitHub Pages / Nginx），即成一个公开可访问的求职备考 APP；手机「添加到主屏幕」可当 APP 用。

---

## 七、后端 API 速览

所有接口前缀 `/api`，数据隔离基于请求头 `X-Visitor`（匿名）或 `X-Account`（已登录 token）。

| 分组 | 端点 |
|---|---|
| 账户（可选） | `POST /api/register` · `POST /api/login_account` · `POST /api/account_logout` · `GET /api/me` |
| 简历 | `GET /api/resumes` · `POST /api/resumes/upload` · `GET /api/resumes/<id>/preview` · `POST /api/resumes/<id>/default` · `DELETE /api/resumes/<id>` |
| 平台 | `GET /api/platforms` · `GET /api/categories` · `POST /api/platforms/<key>` · `GET /api/search_links` |
| 热门行业 | `GET /api/hot_industries` |
| 计划打卡 | `GET/POST /api/plans` · `POST /api/plans/generate` · `GET/DELETE /api/plans/<id>` · `POST /api/plans/<id>/tasks` · `POST/DELETE /api/plans/<id>/tasks/<tid>` · `POST /api/plans/<id>/checkin` |
| 职位 | `GET/POST /api/jobs` · `POST /api/jobs/import` · `GET/POST/DELETE /api/jobs/<id>` · `POST /api/jobs/<id>/blacklist` |
| 匹配 | `POST /api/match/<id>` · `POST /api/match_all` |
| 统计 / 数据 | `GET /api/stats` · `GET /api/export` · `POST /api/demo` · `POST /api/reset` · `DELETE /api/my_data` |
| 备考节点 | `GET/POST /api/milestones` · `POST/DELETE /api/milestones/<id>` · `POST /api/milestones/<id>/toggle` |
| 投递记录 | `POST /api/deliver` · `POST /api/deliver/batch` · `GET/POST /api/deliveries` · `GET /api/deliveries/today` · `DELETE/PUT /api/delivery/<id>` |
| 收藏 | `POST /api/save` · `GET /api/saved` · `DELETE /api/saved/<id>` |
| 官方信息源 | `GET /api/resources`（sources / exams / disability / provinces） |

---

## 八、数据模型（SQLite）

数据隔离模型：**未登录**按浏览器访客 `visitor_id` 隔离；**已登录**按 `account_id` 隔离；职位池为共享演示数据。

| 表 | 职责 |
|---|---|
| `user_profiles` | 个人画像（中性默认，按 owner 隔离） |
| `accounts` / `account_tokens` | 可选账户与登录 token（密码 PBKDF2 哈希） |
| `resumes` | 简历原文 + 结构化解析结果 |
| `platforms` | 平台注册表（key / 分类 / 搜索模板） |
| `jobs` / `app_history` | 职位库 + 状态变更历史 |
| `milestones` | 备考关键节点（种子数据） |
| `deliveries` | 投递流水 |
| `saved_jobs` | 岗位收藏 |
| `plans` / `plan_tasks` / `plan_checkins` | 计划打卡三件套 |
| `demo_data` 相关 | 演示职位由 `core/demo_data.py` 注入 |

> 数据库首次启动由 `core/db.py::init_db()` 自动建表并注入平台、节点种子；旧库有向前迁移逻辑，升级安全。

---

## 九、二次开发指南（重点）

仓库零构建、纯 Python + 原生前端，改完即生效。常见扩展点：

### 1. 新增招聘平台
编辑 `local/core/db.py` 的 `DEFAULT_PLATFORMS` 列表，加一项：
```python
{"key": "x", "name": "新平台", "color": "#RRGGBB", "icon": "🔗",
 "category": "求职",          # 求职 / 考公考编 / 资格考试 / 考研
 "search_template": "https://x.com/search?q={kw}&city={boss}",
 "note": "说明"}
```
搜索模板支持占位符：`{kw}` 关键词、`{city}` 城市名、`{boss}` BOSS 城市码、`{58}` 58 同城拼音。城市码 / 拼音来自 `PROVINCE_CITIES`。也可在 UI「设置 / 平台中心」直接加，无需改码。

### 2. 新增热门行业（云贵川广西）
编辑 `local/core/hot_industries.py` 的 `get_hot_industries()` 返回结构（省份 → 产业 → 代表城市 / 企业 / 适合专业 / 薪资 / 趋势）。

### 3. 新增备考赛道 / 节点
- 赛道列表：`core/db.py` 的 `CATEGORIES`（如新增「教师编」）。
- 节点种子：`core/db.py` 的 `SEED_MILESTONES`（首次启动注入；已启动的库用 UI 添加即可）。

### 4. 新增智能计划模板
编辑 `local/core/planner.py`：
- `TEMPLATES`：每种目标类型的分阶段任务（准备 / 基础 / 强化 / 冲刺 / 复盘，`pct` 为相对总天数百分比）。
- `DETECT`：目标关键词 → 模板类型映射（如「考研」「减肥」自动识别）。
纯规则驱动，无需大模型。

### 5. 自定义匹配规则
编辑 `local/core/matcher.py`：
- `FIELD_GROUPS`：领域桥接分组（简历与 JD 同领域不同用词也能命中）。
- `CORE_MAJOR`：核心专业加权词。
本地匹配 = 关键词覆盖(50) + 领域相关(40) + 核心专业加权(≤10)。

### 6. 新增演示职位
编辑 `local/core/demo_data.py` 的 `DEMO_JOBS`（云贵川广西多行业样例），用于首次体验。

### 7. 接入大模型深度匹配
设置页开启 Ollama，填 `ollama_url`（默认 `http://localhost:11434`）与 `ollama_model`（默认 `qwen3.6:35b-a3b`）。匹配逻辑见 `core/matcher.py` 的 `ollama_match`。

---

## 十、隐私与安全

- **数据隔离**：未登录按浏览器访客隔离，已登录按账户隔离；每个人的简历 / 收藏 / 投递互不串。
- **中性默认画像**：个人画像默认空白，绝不预置任何用户专业，分享链接不会泄漏他人信息。
- **密码安全**：可选登录的密码经 PBKDF2-SHA256 加盐哈希后仅存本机服务器，绝不外传。
- **零外部调用**：简历解析、职位匹配、计划生成均在本地完成；除非你主动开启 Ollama，否则不联网调用任何模型。
- **合规**：不提供自动批量投递，不硬编码任何平台账号密码。

---

## 十一、免责声明

1. 本工作台仅做**信息聚合与本地求职 / 备考管理**，不对任何求职、考试结果负责。
2. 各平台搜索链接、考试时间、考试目录均整理自公开官方信息，**以各官方当年公告为准**；链接失效 / 日期变动请自行核实。
3. 招聘平台**没有公开投递 API**，自动脚本投递违反其用户协议、存在封号风险；本工具仅提供「一键直达 + 状态记录」，不构成投递建议。
4. 软件按「原样」提供，作者不对使用后果承担任何责任；下载 / 使用即视为同意本声明。

---

## 十二、开源协议

本项目以 **MIT 协议**开源，详见 [LICENSE](./LICENSE)。可自由 Fork、修改、再分发，请保留版权与许可声明。

## 十三、如何贡献

1. Fork 本仓库，新建分支（`feat/xxx` 或 `fix/xxx`）。
2. 本地 `cd local && pip install -r requirements.txt && python app.py` 验证。
3. 提交 PR，描述改动与测试方式。
4. 欢迎补充：新平台、新行业、新赛道、新计划模板、新匹配规则。

---

**Made with ☕ by schvinkk** · 让求职与备考少一点信息差。
