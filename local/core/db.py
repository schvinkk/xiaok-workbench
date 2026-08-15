"""
小凯求职工作台 —— 数据层 (SQLite)
本地/云端通用，隐私自托管。

数据隔离模型（公开多用户 + 可选账户）：
- 未登录：按浏览器访客标识 visitor_id 隔离（各自简历/收藏/投递互不串）。
- 已登录：按 account_id 隔离（自选用户名，跨设备保存）。
- 任何"个人画像"默认都是中性空白，绝不预置主人专业，避免分享后泄漏。
- 职位池(jobs)为共享演示数据，不属于个人隐私。
"""
import hashlib
import json
import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "app.db")

# 中性默认画像：空白姓名/关键词，绝不预置"中药学"等主人资料，避免分享泄漏
NEUTRAL_USER_PROFILE = {
    "name": "",
    "target_title": "",
    "keywords": "",
    "city_name": "昆明",
    "city_boss_code": "101290100",   # BOSS 城市码（按所选城市自动映射）
    "city_58_pinyin": "kunming",     # 58同城城市拼音（按所选城市自动映射）
    "ollama_url": "http://localhost:11434",
    "ollama_model": "qwen3.6:35b-a3b",
    "ollama_enabled": False,
    "blacklist": "",
    "province": "云南",
    "education": "",
    "manual_major": "",        # 无简历时手动填写的筛选背景（跨会话记住）
    "manual_skills": "",
    "manual_keywords": "",
    "notify_enabled": False,   # 浏览器桌面提醒（临近备考节点）
    "followed_exams": [],      # 关注的考试（考试雷达），元素 {key,name,url,when,m}
    "daily_cap": 0,            # 每日最多投递数（0=不限制），防平台风控
}

# 四省州市：BOSS 城市码 + 58 同城拼音（用于 deep-link 自动映射；码为常用值，以平台实际为准）
# 省会排在第一位，作为该省默认城市。
PROVINCE_ORDER = ["云南", "贵州", "四川", "广西"]
PROVINCE_CITIES = {
    "云南": {
        "昆明":   {"boss": "101290100", "58": "kunming"},
        "曲靖":   {"boss": "101291000", "58": "qujing"},
        "玉溪":   {"boss": "101290800", "58": "yuxi"},
        "保山":   {"boss": "101292300", "58": "baoshan"},
        "昭通":   {"boss": "101291900", "58": "zhaotong"},
        "丽江":   {"boss": "101292400", "58": "lijiang"},
        "普洱":   {"boss": "101292800", "58": "puer"},
        "临沧":   {"boss": "101293000", "58": "lincang"},
        "楚雄":   {"boss": "101290600", "58": "chuxiong"},
        "红河":   {"boss": "101293400", "58": "honghe"},
        "文山":   {"boss": "101293700", "58": "wenshan"},
        "西双版纳": {"boss": "101292900", "58": "xishuangbanna"},
        "大理":   {"boss": "101290200", "58": "dali"},
        "德宏":   {"boss": "101293100", "58": "dehong"},
        "怒江":   {"boss": "101294000", "58": "nujiang"},
        "迪庆":   {"boss": "101294200", "58": "diqing"},
    },
    "贵州": {
        "贵阳":   {"boss": "101300100", "58": "guiyang"},
        "遵义":   {"boss": "101300200", "58": "zunyi"},
        "毕节":   {"boss": "101300500", "58": "bijie"},
        "黔南":   {"boss": "101300800", "58": "qiannan"},
        "黔东南": {"boss": "101300700", "58": "qiandongnan"},
        "铜仁":   {"boss": "101300600", "58": "tongren"},
        "安顺":   {"boss": "101300300", "58": "anshun"},
        "六盘水": {"boss": "101300400", "58": "liupanshui"},
        "黔西南": {"boss": "101300900", "58": "qianxinan"},
    },
    "四川": {
        "成都":   {"boss": "101270100", "58": "chengdu"},
        "绵阳":   {"boss": "101270200", "58": "mianyang"},
        "德阳":   {"boss": "101271400", "58": "deyang"},
        "宜宾":   {"boss": "101271100", "58": "yibin"},
        "泸州":   {"boss": "101271000", "58": "luzhou"},
        "南充":   {"boss": "101271600", "58": "nanchong"},
        "达州":   {"boss": "101271800", "58": "dazhou"},
        "乐山":   {"boss": "101270700", "58": "leshan"},
        "自贡":   {"boss": "101270300", "58": "zigong"},
        "攀枝花": {"boss": "101271500", "58": "panzhihua"},
        "遂宁":   {"boss": "101271200", "58": "suining"},
        "内江":   {"boss": "101270900", "58": "neijiang"},
        "凉山":   {"boss": "101272000", "58": "liangshan"},
        "眉山":   {"boss": "101270400", "58": "meishan"},
    },
    "广西": {
        "南宁":   {"boss": "101300100", "58": "nanning"},
        "柳州":   {"boss": "101300200", "58": "liuzhou"},
        "桂林":   {"boss": "101300400", "58": "guilin"},
        "北海":   {"boss": "101300500", "58": "beihai"},
        "玉林":   {"boss": "101300900", "58": "yulin"},
        "钦州":   {"boss": "101301100", "58": "qinzhou"},
        "防城港": {"boss": "101301000", "58": "fangchenggang"},
        "贵港":   {"boss": "101300700", "58": "guigang"},
        "百色":   {"boss": "101301300", "58": "baise"},
        "河池":   {"boss": "101301400", "58": "hechi"},
        "梧州":   {"boss": "101300600", "58": "wuzhou"},
        "崇左":   {"boss": "101301500", "58": "chongzuo"},
        "来宾":   {"boss": "101301200", "58": "laibin"},
        "贺州":   {"boss": "101300800", "58": "hezhou"},
    },
}
# 兼容旧引用
YUNNAN_CITIES = PROVINCE_CITIES["云南"]

# 平台注册表：分类 = 求职 / 考公考编 / 资格考试 / 考研
DEFAULT_PLATFORMS = [
    # 求职
    {"key": "boss", "name": "BOSS直聘", "color": "#F2C200", "icon": "💼", "category": "求职",
     "search_template": "https://www.zhipin.com/web/geek/job?query={kw}&city={boss}",
     "note": "官方搜索页（首次打开可能需登录/验证）"},
    {"key": "zhaopin", "name": "智联招聘", "color": "#2B6CFF", "icon": "🟦", "category": "求职",
     "search_template": "https://sou.zhaopin.com/?kw={kw}",
     "note": "关键词搜索，城市在站内筛选"},
    {"key": "liepin", "name": "猎聘", "color": "#1F9D55", "icon": "🟩", "category": "求职",
     "search_template": "https://www.liepin.com/zhaopin/?key={kw}",
     "note": "中高端，key=关键词"},
    {"key": "job58", "name": "58同城", "color": "#FF7A00", "icon": "🟧", "category": "求职",
     "search_template": "https://{58}.58.com/job/?key={kw}&final=1",
     "note": "蓝领/基层为主，城市拼音子域"},
    {"key": "guopin", "name": "国聘", "color": "#C8102E", "icon": "🏛️", "category": "求职",
     "search_template": "https://job.iguopin.com/search?keyword={kw}",
     "note": "央企国企招聘"},
    {"key": "yupao", "name": "鱼泡直聘", "color": "#00B4A0", "icon": "🐟", "category": "求职",
     "search_template": "https://www.yupao.com/search?keyword={kw}",
     "note": "工程/制造/物流"},
    {"key": "maimai", "name": "脉脉", "color": "#1B1F3B", "icon": "🔗", "category": "求职",
     "search_template": "https://maimai.cn/web/jobs?keyword={kw}",
     "note": "职场社交+内推"},
    {"key": "job51", "name": "前程无忧", "color": "#FF4D4F", "icon": "📋", "category": "求职",
     "search_template": "https://search.51job.com/list/000000,000000,0000,00,9,99,{kw},2,1.html",
     "note": "老牌综合站"},
    {"key": "lagou", "name": "拉勾", "color": "#00C2B3", "icon": "🌐", "category": "求职",
     "search_template": "https://www.lagou.com/wn/jobs?kd={kw}",
     "note": "互联网/技术"},

    # 考公考编
    {"key": "guokao", "name": "国家公务员局", "color": "#B22222", "icon": "🏛️", "category": "考公考编",
     "search_template": "https://bm.scs.gov.cn/pp/gkweb/core/web/ui/business/home/gkhome.html",
     "note": "国考职位表与报名入口"},
    {"key": "qgsydw", "name": "全国事业单位招聘网", "color": "#2E7D32", "icon": "📚", "category": "考公考编",
     "search_template": "https://www.qgsydw.com/",
     "note": "事业单位招聘公告聚合"},
    {"key": "ynsrs", "name": "云南人事考试网", "color": "#1565C0", "icon": "📝", "category": "考公考编",
     "search_template": "http://hrss.yn.gov.cn/ynrsksw/index.html",
     "note": "云南省考/事业编/资格考试官方入口"},
    {"key": "cpta", "name": "中国人事考试网", "color": "#D84315", "icon": "📜", "category": "考公考编",
     "search_template": "http://www.cpta.com.cn/",
     "note": "人事考试、执业药师等"},
    {"key": "chinazy", "name": "中央机关事业编平台", "color": "#6A1B9A", "icon": "🏢", "category": "考公考编",
     "search_template": "http://www.mohrss.gov.cn/SYrlzyhshbzb/fwyd/SYkaoshizhaopin/zyhgjjgsygw/",
     "note": "中央和国家机关所属事业单位公开招聘"},

    # 资格考试
    {"key": "wecan21", "name": "中国卫生人才网", "color": "#00838F", "icon": "⚕️", "category": "资格考试",
     "search_template": "https://www.21wecan.com/",
     "note": "中药士/主管药师等卫生资格考试报名"},
    {"key": "zyys", "name": "执业药师资格认证中心", "color": "#5E35B1", "icon": "💊", "category": "资格考试",
     "search_template": "https://www.cqlp.org/",
     "note": "执业药师考试政策与报名"},

    # 考研
    {"key": "chsi", "name": "研招网", "color": "#1565C0", "icon": "🎓", "category": "考研",
     "search_template": "https://yz.chsi.com.cn/",
     "note": "中国研究生招生信息网（报名/调剂/专业目录）"},
    {"key": "kaoyan", "name": "考研帮", "color": "#FF7043", "icon": "📖", "category": "考研",
     "search_template": "https://www.kaoyan.com/sou/?keyword={kw}",
     "note": "院校/专业/经验帖搜索"},
]

STATUSES = ["todo", "applied", "viewed", "interview", "offer", "rejected"]
STATUS_LABELS = {
    "todo": "待投递", "applied": "已投递", "viewed": "已读/跟进",
    "interview": "面试中", "offer": "已拿Offer", "rejected": "已拒绝",
}
CATEGORIES = ["求职", "考公考编", "资格考试", "考研"]

# 备考关键节点种子（已联网核实 2026-2027 周期；带"预计/以官方为准"的为推测日期）
SEED_MILESTONES = [
    # 考研（2027届）
    {"track": "考研", "title": "2027考研 正式报名", "date": "2026-10-15", "note": "预计10月中旬，研招网 yz.chsi.com.cn"},
    {"track": "考研", "title": "2027考研 网上确认", "date": "2026-11-05", "note": "11月上旬，各省级考试机构通知"},
    {"track": "考研", "title": "2027考研 初试", "date": "2026-12-19", "note": "12月19-21日（超过3小时科目在21日）"},
    {"track": "考研", "title": "2027考研 出分", "date": "2027-02-20", "note": "预计2月中下旬，随后公布国家线"},
    {"track": "考研", "title": "2027考研 复试/调剂", "date": "2027-03-20", "note": "3-4月各校组织，研招网调剂系统同步开"},
    # 考公考编
    {"track": "考公考编", "title": "2027国考 公告发布", "date": "2026-10-14", "note": "预计10月14日，bm.scs.gov.cn"},
    {"track": "考公考编", "title": "2027国考 网上报名", "date": "2026-10-15", "note": "10月15-24日，唯一入口 bm.scs.gov.cn"},
    {"track": "考公考编", "title": "2027国考 笔试", "date": "2026-11-29", "note": "11月28-29日（行测+申论）"},
    {"track": "考公考编", "title": "2027云南省考 笔试", "date": "2027-03-15", "note": "省考联考预计3月中旬，以 ynsrs 公告为准"},
    # 资格考试（中药士 / 执业药师）
    {"track": "资格考试", "title": "2026执业药师(云南) 报名", "date": "2026-08-04", "note": "云南考区8月4日09:00-14日17:00，紧迫！以 hrss.yn.gov.cn 为准"},
    {"track": "资格考试", "title": "2026执业药师 考试", "date": "2026-10-31", "note": "10月31日-11月1日（药事法规+综合等）"},
    {"track": "资格考试", "title": "2027中药士 网上报名", "date": "2026-12-20", "note": "通常12月-次年1月，中国卫生人才网 21wecan.com"},
    {"track": "资格考试", "title": "2027中药士 考试", "date": "2027-04-12", "note": "预计4月（卫生专业技术资格考试），以官方为准"},
    # 求职
    {"track": "求职", "title": "2026秋招 黄金启动期", "date": "2026-09-01", "note": "药企/国企秋招9月起，提前备好简历"},
    {"track": "求职", "title": "2027春招 补录期", "date": "2027-03-01", "note": "春招补录，考研落榜可同步投递"},
]


# 官方信息源（接通四省人社厅 / 人事考试网 / 招考院 + 国家部委 + 残联）
# 目的：对标"公考雷达"，把分散在各厅局的考试通知 / 政策福利入口集中到一处，打破信息差。
# 链接均为各官方站点首页或对应栏目（已联网核实 2026 年现行域名）。
OFFICIAL_SOURCES = [
    # 全国
    {"key": "scs", "name": "国家公务员局", "region": "全国", "kind": "国家部委", "url": "https://bm.scs.gov.cn", "note": "国考报名/公告唯一入口"},
    {"key": "cpta", "name": "中国人事考试网", "region": "全国", "kind": "国家部委", "url": "http://www.cpta.com.cn", "note": "各类执(职)业资格统考报名/成绩"},
    {"key": "mohrss", "name": "人力资源社会保障部", "region": "全国", "kind": "国家部委", "url": "http://www.mohrss.gov.cn", "note": "全国就业/社保/人事政策"},
    {"key": "yz", "name": "中国研究生招生信息网(研招网)", "region": "全国", "kind": "国家部委", "url": "https://yz.chsi.com.cn", "note": "考研报名/调剂/录取"},
    {"key": "cdpf", "name": "中国残疾人联合会", "region": "全国", "kind": "残联", "url": "https://www.cdpf.org.cn", "note": "全国残疾人政策/就业服务"},
    # 云南
    {"key": "yn_hrss", "name": "云南省人力资源和社会保障厅", "region": "云南", "kind": "人社厅", "url": "http://hrss.yn.gov.cn", "note": "云南考试/就业/人才政策"},
    {"key": "yn_ks", "name": "云南人事考试网", "region": "云南", "kind": "人事考试", "url": "https://hrss.yn.gov.cn/ynrsksw/", "note": "云南公务员/事业单位/资格考公告"},
    {"key": "yn_zk", "name": "云南省招生考试院", "region": "云南", "kind": "招考院", "url": "https://www.ynzs.cn", "note": "云南高考/专升本/自考"},
    {"key": "yn_cl", "name": "云南省残疾人联合会", "region": "云南", "kind": "残联", "url": "https://www.yncl.org.cn", "note": "云南残疾人就业/补贴政策"},
    # 贵州
    {"key": "gz_hrss", "name": "贵州省人力资源和社会保障厅", "region": "贵州", "kind": "人社厅", "url": "http://rst.guizhou.gov.cn", "note": "贵州考试/就业/人才政策"},
    {"key": "gz_ks", "name": "贵州人事考试信息网", "region": "贵州", "kind": "人事考试", "url": "https://www.gzrsks.com.cn/", "note": "贵州公务员/事业单位/资格考公告"},
    {"key": "gz_zk", "name": "贵州省招生考试院", "region": "贵州", "kind": "招考院", "url": "https://zsksy.guizhou.gov.cn", "note": "贵州高考/专升本/自考"},
    {"key": "gz_cl", "name": "贵州省残疾人联合会", "region": "贵州", "kind": "残联", "url": "http://www.gzsdpf.org.cn", "note": "贵州残疾人就业/补贴政策"},
    # 四川
    {"key": "sc_hrss", "name": "四川省人力资源和社会保障厅", "region": "四川", "kind": "人社厅", "url": "http://rst.sc.gov.cn", "note": "四川考试/就业/人才政策"},
    {"key": "sc_ks", "name": "四川省人事考试网", "region": "四川", "kind": "人事考试", "url": "https://www.scpta.com.cn/", "note": "四川公务员/事业单位/资格考公告"},
    {"key": "sc_zk", "name": "四川省教育考试院", "region": "四川", "kind": "招考院", "url": "https://www.sceea.cn", "note": "四川高考/专升本/自考"},
    {"key": "sc_cl", "name": "四川省残疾人联合会", "region": "四川", "kind": "残联", "url": "http://www.scdpf.org.cn", "note": "四川残疾人就业/补贴政策"},
    # 广西
    {"key": "gx_hrss", "name": "广西壮族自治区人力资源和社会保障厅", "region": "广西", "kind": "人社厅", "url": "http://rst.gxzf.gov.cn", "note": "广西考试/就业/人才政策"},
    {"key": "gx_ks", "name": "广西人事考试网", "region": "广西", "kind": "人事考试", "url": "https://www.gxpta.com.cn/", "note": "广西公务员/事业单位/资格考公告"},
    {"key": "gx_zk", "name": "广西招生考试院", "region": "广西", "kind": "招考院", "url": "https://www.gxeea.cn", "note": "广西高考/专升本/自考"},
    {"key": "gx_cl", "name": "广西壮族自治区残疾人联合会", "region": "广西", "kind": "残联", "url": "http://www.gxdpf.org.cn", "note": "广西残疾人就业/补贴政策"},
]

# 考试目录（对标公考雷达）：覆盖国家/部门正式组织、面向社会公开招考的主要考试
# 每条指向其官方报名/公告权威站点；时间以官方当年公告为准。
EXAM_CATALOG = [
    # 公务员
    {"name": "国家公务员考试(国考)", "cat": "公务员", "url": "https://bm.scs.gov.cn", "note": "每年10月报名、11月底笔试，应届生主战场"},
    {"name": "云南省考试录用公务员", "cat": "公务员", "url": "https://hrss.yn.gov.cn/ynrsksw/", "note": "联考省份，一般2-3月报名"},
    {"name": "贵州省考试录用公务员", "cat": "公务员", "url": "https://www.gzrsks.com.cn/", "note": "联考省份，一般2-3月报名"},
    {"name": "四川省考试录用公务员", "cat": "公务员", "url": "https://www.scpta.com.cn/", "note": "联考省份，一般2-3月报名"},
    {"name": "广西壮族自治区考试录用公务员", "cat": "公务员", "url": "https://www.gxpta.com.cn/", "note": "联考省份，一般2-3月报名"},
    {"name": "选调生(定向/普通)", "cat": "公务员", "url": "https://bm.scs.gov.cn", "note": "面向应届生，各省组织，关注人社厅/校招"},
    {"name": "公安/法检专项招录", "cat": "公务员", "url": "https://www.gxpta.com.cn/ksxm/gwyzlks/", "note": "法检助理、公安特殊岗，见各省人事考试网"},
    # 事业单位
    {"name": "各省事业单位统考/联考", "cat": "事业单位", "url": "https://hrss.yn.gov.cn/ynrsksw/", "note": "上半年(3-5月)与下半年多批次，见各省人事考试网"},
    {"name": "医疗卫生事业单位", "cat": "事业单位", "url": "https://www.21wecan.com", "note": "医院/疾控招聘，部分走卫生人才网"},
    {"name": "军队文职人员招考", "cat": "事业单位", "url": "http://81rc.81.cn", "note": "全军招考，一般12月-次年1月报名"},
    # 教师
    {"name": "教师资格证(笔试/面试)", "cat": "教师", "url": "https://ntce.neea.edu.cn", "note": "每年3月、9月笔试，需对应学历"},
    {"name": "特岗教师", "cat": "教师", "url": "https://hrss.yn.gov.cn/ynrsksw/", "note": "基层支教，应届/往届可报，关注各省公告"},
    {"name": "教师招聘(事业单位教师岗)", "cat": "教师", "url": "https://hrss.yn.gov.cn/ynrsksw/", "note": "随事业单位统考，学科对口"},
    # 基层项目
    {"name": "三支一扶", "cat": "基层项目", "url": "http://www.mohrss.gov.cn", "note": "支农/支教/支医/帮扶乡村振兴，应届为主"},
    {"name": "大学生志愿服务西部计划", "cat": "基层项目", "url": "http://www.mohrss.gov.cn", "note": "团中央/人社组织，服务西部基层"},
    {"name": "社区工作者", "cat": "基层项目", "url": "https://hrss.yn.gov.cn/ynrsksw/", "note": "街道/社区招考，大专起可报"},
    # 国企央企
    {"name": "国家电网招聘", "cat": "国企央企", "url": "https://zhaopin.sgcc.com.cn", "note": "一批(11月)/二批(3月)，电工类为主"},
    {"name": "南方电网招聘", "cat": "国企央企", "url": "https://zhaopin.csg.cn", "note": "秋招/春招，电气/通信/财会"},
    {"name": "国家烟草专卖(中烟)", "cat": "国企央企", "url": "http://www.tobacco.gov.cn", "note": "各省中烟/烟草专卖局，关注省局公告"},
    {"name": "国有银行(六大行/政策性)", "cat": "国企央企", "url": "http://www.pbc.gov.cn", "note": "人行+六大行秋招(9-10月)，专业不限岗多"},
    {"name": "铁路局及央企总部", "cat": "国企央企", "url": "http://www.china-railway.com.cn", "note": "各铁路局、央企官网招聘栏"},
    {"name": "国资委央企招聘(国资小新)", "cat": "国企央企", "url": "https://www.sasac.gov.cn", "note": "央企校招集中发布"},
    # 医疗健康
    {"name": "执业医师资格", "cat": "医疗健康", "url": "https://www.nmec.org.cn", "note": "临床/中医/口腔，本科及以上"},
    {"name": "护士执业资格", "cat": "医疗健康", "url": "https://www.nmec.org.cn", "note": "大专及以上护理专业"},
    {"name": "执业药师", "cat": "医疗健康", "url": "http://www.cqlp.org", "note": "药学/中药学，大专起(需工作年限)"},
    {"name": "卫生专业技术资格(中药士等)", "cat": "医疗健康", "url": "https://www.21wecan.com", "note": "药/护/技初/中级，对应学历+年限"},
    # 资格证
    {"name": "法律职业资格(法考)", "cat": "资格证", "url": "http://www.moj.gov.cn", "note": "法本/非法本+法律硕士等，客观+主观"},
    {"name": "注册会计师(CPA)", "cat": "资格证", "url": "https://www.cicpa.org.cn", "note": "大专及以上，6科"},
    {"name": "会计(初/中/高级)", "cat": "资格证", "url": "http://kzp.mof.gov.cn", "note": "初级高中起，中级大专+年限"},
    {"name": "一级/二级建造师", "cat": "资格证", "url": "https://www.pqrc.org.cn", "note": "工程类，对应学历+工作年限"},
    {"name": "计算机技术与软件(软考)", "cat": "资格证", "url": "https://www.ruankao.org.cn", "note": "不限学历，初/中/高级"},
    {"name": "翻译专业资格(CATTI)", "cat": "资格证", "url": "http://www.catticenter.com", "note": "外语相关，各级"},
    {"name": "经济专业技术资格", "cat": "资格证", "url": "http://www.cpta.com.cn", "note": "初/中/高级，对应学历+年限"},
    # 考研
    {"name": "全国硕士研究生统考", "cat": "考研", "url": "https://yz.chsi.com.cn", "note": "12月笔试，9-10月报名"},
    # 其他
    {"name": "社会工作者职业资格", "cat": "其他", "url": "https://www.cpta.com.cn", "note": "民政系统，初/中/高级"},
]

# 考试近似时间（用于"考试雷达"按最近排序；m=1-12 为大致月份，13=时间不定）
# 以官方当年公告为准，这里只做"大概什么时候"的排序参考。
EXAM_WHEN = {
    "国家公务员考试(国考)": (10, "每年10月报名、11月底笔试"),
    "云南省考试录用公务员": (2, "联考省份，一般2-3月报名"),
    "贵州省考试录用公务员": (2, "联考省份，一般2-3月报名"),
    "四川省考试录用公务员": (2, "联考省份，一般2-3月报名"),
    "广西壮族自治区考试录用公务员": (2, "联考省份，一般2-3月报名"),
    "选调生(定向/普通)": (11, "定向11-12月，普通随省考"),
    "公安/法检专项招录": (2, "随省考/专项公告"),
    "各省事业单位统考/联考": (3, "上半年3-5月为主，下半年也有"),
    "医疗卫生事业单位": (3, "随事业单位统考/医院自主招聘"),
    "军队文职人员招考": (12, "一般12月-次年1月报名"),
    "教师资格证(笔试/面试)": (3, "每年3月、9月笔试"),
    "特岗教师": (5, "一般5-6月报名"),
    "教师招聘(事业单位教师岗)": (3, "随事业单位统考"),
    "三支一扶": (5, "一般5-6月报名"),
    "大学生志愿服务西部计划": (4, "一般4-5月报名"),
    "社区工作者": (6, "各地不一，多在上半年"),
    "国家电网招聘": (11, "一批11月、二批3月"),
    "南方电网招聘": (10, "秋招9-10月、春招3-4月"),
    "国家烟草专卖(中烟)": (10, "秋招9-11月"),
    "国有银行(六大行/政策性)": (9, "秋招9-10月"),
    "铁路局及央企总部": (9, "秋招9-11月"),
    "国资委央企招聘(国资小新)": (9, "央企校招9-11月集中"),
    "执业医师资格": (1, "实践1月、综合8月；报名前一年底"),
    "护士执业资格": (4, "一般4-5月考试"),
    "执业药师": (8, "一般8月报名、10月考试"),
    "卫生专业技术资格(中药士等)": (12, "一般12月报名、次年4月考试"),
    "法律职业资格(法考)": (6, "客观6月、主观9月"),
    "注册会计师(CPA)": (4, "一般4月报名、8月考试"),
    "会计(初/中/高级)": (1, "一般1月报名、5月考试"),
    "一级/二级建造师": (2, "一般2-3月报名、6月考试"),
    "计算机技术与软件(软考)": (5, "每年5月、11月考试"),
    "翻译专业资格(CATTI)": (5, "每年6月、11月考试"),
    "经济专业技术资格": (7, "初中级7月报名、11月考试"),
    "全国硕士研究生统考": (10, "12月笔试、9-10月报名"),
    "社会工作者职业资格": (8, "一般8月报名、10月考试"),
}
for _e in EXAM_CATALOG:
    _w = EXAM_WHEN.get(_e["name"])
    _e["m"] = _w[0] if _w else 13
    _e["when"] = _w[1] if _w else "以官方当年公告为准"

# 残疾人政策福利（单独通道）：可按学历筛选可报考/可享政策
# edu: 不限 / 大专 / 本科 / 硕士 / 博士（含更高学历可享更低门槛）
DISABILITY_BENEFITS = [
    {"title": "残疾人就业补贴(超比例安排就业奖励/社保补贴)", "edu": "不限", "region": "全国", "url": "https://www.cdpf.org.cn", "note": "按比例安排残疾人就业，超比例单位有奖励，残联/人社落实"},
    {"title": "困难残疾人生活补贴 + 重度残疾人护理补贴(两项补贴)", "edu": "不限", "region": "全国", "url": "https://www.cdpf.org.cn", "note": "低保内困难残疾、重度残疾均可申领，户籍地残联办理"},
    {"title": "残疾人免费职业技能培训", "edu": "不限", "region": "全国", "url": "https://www.cdpf.org.cn", "note": "残联组织电商/手工/按摩等培训，免费"},
    {"title": "公务员/事业单位残疾人专项招录(专岗)", "edu": "大专", "region": "全国", "url": "https://bm.scs.gov.cn", "note": "国考/省考设残疾人专岗，大专起，看职位表"},
    {"title": "残疾人创业担保贷款 + 财政贴息", "edu": "不限", "region": "全国", "url": "http://www.mohrss.gov.cn", "note": "自主创业可申创业担保贷款，财政贴息"},
    {"title": "残疾人就业保障金(残保金)减免/缓缴", "edu": "不限", "region": "全国", "url": "http://www.mohrss.gov.cn", "note": "用人单位安排残疾人可减免残保金"},
    {"title": "高校残疾人毕业生专场招聘(应届)", "edu": "本科", "region": "全国", "url": "https://www.cdpf.org.cn", "note": "残联+高校联合，应届残疾大学生优先"},
    {"title": "云南：残疾人按比例就业联网认证", "edu": "不限", "region": "云南", "url": "https://www.yncl.org.cn", "note": "认证安排残疾就业情况，享相关优惠"},
    {"title": "云南：扶残助学/阳光助学", "edu": "不限", "region": "云南", "url": "https://www.yncl.org.cn", "note": "残疾学生及残疾人子女助学资助"},
    {"title": "贵州：残疾人创业就业扶持", "edu": "不限", "region": "贵州", "url": "http://www.gzsdpf.org.cn", "note": "创业补贴、盲人按摩扶持等"},
    {"title": "四川：残疾人就业服务", "edu": "不限", "region": "四川", "url": "http://www.scdpf.org.cn", "note": "职业培训、辅助器具、就业援助"},
    {"title": "广西：残疾人就业援助/补贴", "edu": "不限", "region": "广西", "url": "http://www.gxdpf.org.cn", "note": "就业补贴、农村残疾人产业扶持"},
]


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _conn():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=8000")  # 容忍短暂写锁，避免 database is locked
    return conn


def init_db():
    conn = _conn()
    c = conn.cursor()
    # 个人画像（按用户隔离）：account_id / visitor_id 二选一标识归属
    c.execute("""CREATE TABLE IF NOT EXISTS user_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER,
        visitor_id TEXT,
        data TEXT,
        UNIQUE(account_id, visitor_id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        salt TEXT,
        pass_hash TEXT,
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS account_tokens (
        token TEXT PRIMARY KEY,
        account_id INTEGER,
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER,
        visitor_id TEXT,
        name TEXT, filename TEXT, path TEXT,
        text TEXT, parsed TEXT,
        is_default INTEGER DEFAULT 0, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS platforms (
        key TEXT PRIMARY KEY, name TEXT, color TEXT, icon TEXT,
        enabled INTEGER DEFAULT 1, search_template TEXT, note TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform_key TEXT, title TEXT, company TEXT, city TEXT,
        salary TEXT, url TEXT, description TEXT, source TEXT,
        created_at TEXT, status TEXT DEFAULT 'todo',
        applied_at TEXT, resume_used TEXT, match_score INTEGER,
        notes TEXT, blacklisted INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS app_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER, status TEXT, changed_at TEXT, note TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS milestones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        track TEXT, title TEXT, date TEXT, note TEXT,
        done INTEGER DEFAULT 0, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS deliveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER,
        visitor_id TEXT,
        job_id INTEGER, track TEXT, platform_key TEXT,
        title TEXT, company TEXT, city TEXT, url TEXT,
        resume_used TEXT, note TEXT, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS saved_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER,
        visitor_id TEXT,
        job_id INTEGER, title TEXT, company TEXT,
        platform_key TEXT, city TEXT, url TEXT, created_at TEXT
    )""")
    # 计划打卡（万能工作台通用模块）：计划 / 任务 / 打卡记录，均按 owner 隔离
    c.execute("""CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER,
        visitor_id TEXT,
        title TEXT, goal TEXT, smart INTEGER DEFAULT 0,
        start_date TEXT, target_date TEXT, status TEXT DEFAULT 'active',
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS plan_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER, content TEXT, due_date TEXT, sort_idx INTEGER DEFAULT 0,
        done INTEGER DEFAULT 0, done_at TEXT, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS plan_checkins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER, date TEXT, note TEXT, created_at TEXT
    )""")
    # 迁移：兼容旧库（曾有 visitor_id 单列、无 account_id 的库）
    for tbl in ("resumes", "saved_jobs", "deliveries"):
        try:
            c.execute(f"ALTER TABLE {tbl} ADD COLUMN account_id INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute(f"ALTER TABLE {tbl} ADD COLUMN visitor_id TEXT")
        except sqlite3.OperationalError:
            pass
    # 迁移：给 platforms 增加 category 列
    try:
        c.execute("ALTER TABLE platforms ADD COLUMN category TEXT DEFAULT '求职'")
    except sqlite3.OperationalError:
        pass
    # 迁移：给 deliveries 增加 follow_at 列（跟进提醒日期）
    try:
        c.execute("ALTER TABLE deliveries ADD COLUMN follow_at TEXT")
    except sqlite3.OperationalError:
        pass
    # 迁移：用最新默认平台配置刷新已存在行（search_template/note 等系统字段），
    # 同时补齐缺失平台；用户自定义的新增平台（key 不在默认表）与 enabled 开关均保留。
    for p in DEFAULT_PLATFORMS:
        c.execute("""UPDATE platforms SET
            name=?, color=?, icon=?, category=?, search_template=?, note=?
            WHERE key=?""",
            (p["name"], p["color"], p["icon"], p["category"],
             p["search_template"], p["note"], p["key"]))
    existing = {r["key"] for r in c.execute("SELECT key FROM platforms").fetchall()}
    for p in DEFAULT_PLATFORMS:
        if p["key"] not in existing:
            c.execute("""INSERT INTO platforms
                (key,name,color,icon,category,enabled,search_template,note)
                VALUES (?,?,?,?,?,1,?,?)""",
                (p["key"], p["name"], p["color"], p["icon"], p["category"],
                 p["search_template"], p["note"]))
    # 首次启动注入备考关键节点种子
    c.execute("SELECT COUNT(*) AS n FROM milestones")
    if c.fetchone()["n"] == 0:
        for m in SEED_MILESTONES:
            c.execute("""INSERT INTO milestones (track,title,date,note,done,created_at)
                VALUES (?,?,?,?,0,?)""",
                (m["track"], m["title"], m["date"], m["note"], now()))
    conn.commit()
    conn.close()


# ---------- 个人画像（按用户隔离，中性默认） ----------
def get_user_profile(account_id: int = None, visitor_id: str = None):
    """返回某用户的画像；无记录时返回中性默认（绝不预置主人专业）。
    取最新一行（id 最大），避免历史重复行干扰。"""
    conn = _conn(); c = conn.cursor()
    row = None
    if account_id:
        row = c.execute("SELECT data FROM user_profiles WHERE account_id=? AND visitor_id IS NULL ORDER BY id DESC LIMIT 1",
                        (account_id,)).fetchone()
    elif visitor_id:
        row = c.execute("SELECT data FROM user_profiles WHERE visitor_id=? AND account_id IS NULL ORDER BY id DESC LIMIT 1",
                        (visitor_id,)).fetchone()
    conn.close()
    if row and row["data"]:
        d = json.loads(row["data"])
        base = dict(NEUTRAL_USER_PROFILE)
        base.update(d)
        return base
    return dict(NEUTRAL_USER_PROFILE)


def save_user_profile(data: dict, account_id: int = None, visitor_id: str = None):
    """更新画像。SQLite 中 UNIQUE(account_id, visitor_id) 在 account_id 为 NULL 时
    不会去重（NULL 互不相等），故改用「先 UPDATE、无则 INSERT」并清理重复行。"""
    conn = _conn(); c = conn.cursor()
    cur = get_user_profile(account_id=account_id, visitor_id=visitor_id)
    cur.update({k: v for k, v in data.items() if k in NEUTRAL_USER_PROFILE})
    payload = json.dumps(cur, ensure_ascii=False)
    if account_id:
        c.execute("UPDATE user_profiles SET data=? WHERE account_id=? AND visitor_id IS NULL", (payload, account_id))
        if c.rowcount == 0:
            c.execute("INSERT INTO user_profiles (account_id, visitor_id, data) VALUES (?,NULL,?)", (account_id, payload))
        else:
            c.execute("DELETE FROM user_profiles WHERE account_id=? AND visitor_id IS NULL AND id < (SELECT MAX(id) FROM user_profiles WHERE account_id=? AND visitor_id IS NULL)", (account_id, account_id))
    else:
        c.execute("UPDATE user_profiles SET data=? WHERE visitor_id=? AND account_id IS NULL", (payload, visitor_id))
        if c.rowcount == 0:
            c.execute("INSERT INTO user_profiles (account_id, visitor_id, data) VALUES (NULL,?,?)", (visitor_id, payload))
        else:
            c.execute("DELETE FROM user_profiles WHERE visitor_id=? AND account_id IS NULL AND id < (SELECT MAX(id) FROM user_profiles WHERE visitor_id=? AND account_id IS NULL)", (visitor_id, visitor_id))
    conn.commit(); conn.close()
    return cur


# ---------- 账户（可选登录，本地保存进度） ----------
def _hash_pw(password: str, salt: str):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                               salt.encode("utf-8"), 100000).hex()


def create_account(username: str, password: str):
    """创建账户；用户名已存在返回 (None, 'exists')。"""
    username = (username or "").strip()
    if not username or not password:
        return None, "用户名和密码不能为空"
    if len(password) < 4:
        return None, "密码至少 4 位"
    conn = _conn(); c = conn.cursor()
    if c.execute("SELECT id FROM accounts WHERE username=?", (username,)).fetchone():
        conn.close(); return None, "该用户名已被占用"
    import secrets
    salt = secrets.token_hex(8)
    h = _hash_pw(password, salt)
    c.execute("INSERT INTO accounts (username,salt,pass_hash,created_at) VALUES (?,?,?,?)",
              (username, salt, h, now()))
    aid = c.lastrowid
    conn.commit(); conn.close()
    return aid, None


def verify_account(username: str, password: str):
    conn = _conn(); c = conn.cursor()
    r = c.execute("SELECT id,salt,pass_hash FROM accounts WHERE username=?",
                  ((username or "").strip(),)).fetchone()
    conn.close()
    if not r:
        return None
    if _hash_pw(password, r["salt"]) == r["pass_hash"]:
        return r["id"]
    return None


def issue_token(account_id: int):
    import secrets
    tok = secrets.token_hex(24)
    conn = _conn(); c = conn.cursor()
    c.execute("INSERT INTO account_tokens (token,account_id,created_at) VALUES (?,?,?)",
              (tok, account_id, now()))
    conn.commit(); conn.close()
    return tok


def account_by_token(token: str):
    if not token:
        return None
    conn = _conn(); c = conn.cursor()
    r = c.execute("SELECT account_id FROM account_tokens WHERE token=?", (token,)).fetchone()
    conn.close()
    return r["account_id"] if r else None


def username_of(account_id: int):
    conn = _conn(); c = conn.cursor()
    r = c.execute("SELECT username FROM accounts WHERE id=?", (account_id,)).fetchone()
    conn.close()
    return r["username"] if r else None


def revoke_token(token: str):
    conn = _conn(); c = conn.cursor()
    c.execute("DELETE FROM account_tokens WHERE token=?", (token,))
    conn.commit(); conn.close()


def merge_visitor_to_account(visitor_id: str, account_id: int):
    """登录时把匿名访客的数据并入账户（避免重复劳动、避免退出后"数据没了"）。

    覆盖全部按 owner 隔离的表：简历 / 收藏 / 投递 / 计划打卡 / 个人画像
    （含考试关注、省份设置等）。全局共享表（职位池、考试目录、里程碑）不在此列。
    """
    if not visitor_id:
        return
    conn = _conn(); c = conn.cursor()
    # 带 owner 列的明细表：直接改归属
    for tbl in ("resumes", "saved_jobs", "deliveries", "plans"):
        c.execute(f"UPDATE {tbl} SET account_id=?, visitor_id=NULL WHERE visitor_id=? AND account_id IS NULL",
                  (account_id, visitor_id))
    # 个人画像：account_id 唯一约束 (account_id, visitor_id)，仅当账户尚无画像时并入访客画像，
    # 避免触发 UNIQUE 冲突（账户已有画像则保留账户侧，不覆盖）。
    c.execute(
        """UPDATE user_profiles SET account_id=?, visitor_id=NULL
           WHERE visitor_id=? AND account_id IS NULL
             AND NOT EXISTS (SELECT 1 FROM user_profiles WHERE account_id=? AND visitor_id IS NULL)""",
        (account_id, visitor_id, account_id))
    conn.commit(); conn.close()


# ---------- Resumes ----------
def _owner_sql(account_id, visitor_id):
    if account_id:
        return "account_id=?", (account_id,)
    return "visitor_id=?", (visitor_id,)


def resume_completeness(pp: dict):
    """简历完整度 0-100：姓名/专业/手机/邮箱/学历/技能≥3 六项各 1/6。"""
    checks = [
        bool(pp.get("name")), bool(pp.get("major")),
        bool(pp.get("phone")), bool(pp.get("email")),
        bool(pp.get("degrees")), (len(pp.get("skills") or []) >= 3),
    ]
    return round(sum(checks) / len(checks) * 100)


def list_resumes(account_id: int = None, visitor_id: str = None):
    conn = _conn(); c = conn.cursor()
    frag, params = _owner_sql(account_id, visitor_id)
    rows = c.execute(
        f"SELECT id,name,filename,is_default,created_at,parsed FROM resumes WHERE {frag} ORDER BY created_at DESC",
        params).fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        try:
            pp = json.loads(r["parsed"])
        except Exception:
            pp = {}
        d["major"] = pp.get("major") or ""
        d["skills"] = pp.get("skills") or []
        d["skills_count"] = len(d["skills"])
        d["completeness"] = resume_completeness(pp)
        out.append(d)
    return out


def add_resume(name, filename, path, text, parsed, account_id: int = None, visitor_id: str = None):
    conn = _conn(); c = conn.cursor()
    c.execute("""INSERT INTO resumes (account_id,visitor_id,name,filename,path,text,parsed,is_default,created_at)
        VALUES (?,?,?,?,?,?,?,0,?)""",
        (account_id, visitor_id, name, filename, path, text,
         json.dumps(parsed, ensure_ascii=False), now()))
    rid = c.lastrowid
    conn.commit(); conn.close()
    return rid


def get_resume(rid):
    conn = _conn(); c = conn.cursor()
    r = c.execute("SELECT * FROM resumes WHERE id=?", (rid,)).fetchone()
    conn.close()
    return dict(r) if r else None


def latest_resume(account_id: int = None, visitor_id: str = None):
    """当前用户最近上传的简历（严格按 owner，不外溢到其他用户）。无则返回 None。"""
    conn = _conn(); c = conn.cursor()
    frag, params = _owner_sql(account_id, visitor_id)
    r = c.execute(f"SELECT * FROM resumes WHERE {frag} ORDER BY id DESC LIMIT 1", params).fetchone()
    conn.close()
    return dict(r) if r else None


def default_resume(account_id: int = None, visitor_id: str = None):
    """当前用户的默认简历（is_default=1）；无默认时回退到最近上传的。无则返回 None。"""
    conn = _conn(); c = conn.cursor()
    frag, params = _owner_sql(account_id, visitor_id)
    r = c.execute(f"SELECT * FROM resumes WHERE {frag} AND is_default=1 LIMIT 1", params).fetchone()
    if not r:
        r = c.execute(f"SELECT * FROM resumes WHERE {frag} ORDER BY id DESC LIMIT 1", params).fetchone()
    conn.close()
    return dict(r) if r else None


def delete_resume(rid):
    conn = _conn(); c = conn.cursor()
    r = c.execute("SELECT path FROM resumes WHERE id=?", (rid,)).fetchone()
    if r and r["path"] and os.path.exists(r["path"]):
        try: os.remove(r["path"])
        except Exception: pass
    c.execute("DELETE FROM resumes WHERE id=?", (rid,))
    conn.commit(); conn.close()


def set_default_resume(rid):
    conn = _conn(); c = conn.cursor()
    c.execute("UPDATE resumes SET is_default=0")
    c.execute("UPDATE resumes SET is_default=1 WHERE id=?", (rid,))
    conn.commit(); conn.close()


# ---------- Platforms ----------
def list_platforms(category: str = None):
    conn = _conn(); c = conn.cursor()
    if category:
        rows = c.execute("SELECT * FROM platforms WHERE category=? ORDER BY rowid", (category,)).fetchall()
    else:
        rows = c.execute("SELECT * FROM platforms ORDER BY category,rowid").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_platform(key, fields: dict):
    conn = _conn(); c = conn.cursor()
    allowed = {"name", "color", "icon", "enabled", "search_template", "note", "category"}
    sets = {k: v for k, v in fields.items() if k in allowed}
    if not sets:
        conn.close(); return
    sql = "UPDATE platforms SET " + ",".join(f"{k}=?" for k in sets) + " WHERE key=?"
    c.execute(sql, list(sets.values()) + [key])
    conn.commit(); conn.close()


# ---------- Jobs ----------
def list_jobs(filters: dict = None):
    conn = _conn(); c = conn.cursor()
    sql = "SELECT * FROM jobs"
    where, params = [], []
    if filters:
        if filters.get("platform"):
            where.append("platform_key=?"); params.append(filters["platform"])
        if filters.get("status"):
            where.append("status=?"); params.append(filters["status"])
        if filters.get("q"):
            where.append("(title LIKE ? OR company LIKE ? OR description LIKE ?)")
            params += ["%"+filters["q"]+"%"]*3
        if filters.get("category"):
            where.append("platform_key IN (SELECT key FROM platforms WHERE category=?)")
            params.append(filters["category"])
        if filters.get("city") and filters.get("city") != "全省":
            where.append("city LIKE ?")
            params.append("%"+filters["city"]+"%")
        elif filters.get("province"):
            # 选了省份但未指定具体城市时，只看该省岗位（城市码在四省表中）
            cities = list(PROVINCE_CITIES.get(filters["province"], {}).keys())
            if cities:
                ph = ",".join("?" * len(cities))
                where.append(f"city IN ({ph})")
                params += cities
        if filters.get("blacklisted") is not None:
            where.append("blacklisted=?")
            params.append(1 if filters["blacklisted"] else 0)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC"
    rows = c.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_job(d: dict):
    conn = _conn(); c = conn.cursor()
    c.execute("""INSERT INTO jobs
        (platform_key,title,company,city,salary,url,description,source,created_at,status)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (d.get("platform_key"), d.get("title"), d.get("company"), d.get("city"),
         d.get("salary"), d.get("url"), d.get("description"), d.get("source", "manual"),
         now(), d.get("status", "todo")))
    jid = c.lastrowid
    conn.commit(); conn.close()
    return jid


def get_job(jid):
    conn = _conn(); c = conn.cursor()
    r = c.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
    conn.close()
    return dict(r) if r else None


def update_job(jid, fields: dict):
    conn = _conn(); c = conn.cursor()
    allowed = {"title", "company", "city", "salary", "url", "description",
               "status", "applied_at", "resume_used", "match_score", "notes", "blacklisted"}
    sets = {k: v for k, v in fields.items() if k in allowed}
    if "status" in sets and sets["status"] not in STATUSES:
        sets["status"] = "todo"
    if not sets:
        conn.close(); return
    if "status" in sets:
        c.execute("INSERT INTO app_history (job_id,status,changed_at,note) VALUES (?,?,?,?)",
                  (jid, sets["status"], now(), sets.get("note", "")))
        if sets["status"] == "applied" and not sets.get("applied_at"):
            sets["applied_at"] = now()
    sql = "UPDATE jobs SET " + ",".join(f"{k}=?" for k in sets) + " WHERE id=?"
    c.execute(sql, list(sets.values()) + [jid])
    conn.commit(); conn.close()


def delete_job(jid):
    conn = _conn(); c = conn.cursor()
    c.execute("DELETE FROM app_history WHERE job_id=?", (jid,))
    c.execute("DELETE FROM jobs WHERE id=?", (jid,))
    conn.commit(); conn.close()


def set_blacklist(jid, val: bool):
    update_job(jid, {"blacklisted": 1 if val else 0})


def import_jobs(jobs: list):
    ids = []
    for d in jobs:
        if d.get("title"):
            ids.append(add_job(d))
    return ids


def stats(account_id: int = None, visitor_id: str = None):
    conn = _conn(); c = conn.cursor()
    total = c.execute("SELECT COUNT(*) AS n FROM jobs").fetchone()["n"]
    by_status = {}
    for s in STATUSES:
        by_status[s] = c.execute("SELECT COUNT(*) AS n FROM jobs WHERE status=?", (s,)).fetchone()["n"]
    by_platform = {}
    for r in c.execute("SELECT platform_key, COUNT(*) AS n FROM jobs GROUP BY platform_key"):
        by_platform[r["platform_key"]] = r["n"]
    by_category = {}
    for r in c.execute("""SELECT COALESCE(p.category,'求职') AS cat, COUNT(*) AS n
                           FROM jobs j LEFT JOIN platforms p ON j.platform_key=p.key
                           GROUP BY cat"""):
        by_category[r["cat"]] = r["n"]
    applied = by_status["applied"] + by_status["viewed"] + by_status["interview"] + by_status["offer"]
    offers = by_status["offer"]
    frag, params = _owner_sql(account_id, visitor_id)
    deliveries = c.execute(f"SELECT COUNT(*) AS n FROM deliveries WHERE {frag}", params).fetchone()["n"]
    saved = c.execute(f"SELECT COUNT(*) AS n FROM saved_jobs WHERE {frag}", params).fetchone()["n"]
    ms_total = c.execute("SELECT COUNT(*) AS n FROM milestones").fetchone()["n"]
    ms_done = c.execute("SELECT COUNT(*) AS n FROM milestones WHERE done=1").fetchone()["n"]
    conn.close()
    return {"total": total, "by_status": by_status,
            "by_platform": by_platform, "by_category": by_category,
            "applied": applied, "offers": offers,
            "deliveries": deliveries, "saved": saved,
            "ms_total": ms_total, "ms_done": ms_done}


def export_data(account_id: int = None, visitor_id: str = None):
    return {
        "profile": get_user_profile(account_id=account_id, visitor_id=visitor_id),
        "platforms": list_platforms(),
        "resumes_meta": list_resumes(account_id=account_id, visitor_id=visitor_id),
        "jobs": list_jobs(),
        "exported_at": now(),
    }


def reset_demo():
    conn = _conn(); c = conn.cursor()
    c.execute("DELETE FROM app_history")
    c.execute("DELETE FROM jobs")
    conn.commit(); conn.close()


# ---------- Milestones（备考关键节点） ----------
def list_milestones(track: str = None):
    conn = _conn(); c = conn.cursor()
    if track:
        rows = c.execute("SELECT * FROM milestones WHERE track=? ORDER BY date", (track,)).fetchall()
    else:
        rows = c.execute("SELECT * FROM milestones ORDER BY date").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_milestone(d: dict):
    conn = _conn(); c = conn.cursor()
    c.execute("""INSERT INTO milestones (track,title,date,note,done,created_at)
        VALUES (?,?,?,?,?,?)""",
        (d.get("track", "考研"), d.get("title"), d.get("date"),
         d.get("note", ""), 1 if d.get("done") else 0, now()))
    mid = c.lastrowid
    conn.commit(); conn.close()
    return mid


def update_milestone(mid, fields: dict):
    conn = _conn(); c = conn.cursor()
    allowed = {"track", "title", "date", "note", "done"}
    sets = {k: (1 if v else 0) if k == "done" else v for k, v in fields.items() if k in allowed}
    if not sets:
        conn.close(); return
    sql = "UPDATE milestones SET " + ",".join(f"{k}=?" for k in sets) + " WHERE id=?"
    c.execute(sql, list(sets.values()) + [mid])
    conn.commit(); conn.close()


def delete_milestone(mid):
    conn = _conn(); c = conn.cursor()
    c.execute("DELETE FROM milestones WHERE id=?", (mid,))
    conn.commit(); conn.close()


def toggle_milestone(mid, val: bool):
    update_milestone(mid, {"done": 1 if val else 0})


# ---------- 投递记录（投递流水） ----------
def add_delivery(d: dict):
    conn = _conn(); c = conn.cursor()
    c.execute("""INSERT INTO deliveries
        (account_id,visitor_id,job_id,track,platform_key,title,company,city,url,resume_used,note,created_at,follow_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (d.get("account_id"), d.get("visitor_id"), d.get("job_id"), d.get("track"),
         d.get("platform_key"), d.get("title"), d.get("company"), d.get("city"),
         d.get("url"), d.get("resume_used"), d.get("note", ""),
         d.get("created_at") or now(), d.get("follow_at")))
    did = c.lastrowid
    if d.get("job_id"):
        jid = int(d["job_id"])
        c.execute("UPDATE jobs SET status=?, applied_at=?, resume_used=? WHERE id=?",
                  ("applied", now(), d.get("resume_used", ""), jid))
        c.execute("INSERT INTO app_history (job_id,status,changed_at,note) VALUES (?,?,?,?)",
                  (jid, "applied", now(), ""))
    conn.commit(); conn.close()
    return did


def update_delivery(did: int, **fields):
    """更新投递记录的可编辑字段（note / follow_at / title / company 等）。"""
    ALLOW = {"note", "follow_at", "title", "company", "city", "platform_key", "url", "resume_used"}
    sets = []; params = []
    for k, v in fields.items():
        if k in ALLOW:
            sets.append(f"{k}=?"); params.append(v)
    if not sets:
        return False
    conn = _conn(); c = conn.cursor()
    c.execute(f"UPDATE deliveries SET {', '.join(sets)} WHERE id=?", params + [int(did)])
    conn.commit(); conn.close()
    return True


def list_deliveries(track: str = None, platform: str = None, account_id: int = None, visitor_id: str = None):
    conn = _conn(); c = conn.cursor()
    where, params = [], []
    if track:
        where.append("track=?"); params.append(track)
    if platform:
        where.append("platform_key=?"); params.append(platform)
    frag, oparams = _owner_sql(account_id, visitor_id)
    where.append(frag); params += oparams
    sql = "SELECT * FROM deliveries"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC"
    rows = c.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_delivery(did):
    conn = _conn(); c = conn.cursor()
    c.execute("DELETE FROM deliveries WHERE id=?", (did,))
    conn.commit(); conn.close()


def delivery_exists(job_id):
    if not job_id:
        return False
    conn = _conn(); c = conn.cursor()
    n = c.execute("SELECT COUNT(*) AS n FROM deliveries WHERE job_id=?", (int(job_id),)).fetchone()["n"]
    conn.close()
    return n > 0


def owner_delivery_exists(job_id, account_id: int = None, visitor_id: str = None):
    """该用户是否已投递过这个岗位（去重用）。"""
    if not job_id:
        return False
    frag, params = _owner_sql(account_id, visitor_id)
    conn = _conn(); c = conn.cursor()
    n = c.execute(f"SELECT COUNT(*) AS n FROM deliveries WHERE {frag} AND job_id=?",
                  params + (int(job_id),)).fetchone()["n"]
    conn.close()
    return n > 0


def count_deliveries_today(account_id: int = None, visitor_id: str = None):
    """统计该用户今天（本地日期 YYYY-MM-DD）的投递次数，用于频率保护。"""
    frag, params = _owner_sql(account_id, visitor_id)
    today = now()[:10]
    conn = _conn(); c = conn.cursor()
    n = c.execute(f"SELECT COUNT(*) AS n FROM deliveries WHERE {frag} AND created_at LIKE ?",
                  params + (today + "%",)).fetchone()["n"]
    conn.close()
    return n


# ---------- 岗位收藏 ----------
def toggle_saved(d: dict):
    conn = _conn(); c = conn.cursor()
    existing = None
    jid = d.get("job_id")
    frag, params = _owner_sql(d.get("account_id"), d.get("visitor_id"))
    if jid:
        existing = c.execute(f"SELECT id FROM saved_jobs WHERE job_id=? AND {frag}",
                             (int(jid),) + params).fetchone()
    if existing:
        c.execute("DELETE FROM saved_jobs WHERE id=?", (existing["id"],))
        conn.commit(); conn.close()
        return {"saved": False, "id": existing["id"]}
    c.execute("""INSERT INTO saved_jobs
        (account_id,visitor_id,job_id,title,company,platform_key,city,url,created_at)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (d.get("account_id"), d.get("visitor_id"), jid, d.get("title"), d.get("company"),
         d.get("platform_key"), d.get("city"), d.get("url"), now()))
    sid = c.lastrowid
    conn.commit(); conn.close()
    return {"saved": True, "id": sid}


def list_saved(account_id: int = None, visitor_id: str = None):
    conn = _conn(); c = conn.cursor()
    frag, params = _owner_sql(account_id, visitor_id)
    rows = c.execute(f"SELECT * FROM saved_jobs WHERE {frag} ORDER BY created_at DESC", params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_saved(sid):
    conn = _conn(); c = conn.cursor()
    c.execute("DELETE FROM saved_jobs WHERE id=?", (sid,))
    conn.commit(); conn.close()


def clear_owner_data(account_id: int = None, visitor_id: str = None):
    """清空某用户的简历/收藏/投递（"清空我的数据"）。"""
    if not account_id and not visitor_id:
        return 0
    conn = _conn(); c = conn.cursor()
    frag, params = _owner_sql(account_id, visitor_id)
    for r in c.execute(f"SELECT path FROM resumes WHERE {frag}", params).fetchall():
        p = r["path"]
        if p and os.path.exists(p):
            try: os.remove(p)
            except Exception: pass
    n = 0
    c.execute(f"DELETE FROM resumes WHERE {frag}", params); n += c.execute("SELECT changes() AS n").fetchone()["n"]
    c.execute(f"DELETE FROM saved_jobs WHERE {frag}", params); n += c.execute("SELECT changes() AS n").fetchone()["n"]
    c.execute(f"DELETE FROM deliveries WHERE {frag}", params); n += c.execute("SELECT changes() AS n").fetchone()["n"]
    for pid in [r["id"] for r in c.execute(f"SELECT id FROM plans WHERE {frag}", params).fetchall()]:
        c.execute("DELETE FROM plan_tasks WHERE plan_id=?", (pid,))
        c.execute("DELETE FROM plan_checkins WHERE plan_id=?", (pid,))
    c.execute(f"DELETE FROM plans WHERE {frag}", params); n += c.execute("SELECT changes() AS n").fetchone()["n"]
    conn.commit(); conn.close()
    return n


# ---------- 计划打卡（万能工作台通用模块） ----------
def list_plans(account_id: int = None, visitor_id: str = None):
    conn = _conn(); c = conn.cursor()
    frag, params = _owner_sql(account_id, visitor_id)
    rows = c.execute(f"SELECT * FROM plans WHERE {frag} ORDER BY created_at DESC", params).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        done, total = plan_progress(d["id"])
        d["done"] = done; d["total"] = total
        d["streak"] = plan_streak(d["id"])
        d["checked_today"] = plan_checked_today(d["id"])
        out.append(d)
    conn.close()
    return out


def get_plan(pid, account_id: int = None, visitor_id: str = None):
    frag, params = _owner_sql(account_id, visitor_id)
    conn = _conn(); c = conn.cursor()
    r = c.execute(f"SELECT * FROM plans WHERE id=? AND {frag}", (pid,) + params).fetchone()
    if not r:
        conn.close(); return None
    d = dict(r)
    tasks = c.execute("SELECT * FROM plan_tasks WHERE plan_id=? ORDER BY sort_idx ASC, id ASC", (pid,)).fetchall()
    checkins = c.execute("SELECT date,note FROM plan_checkins WHERE plan_id=? ORDER BY date ASC", (pid,)).fetchall()
    conn.close()
    d["tasks"] = [dict(t) for t in tasks]
    d["checkins"] = [dict(x) for x in checkins]
    done, total = plan_progress(pid)
    d["done"] = done; d["total"] = total; d["streak"] = plan_streak(pid)
    d["checked_today"] = plan_checked_today(pid)
    return d


def add_plan(title, goal, smart, start_date, target_date, account_id: int = None, visitor_id: str = None):
    conn = _conn(); c = conn.cursor()
    c.execute("""INSERT INTO plans (account_id,visitor_id,title,goal,smart,start_date,target_date,status,created_at)
        VALUES (?,?,?,?,?,?,?,'active',?)""",
        (account_id, visitor_id, title, goal, 1 if smart else 0, start_date, target_date, now()))
    pid = c.lastrowid
    conn.commit(); conn.close()
    return pid


def delete_plan(pid, account_id: int = None, visitor_id: str = None):
    frag, params = _owner_sql(account_id, visitor_id)
    conn = _conn(); c = conn.cursor()
    c.execute(f"DELETE FROM plans WHERE id=? AND {frag}", (pid,) + params)
    if c.execute("SELECT changes() AS n").fetchone()["n"]:
        c.execute("DELETE FROM plan_tasks WHERE plan_id=?", (pid,))
        c.execute("DELETE FROM plan_checkins WHERE plan_id=?", (pid,))
    conn.commit(); conn.close()
    return True


def add_plan_task(plan_id, content, due_date=None, account_id: int = None, visitor_id: str = None):
    if not get_plan(plan_id, account_id, visitor_id):
        return None  # 越权/不存在
    conn = _conn(); c = conn.cursor()
    mx = c.execute("SELECT MAX(sort_idx) AS m FROM plan_tasks WHERE plan_id=?", (plan_id,)).fetchone()["m"] or 0
    c.execute("INSERT INTO plan_tasks (plan_id,content,due_date,sort_idx,created_at) VALUES (?,?,?,?,?)",
              (plan_id, content, due_date or "", mx + 1, now()))
    tid = c.lastrowid
    conn.commit(); conn.close()
    return tid


def toggle_plan_task(tid, account_id: int = None, visitor_id: str = None):
    conn = _conn(); c = conn.cursor()
    t = c.execute("SELECT * FROM plan_tasks WHERE id=?", (tid,)).fetchone()
    if not t:
        conn.close(); return None
    if not get_plan(t["plan_id"], account_id, visitor_id):
        conn.close(); return None  # 越权
    new = 0 if t["done"] else 1
    c.execute("UPDATE plan_tasks SET done=?, done_at=? WHERE id=?",
              (new, now() if new else None, tid))
    conn.commit(); conn.close()
    return new


def delete_plan_task(tid, account_id: int = None, visitor_id: str = None):
    conn = _conn(); c = conn.cursor()
    t = c.execute("SELECT * FROM plan_tasks WHERE id=?", (tid,)).fetchone()
    if not t:
        conn.close(); return False
    if not get_plan(t["plan_id"], account_id, visitor_id):
        conn.close(); return False
    c.execute("DELETE FROM plan_tasks WHERE id=?", (tid,))
    conn.commit(); conn.close()
    return True


def add_checkin(plan_id, date, note="", account_id: int = None, visitor_id: str = None):
    if not get_plan(plan_id, account_id, visitor_id):
        return None
    date = date or now()[:10]
    conn = _conn(); c = conn.cursor()
    ex = c.execute("SELECT id FROM plan_checkins WHERE plan_id=? AND date=?", (plan_id, date)).fetchone()
    if ex:
        c.execute("UPDATE plan_checkins SET note=? WHERE id=?", (note, ex["id"]))
    else:
        c.execute("INSERT INTO plan_checkins (plan_id,date,note,created_at) VALUES (?,?,?,?)",
                  (plan_id, date, note, now()))
    conn.commit(); conn.close()
    return True


def plan_checked_today(plan_id):
    from datetime import date as _d
    today = _d.today().strftime("%Y-%m-%d")
    conn = _conn(); c = conn.cursor()
    r = c.execute("SELECT id FROM plan_checkins WHERE plan_id=? AND date=?",
                  (plan_id, today)).fetchone()
    conn.close()
    return bool(r)


def plan_progress(plan_id):
    conn = _conn(); c = conn.cursor()
    r = c.execute("SELECT COUNT(*) AS n, COALESCE(SUM(done),0) AS d FROM plan_tasks WHERE plan_id=?",
                  (plan_id,)).fetchone()
    conn.close()
    return (r["d"] or 0), (r["n"] or 0)


def plan_streak(plan_id):
    from datetime import date as _d
    conn = _conn(); c = conn.cursor()
    rows = c.execute("SELECT DISTINCT date FROM plan_checkins WHERE plan_id=?", (plan_id,)).fetchall()
    conn.close()
    s = set(r["date"] for r in rows)
    if not s:
        return 0
    today = _d.today()
    fmt = lambda dt: dt.strftime("%Y-%m-%d")
    if fmt(today) in s:
        cur = today
    elif fmt(_d.fromordinal(today.toordinal() - 1)) in s:
        cur = _d.fromordinal(today.toordinal() - 1)
    else:
        return 0
    n = 0
    while fmt(cur) in s:
        n += 1
        cur = _d.fromordinal(cur.toordinal() - 1)
    return n
