"""
演示数据：覆盖云贵川广西四省 · 多热门行业（文旅/大数据/新能源/白酒/制造/农业/电子信息/医疗/跨境等）。
用于开箱即验「职位看板」与「智能匹配」。数据为公开雇主+通用就业方向示例，真实岗位请以各平台为准；
可随时在「设置」清空后导入你自己的真实职位。多行业设计，避免分享后只看到单一专业。
"""
DEMO_JOBS = [
    # ===== 云南 · 绿色能源 / 铝硅 =====
    {"platform_key":"boss","title":"光伏电池工艺技术员","company":"隆基绿能(云南)","city":"昆明","salary":"7-11K","url":"https://www.zhipin.com/c101290100/?query=光伏工艺","description":"单晶/电池片产线工艺与良率提升；熟悉丝网印刷、PECVD；材料/化工背景优先。"},
    {"platform_key":"zhaopin","title":"风电场运维工程师","company":"华能云南分公司","city":"曲靖","salary":"8-13K","url":"https://sou.zhaopin.com/?kw=风电运维","description":"风电机组日常维护与故障处理；电气/能源动力背景，持高低压电工证优先。"},
    {"platform_key":"liepin","title":"绿色铝生产质量主管","company":"云南神火铝业","city":"文山","salary":"10-15K","url":"https://www.liepin.com/zhaopin/?key=铝业质量","description":"电解铝/铝加工质量体系与过程管控；冶金/材料背景，5年以上经验。"},
    # ===== 云南 · 文旅康养 =====
    {"platform_key":"boss","title":"康养度假管家","company":"腾冲玛御谷温泉","city":"保山","salary":"5-8K","url":"https://www.zhipin.com/c101292300/?query=康养管家","description":"高端康养客户全程服务与活动策划；旅游管理/酒店管理背景，沟通力强。"},
    {"platform_key":"job58","title":"民宿运营店长","company":"大理洱海民宿集群","city":"大理","salary":"5-9K+提成","url":"https://dali.58.com/job/?key=民宿店长","description":"民宿日常运营、OTA管理与客诉处理；熟悉携程/美团后台，有团队管理经验。"},
    # ===== 云南 · 生物医药（含中药方向，作为多元之一） =====
    {"platform_key":"boss","title":"中药QC检验员","company":"昆药集团股份有限公司","city":"昆明","salary":"5-8K·13薪","url":"https://www.zhipin.com/c101290100/?query=中药QC","description":"中药材/中药饮片/中成药理化与微生物检验；熟练HPLC；中药学/药学背景。"},
    {"platform_key":"zhaopin","title":"疫苗生产工程师","company":"沃森生物技术","city":"昆明","salary":"7-12K","url":"https://sou.zhaopin.com/?kw=疫苗生产","description":"重组蛋白/mRNA 疫苗产线操作与工艺记录；生物工程/生物技术背景。"},
    # ===== 云南 · 高原农业 =====
    {"platform_key":"maimai","title":"咖啡品控专员","company":"云南农垦咖啡","city":"普洱","salary":"5-8K","url":"https://maimai.cn/web/jobs?keyword=咖啡品控","description":"咖啡生豆分级与烘焙品控；食品科学/园艺背景，能出差产地。"},

    # ===== 贵州 · 大数据 =====
    {"platform_key":"boss","title":"云计算运维工程师","company":"华为云(贵安)","city":"贵阳","salary":"10-18K","url":"https://www.zhipin.com/c101310100/?query=云计算运维","description":"云数据中心运维与故障排查；Linux/网络/存储基础扎实，有认证优先。"},
    {"platform_key":"lagou","title":"数据标注/算法训练专员","company":"白山云科技","city":"贵阳","salary":"6-10K","url":"https://www.lagou.com/wn/jobs?kd=数据标注","description":"AI 训练数据清洗与标注管理；计算机/统计背景，细心严谨。"},
    {"platform_key":"zhaopin","title":"大数据开发工程师","company":"满帮集团","city":"贵阳","salary":"12-20K","url":"https://sou.zhaopin.com/?kw=大数据开发","description":"物流平台离线/实时数仓开发；熟悉Hadoop/Spark/Flink；本科及以上。"},
    # ===== 贵州 · 白酒 =====
    {"platform_key":"boss","title":"白酒酿造技术员","company":"贵州茅台股份","city":"遵义","salary":"6-12K","url":"https://www.zhipin.com/c101310300/?query=白酒酿造","description":"酱香型白酒制曲/发酵/蒸馏工序；发酵工程/食品科学背景优先。"},
    {"platform_key":"job58","title":"酒类质量检验员","company":"习酒集团","city":"遵义","salary":"5-9K","url":"https://zunyi.58.com/job/?key=酒类质检","description":"原酒与成品酒理化/感官检验；食品检验工证书优先，能适应倒班。"},
    # ===== 贵州 · 新能源电池 =====
    {"platform_key":"liepin","title":"动力电池工艺工程师","company":"宁德时代(贵州)","city":"贵阳","salary":"10-16K","url":"https://www.liepin.com/zhaolin/?key=动力电池工艺","description":"电芯制造工艺改善与良率提升；材料/化工/电气背景，3年以上。"},
    {"platform_key":"yupao","title":"新能源设备维修技师","company":"比亚迪(贵阳)基地","city":"贵阳","salary":"7-12K","url":"https://www.yupao.com/search?keyword=设备维修","description":"产线自动化设备点检与维修；机电一体化背景，持电工证。"},

    # ===== 四川 · 电子信息 =====
    {"platform_key":"boss","title":"集成电路测试工程师","company":"振芯科技","city":"成都","salary":"10-18K","url":"https://www.zhipin.com/c101280100/?query=集成电路测试","description":"芯片测试方案开发与ATE调试；微电子/通信背景，熟悉探针台/测试机。"},
    {"platform_key":"lagou","title":"嵌入式软件工程师","company":"长虹电子","city":"绵阳","salary":"11-20K","url":"https://www.lagou.com/wn/jobs?kd=嵌入式软件","description":"智能家居/显示终端固件开发；C/C++，RTOS经验，本科及以上。"},
    {"platform_key":"zhaopin","title":"新型显示工艺工程师","company":"京东方(成都)","city":"成都","salary":"9-16K","url":"https://sou.zhaopin.com/?kw=显示工艺","description":"OLED/液晶面板产线工艺与缺陷分析；光电/材料背景优先。"},
    # ===== 四川 · 装备制造 =====
    {"platform_key":"liepin","title":"航空结构工艺员","company":"航空工业成飞","city":"成都","salary":"10-17K","url":"https://www.liepin.com/zhaopin/?key=航空工艺","description":"飞机零部件工艺编制与现场问题处理；航空航天/机械背景，涉密岗需政审。"},
    {"platform_key":"job51","title":"轨道交通电气工程师","company":"中车四方(四川)","city":"成都","salary":"9-15K","url":"https://search.51job.com/list/000000,000000,0000,00,9,99,轨交电气,2,1.html","description":"城轨车辆电气系统设计；电气工程/自动化背景，熟悉列车网络。"},
    # ===== 四川 · 白酒/食品 =====
    {"platform_key":"boss","title":"食品研发工程师","company":"千禾味业","city":"眉山","salary":"8-14K","url":"https://www.zhipin.com/c101300500/?query=食品研发","description":"调味品配方与工艺开发；食品科学/发酵工程背景，有量产经验优先。"},
    {"platform_key":"maimai","title":"白酒销售区域经理","company":"泸州老窖","city":"泸州","salary":"8-15K+提成","url":"https://maimai.cn/web/jobs?keyword=白酒销售","description":"区域渠道开发与维护；市场营销背景，能出差，有酒水经验加分。"},
    # ===== 四川 · 动力电池 =====
    {"platform_key":"guopin","title":"电池材料研发工程师","company":"宁德时代(宜宾)","city":"宜宾","salary":"12-20K","url":"https://job.iguopin.com/search?keyword=电池材料","description":"正极/电解液材料研发与中试；材料化学/化工背景，硕士优先。"},
    # ===== 四川 · 医药健康 =====
    {"platform_key":"zhaopin","title":"医药代表（川内）","company":"科伦药业","city":"成都","salary":"8-15K+提成","url":"https://sou.zhaopin.com/?kw=医药代表","description":"医院/终端学术推广；药学/临床背景，沟通强，能适应出差。"},

    # ===== 广西 · 跨境电商/东盟 =====
    {"platform_key":"boss","title":"跨境电商运营（东盟）","company":"南宁跨境电商标杆企业","city":"南宁","salary":"6-11K","url":"https://www.zhipin.com/c101300100/?query=跨境电商运营","description":"Shopee/Lazada 店铺运营与选品；国际贸易/小语种背景，英语/泰语优先。"},
    {"platform_key":"lagou","title":"小语种（越南语）运营","company":"TikTok Shop 服务商","city":"崇左","salary":"5-10K","url":"https://www.lagou.com/wn/jobs?kd=越南语运营","description":"越南市场内容本地化与直播运营；越南语专四以上，跨文化沟通。"},
    # ===== 广西 · 有色金属 =====
    {"platform_key":"boss","title":"有色金属冶炼技术员","company":"广西华锡集团","city":"河池","salary":"6-11K","url":"https://www.zhipin.com/c101340900/?query=有色金属冶炼","description":"锡/锑等金属冶炼与质检；冶金/材料背景，能适应倒班。"},
    {"platform_key":"job58","title":"铝加工质量工程师","company":"南南铝加工","city":"南宁","salary":"7-12K","url":"https://nanning.58.com/job/?key=铝加工质量","description":"铝型材/板带箔过程质量与体系；材料/机械背景，熟悉ISO体系。"},
    # ===== 广西 · 临港/新能源 =====
    {"platform_key":"liepin","title":"钢铁工艺工程师","company":"广西盛隆冶金","city":"防城港","salary":"8-14K","url":"https://www.liepin.com/zhaolin/?key=钢铁工艺","description":"炼钢/轧钢工艺优化与成本管控；冶金工程背景，3年以上经验。"},
    {"platform_key":"yupao","title":"汽车总装设备技师","company":"上汽通用五菱","city":"柳州","salary":"6-11K","url":"https://www.yupao.com/search?keyword=汽车总装","description":"整车总装线设备维护；机电/汽车工程背景，持电工证优先。"},
    # ===== 广西 · 装备制造 =====
    {"platform_key":"boss","title":"工程机械研发工程师","company":"柳工集团","city":"柳州","salary":"9-16K","url":"https://www.zhipin.com/c101300400/?query=工程机械研发","description":"装载机/挖掘机结构件与液压系统设计；机械设计/车辆工程背景。"},
    # ===== 广西 · 文旅 =====
    {"platform_key":"job58","title":"景区运营专员","company":"桂林旅游股份","city":"桂林","salary":"4-7K","url":"https://guilin.58.com/job/?key=景区运营","description":"景区接待、活动执行与游客服务；旅游管理背景，形象好沟通佳。"},

    # ===== 四省通用 · 国企事业单位 =====
    {"platform_key":"guopin","title":"质量管理（省属国企）","company":"云贵川桂国企联合岗","city":"昆明","salary":"9-14K","url":"https://job.iguopin.com/search?keyword=质量管理","description":"省属制造/能源国企质量体系岗；专业不限，管理体系经验优先。"},
    {"platform_key":"job51","title":"应届生全省统招（多行业）","company":"西南地区企业联合校招","city":"成都","salary":"5-9K","url":"https://search.51job.com/list/000000,000000,0000,00,9,99,应届统招,2,1.html","description":"面向云贵川桂药企/制造/文旅/互联网的应届统招岗；本科及以上。"},
]
