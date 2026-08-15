"""
智能匹配引擎
- local_match: 本地关键词覆盖度评分（零依赖、离线可用、永远可用）
- ollama_match: 可选调用本机 Ollama Qwen 做深度人岗分析（需用户开启）
"""
import json
import re
import urllib.request
from .resume_parser import build_match_corpus

CORE_MAJOR = ["中药学", "药学", "中药制剂", "药物制剂", "制药工程", "质量管理", "QC", "质量检验"]
MAJOR_HINT = ["中药", "药", "饮片", "制剂", "检验", "质检", "化验", "GMP", "QC"]

# 领域桥接：简历与 JD 用词不同（Python vs Java、数据分析 vs 数据仓库）时，
# 用「领域组」把同领域技能归并，避免表面上完全不匹配。
FIELD_GROUPS = [
    ("编程开发", ["python", "java", "javascript", "typescript", "go", "c++", "c#", "php",
               "ruby", "前端", "后端", "全栈", "开发", "软件", "编程", "vue", "react",
               "django", "spring", "flask", "node", "程序员"]),
    ("数据与云", ["大数据", "云计算", "云", "数据仓库", "hadoop", "spark", "flink", "数据分析",
               "数据挖掘", "数据可视化", "数据库", "mysql", "redis", "mongodb", "运维", "bi", "数仓"]),
    ("硬件嵌入式", ["嵌入式", "单片机", "stm32", "电路设计", "pcb", "fpga", "集成电路", "半导体",
                "芯片", "微电子", "硬件", "电子", "固件"]),
    ("医药健康", ["中药", "药学", "中药学", "制药", "药物", "检验", "质检", "化验", "gmp", "gcp",
               "qc", "qa", "医学", "护理", "临床", "健康"]),
    ("制造工程", ["机械", "自动化", "cad", "solidworks", "土木", "建筑", "化工", "材料", "电气",
               "能源", "制造", "工程"]),
    ("职能管理", ["项目管理", "产品", "运营", "市场", "人力", "财务", "会计", "供应链", "物流",
               "行政", "管理"]),
    ("设计媒体", ["ui", "ux", "设计", "剪辑", "排版", "新媒体", "短视频", "直播", "摄影", "文案"]),
]


def _norm(s: str) -> str:
    return (s or "").lower()


def local_match(resume_parsed: dict, profile: dict, job: dict) -> dict:
    """本地匹配：简历关键词覆盖 + 领域桥接（同领域不同用词也能命中）。"""
    corpus = build_match_corpus(resume_parsed, profile.get("keywords", ""))
    if not corpus:
        return {"score": 0, "matched": [], "missing": [], "reason": "简历无可用关键词"}
    corpus_l = {_norm(k) for k in corpus}
    job_blob = _norm(" ".join([job.get("title", ""), job.get("company", ""),
                               job.get("description", ""), job.get("city", "")]))

    # 1) 精确关键词覆盖
    matched, missing = [], []
    for kw in corpus:
        if _norm(kw) in job_blob:
            matched.append(kw)
        else:
            missing.append(kw)
    exact_cov = len(matched) / max(1, len(corpus))

    # 2) 领域桥接：简历与 JD 命中同一领域组 → 视为相关
    resume_fields, job_fields = set(), set()
    for g, terms in FIELD_GROUPS:
        if any(t in corpus_l for t in terms):
            resume_fields.add(g)
        if any(t in job_blob for t in terms):
            job_fields.add(g)
    field_matched = resume_fields & job_fields
    field_rel = len(field_matched) / max(1, len(resume_fields)) if resume_fields else 0

    # 3) 综合打分：精确覆盖(50) + 领域相关(40) + 核心/专业加权(<=10)
    score = exact_cov * 50 + field_rel * 40
    title = _norm(job.get("title", ""))
    jblob = _norm(" ".join([job.get("title", ""), job.get("description", "")]))
    core_hit = [k for k in matched if k in CORE_MAJOR]
    if core_hit:
        score += 5
    if any(_norm(k) in title for k in CORE_MAJOR):
        score += 5
    if any(_norm(m) in jblob for m in MAJOR_HINT):
        score += 5
    if not resume_fields:  # 简历无领域标签时回退纯覆盖
        score = exact_cov * 80
    score = max(0, min(100, round(score)))

    reason = f"精确命中 {len(matched)} 项"
    if field_matched:
        reason += f"；领域相关：{','.join(list(field_matched)[:3])}"
    if core_hit:
        reason += f"；核心命中：{','.join(core_hit[:3])}"
    level = "高" if score >= 60 else ("中" if score >= 30 else "低")
    return {"score": score, "level": level, "matched": matched,
            "missing": missing[:12], "reason": reason}


def ollama_match(resume_text: str, job: dict, profile: dict) -> dict:
    """调用本机 Ollama 做深度分析。失败返回 None（回退本地）。"""
    if not profile.get("ollama_enabled"):
        return None
    url = (profile.get("ollama_url") or "http://localhost:11434").rstrip("/")
    model = profile.get("ollama_model") or "qwen3.6:35b-a3b"
    job_blob = " | ".join([job.get("title", ""), job.get("company", ""),
                           job.get("city", ""), job.get("salary", ""), job.get("description", "")])
    prompt = (
        "你是一名资深招聘顾问。请根据下方【简历摘要】与【岗位JD】，"
        "用中文输出 JSON：{\"score\":0-100, \"level\":\"高/中/低\", "
        "\"matched\":[匹配点], \"missing\":[差距], \"reason\":\"一句话结论\"}。"
        "只输出 JSON，不要解释。\n\n"
        f"【简历摘要】\n{resume_text[:1500]}\n\n【岗位JD】\n{job_blob[:1500]}"
    )
    try:
        payload = json.dumps({"model": model, "prompt": prompt, "stream": False,
                              "format": "json"}).encode("utf-8")
        req = urllib.request.Request(f"{url}/api/generate", data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode("utf-8"))
        out = data.get("response", "")
        m = re.search(r"\{.*\}", out, re.S)
        if m:
            return json.loads(m.group(0))
    except Exception:
        return None
    return None


def match_job(resume_parsed: dict, resume_text: str, profile: dict, job: dict) -> dict:
    """统一入口：优先 Ollama，失败回退本地。"""
    res = ollama_match(resume_text, job, profile)
    if res and isinstance(res, dict) and "score" in res:
        res["engine"] = "ollama"
        return res
    local = local_match(resume_parsed, profile, job)
    local["engine"] = "local"
    return local
