"""
简历解析：文本抽取 + 结构化字段提取（姓名/电话/邮箱/学历/技能/专业/经历）
纯本地运行，不上传任何第三方服务。
"""
import os
import re
import zipfile
import io
import unicodedata

# ---------- 文本抽取 ----------
def extract_pdf_text(path: str) -> str:
    """优先用 PyMuPDF(fitz)：速度快、稳定；失败再回退 pdfminer / pdftotext。"""
    try:
        import fitz
        doc = fitz.open(path)
        parts = [page.get_text() for page in doc]
        doc.close()
        return "\n".join(parts)
    except Exception:
        pass
    try:
        from pdfminer.high_level import extract_text
        return extract_text(path) or ""
    except Exception:
        pass
    try:
        import subprocess
        return subprocess.run(["pdftotext", path, "-"],
                              capture_output=True, text=True, timeout=30).stdout or ""
    except Exception:
        return ""


def extract_docx_text(path: str) -> str:
    """docx 本质是 zip 包，docProps + word/document.xml 内含文本。"""
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8", "ignore")
        # 段落与换行
        xml = re.sub(r"</w:p>", "\n", xml)
        xml = re.sub(r"<w:br[^>]*/>", "\n", xml)
        text = re.sub(r"<[^>]+>", "", xml)
        return text
    except Exception:
        return ""


def extract_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return extract_pdf_text(path)
    if ext in (".docx",):
        return extract_docx_text(path)
    if ext in (".txt", ".md"):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    if ext == ".doc":
        # 老版 .doc 无标准库方案，尝试纯文本兜底
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""


# ---------- 结构化提取 ----------
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)")
DEGREE_RE = re.compile(r"(博士|硕士|研究生|本科|大专|专科|高中|中专|技校|Bachelor|Bachelors|Master|Masters|PhD|Doctor|Diploma|Undergraduate|Graduate)")
# 常见专业词库（覆盖药类 + 云贵川广西全行业通用岗位），用于兜底识别。
MAJOR_KEYS = [
    # 药学/医药/护理类
    "中药学", "药学", "药物制剂", "中药制剂", "制药工程", "生物技术", "生物工程",
    "化学", "应用化学", "食品科学", "食品质量与安全", "护理学", "中医学", "临床医学",
    "医学影像技术", "医学检验技术", "康复治疗学", "预防医学", "口腔医学", "针灸推拿",
    # 工科/计算机/电子信息
    "软件工程", "计算机科学与技术", "计算机", "电子信息工程", "通信工程", "信息工程",
    "电气工程", "电气工程及其自动化", "自动化", "机械设计制造及其自动化", "机械工程",
    "机械电子", "车辆工程", "土木工程", "工程管理", "建筑学", "城乡规划", "给排水",
    "材料科学与工程", "材料成型", "化学工程与工艺", "环境工程", "环境科学", "能源与动力工程",
    "人工智能", "数据科学与大数据技术", "大数据", "物联网工程", "网络工程", "信息安全",
    "微电子", "集成电路", "电子科学与技术", "光电信息", "测控技术与仪器", "新能源科学与工程",
    # 能源/制造/农林
    "农业机械化", "农学", "园艺", "植物保护", "茶学", "动物科学", "动物医学", "林学",
    "水土保持", "农业资源与环境", "食品营养", "酿酒工程", "轻化工程", "包装工程",
    # 经管/文科/其他
    "会计学", "财务管理", "金融学", "审计学", "市场营销", "工商管理", "国际经济与贸易",
    "汉语言文学", "新闻学", "广告学", "行政管理", "人力资源管理", "物流管理", "旅游管理",
    "农林经济管理", "经济学", "统计学", "数学与应用数学", "应用数学", "应用统计学",
    "社会学", "法学", "知识产权", "思想政治教育", "历史学", "哲学", "心理学",
    "英语", "商务英语", "日语", "翻译", "学前教育", "小学教育", "教育学", "特殊教育",
    "酒店管理", "会展经济", "烹饪", "电子商务", "数字经济", "跨境电子商务",
]
# 显式「专业：」标签
MAJOR_LABEL_RE = re.compile(r"(专业|所学专业|Major)\s*[:：]\s*([\u4e00-\u9fff]{2,12})")
# 「XX大学 软件工程 本科」这类"院校+专业+学历"结构
MAJOR_UNIV_RE = re.compile(r"(大学|学院)\s+([\u4e00-\u9fff]{2,12})\s+(本科|硕士|研究生|大专|专科)")
# 英文「XX University Computer Science Bachelor」结构
MAJOR_UNIV_EN_RE = re.compile(r"(University|College|大学|学院)\s+([A-Z][a-zA-Z ]{2,30}?)\s+(Bachelor|Bachelors|Master|Masters|PhD|Doctor|Undergraduate|Graduate)")


def _split_tokens(text: str):
    # 中文按字/词粗分，英文按词
    cn = re.findall(r"[\u4e00-\u9fff]+", text)
    en = re.findall(r"[A-Za-z][A-Za-z0-9\+\#\.\-]{1,}", text)
    return cn, en


def _dedupe(lst):
    seen = set(); out = []
    for x in lst:
        if x and x not in seen:
            seen.add(x); out.append(x)
    return out


# 技能区块标题（命中后到下一节之前的内容都视为技能候选）
SKILL_HEAD_RE = re.compile(r"(专业技能|核心技能|技能特长|技能与特长|个人技能|职业技能|熟悉软件|掌握工具|技能关键字|技能|Skills|SKILLS|Skill|熟悉|掌握|熟练掌握)")
# 技能区块到此结束（遇到这些标题说明进入了别的板块）
SECTION_STOP_RE = re.compile(r"(教育|学历|学习|经历|项目|工作|实习|实践|自我评价|个人评价|获奖|荣誉|证书|资格|语言|期望|求职|意向|个人简介|概述|总结|自荐)")
# 技能候选里要剔除的虚词/动词，避免把经历描述当技能
SKILL_STOP = {"掌握", "熟悉", "熟练", "了解", "使用", "运用", "具备", "良好", "一定",
              "较强", "能力", "经验", "以上", "等", "及", "与", "和", "并", "通过", "负责",
              "参与", "完成", "进行", "能够", "可以", "善于", "乐于", "具有", "拥有", "相关",
              "熟练使用", "熟练掌握", "熟悉使用"}
# 英文自由技能里要剔除的普通词（句子词，不是技能）
ENGLISH_STOP = {"in", "with", "and", "the", "for", "to", "of", "a", "an", "is", "are",
                "or", "on", "at", "by", "as", "be", "do", "we", "i", "you", "he", "she",
                "they", "this", "that", "it", "from", "into", "using", "use", "used",
                "have", "has", "had", "familiar", "proficient", "develop", "developed",
                "developing", "experience", "experiences", "skill", "skills", "etc",
                "such", "like", "also", "can", "will", "our", "their", "his", "her",
                "not", "but", "if", "so", "about", "than", "then", "that", "these",
                "those", "was", "were", "been", "being", "am", "are", "knowledge"}
# 中文自由技能片段噪声：包含这些词的基本是句子片段而非技能
FRAGMENT_NOISE = ["框架", "数据库", "部署", "架构", "工具", "进行", "公司", "负责", "参与",
                  "内容", "描述", "说明", "简介", "方面", "要求", "相关", "开发", "设计",
                  "工作", "项目", "能力", "经验", "分析", "处理", "管理", "维护", "支持",
                  "提供", "实现", "完成", "学习", "研究", "了解", "掌握", "运用", "从事",
                  "擅长", "包括", "例如", "其中", "以及", "并且", "能够", "可以", "具有"]


def extract_section_skills(text: str):
    """从「技能」区块提取自由书写的技能（弥补固定词典覆盖不到的词）。"""
    out = []
    capture = False
    for line in text.split("\n"):
        ls = line.strip()
        if not ls:
            continue
        if SKILL_HEAD_RE.search(ls) and not SECTION_STOP_RE.search(ls):
            capture = True
            tail = SKILL_HEAD_RE.sub("", ls).strip(" ：:，、；;")
            out += _split_skill_line(tail)
            continue
        if capture:
            if SECTION_STOP_RE.search(ls):
                capture = False
                continue
            out += _split_skill_line(ls)
    return out


def _split_skill_line(line: str):
    toks = re.split(r"[\s,，、;；/\\|（）()\[\]【】:：.。()]+", line)
    out = []
    for t in toks:
        t = t.strip().strip("。；;，,、")
        if not t:
            continue
        if t in SKILL_STOP:
            continue
        # 中文片段噪声（含框架/数据库/部署等句子的词 → 丢弃）
        if any(n in t for n in FRAGMENT_NOISE):
            continue
        # 纯英文 token
        if re.fullmatch(r"[A-Za-z0-9\+#\.\-]+", t):
            tl = t.lower()
            if tl in ENGLISH_STOP:
                continue
            if len(t) < 2:
                continue
            # 保留看起来像技术词的：含数字/+/#、首字母大写、或长度≥3
            if not (re.search(r"[0-9\+#]", t) or t[0].isupper() or len(t) >= 3):
                continue
            out.append(t)
        # 中文 token：长度 2-10 且含汉字
        elif 2 <= len(t) <= 10 and re.search(r"[\u4e00-\u9fff]", t):
            out.append(t)
    return out


NAME_STOP = {"简历", "个人简历", "求职简历", "基本信息", "个人资料", "个人信息", "联系方式",
             "自我评价", "个人简介", "教育背景", "工作经历", "项目经历", "技能", "荣誉", "证书",
             "求职意向", "专业技能", "核心技能", "个人技能", "技能特长", "技能与特长"}


def extract_name(text: str):
    """姓名提取：标签 > 顶部单独成行的中文名 > 英文名。"""
    # 1) 标签
    m = re.search(r"(姓名|Name)\s*[:：]\s*([\u4e00-\u9fff]{2,4})", text)
    if m:
        return m.group(2)
    # 2) 英文名
    me = re.search(r"(姓名|Name)\s*[:：]\s*([A-Za-z]+\.?\s?[A-Za-z]+)", text)
    if me:
        return me.group(2).strip()
    # 3) 顶部前几行里，单独成行、2-4 个汉字、且不是板块标题词的，视为姓名
    for line in text.split("\n")[:6]:
        ls = line.strip()
        if not ls:
            continue
        if re.fullmatch(r"[\u4e00-\u9fff]{2,4}", ls) and ls not in NAME_STOP:
            return ls
    # 4) 英文简历：顶部 "First Last"（首字母大写的两个英文词）
    for line in text.split("\n")[:6]:
        ls = line.strip()
        if re.fullmatch(r"[A-Z][a-z]+\.?\s[A-Z][a-z]+", ls):
            return ls
    return ""


def parse_resume(text: str, filename: str = "") -> dict:
    text = text or ""
    # 归一化：把全角字符、CJK 兼容变体（如 李 U+F9E1 → 李）统一为标准码位，
    # 否则部分 PDF 生成的兼容汉字会导致姓名/技能正则完全失效。
    text = unicodedata.normalize("NFKC", text)
    emails = EMAIL_RE.findall(text)
    phones = PHONE_RE.findall(text)
    degrees = DEGREE_RE.findall(text)

    # 技能词典（与求职匹配共用，覆盖中药/制药/通用 + 云贵川桂全行业：
    # 光伏风电水电、有色化工、白酒食品、旅游农业、大数据云计算、集成电路、
    # 跨境电商物流、建筑、护理教育、政务等）
    SKILLS = [
        # 药学/制药/医疗
        "中药学", "药学", "中药鉴定", "中药炮制", "中药制剂", "药物分析", "药理学",
        "临床医学", "护理学", "中医学", "医学影像", "医学检验", "康复治疗",
        "QC", "QA", "质量检验", "质检", "化验", "GMP", "GLP", "GSP", "HPLC",
        "气相色谱", "液相色谱", "薄层色谱", "紫外分光", "原子吸收", "微生物检验",
        "无菌检验", "限度检查", "含量测定", "滴定", "标准操作规程", "SOP",
        "药品生产", "工艺验证", "清洁验证", "偏差处理", "变更控制", "CAPA",
        "物料平衡", "批记录", "注册检验", "稳定性考察", "留样", "不良反应监测",
        # IT / 软件 / 数据
        "Python", "Java", "JavaScript", "TypeScript", "Go", "C++", "C#", "PHP", "Ruby", "Scala",
        "SQL", "MySQL", "PostgreSQL", "Oracle", "MongoDB", "Redis", "ClickHouse",
        "HTML", "CSS", "Vue", "React", "Angular", "Node", "Django", "Spring", "Flask", "Express",
        "Linux", "Docker", "Kubernetes", "K8s", "Git", "CI", "CD", "Nginx", "Tomcat",
        "云计算", "云服务", "AWS", "阿里云", "腾讯云", "华为云", "OpenStack",
        "大数据", "Hadoop", "Spark", "Flink", "Hive", "数据仓库", "数据治理",
        "数据分析", "数据挖掘", "数据可视化", "BI", "Tableau", "PowerBI", "Excel",
        "人工智能", "机器学习", "深度学习", "神经网络", "NLP", "计算机视觉", "OCR",
        "物联网", "嵌入式", "单片机", "STM32", "PLC", "FPGA", "电路设计", "PCB",
        "集成电路", "半导体", "芯片", "微电子", "晶圆", "封装测试", "版图设计",
        "网络安全", "信息安全", "渗透测试", "防火墙", "等保", "密码学",
        "前端", "后端", "全栈", "小程序", "Android", "iOS", "鸿蒙", "移动开发",
        "WordPress", "SEO", "SEM", "爬虫", "自动化测试", "性能优化",
        # 工程 / 制造 / 能源
        "光伏", "风电", "水电", "新能源", "储能", "电池", "锂电池", "逆变器",
        "电气工程", "自动化", "机械设计", "CAD", "SolidWorks", "UG", "ProE",
        "数控", "焊接", "模具", "工艺设计", "精益生产", "六西格玛", "TPM",
        "化工", "化学反应", "蒸馏", "萃取", "催化", "涂料", "橡胶", "塑料",
        "有色金属", "冶金", "冶炼", "电解", "选矿", "铝业", "铜业", "钢铁",
        "土木", "建筑", "工程造价", "BIM", "施工管理", "监理", "结构设计", "给排水",
        "环境工程", "污水处理", "环保", "环评", "安全工程", "EHS", "消防",
        "食品科学", "食品加工", "酿酒", "白酒", "品酒", "质量管理", "ISO9001", "HACCP",
        # 业务 / 职能 / 通用
        "项目管理", "PMP", "敏捷", "Scrum", "PRINCE2", "OKR", "需求分析",
        "产品设计", "原型", "Axure", "Figma", "UI", "UX", "交互设计",
        "市场营销", "品牌", "新媒体", "短视频", "直播", "电商", "跨境电商",
        "淘宝", "天猫", "京东", "拼多多", "抖音", "运营", "用户增长", "私域",
        "供应链管理", "采购", "物流", "仓储", "运输", "报关", "报检", "国际贸易",
        "财务会计", "会计", "审计", "税务", "Excel", "用友", "金蝶", "SAP",
        "人力资源", "招聘", "薪酬", "绩效", "培训", "劳动关系",
        "行政管理", "公文写作", "会务", "档案管理", "政务服务", "窗口服务",
        "法律", "合同审查", "合规", "知识产权", "专利",
        "教学", "课程设计", "备课", "班主任", "普通话", "教师资格",
        "英语", "CET", "雅思", "托福", "翻译", "口译",
        "农林", "种植", "养殖", "园艺", "茶学", "农学", "植保", "土壤",
        "旅游", "导游", "酒店管理", "前厅", "餐饮", "会展", "客户接待",
        "沟通", "表达", "团队协作", "抗压", "执行力", "学习能力", "服务意识",
        "Photoshop", "PR", "AE", "剪辑", "排版", "文案", "摄影",
    ]
    found = []
    for s in SKILLS:
        # 纯英文短词（如 UI/QA/SEM）用单词边界匹配，避免 "ui" 命中 "guidance"
        if re.fullmatch(r"[A-Za-z0-9\+#\.\-]+", s):
            if re.search(r"(?<![A-Za-z0-9])" + re.escape(s) + r"(?![A-Za-z0-9])", text, re.I):
                found.append(s)
        elif s in text:
            found.append(s)
    # 区块自由技能（弥补词典覆盖不到的自定义技能）
    found += extract_section_skills(text)
    found = _dedupe(found)

    # 专业推断：优先「专业：」标签 → 院校+专业+学历结构 → MAJOR_KEYS 兜底
    major = ""
    ml = MAJOR_LABEL_RE.search(text)
    if ml:
        major = ml.group(2)
    if not major:
        mu = MAJOR_UNIV_RE.search(text)
        if mu:
            major = mu.group(2)
    if not major:
        mue = MAJOR_UNIV_EN_RE.search(text)
        if mue:
            major = mue.group(2).strip()
    if not major:
        for m in MAJOR_KEYS:
            if m in text:
                major = m
                break

    # 姓名提取（标签 / 顶部成行 / 英文）
    name = extract_name(text)

    # 关键词集合（用于匹配）
    keywords = []
    keywords += found
    keywords += [d for d in degrees]
    if major:
        keywords.append(major)
    kw = _dedupe(keywords)

    return {
        "name": name,
        "email": emails[0] if emails else "",
        "phone": phones[0] if phones else "",
        "degrees": list(dict.fromkeys(degrees)),
        "major": major,
        "skills": found,
        "keywords": kw,
        "text_len": len(text),
    }


def build_match_corpus(parsed: dict, profile_keywords: str = "") -> set:
    """构建用于匹配的关键词语料（简历关键词 + 用户设定关键词）。"""
    corp = set(parsed.get("keywords", []))
    for k in (profile_keywords or "").split(","):
        k = k.strip()
        if k:
            corp.add(k)
    return corp
