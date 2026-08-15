"""
小K万能工作台 —— 后端 (Flask)
本地运行，单文件启动。所有数据存于 ./data。

数据模型（公开多用户 + 可选账户）：
- 公开可用：任何人打开即用，无需登录。
- 未登录：按浏览器访客标识 visitor_id 隔离（各自简历/收藏/投递互不串）。
- 已登录：按自选用户名账户 account_id 隔离（跨设备保存进度）。
- 个人画像默认中性空白，绝不预置任何用户专业，分享链接也不会泄漏他人信息。
- 职位池为共享演示数据，不属于个人隐私。
"""
import io
import json
import os
import sys

from flask import Flask, request, jsonify, send_from_directory, Response

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import db
from core.resume_parser import extract_text, parse_resume
from core.matcher import match_job, local_match
from core.platforms import all_search_links
from core.hot_industries import get_hot_industries
from core.planner import smart_plan

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("WB_SECRET", "kai-workbench-secret")
db.init_db()


# ---------------- 访问控制 ----------------
# 公开版：任何人可用，无需登录。数据按 visitor_id / account_id 隔离。
@app.before_request
def _guard():
    return  # 公开访问，不做鉴权拦截


def get_vid():
    """访客标识：优先请求头 X-Visitor，其次 Cookie wb_vid。"""
    return (request.headers.get("X-Visitor")
            or request.cookies.get("wb_vid") or "")


def get_owner():
    """解析当前数据归属：已登录账户优先，否则按浏览器访客。"""
    tok = request.headers.get("X-Account") or request.cookies.get("wb_acct")
    aid = db.account_by_token(tok) if tok else None
    if aid:
        return {"account_id": aid, "visitor_id": None}
    return {"account_id": None, "visitor_id": get_vid()}


# ---------------- 账户（可选登录，本地保存进度） ----------------
@app.route("/api/register", methods=["POST"])
def register():
    d = request.get_json(force=True, silent=True) or {}
    aid, err = db.create_account(d.get("username", ""), d.get("password", ""))
    if err:
        return jsonify({"error": err}), 400
    tok = db.issue_token(aid)
    # 登录时把当前匿名访客的数据并入账户，避免重复劳动
    db.merge_visitor_to_account(get_vid(), aid)
    return jsonify({"ok": True, "token": tok, "username": d.get("username")})


@app.route("/api/login_account", methods=["POST"])
def login_account():
    d = request.get_json(force=True, silent=True) or {}
    aid = db.verify_account(d.get("username", ""), d.get("password", ""))
    if not aid:
        return jsonify({"error": "用户名或密码错误"}), 401
    tok = db.issue_token(aid)
    db.merge_visitor_to_account(get_vid(), aid)
    return jsonify({"ok": True, "token": tok, "username": d.get("username")})


@app.route("/api/account_logout", methods=["POST"])
def account_logout():
    tok = request.headers.get("X-Account") or request.get_json(force=True, silent=True) or {}
    if isinstance(tok, dict):
        tok = tok.get("token") or request.cookies.get("wb_acct")
    db.revoke_token(tok)
    return jsonify({"ok": True})


@app.route("/api/me", methods=["GET"])
def me():
    tok = request.headers.get("X-Account") or request.cookies.get("wb_acct")
    aid = db.account_by_token(tok) if tok else None
    uname = db.username_of(aid) if aid else None
    return jsonify({"account": uname, "visitor": get_vid()})


# ---------------- 页面 ----------------
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


# ---------------- Profile（按用户隔离，中性默认） ----------------
@app.route("/api/profile", methods=["GET"])
def get_profile():
    return jsonify(db.get_user_profile(**get_owner()))


@app.route("/api/profile", methods=["POST"])
def save_profile():
    data = request.get_json(force=True, silent=True) or {}
    return jsonify(db.save_user_profile(data, **get_owner()))


# ---------------- Resumes ----------------
@app.route("/api/resumes", methods=["GET"])
def resumes():
    return jsonify(db.list_resumes(**get_owner()))


@app.route("/api/resumes/upload", methods=["POST"])
def upload_resume():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "未收到文件"}), 400
    filename = f.filename or "resume.pdf"
    safe = f"{int(__import__('time').time())}_{filename}"
    path = os.path.join(UPLOAD_DIR, safe)
    try:
        f.save(path)
        text = extract_text(path)
        parsed = parse_resume(text, filename)
        rid = db.add_resume(parsed.get("name") or filename, filename, path, text, parsed, **get_owner())
        return jsonify({"id": rid, "parsed": parsed})
    except Exception as e:
        return jsonify({"error": f"解析失败：{e}"}), 500


@app.route("/api/resumes/<int:rid>/preview", methods=["GET"])
def preview_resume(rid):
    r = db.get_resume(rid)
    if not r:
        return jsonify({"error": "not found"}), 404
    return jsonify({"text": r["text"][:8000], "parsed": json.loads(r["parsed"])})


@app.route("/api/resumes/<int:rid>/default", methods=["POST"])
def default_resume(rid):
    db.set_default_resume(rid)
    return jsonify({"ok": True})


@app.route("/api/resumes/<int:rid>", methods=["DELETE"])
def del_resume(rid):
    db.delete_resume(rid)
    return jsonify({"ok": True})


# ---------------- Platforms ----------------
@app.route("/api/platforms", methods=["GET"])
def platforms():
    cat = request.args.get("category")
    return jsonify(db.list_platforms(category=cat))


@app.route("/api/categories", methods=["GET"])
def categories():
    return jsonify(db.CATEGORIES)


@app.route("/api/platforms/<key>", methods=["POST"])
def upd_platform(key):
    data = request.get_json(force=True, silent=True) or {}
    db.update_platform(key, data)
    return jsonify({"ok": True})


@app.route("/api/search_links", methods=["GET"])
def search_links():
    kw = request.args.get("kw")
    cat = request.args.get("category")
    o = get_owner()
    # 未显式给关键词时，默认用"当前用户自己简历"里的专业/技能词（按自己的简历搜岗位）。
    # 若用户尚未上传简历，则中性返回平台基础链接并标记 need_resume，绝不回退到任何他人专业。
    if not kw:
        res = db.latest_resume(**o)
        if res:
            p = json.loads(res["parsed"])
            kw = (p.get("major")
                  or (p.get("skills") or [None])[0]
                  or (p.get("keywords") or [None])[0])
    if not kw:
        links = all_search_links(db.get_user_profile(**o), None, category=cat)
        for l in links:
            l["need_resume"] = True
        return jsonify(links)
    return jsonify(all_search_links(db.get_user_profile(**o), kw, category=cat))


# ---------------- 热门行业（云贵川广西） ----------------
@app.route("/api/hot_industries", methods=["GET"])
def hot_industries():
    return jsonify(get_hot_industries())


# ---------------- 计划打卡（万能工作台通用模块） ----------------
@app.route("/api/plans", methods=["GET"])
def plans_list():
    return jsonify(db.list_plans(**get_owner()))


@app.route("/api/plans", methods=["POST"])
def plans_create():
    d = request.get_json(force=True, silent=True) or {}
    title = (d.get("title") or "").strip() or (d.get("goal") or "未命名计划")
    pid = db.add_plan(title, d.get("goal", "") or "", False,
                      d.get("start_date") or "", d.get("target_date") or "", **get_owner())
    return jsonify({"id": pid, "plan": db.get_plan(pid, **get_owner())})


@app.route("/api/plans/generate", methods=["POST"])
def plans_generate():
    """智能分析目标 + 倒计时，生成分阶段计划与任务。"""
    d = request.get_json(force=True, silent=True) or {}
    goal = (d.get("goal") or "").strip()
    if not goal:
        return jsonify({"error": "请填写目标，例如：考研 / 教资 / 减肥"}), 400
    sp = smart_plan(goal, d.get("start_date"), d.get("target_date"))
    pid = db.add_plan(sp["title"], sp["goal"], True,
                      sp["start_date"], sp["target_date"], **get_owner())
    for t in sp["tasks"]:
        db.add_plan_task(pid, t["content"], t["due_date"], **get_owner())
    return jsonify({"id": pid, "plan": db.get_plan(pid, **get_owner()),
                    "generated": len(sp["tasks"])})


@app.route("/api/plans/<int:pid>", methods=["GET"])
def plan_detail(pid):
    p = db.get_plan(pid, **get_owner())
    if not p:
        return jsonify({"error": "not found"}), 404
    return jsonify(p)


@app.route("/api/plans/<int:pid>", methods=["DELETE"])
def plan_delete(pid):
    ok = db.delete_plan(pid, **get_owner())
    return jsonify({"ok": bool(ok)})


@app.route("/api/plans/<int:pid>/tasks", methods=["POST"])
def plan_task_add(pid):
    d = request.get_json(force=True, silent=True) or {}
    content = (d.get("content") or "").strip()
    if not content:
        return jsonify({"error": "任务内容不能为空"}), 400
    tid = db.add_plan_task(pid, content, d.get("due_date"), **get_owner())
    if tid is None:
        return jsonify({"error": "计划不存在或无权限"}), 404
    return jsonify({"id": tid, "plan": db.get_plan(pid, **get_owner())})


@app.route("/api/plans/<int:pid>/tasks/<int:tid>", methods=["POST"])
def plan_task_toggle(pid, tid):
    new = db.toggle_plan_task(tid, **get_owner())
    if new is None:
        return jsonify({"error": "无权限或任务不存在"}), 404
    return jsonify({"done": new, "plan": db.get_plan(pid, **get_owner())})


@app.route("/api/plans/<int:pid>/tasks/<int:tid>", methods=["DELETE"])
def plan_task_del(pid, tid):
    ok = db.delete_plan_task(tid, **get_owner())
    return jsonify({"ok": bool(ok)})


@app.route("/api/plans/<int:pid>/checkin", methods=["POST"])
def plan_checkin(pid):
    d = request.get_json(force=True, silent=True) or {}
    ok = db.add_checkin(pid, d.get("date"), d.get("note", "") or "", **get_owner())
    if not ok:
        return jsonify({"error": "计划不存在或无权限"}), 404
    return jsonify({"ok": True, "plan": db.get_plan(pid, **get_owner())})


# ---------------- Jobs ----------------
@app.route("/api/jobs", methods=["GET"])
def jobs():
    filters = {}
    if request.args.get("platform"):
        filters["platform"] = request.args.get("platform")
    if request.args.get("status"):
        filters["status"] = request.args.get("status")
    if request.args.get("q"):
        filters["q"] = request.args.get("q")
    if request.args.get("category"):
        filters["category"] = request.args.get("category")
    if request.args.get("city"):
        filters["city"] = request.args.get("city")
    if request.args.get("province"):
        filters["province"] = request.args.get("province")
    if request.args.get("blacklisted") is not None:
        filters["blacklisted"] = request.args.get("blacklisted") == "1"
    return jsonify(db.list_jobs(filters or None))


@app.route("/api/jobs", methods=["POST"])
def add_job():
    data = request.get_json(force=True, silent=True) or {}
    jid = db.add_job(data)
    return jsonify({"id": jid})


@app.route("/api/jobs/import", methods=["POST"])
def import_jobs():
    data = request.get_json(force=True, silent=True) or {}
    items = data.get("items")
    if isinstance(items, str):
        items = _parse_text_jobs(items)
    jids = db.import_jobs(items or [])
    return jsonify({"imported": len(jids), "ids": jids})


def _parse_text_jobs(text: str):
    out = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            continue
        out.append({
            "title": parts[0], "company": parts[1] if len(parts) > 1 else "",
            "platform_key": parts[2] if len(parts) > 2 else "boss",
            "city": parts[3] if len(parts) > 3 else "",
            "salary": parts[4] if len(parts) > 4 else "",
            "url": parts[5] if len(parts) > 5 else "",
            "source": "paste",
        })
    return out


@app.route("/api/jobs/<int:jid>", methods=["GET"])
def get_job(jid):
    r = db.get_job(jid)
    if not r:
        return jsonify({"error": "not found"}), 404
    return jsonify(r)


@app.route("/api/jobs/<int:jid>", methods=["POST", "PUT"])
def upd_job(jid):
    data = request.get_json(force=True, silent=True) or {}
    db.update_job(jid, data)
    return jsonify({"ok": True})


@app.route("/api/jobs/<int:jid>", methods=["DELETE"])
def del_job(jid):
    db.delete_job(jid)
    return jsonify({"ok": True})


@app.route("/api/jobs/<int:jid>/blacklist", methods=["POST"])
def blacklist_job(jid):
    data = request.get_json(force=True, silent=True) or {}
    db.set_blacklist(jid, bool(data.get("value", True)))
    return jsonify({"ok": True})


# ---------------- Match ----------------
def manual_parsed(m: dict):
    """用用户手动输入的专业/学历/技能构造一个"简历替身"用于匹配。"""
    major = (m.get("major") or "").strip()
    edu = (m.get("education") or "").strip()
    skills = [s.strip() for s in (m.get("skills") or "").split(",") if s.strip()]
    kws = [k.strip() for k in (m.get("keywords") or "").split(",") if k.strip()]
    keywords = set(kws)
    if major:
        keywords.add(major)
    if edu:
        keywords.add(edu)
    keywords.update(skills)
    parsed = {
        "name": "", "major": major,
        "education": [edu] if edu else [],
        "degrees": [edu] if edu else [],
        "skills": skills, "keywords": list(keywords),
    }
    text = " ".join([major, edu] + skills + kws)
    return parsed, text


def _resolve_match_input():
    """请求体显式带 manual 时优先用（手动填写的专业/学历可独立于简历）；
    否则优先用最新简历；都没有时返回 None。"""
    d = request.get_json(force=True, silent=True) or {}
    manual = d.get("manual")
    if manual and (manual.get("major") or "").strip():
        return manual_parsed(manual)
    res = db.default_resume(**get_owner())
    if res:
        return json.loads(res["parsed"]), res["text"]
    if manual:
        return manual_parsed(manual)
    return None, ""


@app.route("/api/match/<int:jid>", methods=["POST"])
def match_one(jid):
    job = db.get_job(jid)
    if not job:
        return jsonify({"error": "not found"}), 404
    parsed, text = _resolve_match_input()
    if parsed is None:
        return jsonify({"error": "请先上传简历，或在右侧手动填写专业/学历后再匹配"}), 400
    profile = db.get_user_profile(**get_owner())
    result = match_job(parsed, text, profile, job)
    db.update_job(jid, {"match_score": result.get("score")})
    return jsonify(result)


@app.route("/api/match_all", methods=["POST"])
def match_all():
    parsed, text = _resolve_match_input()
    if parsed is None:
        return jsonify({"error": "请先上传你的简历，或在右侧手动填写专业/学历后再匹配"}), 400
    profile = db.get_user_profile(**get_owner())
    jobs = db.list_jobs()
    for job in jobs:
        r = local_match(parsed, profile, job)
        db.update_job(job["id"], {"match_score": r.get("score")})
    return jsonify({"ok": True, "count": len(jobs)})


# ---------------- Stats / Export / Demo ----------------
@app.route("/api/stats", methods=["GET"])
def stats():
    return jsonify(db.stats(**get_owner()))


@app.route("/api/export", methods=["GET"])
def export_data():
    data = db.export_data(**get_owner())
    return Response(json.dumps(data, ensure_ascii=False, indent=2),
                    mimetype="application/json",
                    headers={"Content-Disposition": "attachment; filename=job_workbench_export.json"})


@app.route("/api/demo", methods=["POST"])
def load_demo():
    from core.demo_data import DEMO_JOBS
    db.reset_demo()
    jids = db.import_jobs(DEMO_JOBS)
    return jsonify({"ok": True, "imported": len(jids)})


@app.route("/api/reset", methods=["POST"])
def reset_jobs():
    db.reset_demo()
    return jsonify({"ok": True})


# ---------------- Milestones（备考关键节点） ----------------
@app.route("/api/milestones", methods=["GET"])
def milestones():
    cat = request.args.get("track")
    return jsonify(db.list_milestones(track=cat))


@app.route("/api/milestones", methods=["POST"])
def add_milestone():
    d = request.get_json(force=True, silent=True) or {}
    if not d.get("title") or not d.get("date"):
        return jsonify({"error": "标题和日期必填"}), 400
    mid = db.add_milestone(d)
    return jsonify({"id": mid})


@app.route("/api/milestones/<int:mid>", methods=["POST", "PUT"])
def upd_milestone(mid):
    d = request.get_json(force=True, silent=True) or {}
    db.update_milestone(mid, d)
    return jsonify({"ok": True})


@app.route("/api/milestones/<int:mid>", methods=["DELETE"])
def del_milestone(mid):
    db.delete_milestone(mid)
    return jsonify({"ok": True})


@app.route("/api/milestones/<int:mid>/toggle", methods=["POST"])
def toggle_milestone(mid):
    d = request.get_json(force=True, silent=True) or {}
    db.toggle_milestone(mid, bool(d.get("value", True)))
    return jsonify({"ok": True})


# ---------------- Deliveries（投递记录） ----------------
@app.route("/api/deliver", methods=["POST"])
def deliver():
    d = request.get_json(force=True, silent=True) or {}
    o = get_owner()
    d["account_id"] = o["account_id"]
    d["visitor_id"] = o["visitor_id"]
    did = db.add_delivery(d)
    return jsonify({"ok": True, "id": did})


@app.route("/api/deliver/batch", methods=["POST"])
def deliver_batch():
    """简历一键投递：一次把多份岗位记入投递流水（附默认简历名），供前端批量打开平台投递页。
    服务端去重：同一用户已投过的岗位不再重复记入。"""
    d = request.get_json(force=True, silent=True) or {}
    items = d.get("items") or []
    if not isinstance(items, list) or not items:
        return jsonify({"error": "请先选择要投递的岗位"}), 400
    o = get_owner()
    inserted, skipped = [], 0
    for it in items:
        if not isinstance(it, dict) or not it.get("job_id"):
            continue
        jid = int(it["job_id"])
        if db.owner_delivery_exists(jid, **o):
            skipped += 1
            continue
        it = dict(it)
        it["account_id"] = o["account_id"]
        it["visitor_id"] = o["visitor_id"]
        inserted.append(db.add_delivery(it))
    return jsonify({"ok": True, "count": len(inserted), "ids": inserted, "skipped": skipped})


@app.route("/api/deliveries/today", methods=["GET"])
def deliveries_today():
    return jsonify({"count": db.count_deliveries_today(**get_owner())})


@app.route("/api/deliveries", methods=["GET", "POST"])
def deliveries():
    if request.method == "POST":
        # 手动记录投递（内推 / 官网直投 / 现场等，未走平台一键投递）
        d = request.get_json(force=True, silent=True) or {}
        o = get_owner()
        d["account_id"] = o["account_id"]
        d["visitor_id"] = o["visitor_id"]
        d["job_id"] = d.get("job_id")  # 手动记录可无 job_id
        did = db.add_delivery(d)
        return jsonify({"ok": True, "id": did})
    cat = request.args.get("track")
    plat = request.args.get("platform")
    return jsonify(db.list_deliveries(track=cat, platform=plat, **get_owner()))


@app.route("/api/delivery/<int:did>", methods=["DELETE", "PUT"])
def del_delivery(did):
    if request.method == "PUT":
        d = request.get_json(force=True, silent=True) or {}
        db.update_delivery(did, note=d.get("note"), follow_at=d.get("follow_at"))
        return jsonify({"ok": True})
    db.delete_delivery(did)
    return jsonify({"ok": True})


# ---------------- Saved Jobs（岗位收藏） ----------------
@app.route("/api/save", methods=["POST"])
def save():
    d = request.get_json(force=True, silent=True) or {}
    o = get_owner()
    d["account_id"] = o["account_id"]
    d["visitor_id"] = o["visitor_id"]
    return jsonify(db.toggle_saved(d))


@app.route("/api/saved", methods=["GET"])
def saved():
    return jsonify(db.list_saved(**get_owner()))


@app.route("/api/saved/<int:sid>", methods=["DELETE"])
def del_saved(sid):
    db.delete_saved(sid)
    return jsonify({"ok": True})


# ---------------- 清空我的数据（公开多用户） ----------------
@app.route("/api/my_data", methods=["DELETE"])
def my_data():
    n = db.clear_owner_data(**get_owner())
    return jsonify({"ok": True, "cleared": n})


# ---------------- 官方信息源 / 考试目录 / 残疾人政策（对标公考雷达） ----------------
@app.route("/api/resources", methods=["GET"])
def resources():
    return jsonify({
        "sources": db.OFFICIAL_SOURCES,
        "exams": db.EXAM_CATALOG,
        "disability": db.DISABILITY_BENEFITS,
        "provinces": db.PROVINCE_ORDER,
    })


if __name__ == "__main__":
    # 默认 3000：与云端发布代理端口一致
    port = int(os.environ.get("PORT", 3000))
    print(f"小K万能工作台已启动 -> http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
