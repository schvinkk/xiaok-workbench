/* 小凯求职工作台 —— 前端逻辑 (原生 JS) */
const STATUSES = ["todo","applied","viewed","interview","offer","rejected"];
const SLABEL = {todo:"待投递",applied:"已投递",viewed:"已读/跟进",interview:"面试中",offer:"已拿Offer",rejected:"已拒绝"};
const SCOLOR = {todo:"#8b93a7",applied:"#3b82f6",viewed:"#a06bff",interview:"#f5b942",offer:"#2ecc71",rejected:"#ff3b46"};

const state = { profile:null, platforms:[], pfMap:{}, resumes:[], jobs:[], stats:null, saved:[], savedIds:new Set(), account:null, hot:null, provKey:null, selJobs:new Set(), __delivered:new Set(), todayDelivered:0 };

/* 四赛道：显示名 / 图标 / 对应平台分类 */
const TRACKS=[
  ["求职","💼","求职"],
  ["考公考编","🏛️","考公考编"],
  ["职业资格","📜","资格考试"],
  ["考研","🎓","考研"],
];
function goTrack(cat){
  pfCat=cat;
  $$('.nav-btn').forEach(x=>x.classList.remove('active'));
  const b=document.querySelector('.nav-btn[data-view="platforms"]');if(b)b.classList.add('active');
  $$('.view').forEach(v=>v.classList.remove('active'));
  $('#view-platforms').classList.add('active');
  render('platforms');closeSidebar();
}
function goView(view){
  $$('.nav-btn').forEach(x=>x.classList.remove('active'));
  const b=document.querySelector('.nav-btn[data-view="'+view+'"]');if(b)b.classList.add('active');
  $$('.view').forEach(v=>v.classList.remove('active'));
  $('#view-'+view).classList.add('active');
  render(view);closeSidebar();
}

/* 四省份州市（用于搜索/职位按城市筛选；城市码由后端自动映射） */
const PROV_ORDER=["云南","贵州","四川","广西"];
const PROV_CITIES={
  "云南":["昆明","曲靖","玉溪","保山","昭通","丽江","普洱","临沧","楚雄","红河","文山","西双版纳","大理","德宏","怒江","迪庆","全省"],
  "贵州":["贵阳","遵义","安顺","黔南","黔东南","铜仁","毕节","六盘水","黔西南","全省"],
  "四川":["成都","绵阳","德阳","宜宾","南充","泸州","达州","乐山","凉山","内江","自贡","攀枝花","遂宁","眉山","全省"],
  "广西":["南宁","柳州","桂林","北海","玉林","钦州","百色","梧州","河池","贵港","崇左","来宾","贺州","防城港","全省"]
};
const PROV_CAT={"云南":"yn","贵州":"gz","四川":"sc","广西":"gx"};
function provOptions(){
  return PROV_ORDER.map(p=>`<option value="${p}" ${state.profile&&state.profile.province===p?'selected':''}>${p}</option>`).join('');
}
function cityOptions(){
  const cities=PROV_CITIES[state.profile&&state.profile.province]||PROV_CITIES["云南"];
  return cities.map(c=>`<option value="${c}" ${state.profile&&state.profile.city_name===c?'selected':''}>${c}</option>`).join('');
}
async function setProvince(p){
  state.profile.province=p;
  const cities=PROV_CITIES[p]||PROV_CITIES["云南"];
  if(!cities.includes(state.profile.city_name)) state.profile.city_name=cities[0];
  await api('POST','/api/profile',{province:p,city_name:state.profile.city_name});
  toast('已切换到 '+p,'ok');
  rerenderCurrent();
}
async function setCity(c){
  state.profile.city_name=c;
  await api('POST','/api/profile',{city_name:c});
  toast('搜索城市：'+c,'ok');
  rerenderCurrent();
}
function rerenderCurrent(){
  const v=document.querySelector('.view.active');
  if(!v)return;
  const id=v.id.replace('view-','');
  const fn={dashboard:renderDashboard,resumes:renderResumes,platforms:renderPlatforms,jobs:renderJobs,track:renderTrack,match:renderMatch,plans:renderPlans,timeline:renderTimeline,exams:renderExams,disability:renderDisability,settings:renderSettings}[id];
  if(fn)fn();
}

/* ---------- 基础工具 ---------- */
const $ = (s,r=document)=>r.querySelector(s);
const $$ = (s,r=document)=>[...r.querySelectorAll(s)];
function esc(s){return (s==null?"":String(s)).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}

/* 薪资解析（粗略估算：提取带 K 的数值，按月薪计） */
function parseSalary(str){
  if(!str) return [];
  if(!/[kK]/.test(str)) return []; // 无 K/万 标记的不纳入统计
  const out=[];const re=/(\d+(?:\.\d+)?)\s*[kK]/g;let m;
  while((m=re.exec(str))){const v=parseFloat(m[1]);if(!isNaN(v))out.push(v*1000);}
  return out;
}
function salaryStats(list){
  let lo=Infinity,hi=-Infinity,sum=0,n=0;
  (list||[]).forEach(j=>parseSalary(j.salary).forEach(v=>{lo=Math.min(lo,v);hi=Math.max(hi,v);sum+=v;n++;}));
  if(n===0) return null;
  return {lo,hi,avg:Math.round(sum/n)};
}
function exportJobsCSV(){
  if(!state.jobs||!state.jobs.length){toast('没有可导出的职位','err');return;}
  const cols=[['title','职位'],['company','公司'],['platform_key','平台'],['city','城市'],['salary','薪资'],['status','状态'],['match_score','匹配度'],['applied_at','投递时间'],['url','链接']];
  const head=cols.map(c=>c[1]).join(',');
  const rows=state.jobs.map(j=>cols.map(([k])=>{
    let v=j[k]==null?'':String(j[k]);
    if(k==='platform_key')v=pf(j.platform_key).name;
    if(k==='status')v=SLABEL[j.status]||j.status;
    return '"'+v.replace(/"/g,'""')+'"';
  }).join(','));
  const csv='\ufeff'+head+'\n'+rows.join('\n');
  const blob=new Blob([csv],{type:'text/csv;charset=utf-8'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='职位看板.csv';a.click();
  toast('已导出 CSV','ok');
}
async function markApplied(id){
  const j=state.jobs.find(x=>x.id===id); if(!j){return;}
  const track=pf(j.platform_key).category||'求职';
  const resume_used=state.resumes.find(r=>r.is_default)?.name||'';
  if(db_delivered(id)){await api('POST','/api/jobs/'+id,{status:'applied'});toast('已标记为已投递');renderJobs();return;}
  await api('POST','/api/jobs/'+id,{status:'applied'});
  await api('POST','/api/deliver',{job_id:j.id,track,platform_key:j.platform_key,title:j.title,company:j.company,city:j.city,url:j.url,resume_used});
  toast('已标记已投递并记录到流水','ok');renderJobs();
}
function daysSince(iso){const d=new Date((iso||'').slice(0,10)+'T00:00:00');return Math.floor((Date.now()-d)/86400000);}
function staleCls(j){return (['applied','viewed','interview'].includes(j.status)&&j.applied_at&&daysSince(j.applied_at)>=7)?'stale':'';}
function staleTag(j){return (['applied','viewed','interview'].includes(j.status)&&j.applied_at&&daysSince(j.applied_at)>=7)?`<div class="kfollow">📞 ${daysSince(j.applied_at)}天未跟进</div>`:'';}
/* 访客标识：公开多用户，每人用浏览器本地 UUID 隔离自己的简历/收藏/投递 */
function ensureVid(){
  let v=localStorage.getItem('wb_vid');
  if(!v){v=(crypto.randomUUID&&crypto.randomUUID())||('v'+Date.now()+Math.random().toString(16).slice(2));localStorage.setItem('wb_vid',v);}
  document.cookie='wb_vid='+v+';path=/;max-age=31536000';
  return v;
}
const VID=ensureVid();
async function api(method,url,body){
  const opt={method,headers:{}};
  opt.headers['X-Visitor']=VID;
  const at=localStorage.getItem('wb_acct');
  if(at)opt.headers['X-Account']=at;
  if(body!==undefined){opt.headers['Content-Type']='application/json';opt.body=JSON.stringify(body);}
  const r=await fetch(url,opt);
  if(!r.ok) throw new Error('请求失败 '+r.status);
  const t=await r.text();
  try{return t?JSON.parse(t):{};}catch(e){return {};}
}
let toastT;
function toast(msg,type='',dur=2400){const e=$('#toast');e.textContent=msg;e.className='toast show '+type;clearTimeout(toastT);toastT=setTimeout(()=>e.className='toast',dur);}
function openModal(html){$('#modalBox').innerHTML=html;$('#modalBg').classList.add('show');}
function closeModal(){$('#modalBg').classList.remove('show');window.__lockModal=false;}
$('#modalBg').addEventListener('click',e=>{if(e.target.id==='modalBg'&&!window.__lockModal)closeModal();});

/* ---------- 路由 ---------- */
$$('.nav-btn').forEach(b=>b.addEventListener('click',()=>{
  $$('.nav-btn').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');
  $$('.view').forEach(v=>v.classList.remove('active'));
  $('#view-'+b.dataset.view).classList.add('active');
  render(b.dataset.view);
  closeSidebar();
}));
function render(view){
  ({dashboard:renderDashboard,resumes:renderResumes,platforms:renderPlatforms,
    jobs:renderJobs,track:renderTrack,plans:renderPlans,match:renderMatch,
    timeline:renderTimeline,exams:renderExams,disability:renderDisability,
    settings:renderSettings}[view]||renderDashboard)();
}

/* ---------- 移动端侧边抽屉 ---------- */
function toggleSidebar(){
  const sb=$('#sidebar'), sc=$('#sidebarScrim');
  if(sb.classList.contains('open')){closeSidebar();}
  else{sb.classList.add('open');sc.classList.add('show');}
}
function closeSidebar(){
  const sb=$('#sidebar'), sc=$('#sidebarScrim');
  if(sb)sb.classList.remove('open');
  if(sc)sc.classList.remove('show');
}
const __scrim=document.getElementById('sidebarScrim');
if(__scrim)__scrim.addEventListener('click',closeSidebar);

/* ---------- 初始化 ---------- */
async function init(){
  const me=await api('GET','/api/me');
  state.account=me.account||null;
  renderAcctBox();
  state.profile=await api('GET','/api/profile');
  state.platforms=await api('GET','/api/platforms');
  state.pfMap={};state.platforms.forEach(p=>state.pfMap[p.key]=p);
  state.saved=await api('GET','/api/saved');
  state.savedIds=new Set(state.saved.map(s=>s.job_id).filter(Boolean));
  renderDashboard();
}
function pf(key){return state.pfMap[key]||{name:key,color:'#555',icon:'•'};}

/* ---------- 账户（可选登录，保存进度） ---------- */
function renderAcctBox(){
  const el=document.getElementById('acctBox');
  if(state.account){
    el.innerHTML=`<div class="acct-box">
      <div class="ab-top"><span class="adot"></span><div><div class="ab-name">👤 ${esc(state.account)}</div><div class="ab-tag">已登录 · 进度已保存</div></div></div>
      <div class="ab-actions">
        <div class="ab-btn" onclick="doLogout()">退出</div>
      </div>
      <div class="ab-note">数据按你的账户隔离保存，跨设备可用，绝不外传。</div>
    </div>`;
  }else{
    el.innerHTML=`<div class="acct-box">
      <div class="ab-top"><span class="adot" style="background:#c7cbef;box-shadow:none"></span><div><div class="ab-name">🌐 游客模式</div><div class="ab-tag">数据存于本浏览器</div></div></div>
      <div class="ab-actions">
        <div class="ab-btn" onclick="openLogin()">登录 / 注册</div>
      </div>
      <div class="ab-note">选一个用户名登录，即可跨设备保存简历/收藏/投递。</div>
    </div>`;
  }
}
function openLogin(){
  openModal(`<span class="close" onclick="closeModal()">×</span>
    <h3>🔐 登录 / 注册（保存我的进度）</h3>
    <div class="login-modal">
      <div class="lm-tabs">
        <div class="lm-tab active" id="lmTabLogin" onclick="switchLm('login')">登录</div>
        <div class="lm-tab" id="lmTabReg" onclick="switchLm('reg')">注册新账户</div>
      </div>
      <div class="field"><label>用户名（自选，用于标识你的数据）</label><input id="lmUser" placeholder="例如：xiaokai / 小明"></div>
      <div class="field"><label>密码（至少 4 位）</label><input id="lmPass" type="password" placeholder="设置或输入密码"></div>
      <div class="row"><button class="btn primary" onclick="submitLogin()" style="flex:1">确认</button>
        <button class="btn ghost" onclick="closeModal()">取消</button></div>
      <div class="safety">🔒 安全说明：账户与密码仅经哈希后保存在<b>本机服务器</b>，绝不向任何第三方发送；你的简历/收藏/投递严格按账户隔离，他人无法看到。这是"保存进度"用的轻量账户，不是平台注册。</div>
    </div>`);
}
function switchLm(mode){
  document.getElementById('lmTabLogin').classList.toggle('active',mode==='login');
  document.getElementById('lmTabReg').classList.toggle('active',mode==='reg');
  window.__lmMode=mode;
}
async function submitLogin(){
  const u=document.getElementById('lmUser').value.trim();
  const p=document.getElementById('lmPass').value;
  if(!u||!p){toast('请填写用户名和密码','err');return;}
  const mode=window.__lmMode||'login';
  let r;
  if(mode==='reg') r=await api('POST','/api/register',{username:u,password:p});
  else r=await api('POST','/api/login_account',{username:u,password:p});
  if(r.error){toast(r.error,'err');return;}
  if(r.token){localStorage.setItem('wb_acct',r.token);}
  closeModal();
  toast((mode==='reg'?'注册成功，':'登录成功，')+'进度已保存','ok');
  await init();
}
async function doLogout(){
  await api('POST','/api/account_logout');
  localStorage.removeItem('wb_acct');
  state.account=null;
  renderAcctBox();
  toast('已退出。你账户里的全部记录（简历/收藏/投递/计划）仍在，重新登录即可恢复','ok',3200);
  await init();
}

/* ================= 仪表盘 ================= */
/* 轻量 SVG 环形图（无需第三方库，性能友好） */
function donut(segs, size=130, stroke=18){
  const total=segs.reduce((a,s)=>a+s.value,0);
  if(total<=0) return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}"><circle cx="${size/2}" cy="${size/2}" r="${(size-stroke)/2}" fill="none" stroke="#222633" stroke-width="${stroke}"/></svg>`;
  const r=(size-stroke)/2, c=2*Math.PI*r, cx=size/2, cy=size/2;
  let off=0;
  const arcs=segs.map(s=>{
    const frac=s.value/total, len=frac*c;
    const el=`<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${s.color}" stroke-width="${stroke}" stroke-dasharray="${len.toFixed(2)} ${(c-len).toFixed(2)}" stroke-dashoffset="${(-off).toFixed(2)}" transform="rotate(-90 ${cx} ${cy})"/>`;
    off+=len; return el;
  }).join('');
  return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">${arcs}<text x="${cx}" y="${cy}" text-anchor="middle" dominant-baseline="central" fill="#fff" font-size="22" font-weight="800">${total}</text></svg>`;
}

async function renderDashboard(){
  const v=$('#view-dashboard');
  state.stats=await api('GET','/api/stats');
  const s=state.stats; const p=state.profile;
  state.hot=await api('GET','/api/hot_industries');
  if(!state.provKey && state.hot.length) state.provKey=state.hot[0].key;
  const links=await api('GET','/api/search_links');
  const recent=await api('GET','/api/jobs'); state.jobs=recent;
  const msAll=await api('GET','/api/milestones');
  state.milestones=msAll;
  const dels=await api('GET','/api/deliveries');
  const plans=await api('GET','/api/plans');
  const plansCount=plans.length;
  const _t0=new Date();_t0.setHours(0,0,0,0);
  const upcoming=msAll.map(m=>{const d=new Date(m.date+'T00:00:00');return {...m,days:Math.round((d-_t0)/86400000)};})
    .filter(m=>!m.done&&m.days>=0).sort((a,b)=>a.days-b.days).slice(0,4);
  const pfDist=Object.entries(s.by_platform).map(([k,n])=>{
    const pm=pf(k);return {name:pm.name,color:pm.color,icon:pm.icon,n};
  }).sort((a,b)=>b.n-a.n);
  const maxPf=Math.max(1,...pfDist.map(x=>x.n));
  // 城市分布 Top
  const cityMap={};recent.forEach(j=>{const c=j.city||'未注明';cityMap[c]=(cityMap[c]||0)+1;});
  const cityDist=Object.entries(cityMap).sort((a,b)=>b[1]-a[1]).slice(0,8);
  const maxCity=Math.max(1,...cityDist.map(x=>x[1]));
  // 求职就绪度（画像4项 + 简历 + 投递）
  const profChecks=[p.name,p.target_title,p.keywords,p.city_name].filter(Boolean).length;
  const hasResume=state.resumes.length>0?1:0;
  const hasDeliver=(s.deliveries||0)>0?1:0;
  const readiness=Math.round((profChecks+hasResume+hasDeliver)/6*100);
  const compPct=readiness;
  // 今日行动清单：跨模块聚合
  const plansTodayTodo=plans.filter(x=>!x.checked_today).length;
  const daysSince=iso=>{const d=new Date((iso||'').slice(0,10)+'T00:00:00');return Math.floor((Date.now()-d)/86400000);};
  const staleFollow=recent.filter(j=>['applied','viewed','interview'].includes(j.status)&&j.applied_at&&daysSince(j.applied_at)>=7).length;
  const todoJobs=recent.filter(j=>j.status==='todo').length;
  const actions=[];
  if(plansTodayTodo>0) actions.push({u:'urgent',ic:'📅',t:`${plansTodayTodo} 个计划今天还没打卡`,d:'坚持打卡，进度条才会一点点涨',view:'plans'});
  if(staleFollow>0) actions.push({u:'warn',ic:'📞',t:`${staleFollow} 个投递超过 7 天没动静`,d:'该发邮件 / 催一下 HR 跟进了',view:'track'});
  if(upcoming.length) actions.push({u:'urgent',ic:'⏰',t:`${upcoming.length} 个备考节点临近（最近 ${upcoming[0].days} 天）`,d:esc(upcoming[0].title),view:'timeline'});
  if(todoJobs>0) actions.push({ic:'💼',t:`${todoJobs} 个职位还没投递`,d:'挑几个先投出去，别让机会溜走',view:'jobs'});
  if(readiness<60) actions.push({u:'warn',ic:'📄',t:`求职就绪度仅 ${readiness}%`,d:hasResume?'完善求职画像，匹配更准':'上传简历 + 完善画像，匹配更准',view:hasResume?'settings':'resumes'});
  if(!actions.length) actions.push({ic:'✅',t:'今天该做的都做完了，稳！',d:'随时回来检查进度'});
  // 分轨备考进度
  const tm={};TRACKS.forEach(([nm,ic,cat])=>tm[cat]={nm,ic});
  const trkProg=TRACKS.map(([nm,ic,cat])=>{
    const arr=msAll.filter(m=>m.track===cat);
    const done=arr.filter(m=>m.done).length;
    return {nm,ic,cat,done,total:arr.length,pct:arr.length?Math.round(done/arr.length*100):0};
  });
  // 浏览器提醒
  maybeNotify(upcoming[0]);
  // 本省在招数（按所选省份州市筛）
  const provCities=PROV_CITIES[state.profile.province]||PROV_CITIES["云南"];
  const provJobsCount=(state.jobs||[]).filter(j=>(provCities||[]).includes(j.city)).length;

  const greet = state.account ? `👋 你好，${esc(state.account)}` : `👋 你好，求职者`;
  v.innerHTML=`
  <h2>🧭 首页 · 就业风向标</h2>
  <div class="sub">面向大学生求职，也服务所有想<b>好就业、就好业、提升自己</b>的人。公开可用 · 数据按你隔离（绝不外传） · 上传简历后即按<b>你的专业/技能</b>智能匹配云贵川广西岗位。</div>
  <div class="hero">
    <div>
      <div class="hero-h">🚀 你的下一份 offer，从这里开始</div>
      <div class="hero-s">${greet} · 一步一脚印，今天也比昨天更接近目标 ✨ 临近备考节点请看右侧提醒。</div>
    </div>
    <div class="hero-stat">
      <div class="hn">${upcoming[0]?upcoming[0].days+' 天':'—'}</div>
      <div class="hl2">${upcoming[0]?esc(upcoming[0].title):'暂无临近节点'}</div>
    </div>
  </div>
  ${moduleWallHtml(s, plansCount, msAll.length, compPct)}
  ${actionListHtml(actions)}
  <div class="prov-pill" onclick="jobFilter.province=state.profile.province;jobFilter.city='';goView('jobs')">
    📍 ${esc(state.profile.province)} · 本省在招 <b>${provJobsCount}</b> 个岗位
    <span class="tiny">点击查看本省岗位 ›</span>
  </div>
  ${hotSection()}
  <div class="grid cards-4 mb">
    <div class="stat"><div class="lab">职位总数</div><div class="num">${s.total}</div></div>
    <div class="stat"><div class="lab">累计投递</div><div class="num red">${s.deliveries}</div></div>
    <div class="stat"><div class="lab">收藏岗位</div><div class="num amber">${s.saved}</div></div>
    <div class="stat"><div class="lab">已拿Offer</div><div class="num green">${s.offers}</div></div>
  </div>
  <div class="track-cards">
    ${TRACKS.map(([nm,ic,cat])=>{
      const n=(s.by_category&&s.by_category[cat])||0;
      const pct=Math.round(n/Math.max(1,s.total)*100);
      return `<button class="tcard" onclick="goTrack('${esc(cat)}')">
        <span class="go">›</span>
        <div class="ic">${ic}</div>
        <div class="nm">${esc(nm)}</div>
        <div class="n">${n}<small> 条</small></div>
        <div class="bar"><i style="width:${pct}%"></i></div>
      </button>`;
    }).join('')}
  </div>

  <div class="grid cards-3">
    <div class="panel">
      <h3>🏢 平台职位分布</h3>
      <div class="donut-wrap">${donut(pfDist.map(x=>({value:x.n,color:x.color})),130,18)}
        <div class="donut-leg">${pfDist.slice(0,6).map(x=>`<div class="dl"><i style="background:${x.color}"></i>${x.icon} ${esc(x.name)} <b>${x.n}</b></div>`).join('')}</div>
      </div>
    </div>
    <div class="panel">
      <h3>🧭 求职就绪度 <span class="tag">画像 + 简历 + 投递的综合状态</span></h3>
      <div class="donut-wrap">${donut([{value:readiness,color:'#4f46e5'},{value:100-readiness,color:'#e3e6f0'}],130,18)}
        <div class="donut-leg">
          <div class="dl"><i style="background:#4f46e5"></i>就绪度 <b>${readiness}%</b></div>
          <div class="dl"><i style="background:#3b82f6"></i>简历 ${state.resumes.length?'已上传'+state.resumes.length+'份':'未上传'}</div>
          <div class="dl"><i style="background:#6366f1"></i>投递 ${s.deliveries?'已投'+s.deliveries+'次':'暂无'}</div>
          <div class="dl tiny">画像填全 + 上传简历 + 开始投递，就绪度越高</div>
        </div>
      </div>
    </div>
    <div class="panel">
      <h3>📚 各赛道备考进度</h3>
      ${trkProg.map(t=>`<div class="pbar"><div class="pn">${t.ic} ${esc(t.nm)} <b>${t.done}/${t.total}</b></div>
        <div class="track"><div class="fill" style="width:${t.pct}%;background:linear-gradient(90deg,#4f46e5,#6366f1)">${t.pct}%</div></div></div>`).join('')}
      <div class="tiny mt">进度 = 已完成节点 / 总节点（去「时间线」勾选完成）</div>
    </div>
  </div>

  <div class="grid cards-2">
    <div class="panel">
      <h3>📈 投递漏斗 <span class="tag">从待投递到 Offer 的转化</span></h3>
      <div class="funnel">
        ${STATUSES.map(st=>({st,n:s.by_status[st]})).filter(x=>x.n>0||x.st==='todo').map(f=>`
          <div class="fbar">
            <div class="nm">${SLABEL[f.st]}</div>
            <div class="track"><div class="fill" style="width:${Math.round(f.n/Math.max(1,...STATUSES.map(x=>s.by_status[x.st]))*100)}%;background:${SCOLOR[f.st]}">${f.n}</div></div>
            <div class="v">${f.n}</div>
          </div>`).join('')}
      </div>
      <div class="warn mt">📌 自动投递说明：各平台无公开投递 API，且自动脚本违反其用户协议、有封号风险。本工作台采用<span class="hl">「一键直达平台投递页 + 自动记录状态」</span>的合规方案——点击职位「去投递」即打开该平台真实申请页，并自动记入「投递流水」。</div>
    </div>
    <div class="panel">
      <h3>🔗 全网一键搜 <span class="tag">按你的专业/技能精准搜</span></h3>
      ${links[0] && links[0].need_resume && !state.profile.manual_major ? `
      <div class="warn">📄 你还没有上传简历，也未填写专业。可直接点下方平台逐一点搜索，或先到「简历库」上传 / 在「智能匹配」填专业后更精准。</div>
      ` : (links[0] && links[0].need_resume && state.profile.manual_major ? `
      <div class="warn">📄 未上传简历，将用你填的专业「<b>${esc(state.profile.manual_major)}</b>」作为搜索词直达各平台（去「简历库」上传可更精准）。</div>
      ` : '')}
      <div class="chips mb">${links.map(l=>`<a class="chip" href="${esc(l.url)}" target="_blank" rel="noopener" style="border-color:${l.color}55;color:${l.color};text-decoration:none;cursor:pointer">${l.icon} ${esc(l.name)}</a>`).join('')}</div>
      <div class="row">
        <select id="dashProv" onchange="setProvince(this.value)" style="max-width:90px">${provOptions()}</select>
        <select id="dashCity" onchange="setCity(this.value)" style="max-width:130px">${cityOptions()}</select>
        <input id="dashKw" placeholder="关键词（如：大数据 / 新能源 / 软件工程）" style="max-width:200px">
        <button class="btn primary" onclick="searchAll(document.getElementById('dashKw').value)">🚀 全部平台搜索</button>
      </div>
      <div class="tiny mt">点平台名或「全部平台搜索」即在新标签打开对应平台搜索页；首次打开可能需登录/验证（平台防爬机制），登录后正常。</div>
    </div>
  </div>
  <div class="panel mt">
    <h3>⏰ 临近节点 <span class="tag">最近 4 个待办 · 红=30天内</span></h3>
    ${upcoming.length?`<div class="ms-list">${upcoming.map(m=>{
      const cls=m.days<=30?'urg':m.days<=90?'soon':'';
      return `<div class="ms ${cls}"><div class="ms-date">${esc(m.date)}</div>
        <div class="ms-body"><div class="ms-title">${esc(m.title)}</div>
        <div class="ms-note">${esc(m.track)} · 还有 ${m.days} 天</div></div>
        <div class="ms-side"><button class="btn sm" onclick="goView('timeline')">看时间线 ›</button></div></div>`;
    }).join('')}</div>`:'<div class="empty">暂无临近节点，去「时间线」添加</div>'}
  </div>
  <div class="panel mt">
    <h3>🗺️ 岗位城市分布 <span class="tag">Top ${cityDist.length} · 四省覆盖</span></h3>
    ${cityDist.length?`<div class="funnel">${cityDist.map(([c,n])=>`
      <div class="fbar"><div class="nm">📍 ${esc(c)}</div>
      <div class="track"><div class="fill" style="width:${Math.round(n/maxCity*100)}%;background:#5b8cff">${n}</div></div>
      <div class="v">${n}</div></div>`).join('')}</div>`
    :'<div class="empty">暂无职位，去「职位看板」添加或导入</div>'}
  </div>
  <div class="panel mt">
    <h3>📤 最近投递记录 <span class="tag">${s.deliveries} 条 · 来自「去投递」自动记录</span></h3>
    ${dels.length?`<div class="ms-list">${dels.slice(0,6).map(d=>`
      <div class="ms">
        <div class="ms-date">${esc((d.created_at||'').slice(0,10))}</div>
        <div class="ms-body"><div class="ms-title joblink" onclick="${d.job_id?`showJobDetail(${d.job_id})`:''}">${esc(d.title||'职位')}</div>
          <div class="ms-note">${pf(d.platform_key).icon} ${esc(pf(d.platform_key).name)} · ${esc(d.company||'')} · ${esc(d.city||'')}</div></div>
        <div class="ms-side"><button class="btn sm danger" onclick="delDelivery(${d.id})">撤</button></div>
      </div>`).join('')}</div>
      <div class="tiny mt"><button class="btn sm" onclick="goView('track')">看完整投递流水 ›</button></div>`
    :'<div class="empty">还没有投递记录。去「职位看板」点「去投递」，会自动记到这里。</div>'}
  </div>
  <div class="panel mt">
    <h3>⭐ 我的收藏 <span class="tag">${state.saved.length} 个</span></h3>
    ${state.saved.length?`<div class="ms-list">${state.saved.slice(0,5).map(sv=>`
      <div class="ms">
        <div class="ms-body"><div class="ms-title">${esc(sv.title||'职位')}</div>
          <div class="ms-note">${pf(sv.platform_key).icon} ${esc(pf(sv.platform_key).name)} · ${esc(sv.company||'')}</div></div>
        <div class="ms-side"><button class="btn sm" onclick="event.stopPropagation();window.open('${esc(sv.url||'')}','_blank')">打开</button>
          <button class="btn sm danger" onclick="toggleSave({job_id:${sv.job_id||'null'},title:'${esc((sv.title||'').replace(/'/g,"\\'"))}',company:'${esc((sv.company||'').replace(/'/g,"\\'"))}',platform_key:'${esc(sv.platform_key)}',city:'${esc((sv.city||'').replace(/'/g,"\\'"))}',url:'${esc((sv.url||'').replace(/'/g,"\\'"))}'})">取消</button></div>
      </div>`).join('')}</div>
      <div class="tiny mt"><button class="btn sm" onclick="setJobSavedFilter(true)">查看全部收藏 ›</button></div>`
    :'<div class="empty">还没有收藏。职位卡片点 ⭐ 即可收藏，集中管理心仪岗位。</div>'}
  </div>
  <div class="panel mt">
    <h3>🕒 最近添加的职位</h3>
    ${recent.length?`<table><tr><th>职位</th><th>公司</th><th>平台</th><th>薪资</th><th>匹配</th><th>状态</th></tr>
      ${recent.slice(0,8).map(j=>`<tr>
        <td>${esc(j.title)}</td><td>${esc(j.company)}</td>
        <td><span class="pfbadge" style="background:${pf(j.platform_key).color}22;color:${pf(j.platform_key).color}">${pf(j.platform_key).icon} ${esc(pf(j.platform_key).name)}</span></td>
        <td class="sal" style="color:var(--primary)">${esc(j.salary||'-')}</td>
        <td>${j.match_score!=null?`<span class="score ${j.match_score>=50?'hi':j.match_score>=30?'mid':'lo'}" style="width:34px;height:34px;font-size:12px">${j.match_score}</span>`:'<span class="tiny">未匹配</span>'}</td>
        <td style="color:${SCOLOR[j.status]}">${SLABEL[j.status]}</td></tr>`).join('')}</table>`
    :'<div class="empty">还没有职位</div>'}
  </div>`;
}
/* ---------- 模块入口卡片墙（总入口） ---------- */
function moduleWallHtml(s, plansCount, msCount, compPct){
  const mods=[
    {ic:'📄',name:'简历库',desc:'上传 PDF/Word，自动解析姓名/专业/技能，按你的背景匹配岗位',stat:state.resumes.length,unit:'份',view:'resumes',tag:'智能解析'},
    {ic:'🔗',name:'平台中心',desc:'管理 40+ 招聘平台开关与搜索模板，一键直达各平台投递页',stat:state.platforms.length,unit:'个',view:'platforms',tag:'全网覆盖'},
    {ic:'💼',name:'职位看板',desc:'手动添加 / 批量导入职位，自动算匹配度、按赛道与城市筛选',stat:s.total,unit:'个',view:'jobs',tag:'投递前必看'},
    {ic:'📌',name:'投递追踪',desc:'Kanban 看板拖拽改状态，自动记录完整投递流水',stat:s.deliveries,unit:'次',view:'track',tag:'待投→Offer'},
    {ic:'📅',name:'计划打卡',desc:'自定义或智能生成阶段计划，每天打卡看进度条一点点涨',stat:plansCount,unit:'个',view:'plans',tag:'万能计划'},
    {ic:'🎯',name:'智能匹配',desc:'用你的简历对全部职位算匹配度，列出命中技能与差距',stat:s.matched||0,unit:'已匹配',view:'match',tag:'人岗比对'},
    {ic:'🗓️',name:'备考时间线',desc:'四赛道报名/笔试/考试节点倒计时，红字紧迫提醒不漏',stat:msCount,unit:'节点',view:'timeline',tag:'不漏节点'},
    {ic:'⚙️',name:'设置',desc:'求职画像 / 平台模板 / 本地 AI / 数据导出备份',stat:compPct,unit:'就绪',view:'settings',tag:'你的偏好'},
  ];
  return `<div class="mod-wall">
    <div class="mw-head"><h3>🧭 功能模块总入口</h3><span class="mw-sub">点任意卡片直达对应板块 · 数据按你隔离</span></div>
    <div class="mod-grid">${mods.map(m=>`<button class="mod-card accent" onclick="goView('${m.view}')">
      ${m.tag?`<span class="mc-tag">${m.tag}</span>`:''}
      <div class="mc-ic">${m.ic}</div>
      <div class="mc-name">${esc(m.name)}</div>
      <div class="mc-desc">${esc(m.desc)}</div>
      <div class="mc-foot">
        <div class="mc-stat">${m.stat!==''&&m.stat!=null?`<b>${m.stat}</b> ${m.unit}`:'<span class="tiny">配置项</span>'}</div>
        <div class="mc-go">进入 ›</div>
      </div>
    </button>`).join('')}</div>
  </div>`;
}

/* ---------- 今日行动清单（跨模块聚合） ---------- */
function actionListHtml(actions){
  return `<div class="action-panel">
    <div class="ap-head"><span style="font-size:18px">📋</span><h3>今日行动清单</h3>
      <span class="ap-sub">把各模块今天该做的，一次性摆给你</span></div>
    <div class="action-list">${actions.map(a=>`<div class="action-item ${a.u||''}">
      <div class="ai-ic">${a.ic}</div>
      <div class="ai-main"><div class="ai-t">${a.t}</div><div class="ai-d">${a.d}</div></div>
      <button class="ai-go" onclick="goView('${a.view}')">去处理 ›</button>
    </div>`).join('')}</div>
  </div>`;
}

/* ---------- 热门行业板块（云贵川广西） ---------- */
function provTabsHtml(){
  if(!state.hot) return '';
  return state.hot.map(p=>`<div class="prov-tab ${p.key===state.provKey?'active':''}" onclick="selectProv('${p.key}')"><span class="pi">${p.icon}</span>${esc(p.name)}</div>`).join('');
}
function hotBodyHtml(){
  if(!state.hot) return '';
  const prov=state.hot.find(p=>p.key===state.provKey)||state.hot[0];
  return `<div class="prov-meta">
    <div class="pc">${prov.icon} ${esc(prov.name)} · 省会 ${esc(prov.capital)}</div>
    <div class="pp"><b>定位：</b>${esc(prov.position)}</div>
    <div class="ph">📈 ${esc(prov.highlight)}</div>
  </div>
  <div class="hi-prov-talent">🎓 <b>人才政策总览：</b>${esc(prov.talent)}</div>
  <div class="hi-grid">${prov.industries.map(ind=>`
    <div class="hi-card" style="border-top-color:${prov.color}">
      <div class="hi-top"><div class="hi-ic">${ind.icon}</div><div class="hi-name">${esc(ind.name)}</div></div>
      <div class="hi-tag">${esc(ind.tagline)}</div>
      <div class="hi-badges"><span class="badge sal">💰 ${esc(ind.salary)}</span><span class="badge trend">${esc(ind.trend)}</span></div>
      <div class="hi-info">
        <div class="hi-i"><span class="k">代表城市</span><span class="v">${esc(ind.cities.join(' · '))}</span></div>
        <div class="hi-i"><span class="k">代表企业</span><span class="v">${esc(ind.employers.join(' · '))}</span></div>
        <div class="hi-i full"><span class="k">适合专业</span><span class="v">${esc(ind.majors.join(' · '))}</span></div>
        <div class="hi-i full"><span class="k">适合人群</span><span class="v">${esc(ind.suit)}</span></div>
      </div>
      <div class="hi-policy">📜 <b>人才政策：</b>${esc(ind.policy)}</div>
      <div class="hi-scale"><span class="k">产业规模</span><span class="v">${esc(ind.scale)}</span></div>
      <div class="hi-chips">
        <span class="hc c">📡 招聘渠道：${ind.channels.map(esc).join(' / ')}</span>
        <span class="hc">🎫 相关证书：${ind.certs.map(esc).join(' / ')}</span>
      </div>
      <button class="btn primary sm hi-search" onclick="searchIndustry('${esc(ind.kw)}')">🔍 搜该行业岗位</button>
    </div>`).join('')}</div>`;
}
function hotSection(){
  return `<div class="hi-section">
    <div class="hi-head"><span class="hl-emoji">🌟</span><h3>云贵川广西 · 热门行业就业风向标</h3></div>
    <div class="hi-sub">四省重点产业与人才需求<b>一览无余</b>：每个行业都摆清<b>招聘渠道 / 相关证书 / 人才政策 / 产业规模 / 适合人群</b>，打破信息差。点「搜该行业岗位」直达招聘平台；上传简历后还能按专业精准匹配。</div>
    <div class="prov-tabs" id="provTabs">${provTabsHtml()}</div>
    <div id="hotBody">${hotBodyHtml()}</div>
  </div>`;
}
function selectProv(key){
  state.provKey=key;
  const tabs=document.getElementById('provTabs');
  const body=document.getElementById('hotBody');
  if(tabs)tabs.innerHTML=provTabsHtml();
  if(body)body.innerHTML=hotBodyHtml();
}
function searchIndustry(kw){
  // 显式关键词搜索，未上传简历也允许（通用兴趣搜索）
  searchAll(kw);
}

async function searchAll(kw,cat){
  if(!kw && !state.resumes.length && !state.profile.manual_major){
    toast('先填专业/上传简历，或在框里输入关键词再搜','err');
    goView('match'); return;
  }
  const qp=new URLSearchParams();
  if(kw)qp.set('kw',kw);
  if(cat)qp.set('category',cat);
  const qs=qp.toString();
  const links=await api('GET','/api/search_links'+(qs?'?'+qs:''));
  if(!links.length){toast('没有可搜的平台','err');return;}
  const kwTxt=esc(kw||state.profile.manual_major||'全部岗位');
  const html='<!doctype html><html lang="zh"><head><meta charset="utf-8">'
    +'<meta name="viewport"content="width=device-width,initial-scale=1">'
    +'<title>一键搜 · '+kwTxt+'</title><style>'
    +'body{font-family:system-ui,"PingFang SC",sans-serif;background:#f5f6fb;margin:0;padding:24px;color:#1f2330}'
    +'h2{margin:0 0 4px}.sub{color:#6b7385;font-size:13px;margin-bottom:18px}'
    +'.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}'
    +'a{display:flex;align-items:center;gap:10px;padding:14px 16px;background:#fff;border:1px solid #e3e6f0;border-radius:14px;text-decoration:none;color:#1f2330;font-weight:600;box-shadow:0 2px 8px rgba(20,30,80,.05);transition:.15s}'
    +'a:hover{border-color:#818cf8;transform:translateY(-1px);box-shadow:0 6px 16px rgba(79,70,229,.14)}'
    +'.ic{font-size:20px}.ct{font-size:11px;color:#6b7385;font-weight:500}'
    +'</style></head><body>'
    +'<h2>🔗 一键搜 · '+kwTxt+'</h2>'
    +'<div class="sub">点击下方任意平台，在新标签打开搜索结果（每个链接都能单独点）。首次打开某平台可能要求登录/验证，登录后即正常——这是平台方防爬机制，非本工具问题。</div>'
    +'<div class="g">'+links.map(l=>'<a href="'+esc(l.url)+'" target="_blank" rel="noopener"><span class="ic" style="color:'+l.color+'">'+l.icon+'</span><span>'+esc(l.name)+'<br><span class="ct">'+esc(l.category)+'</span></span></a>').join('')
    +'</div></body></html>';
  const blob=new Blob([html],{type:'text/html'});
  const url=URL.createObjectURL(blob);
  const w=window.open(url,'_blank');
  if(!w){ // 弹窗被拦截时兜底：直接打开第一个
    window.open(links[0].url,'_blank');
    toast('已打开 '+links[0].name+'，其余请在平台中心逐一点','warn');
  }else{
    toast('已打开搜索汇总页（'+links.length+' 个平台均可点）','ok');
  }
  setTimeout(()=>URL.revokeObjectURL(url),60000);
}

/* ---------- 浏览器桌面提醒（临近备考节点） ---------- */
function maybeNotify(next){
  if(!state.profile.notify_enabled) return;
  if(!('Notification' in window)) return;
  if(Notification.permission==='granted' && next && next.days>=0 && next.days<=30){
    new Notification('⏰ 备考节点提醒',{body:`${next.title} · 还有 ${next.days} 天（${next.date}）`,tag:'wb-ms'});
  }
}
function requestNotify(){
  if(!('Notification' in window)){toast('此浏览器不支持桌面通知','err');return;}
  Notification.requestPermission().then(perm=>{
    if(perm==='granted'){
      api('POST','/api/profile',{notify_enabled:true});
      state.profile.notify_enabled=true;
      new Notification('🔔 已开启提醒',{body:'临近 30 天内的备考节点会推送到这里'});
      toast('桌面提醒已开启','ok');
    } else toast('未授权通知权限','err');
  });
}
function testNotify(){
  if(!('Notification' in window)){toast('此浏览器不支持桌面通知','err');return;}
  if(Notification.permission!=='granted'){requestNotify();return;}
  new Notification('🔔 测试提醒',{body:'这是一条来自小K万能工作台的桌面通知'});
}

/* ---------- 投递记录 / 收藏 辅助 ---------- */
async function delDelivery(id){
  if(!confirm('从投递记录中撤回这条？'))return;
  await api('DELETE','/api/delivery/'+id);toast('已撤回');
  const av=document.querySelector('.view.active')?.id;
  if(av==='view-track') renderTrack(); else renderDashboard();
}
async function toggleSave(d){
  const r=await api('POST','/api/save',d);
  state.saved=await api('GET','/api/saved');
  state.savedIds=new Set(state.saved.map(s=>s.job_id).filter(Boolean));
  toast(r.saved?'已收藏 ⭐':'已取消收藏','ok');
  if(window.location && document.querySelector('.view.active')?.id==='view-jobs') renderJobs();
  else if(document.querySelector('.view.active')?.id==='view-dashboard') renderDashboard();
}
function setJobSavedFilter(on){
  jobFilter.saved=on;
  $$('.nav-btn').forEach(x=>x.classList.remove('active'));
  const b=document.querySelector('.nav-btn[data-view="jobs"]');if(b)b.classList.add('active');
  $$('.view').forEach(v=>v.classList.remove('active'));
  $('#view-jobs').classList.add('active');
  renderJobs();closeSidebar();
}

/* ================= 简历库 ================= */
async function renderResumes(){
  const v=$('#view-resumes');
  state.resumes=await api('GET','/api/resumes');
  v.innerHTML=`
  <h2>📄 简历库</h2>
  <div class="sub">上传你的 PDF / Word 简历，本地解析姓名/专业/技能，<b>永不外传</b>。解析后可直接「按我的简历匹配岗位」「全网一键搜」（用你简历里的专业/技能作为关键词）。登录账户后，简历随账户跨设备保存；不登录也存在本浏览器。</div>
  <div class="panel mb">
    <h3>⬆️ 上传简历</h3>
    <div class="dropzone" id="dropzone" onclick="document.getElementById('resFile').click()">
      <div class="dz-ic">📥</div>
      <div class="dz-t">点击选择，或把简历文件拖到这里</div>
      <div class="dz-s">支持 PDF / Word / TXT · 云端解析仅存本机，永不外传</div>
      <input type="file" id="resFile" accept=".pdf,.doc,.docx,.txt" hidden>
    </div>
    <div class="row mt">
      <button class="btn primary" id="upBtn" onclick="uploadResume()">解析并入库</button>
      <div class="spacer"></div>
      <span class="tiny">解析结果用于「智能匹配 / 全网一键搜」。</span>
    </div>
  </div>
  <div class="grid cards-3">
    ${state.resumes.length?state.resumes.map(r=>`
      <div class="panel">
        <div class="row"><div style="font-weight:700">${esc(r.name)}</div>${r.is_default?'<span class="chip g">默认</span>':'<span class="chip g">最新</span>'}</div>
        <div class="tiny mt">${esc(r.filename)} · ${esc(r.created_at)}</div>
        <div class="res-summary">
          ${r.major?`<span class="rs m">🎓 ${esc(r.major)}</span>`:'<span class="rs">未识别专业</span>'}
          ${r.skills.slice(0,6).map(s=>`<span class="rs">${esc(s)}</span>`).join('')}
          ${r.skills_count===0?'<span class="rs">未识别技能</span>':''}
        </div>
        <div class="res-stat"><span>完整度</span><b>${r.completeness!=null?r.completeness:0}%</b></div>
        <div class="comple-bar"><i style="width:${r.completeness!=null?r.completeness:0}%"></i></div>
        <div class="row mt">
          <button class="btn sm" onclick="previewResume(${r.id})">预览解析</button>
          ${r.is_default?'':'<button class="btn sm" onclick="setDefault('+r.id+')">设为默认</button>'}
          <button class="btn sm danger" onclick="delResume(${r.id})">删除</button>
        </div>
      </div>`).join('')
    :'<div class="empty" style="grid-column:1/-1">还没有简历，先上传一份</div>'}
  </div>`;
  const dz=document.getElementById('dropzone');
  if(dz){
    ['dragenter','dragover'].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.classList.add('drag');}));
    ['dragleave','drop'].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.classList.remove('drag');}));
    dz.addEventListener('drop',e=>{const f=e.dataTransfer.files[0];if(f){window.__dropFile=f;toast('已选文件：'+f.name,'ok');}});
  }
}
async function uploadResume(){
  const f=window.__dropFile||($('#resFile').files&&$('#resFile').files[0]);
  if(!f){toast('请先选择文件','err');return;}
  const btn=$('#upBtn'); if(btn){btn.disabled=true;btn.textContent='解析中…';}
  const fd=new FormData();fd.append('file',f);
  try{
    const hd={'X-Visitor':VID};
    const at=localStorage.getItem('wb_acct');
    if(at)hd['X-Account']=at;
    const r=await fetch('/api/resumes/upload',{method:'POST',body:fd,headers:hd}).then(x=>x.json());
    if(r.error){toast(r.error,'err');return;}
    window.__dropFile=null;
    toast('已入库：'+ (r.parsed.name||f.name)+' · 可去「智能匹配/一键搜」','ok');
    renderResumes();
  }catch(e){
    toast('上传失败：'+e.message,'err');
  }finally{
    if(btn){btn.disabled=false;btn.textContent='解析并入库';}
  }
}
async function setDefault(id){await api('POST','/api/resumes/'+id+'/default');toast('已设为默认简历','ok');renderResumes();}
async function delResume(id){
  if(!confirm('确定删除该简历？'))return;
  await api('DELETE','/api/resumes/'+id);toast('已删除');renderResumes();
}
async function previewResume(id){
  const r=await api('GET','/api/resumes/'+id+'/preview');
  const p=r.parsed;
  openModal(`<span class="close" onclick="closeModal()">×</span>
    <h3>📄 简历解析结果</h3>
    <div class="grid cards-2 mb">
      <div class="field"><label>姓名</label><div>${esc(p.name||'未识别')}</div></div>
      <div class="field"><label>专业</label><div class="hl">${esc(p.major||'未识别')}</div></div>
      <div class="field"><label>电话</label><div class="mono">${esc(p.phone||'未识别')}</div></div>
      <div class="field"><label>邮箱</label><div class="mono">${esc(p.email||'未识别')}</div></div>
    </div>
    <div class="field"><label>学历</label><div>${p.degrees&&p.degrees.length?p.degrees.join(' / '):'未识别'}</div></div>
    <div class="field"><label>识别到的技能 (${p.skills.length})</label>
      <div class="chips">${p.skills.map(s=>`<span class="chip g">${esc(s)}</span>`).join('')||'<span class="tiny">无</span>'}</div></div>
    <div class="field"><label>原始文本预览（前 1600 字）</label>
      <textarea rows="8" readonly>${esc(r.text.slice(0,1600))}</textarea></div>
    <div class="row"><button class="btn primary" onclick="closeModal()">知道了</button></div>`);
}

/* ================= 平台中心 ================= */
let pfCat='';
async function renderPlatforms(){
  const v=$('#view-platforms');
  const cats=await api('GET','/api/categories');
  state.platforms=await api('GET','/api/platforms'); // 全量，前端按分类筛
  const shown=pfCat?state.platforms.filter(p=>p.category===pfCat):state.platforms;
  const links=await api('GET','/api/search_links'+(pfCat?'?category='+encodeURIComponent(pfCat):''));
  const linkMap={};links.forEach(l=>linkMap[l.key]=l.url);
  const tabCnt=c=>state.platforms.filter(p=>p.category===c).length;
  const tabs=`<button class="tab ${pfCat===''?'active':''}" onclick="setPfCat('')">全部 <span class="tc">${state.platforms.length}</span></button>`+
    cats.map(c=>`<button class="tab ${pfCat===c?'active':''}" onclick="setPfCat('${esc(c)}')">${esc(c)} <span class="tc">${tabCnt(c)}</span></button>`).join('');
  v.innerHTML=`
  <h2>🔗 平台中心</h2>
  <div class="sub">已接入 ${state.platforms.length} 个平台，覆盖「求职 / 考公考编 / 资格考试 / 考研」四大赛道。开关控制是否出现在「一键搜」中；搜索模板可自定义。</div>
  <div class="tabs">${tabs}</div>
  <div class="row mb">
    <select id="pfProv" onchange="setProvince(this.value)" style="max-width:90px">${provOptions()}</select>
    <select id="pfCity" onchange="setCity(this.value)" style="max-width:130px">${cityOptions()}</select>
    <input id="pfKw" placeholder="覆盖关键词（可选）" style="max-width:200px">
    <button class="btn primary" onclick="searchAll(document.getElementById('pfKw').value,'${esc(pfCat)}')">🚀 ${pfCat?esc(pfCat)+'内':''}一键搜</button>
    ${pfCat?`<span class="tiny">当前赛道：${esc(pfCat)}</span>`:`<span class="tiny">当前省份：<b>${esc(state.profile.province)}</b> · 一键搜按【省份·城市】的真实平台链接打开；未设专业关键词时自动用「手动背景」的专业</span>`}
  </div>
  <div class="pf-grid">
    ${shown.map(p=>`
      <div class="pf-card ${p.enabled?'':'off'}">
        <div class="top">
          <div class="dot" style="background:${p.color}22;color:${p.color}">${p.icon}</div>
          <div class="nm">${esc(p.name)}</div>
          <div class="spacer"></div>
          <div class="switch ${p.enabled?'on':''}" onclick="togglePf('${p.key}',${p.enabled?0:1})"></div>
        </div>
        <div class="note">${esc(p.note)}</div>
        <div class="row">
          <button class="btn sm primary" onclick="window.open('${esc(linkMap[p.key]||'')}','_blank')">🔍 去搜</button>
          <button class="btn sm" onclick="editPf('${p.key}')">✎ 模板</button>
        </div>
      </div>`).join('')}
  </div>`;
}
function setPfCat(c){pfCat=c;renderPlatforms();}
async function togglePf(key,val){await api('POST','/api/platforms/'+key,{enabled:val?1:0});renderPlatforms();}
async function editPf(key){
  const p=state.platforms.find(x=>x.key===key);
  openModal(`<span class="close" onclick="closeModal()">×</span>
    <h3>✎ 编辑「${esc(p.name)}」搜索模板</h3>
    <div class="field"><label>显示名</label><input id="epName" value="${esc(p.name)}"></div>
    <div class="field"><label>图标(emoji)</label><input id="epIcon" value="${esc(p.icon)}" style="max-width:80px"></div>
    <div class="field"><label>主题色</label><input id="epColor" value="${esc(p.color)}" style="max-width:120px"></div>
    <div class="field"><label>搜索模板</label>
      <input id="epTpl" value="${esc(p.search_template)}">
      <div class="tiny">占位符：<span class="mono">{kw}</span> 关键词 · <span class="mono">{city}</span> 城市 · <span class="mono">{boss}</span> BOSS城市码 · <span class="mono">{58}</span> 58城市拼音</div>
    </div>
    <div class="field"><label>备注</label><input id="epNote" value="${esc(p.note)}"></div>
    <div class="row"><button class="btn primary" onclick="savePf('${key}')">保存</button>
      <button class="btn ghost" onclick="closeModal()">取消</button></div>`);
}
async function savePf(key){
  const body={name:$('#epName').value,icon:$('#epIcon').value,color:$('#epColor').value,
    search_template:$('#epTpl').value,note:$('#epNote').value};
  await api('POST','/api/platforms/'+key,body);closeModal();toast('已保存','ok');renderPlatforms();
}

/* ================= 职位看板 ================= */
let jobFilter={};
let matchHighOnly=false;
let resFilterRegion='全部';
let disEdu='不限', disRegion='全部';
let examQ='', disQ='';
let msOnlyUndone=false;
async function renderJobs(){
  const v=$('#view-jobs');
  state.platforms=await api('GET','/api/platforms');
  const dlv=await api('GET','/api/deliveries');
  state.__delivered=new Set(dlv.map(d=>d.job_id).filter(Boolean));
  try{ const tc=await api('GET','/api/deliveries/today'); state.todayDelivered=tc.count||0; }catch(e){}
  // 仅看收藏模式
  if(jobFilter.saved){
    const saved=await api('GET','/api/saved');
    const list=saved.map(s=>({id:s.job_id,title:s.title,company:s.company,platform_key:s.platform_key,city:s.city,salary:'',url:s.url,description:'',status:'saved',match_score:null,blacklisted:0,saved:true}));
    v.innerHTML=`
    <h2>💼 职位看板 <span class="tag">仅看收藏 · ${saved.length}</span></h2>
    <div class="sub">你星标收藏的岗位集中在这里。点 ⭐ 取消收藏。</div>
    <div class="panel mb"><div class="row">
      <button class="btn" onclick="setJobSavedFilter(false)">← 返回全部职位</button>
      <div class="spacer"></div>
      <button class="btn" onclick="openImport()">📥 批量导入</button>
      <button class="btn primary" onclick="openAddJob()">➕ 添加职位</button>
    </div></div>
    <div id="jobList">${list.length?list.map(jobCard).join(''):'<div class="empty">还没有收藏</div>'}</div>`;
    return;
  }
  state.jobs=await api('GET','/api/jobs?'+new URLSearchParams(
    Object.entries(jobFilter).filter(([k,val])=>val).map(([k,val])=>[k,val])));
  const ph=`<option value="">全部平台</option>`+state.platforms.map(p=>`<option value="${p.key}" ${jobFilter.platform===p.key?'selected':''}>${esc(p.name)}</option>`).join('');
  const sh=`<option value="">全部状态</option>`+STATUSES.map(s=>`<option value="${s}" ${jobFilter.status===s?'selected':''}>${SLABEL[s]}</option>`).join('');
  const ch=`<option value="">全赛道</option>`+TRACKS.map(([nm,ic,cat])=>`<option value="${cat}" ${jobFilter.category===cat?'selected':''}>${esc(nm)}</option>`).join('');
  const cyh=`<option value="">全部城市</option>`+(PROV_CITIES[state.profile.province]||PROV_CITIES["云南"]).map(c=>`<option value="${c}" ${jobFilter.city===c?'selected':''}>${esc(c)}</option>`).join('');
  v.innerHTML=`
  <h2>💼 职位看板</h2>
  <div class="sub">手动添加 / 批量导入职位，系统按简历自动算匹配度，一键直达平台投递。不限专业、不限院校、面向所有高校毕业生与求职者——可按赛道（求职 / 考公考编 / 职业资格 / 考研）与省份州市筛选。</div>
  <div class="panel mb">
    <div class="row">
      <select id="jobProv" onchange="setJobProvince(this.value)" style="max-width:90px" title="选省份只看该省岗位（默认四省全部）">${provOptions()}</select>
      <input id="jobQ" placeholder="搜索职位/公司" value="${esc(jobFilter.q||'')}" style="max-width:200px" onkeydown="if(event.key==='Enter')applyJobFilter()">
      <select id="jobCy" onchange="applyJobFilter()" style="max-width:120px">${cyh}</select>
      <select id="jobC" onchange="applyJobFilter()" style="max-width:140px">${ch}</select>
      <select id="jobP" onchange="applyJobFilter()" style="max-width:150px">${ph}</select>
      <select id="jobS" onchange="applyJobFilter()" style="max-width:140px">${sh}</select>
      <button class="btn" onclick="applyJobFilter()">筛选</button>
      <button class="btn ${jobFilter.saved?'primary':''}" onclick="setJobSavedFilter(true)">⭐ 仅看收藏</button>
      <div class="spacer"></div>
      <button class="btn" onclick="exportJobsCSV()">⬇️ 导出CSV</button>
      <button class="btn" onclick="openImport()">📥 批量导入</button>
      <button class="btn primary" onclick="openAddJob()">➕ 添加职位</button>
    </div>
    <div class="tiny mt">范围：${jobFilter.city?esc(jobFilter.city):(jobFilter.province?esc(jobFilter.province)+' · 本省':'云贵川桂四省全部')}　·　选省份可只看本省岗位</div>
  </div>
  <div class="batch-bar" id="batchBar">
    <label class="sel-all"><input type="checkbox" id="selAllBox" onchange="selAll(this.checked)"> 全选本页</label>
    <button class="btn primary sm" onclick="batchDeliver()">⚡ 一键投递选中 <span class="cnt" id="selCnt">${state.selJobs.size}</span></button>
    <button class="btn sm" onclick="quickDeliverTodo()">⚡ 投递全部待投递</button>
    <span class="def-res">默认简历：<b id="defResName">${defaultResumeName()||'（未设，去简历库上传）'}</b></span>
    <span class="today-cnt">今日已投 <b id="todayCnt">${state.todayDelivered||0}</b>${((state.profile&&state.profile.daily_cap)||0)?'/'+state.profile.daily_cap:''}</span>
    <div class="spacer"></div>
    <span class="tiny">勾选岗位 → 一键把你的简历记入投递流水，并打开各平台投递页（自动去重 + 每日上限保护）</span>
  </div>
  ${salaryStats(state.jobs)?`<div class="sal-stats">
    <div class="sal-stat"><div class="sl">平均月薪</div><div class="sv">¥${(salaryStats(state.jobs).avg/1000).toFixed(1)}<small>K</small></div></div>
    <div class="sal-stat"><div class="sl">最高月薪</div><div class="sv">¥${(salaryStats(state.jobs).hi/1000).toFixed(1)}<small>K</small></div></div>
    <div class="sal-stat"><div class="sl">最低月薪</div><div class="sv">¥${(salaryStats(state.jobs).lo/1000).toFixed(1)}<small>K</small></div></div>
  </div>`:''}
  <div id="jobList">
    ${state.jobs.length?state.jobs.map(jobCard).join(''):'<div class="empty">暂无职位。点「添加职位」或「批量导入」，也可在设置里载入演示数据。</div>'}
  </div>`;
}
function applyJobFilter(){
  jobFilter={q:$('#jobQ').value.trim(),category:$('#jobC').value,city:$('#jobCy').value,platform:$('#jobP').value,status:$('#jobS').value,province:jobFilter.province,saved:jobFilter.saved};
  renderJobs();
}
async function setJobProvince(p){
  state.profile.province=p;
  const cities=PROV_CITIES[p]||PROV_CITIES["云南"];
  if(!cities.includes(state.profile.city_name)) state.profile.city_name=cities[0];
  await api('POST','/api/profile',{province:p,city_name:state.profile.city_name});
  jobFilter.province=p;
  jobFilter.city='';
  toast('已切换到 '+p+' · 仅看本省岗位','ok');
  renderJobs();
}
function jobCard(j){
  const p=pf(j.platform_key);
  const ej={title:(j.title||'').replace(/'/g,"\\'"),company:(j.company||'').replace(/'/g,"\\'"),city:(j.city||'').replace(/'/g,"\\'"),url:(j.url||'').replace(/'/g,"\\'")};
  const saved=state.savedIds.has(j.id);
  const delivered=state.__delivered&&state.__delivered.has(j.id);
  const svObj=`{job_id:${j.id==null?'null':j.id},title:'${ej.title}',company:'${ej.company}',platform_key:'${esc(j.platform_key)}',city:'${ej.city}',url:'${ej.url}'}`;
  return `<div class="job ${state.selJobs.has(j.id)?'sel':''}" id="job-${j.id}">
    <label class="jsel" title="勾选后一键投递"><input type="checkbox" ${state.selJobs.has(j.id)?'checked':''} onchange="toggleSel(${j.id},this.checked)"></label>
    <div>
      <div class="title joblink" onclick="showJobDetail(${j.id})">${esc(j.title)} ${j.blacklisted?'<span class="bltag">已屏蔽</span>':''} ${delivered?'<span class="bltag ok">已投递</span>':''} ${saved?'<span class="bltag star">⭐</span>':''}</div>
      <div class="meta">
        <span>${esc(j.company||'-')}</span>
        <span>${p.icon} <span style="color:${p.color}">${esc(p.name)}</span></span>
        <span>📍 ${esc(j.city||'-')}</span>
        <span class="sal">${esc(j.salary||'薪资面议')}</span>
      </div>
      ${j.description?`<div class="desc">${esc(j.description.slice(0,120))}${j.description.length>120?'…':''}</div>`:''}
      <div class="meta mt">
        <span>状态：<b style="color:${SCOLOR[j.status]}">${SLABEL[j.status]}</b></span>
        ${j.applied_at?`<span>投递于 ${esc(j.applied_at)}</span>`:''}
        ${j.resume_used?`<span>使用简历：${esc(j.resume_used)}</span>`:''}
      </div>
    </div>
    <div class="acts">
      <div class="score ${j.match_score>=50?'hi':j.match_score>=30?'mid':'lo'}">${j.match_score!=null?j.match_score:'–'}</div>
      <button class="btn sm green" onclick="applyJob(${j.id})">🚀 去投递</button>
      <button class="btn sm" onclick="markApplied(${j.id})">✓ 已投</button>
      <button class="btn sm ${saved?'amber':'star'}" onclick="toggleSave(${svObj})" title="收藏">${saved?'⭐ 已收藏':'☆ 收藏'}</button>
      <select class="sm" onchange="setStatus(${j.id},this.value)" style="width:96px;padding:4px">
        ${STATUSES.map(s=>`<option value="${s}" ${j.status===s?'selected':''}>${SLABEL[s]}</option>`).join('')}
      </select>
      <button class="btn sm" onclick="matchOne(${j.id})">🎯 匹配</button>
      <button class="btn sm ${j.blacklisted?'danger':''}" onclick="toggleBlack(${j.id},${j.blacklisted?0:1})">${j.blacklisted?'取消屏蔽':'屏蔽'}</button>
      <button class="btn sm danger" onclick="delJob(${j.id})">删</button>
    </div>
  </div>`;
}
async function showJobDetail(id){
  if(id==null||id===''){return;}
  let j;
  try{ j=await api('GET','/api/jobs/'+id); }
  catch(e){
    openModal(`<span class="close" onclick="closeModal()">×</span>
      <div class="panel" style="box-shadow:none"><h3>岗位不存在</h3>
      <div class="tiny">该岗位可能已被删除或尚未录入。</div>
      <div class="row mt"><button class="btn ghost" onclick="closeModal()">关闭</button></div></div>`);
    return;
  }
  const p=pf(j.platform_key);
  const desc=j.description&&j.description.trim()?j.description:'（暂无详细描述，点下面按钮去原平台查看完整 JD，再决定是否投递，别盲目送人头 👊）';
  const delivered=state.__delivered&&state.__delivered.has(j.id);
  openModal(`
    <span class="close" onclick="closeModal()">×</span>
    <div class="jd-head">
      <div class="jd-title">${esc(j.title)}</div>
      <div class="jd-meta">
        <span>${esc(j.company||'未知公司')}</span>
        <span>${p.icon} <span style="color:${p.color}">${esc(p.name)}</span></span>
        <span>📍 ${esc(j.city||'-')}</span>
        <span class="sal">${esc(j.salary||'薪资面议')}</span>
      </div>
      <div class="jd-meta mt">
        <span>状态：<b style="color:${SCOLOR[j.status]}">${SLABEL[j.status]}</b></span>
        ${j.match_score!=null?`<span>匹配度：<b style="color:#4f46e5">${j.match_score}</b></span>`:''}
        ${j.applied_at?`<span>投递于 ${esc(j.applied_at)}</span>`:''}
        ${j.resume_used?`<span>使用简历：${esc(j.resume_used)}</span>`:''}
      </div>
    </div>
    <div class="jd-sub">岗位详情（来自本工作台记录）</div>
    <div class="jd-desc">${esc(desc)}</div>
    <div class="tiny mb">来源平台：${esc(p.name)}　·　完整岗位以原平台为准。看清要求再投递，精准出击。</div>
    <div class="row">
      <button class="btn primary" onclick="closeModal();applyJob(${j.id})">🚀 去平台查看/投递 ›</button>
      ${delivered?'<button class="btn" disabled>已记入投递</button>':`<button class="btn" onclick="markApplied(${j.id});closeModal()">✓ 标记已投</button>`}
      <button class="btn ghost" onclick="closeModal()">关闭</button>
    </div>`);
}
async function openAddJob(){
  const ph=state.platforms.map(p=>`<option value="${p.key}">${esc(p.name)}</option>`).join('');
  openModal(`<span class="close" onclick="closeModal()">×</span>
    <h3>➕ 添加职位</h3>
    <div class="field"><label>职位名称 *</label><input id="ajTitle"></div>
    <div class="field row2"><div><label>公司</label><input id="ajCompany"></div><div><label>城市</label><input id="ajCity" value="${esc(state.profile.city_name)}"></div></div>
    <div class="field row2"><div><label>薪资</label><input id="ajSalary"></div><div><label>平台</label><select id="ajPf">${ph}</select></div></div>
    <div class="field"><label>职位链接（投递页/详情页）</label><input id="ajUrl" placeholder="https://..."></div>
    <div class="field"><label>JD 描述</label><textarea id="ajDesc" rows="4"></textarea></div>
    <div class="row"><button class="btn primary" onclick="saveJob()">保存</button><button class="btn ghost" onclick="closeModal()">取消</button></div>`);
}
async function saveJob(){
  const body={title:$('#ajTitle').value.trim(),company:$('#ajCompany').value.trim(),
    city:$('#ajCity').value.trim(),salary:$('#ajSalary').value.trim(),
    platform_key:$('#ajPf').value,url:$('#ajUrl').value.trim(),description:$('#ajDesc').value.trim()};
  if(!body.title){toast('职位名称必填','err');return;}
  await api('POST','/api/jobs',body);closeModal();toast('已添加','ok');renderJobs();
}
function openImport(){
  openModal(`<span class="close" onclick="closeModal()">×</span>
    <h3>📥 批量导入职位</h3>
    <div class="tiny mb">每行一条，用 <span class="mono">|</span> 分隔：<br><span class="mono">职位 | 公司 | 平台key | 城市 | 薪资 | 链接</span><br>平台key 可选：boss / zhaopin / liepin / job58 / guopin / yupao / maimai / job51</div>
    <textarea id="impText" rows="9" placeholder="中药QC检验员 | 昆药集团 | boss | 昆明 | 5-8K | https://..."></textarea>
    <div class="tiny mt">也可粘贴标准 JSON 数组（字段同添加职位）。</div>
    <div class="row mt"><button class="btn primary" onclick="doImport()">导入</button><button class="btn ghost" onclick="closeModal()">取消</button></div>`);
}
async function doImport(){
  const t=$('#impText').value.trim();if(!t){toast('内容为空','err');return;}
  let items=t;
  if(t.startsWith('[')){try{items=JSON.parse(t);}catch(e){toast('JSON 解析失败','err');return;}}
  const r=await api('POST','/api/jobs/import',{items});
  closeModal();toast('已导入 '+r.imported+' 条','ok');renderJobs();
}
async function applyJob(id){
  const j=state.jobs.find(x=>x.id===id);
  if(!j){return;}
  if(j.url)window.open(j.url,'_blank');
  if(db_delivered(id)){
    toast('已在平台打开投递页（投递记录中已有）','ok');return;
  }
  const track=pf(j.platform_key).category||'求职';
  const resume_used=pickResumeForJob(j);
  if(!resume_used){toast('还没有简历，先去「简历库」上传','err');goView('resumes');return;}
  await api('POST','/api/deliver',{job_id:j.id,track,platform_key:j.platform_key,
    title:j.title,company:j.company,city:j.city,url:j.url,resume_used});
  state.__delivered.add(j.id);
  if(j.status==='todo'){j.status='applied';j.applied_at=nowStr();j.resume_used=resume_used;}
  toast('已打开投递页，并记入「投递流水」（简历：'+resume_used+'）','ok');renderJobs();
}
function db_delivered(id){return state.__delivered?.has(id)||false;}
function defaultResumeName(){
  const d=state.resumes.find(r=>r.is_default)||state.resumes[0];
  return d?d.name:'';
}
function tokenize(s){return (s||'').toLowerCase().split(/[\s,/、，。()（）\-—:：·]+/).map(w=>w.trim()).filter(w=>w.length>=2);}
function pickResumeForJob(job){
  if(!state.resumes.length) return '';
  if(state.resumes.length===1) return state.resumes[0].name;
  const jset=new Set(tokenize((job.title||'')+' '+(job.description||'')));
  let best=null,bestScore=-1;
  state.resumes.forEach(r=>{
    const words=[...(r.skills||[]).map(s=>(''+s).toLowerCase()), (r.major||'').toLowerCase(), (r.name||'').toLowerCase()].filter(Boolean);
    let score=0; words.forEach(w=>{ if(jset.has(w)) score++; });
    if(r.is_default) score+=0.5;                 // 默认简历轻微加权
    if(score>bestScore){bestScore=score;best=r;}
  });
  return best?best.name:(state.resumes.find(r=>r.is_default)||state.resumes[0]).name;
}
function toggleSel(id,on){
  if(on)state.selJobs.add(id);else state.selJobs.delete(id);
  const card=document.getElementById('job-'+id);
  if(card)card.classList.toggle('sel',on);
  updateSelCnt();
}
function selAll(on){
  const ids=state.jobs.map(j=>j.id);
  ids.forEach(id=>{ if(on)state.selJobs.add(id); else state.selJobs.delete(id); });
  document.querySelectorAll('.job .jsel input').forEach(c=>{c.checked=on;});
  document.querySelectorAll('.job').forEach(c=>c.classList.toggle('sel',on));
  updateSelCnt();
}
function updateSelCnt(){
  const el=document.getElementById('selCnt');
  if(el)el.textContent=state.selJobs.size;
}
async function quickDeliverTodo(){
  const todo=state.jobs.filter(j=>j.status==='todo'&&!db_delivered(j.id)).map(j=>j.id);
  if(!todo.length){toast('没有待投递的岗位了','ok');return;}
  todo.forEach(id=>state.selJobs.add(id));
  updateSelCnt();
  await batchDeliver();
}
async function batchDeliver(){
  if(!state.selJobs.size){toast('请先勾选要投递的岗位','err');return;}
  if(!state.resumes.length){toast('还没有简历，先去「简历库」上传并设为默认','err');goView('resumes');return;}
  // 1) 客户端去重：跳过已投递岗位
  const sel=[...state.selJobs];
  const pending=sel.filter(id=>!db_delivered(id));
  const skippedDup=sel.length-pending.length;
  if(!pending.length){toast('勾选的岗位都已投递过，无需重复投递','ok');return;}
  // 2) 频率保护：每日上限
  const cap=(state.profile&&state.profile.daily_cap)||0;
  let todayCount=0;
  if(cap>0){ const t=await api('GET','/api/deliveries/today'); todayCount=t.count||0; }
  let chosen=pending;
  if(cap>0 && pending.length>(cap-todayCount)){
    const remaining=cap-todayCount;
    if(remaining<=0){toast('今日投递上限已用完（'+cap+' 个），明天再投，或去「设置」调高','err');return;}
    chosen=pending.slice(0,remaining);
    toast('今日上限 '+cap+'，仅投递剩余 '+remaining+' 个，其余留到明天','ok',3200);
  }
  // 3) 逐岗选最匹配简历
  const items=[];
  chosen.forEach(id=>{
    const j=state.jobs.find(x=>x.id===id); if(!j)return;
    items.push({job_id:j.id, track:pf(j.platform_key).category||'求职', platform_key:j.platform_key,
      title:j.title, company:j.company, city:j.city, url:j.url, resume_used:pickResumeForJob(j)});
  });
  if(!items.length){toast('没有可投递的岗位','err');return;}
  const r=await api('POST','/api/deliver/batch',{items});
  if(r.error){toast(r.error,'err');return;}
  const done=r.count||0, skipSrv=r.skipped||0;
  items.forEach(it=>{
    state.__delivered.add(it.job_id);
    const j=state.jobs.find(x=>x.id===it.job_id);
    if(j&&j.status==='todo'){j.status='applied';j.applied_at=nowStr();j.resume_used=it.resume_used;}
  });
  let i=0;
  items.forEach(it=>{ if(it.url){ setTimeout(()=>window.open(it.url,'_blank'), i*450); i++; } });
  state.selJobs.clear(); updateSelCnt();
  if(state.todayDelivered!=null) state.todayDelivered=(state.todayDelivered||0)+done;
  let msg='已记录 '+done+' 条投递，已打开各平台投递页';
  if(skippedDup||skipSrv) msg+='（跳过重复 '+(skippedDup+skipSrv)+' 个）';
  toast(msg,'ok',3400);
  showBatchResult(items);
  renderJobs();
}
function nowStr(){const d=new Date();const p=n=>(''+n).padStart(2,'0');return d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate())+' '+p(d.getHours())+':'+p(d.getMinutes());}
function showBatchResult(items){
  openModal(`<span class="close" onclick="closeModal()">×</span>
    <h3>⚡ 一键投递完成（${items.length} 个）</h3>
    <div class="tiny mb">已记入你的「投递追踪」。各平台标签页应已打开；若浏览器拦截弹窗，点下方按钮逐站完成最终提交。多份简历时已按岗位自动选最匹配的简历。</div>
    <div class="batch-list">
      ${items.map(it=>`<div class="bl-row"><div class="bl-info"><b>${esc(it.title)}</b><span>${esc(it.company||'')} · ${esc(it.city||'')} · 简历：${esc(it.resume_used||'—')}</span></div>
        ${it.url?`<button class="btn sm" onclick="window.open('${esc(it.url)}','_blank')">去平台投递 ›</button>`:'<span class="tiny">无链接</span>'}</div>`).join('')}
    </div>
    <div class="row mt"><button class="btn primary" onclick="closeModal()">知道了</button></div>`);
}
async function setStatus(id,st){await api('POST','/api/jobs/'+id,{status:st});toast('状态→'+SLABEL[st]);renderJobs();}
async function matchOne(id){
  toast('匹配中…');
  const mj=document.getElementById('mMajor');
  const body={};
  if(mj&&mj.value.trim()){body.manual={major:mj.value.trim(),education:document.getElementById('mEdu').value,skills:document.getElementById('mSkills').value.trim(),keywords:document.getElementById('mKw').value.trim()};}
  const r=await api('POST','/api/match/'+id,body);
  const m=r.matched||[],mis=r.missing||[];
  openModal(`<span class="close" onclick="closeModal()">×</span>
    <h3>🎯 匹配结果 · ${esc(state.jobs.find(x=>x.id===id)?.title||'')}</h3>
    <div class="row mb"><div class="score ${r.score>=50?'hi':r.score>=30?'mid':'lo'}" style="width:60px;height:60px;font-size:22px">${r.score}</div>
      <div><div style="font-size:13px">匹配度：<b class="hl">${r.level}</b></div><div class="tiny">引擎：${r.engine==='ollama'?'本地Ollama Qwen':'本地关键词'}</div>
      <div class="tiny">${esc(r.reason||'')}</div></div></div>
    <div class="field"><label>✅ 命中 (${m.length})</label><div class="chips">${m.map(x=>`<span class="chip g">${esc(x)}</span>`).join('')||'<span class="tiny">无</span>'}</div></div>
    <div class="field"><label>⚠️ 差距 (${mis.length})</label><div class="chips">${mis.map(x=>`<span class="chip r">${esc(x)}</span>`).join('')||'<span class="tiny">无明显差距</span>'}</div></div>
    <div class="row"><button class="btn primary" onclick="closeModal()">关闭</button></div>`);
}
async function toggleBlack(id,val){await api('POST','/api/jobs/'+id+'/blacklist',{value:val});toast(val?'已加入屏蔽':'已取消屏蔽');renderJobs();}
async function delJob(id){if(!confirm('删除该职位？'))return;await api('DELETE','/api/jobs/'+id);toast('已删除');renderJobs();}

/* ================= 投递追踪 (Kanban) ================= */
async function renderTrack(){
  const v=$('#view-track');
  if(state.dfStat===undefined) state.dfStat='all';
  if(state.dfQ===undefined) state.dfQ='';
  state.jobs=await api('GET','/api/jobs');
  const dels=state.deliveries=await api('GET','/api/deliveries');
  // ---- 统计 ----
  const jobs=state.jobs||[];
  const appliedJobs=jobs.filter(j=>['applied','viewed','interview','offer'].includes(j.status)).length;
  const offerJobs=jobs.filter(j=>j.status==='offer').length;
  const interviewJobs=jobs.filter(j=>j.status==='interview').length;
  const weekDel=dels.filter(d=>daysSince(d.created_at)<=7).length;
  const dueFollow=dels.filter(d=>d.follow_at && d.follow_at<=todayStr()).length;
  const offerRate=appliedJobs?Math.round(offerJobs/appliedJobs*100):0;
  const due=dels.filter(d=>d.follow_at && d.follow_at<=todayStr());
  const cols=STATUSES.map(st=>{
    const items=state.jobs.filter(j=>j.status===st);
    return `<div class="kcol" data-st="${st}">
      <div class="kh"><b style="color:${SCOLOR[st]}">${SLABEL[st]}</b><span>${items.length}</span></div>
      ${items.map(j=>`<div class="kcard ${staleCls(j)}" draggable="true" data-id="${j.id}" ondragstart="drag(event)" onclick="event.stopPropagation()">
        <div class="kt">${esc(j.title)}</div><div class="kc">${esc(j.company||'')} · ${pf(j.platform_key).icon}${esc(pf(j.platform_key).name)}</div>${staleTag(j)}</div>`).join('')}
    </div>`;
  }).join('');
  v.innerHTML=`
  <h2>📌 投递追踪</h2>
  <div class="sub">拖拽卡片改变状态，自动记录到投递历史。从「待投递」一路推到「已拿Offer」。</div>
  <div class="stat-strip">
    <div class="stat"><div class="sv">${dels.length}</div><div class="sl">投递记录</div></div>
    <div class="stat"><div class="sv" style="color:${SCOLOR.offer}">${offerJobs}</div><div class="sl">已拿Offer</div></div>
    <div class="stat"><div class="sv">${offerRate}%</div><div class="sl">Offer率</div></div>
    <div class="stat"><div class="sv" style="color:${SCOLOR.interview}">${interviewJobs}</div><div class="sl">面试中</div></div>
    <div class="stat"><div class="sv">${weekDel}</div><div class="sl">近7天投递</div></div>
    <div class="stat ${dueFollow?'hot':''}"><div class="sv">${dueFollow}</div><div class="sl">待跟进</div></div>
  </div>
  ${dueFollow?`<div class="panel due-panel mt">
    <h3>🔔 今日待跟进 <span class="tag">${dueFollow} 条 ·  recruiter 常已读不回，主动跟进才有戏</span></h3>
    <div class="due-list">${due.map(d=>`<div class="due-item">
      <div class="di-main"><b>${esc(d.title||'职位')}</b> · ${esc(d.company||'-')}
        <span class="tiny">提醒日 ${esc((d.follow_at||'').slice(5))}</span></div>
      <button class="btn sm primary" onclick="clearFollow(${d.id})">已跟进</button></div>`).join('')}</div>
  </div>`:''}
  <div class="kanban mt">${cols}</div>
  <div class="panel mt">
    <h3>📤 投递流水 <span class="tag">${dels.length} 条 · 每次「去投递」自动记录，也可手动补录</span></h3>
    <div class="row mb wrap">
      <div class="chips">
        <button class="btn sm ${state.dfStat==='all'?'primary':''}" onclick="setDStat('all')">全部</button>
        <button class="btn sm ${state.dfStat==='follow'?'primary':''}" onclick="setDStat('follow')">待跟进</button>
        <button class="btn sm ${state.dfStat==='week'?'primary':''}" onclick="setDStat('week')">近7天</button>
      </div>
      <input id="dSearch" placeholder="🔍 搜公司 / 职位" value="${esc(state.dfQ)}" oninput="state.dfQ=this.value;renderTrackTable()" style="max-width:220px">
      <div class="spacer"></div>
      <button class="btn sm" onclick="openManualModal()">＋ 手动记录投递</button>
    </div>
    <div id="dTableWrap">${trackTableHTML()}</div>
  </div>`;
  $$('.kcol').forEach(col=>{
    col.addEventListener('dragover',e=>{e.preventDefault();col.classList.add('dragover');});
    col.addEventListener('dragleave',()=>col.classList.remove('dragover'));
    col.addEventListener('drop',async e=>{e.preventDefault();col.classList.remove('dragover');
      const id=+e.dataTransfer.getData('text');const st=col.dataset.st;
      await api('POST','/api/jobs/'+id,{status:st});toast('→'+SLABEL[st],'ok');renderTrack();});
  });
}
function todayStr(){const d=new Date();return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');}
function addDaysStr(n){const d=new Date();d.setDate(d.getDate()+n);return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');}
function trackTableHTML(){
  let rows=state.deliveries||[];
  if(state.dfStat==='follow') rows=rows.filter(d=>d.follow_at && d.follow_at<=todayStr());
  else if(state.dfStat==='week') rows=rows.filter(d=>daysSince(d.created_at)<=7);
  const q=(state.dfQ||'').trim().toLowerCase();
  if(q) rows=rows.filter(d=>(d.title||'').toLowerCase().includes(q)||(d.company||'').toLowerCase().includes(q));
  if(!rows.length) return '<div class="empty">没有符合条件的投递记录。</div>';
  return `<table><tr><th>时间</th><th>职位</th><th>公司</th><th>平台</th><th>城市</th><th>简历</th><th>跟进提醒</th><th>备注</th><th></th></tr>
    ${rows.map(d=>{const due=d.follow_at && d.follow_at<=todayStr();
      return `<tr class="${due?'due':''}">
        <td class="tiny">${esc((d.created_at||'').slice(0,16))}</td>
        <td>${esc(d.title||'职位')}</td><td>${esc(d.company||'-')}</td>
        <td><span class="pfbadge" style="background:${pf(d.platform_key).color}22;color:${pf(d.platform_key).color}">${pf(d.platform_key).icon} ${esc(pf(d.platform_key).name)}</span></td>
        <td>${esc(d.city||'-')}</td><td class="tiny">${esc(d.resume_used||'-')}</td>
        <td class="tiny ${due?'due-tag':''}">${d.follow_at?esc(d.follow_at.slice(5))+' 🔔':'—'}<br><button class="btn sm" onclick="openFollowModal(${d.id})">设</button></td>
        <td class="tiny note-cell">${esc(d.note||'—')}<br><button class="btn sm" onclick="editNote(${d.id})">📝</button></td>
        <td><button class="btn sm danger" onclick="delDelivery(${d.id})">撤</button></td>
      </tr>`;}).join('')}</table>`;
}
function renderTrackTable(){const w=$('#dTableWrap');if(w)w.innerHTML=trackTableHTML();}
function setDStat(s){state.dfStat=s;renderTrackTable();}
async function editNote(did){
  const d=(state.deliveries||[]).find(x=>x.id===did)||{};
  openModal(`<span class="close" onclick="closeModal()">×</span>
    <h3>📝 编辑跟进备注</h3>
    <textarea id="noteTa" rows="4" style="width:100%;font-size:15px;padding:8px;border-radius:8px;border:1px solid #d6dae3">${esc(d.note||'')}</textarea>
    <div class="row mt"><button class="btn primary" onclick="saveNote(${did})">保存</button><button class="btn" onclick="closeModal()">取消</button></div>`);
}
async function saveNote(did){
  const v=document.getElementById('noteTa').value;
  await api('PUT','/api/delivery/'+did,{note:v});
  closeModal();toast('备注已保存','ok');renderTrack();
}
function openFollowModal(did){
  const d=(state.deliveries||[]).find(x=>x.id===did)||{};
  openModal(`<span class="close" onclick="closeModal()">×</span>
    <h3>🔔 设置跟进提醒</h3>
    <div class="row mb">
      <button class="btn sm" onclick="setFollow(${did},3)">3天后</button>
      <button class="btn sm" onclick="setFollow(${did},7)">7天后</button>
      <button class="btn sm" onclick="setFollow(${did},14)">14天后</button>
    </div>
    <input id="followDate" type="date" value="${esc(d.follow_at||addDaysStr(3))}" style="font-size:15px;padding:6px">
    <div class="row mt"><button class="btn primary" onclick="setFollowCustom(${did})">确定</button>
      ${d.follow_at?`<button class="btn danger" onclick="clearFollow(${did})">清除提醒</button>`:''}
      <button class="btn" onclick="closeModal()">取消</button></div>`);
}
async function setFollow(did,days){await api('PUT','/api/delivery/'+did,{follow_at:addDaysStr(days)});closeModal();toast('已设 '+days+' 天后跟进','ok');renderTrack();}
async function setFollowCustom(did){const v=document.getElementById('followDate').value;if(!v){toast('请选择日期','err');return;}await api('PUT','/api/delivery/'+did,{follow_at:v});closeModal();toast('已设跟进提醒','ok');renderTrack();}
async function clearFollow(did){await api('PUT','/api/delivery/'+did,{follow_at:null});closeModal();toast('已清除提醒','ok');renderTrack();}
function openManualModal(){
  const plats=(state.platforms||[]).map(p=>`<option value="${esc(p.key)}">${p.icon} ${esc(p.name)}</option>`).join('');
  openModal(`<span class="close" onclick="closeModal()">×</span>
    <h3>＋ 手动记录投递</h3>
    <div class="field"><label>职位名称 *</label><input id="mTitle" placeholder="如：中药QC专员"></div>
    <div class="field"><label>公司</label><input id="mCompany" placeholder="如：云南白药"></div>
    <div class="field"><label>投递平台 / 渠道</label><select id="mPlat">${plats}<option value="">（无 / 其他渠道）</option></select></div>
    <div class="field"><label>城市</label><input id="mCity" placeholder="如：昆明"></div>
    <div class="field"><label>投递日期</label><input id="mDate" type="date" value="${todayStr()}"></div>
    <div class="field"><label>备注</label><input id="mNote" placeholder="内推人 / 进展…"></div>
    <div class="row mt"><button class="btn primary" onclick="submitManual()">保存记录</button><button class="btn" onclick="closeModal()">取消</button></div>`);
}
async function submitManual(){
  const title=document.getElementById('mTitle').value.trim();
  if(!title){toast('请填写职位名称','err');return;}
  const d={title,company:document.getElementById('mCompany').value.trim(),
    platform_key:document.getElementById('mPlat').value,
    city:document.getElementById('mCity').value.trim(),
    note:document.getElementById('mNote').value.trim(),
    created_at:document.getElementById('mDate').value||todayStr()};
  await api('POST','/api/deliveries',d);
  closeModal();toast('已记录投递','ok');renderTrack();
}
function drag(e){e.dataTransfer.setData('text',e.target.dataset.id);}

/* ================= 考试政策 / 残疾人通道 ================= */
async function renderExams(){
  const v=$('#view-exams');
  if(!state.resources) state.resources=await api('GET','/api/resources');
  if(!state.profile) state.profile=await api('GET','/api/profile');
  const R=state.resources;
  const regions=['全部',...R.provinces,'全国'];
  const srcs=R.sources.filter(s=>resFilterRegion==='全部'||s.region===resFilterRegion);
  const followed=(state.profile.followed_exams||[]);
  const radar=followed.slice().sort((a,b)=>(a.m||13)-(b.m||13));
  v.innerHTML=`
  <h2>📚 考试政策 · 信息枢纽</h2>
  <div class="sub">对标"公考雷达"——把分散在<b>四省人社厅 / 人事考试网 / 招考院 / 国家部委</b>的考试通知与政策福利入口集中到一处，随时可查，打破信息差。点任意卡片即跳转官方站点（首次打开可能需登录/验证，属平台方机制，非本工具问题）。</div>
  <div class="panel mb">
    <h3>🏛️ 官方信息源（接通人社厅）</h3>
    <div class="row mb">
      ${regions.map(r=>`<button class="btn sm ${resFilterRegion===r?'primary':''}" onclick="setResRegion('${r}')">${r==='全部'?'全部':(r+' ·')}</button>`).join('')}
    </div>
    <div class="res-grid">
      ${srcs.map(s=>`<a class="res-card" href="${esc(s.url)}" target="_blank" rel="noopener">
        <div class="rc-top"><span class="rc-kind">${esc(s.kind)}</span><span class="rc-region">${esc(s.region)}</span></div>
        <div class="rc-name">${esc(s.name)}</div>
        <div class="rc-note">${esc(s.note)}</div>
        <div class="rc-url">${esc(s.url)} ↗</div>
      </a>`).join('')}
    </div>
  </div>
  <div class="panel mb">
    <h3>🛰️ 我的考试雷达 <span class="tag">已关注 ${followed.length}</span></h3>
    ${radar.length?`<div class="radar-list">${radar.map(f=>`<div class="radar-item">
        <div class="ri-main"><a class="ei-name" href="${esc(f.url)}" target="_blank" rel="noopener">${esc(f.name)}</a><div class="ei-when">📅 ${esc(f.when||'以官方公告为准')}</div></div>
        <button class="ei-star on" onclick="toggleExamFollow('${esc(f.name)}','${esc(f.url)}','${esc(f.when||'')}',${f.m||13})">★ 取消关注</button>
      </div>`).join('')}</div>`
      :`<div class="tiny">还没关注考试。在下方目录点 <b>☆</b> 即可加入雷达——按时间排序、跨会话保存，像公考雷达一样盯住你的考试。</div>`}
  </div>
  <div class="panel mt">
    <h3>🎯 考试目录（国家 / 部门正式组织）</h3>
    <div class="row mb">
      <input id="examQ" placeholder="🔍 搜索考试，如：教师 / 银行 / 药师 / 公务员 / 编制" value="${esc(examQ)}" oninput="examQ=this.value;renderExamDir()" style="max-width:300px">
      <div class="spacer"></div>
      <div class="tiny">覆盖公务员/事业单位/教师/基层项目/国企央企/医疗健康/资格证/考研等；点名称直达官方站，☆ 加入雷达。</div>
    </div>
    <div id="examDir"></div>
  </div>`;
  renderExamDir();
}
function setResRegion(r){resFilterRegion=r;renderExams();}
function renderExamDir(){
  const box=$('#examDir'); if(!box) return;
  const R=state.resources; if(!R) return;
  const q=(examQ||'').trim().toLowerCase();
  const catOrder=['公务员','事业单位','教师','基层项目','国企央企','医疗健康','资格证','考研','其他'];
  const followed=(state.profile&&state.profile.followed_exams)||[];
  const isF=(n)=>followed.some(x=>x.name===n);
  const cats={};
  R.exams.forEach(e=>{
    if(q && !(e.name.toLowerCase().includes(q)||(e.note||'').toLowerCase().includes(q)||e.cat.toLowerCase().includes(q))) return;
    (cats[e.cat]=cats[e.cat]||[]).push(e);
  });
  if(!Object.keys(cats).length){box.innerHTML='<div class="empty">没有匹配「'+esc(examQ)+'」的考试，换个词试试。</div>';return;}
  box.innerHTML=catOrder.filter(c=>cats[c]).map(c=>`<div class="exam-cat"><div class="exam-cat-h">${esc(c)}</div>
    <div class="exam-list">${cats[c].map(e=>`<div class="exam-item">
      <div class="ei-main"><a class="ei-name" href="${esc(e.url)}" target="_blank" rel="noopener">${esc(e.name)}</a>
        <div class="exam-note">${esc(e.note)}</div>
        <div class="ei-when">📅 ${esc(e.when||'以官方公告为准')}</div></div>
      <button class="ei-star ${isF(e.name)?'on':''}" onclick="toggleExamFollow('${esc(e.name)}','${esc(e.url)}','${esc(e.when||'')}',${e.m||13})" title="加入考试雷达">${isF(e.name)?'★':'☆'}</button>
    </div>`).join('')}</div></div>`).join('');
}
async function toggleExamFollow(name,url,when,m){
  if(!state.profile) state.profile=await api('GET','/api/profile');
  const f=state.profile.followed_exams||[];
  const i=f.findIndex(x=>x.name===name);
  if(i>=0){f.splice(i,1);toast('已取消关注','ok');}
  else{f.push({name,url,when,m:m||13});toast('已加入考试雷达 ★','ok');}
  state.profile.followed_exams=f;
  await api('POST','/api/profile',{followed_exams:f});
  renderExams();
}
async function renderDisability(){
  const v=$('#view-disability');
  if(!state.resources) state.resources=await api('GET','/api/resources');
  const R=state.resources;
  const edus=['不限','大专','本科','硕士','博士'];
  const regions=['全部',...R.provinces,'全国'];
  v.innerHTML=`
  <h2>♿ 残疾人专项通道 · 政策福利</h2>
  <div class="sub">为残障朋友单独开的小通道。按<b>学历</b>筛出你能报考 / 可享的政策优惠；无论学历，<b>全国性的补贴、培训、就业援助</b>人人可享。点条目直达官方来源。</div>
  <div class="panel mb">
    <div class="row">
      <div class="field"><label>我的学历</label><select onchange="disEdu=this.value;renderDisability()" style="max-width:120px">${edus.map(e=>`<option ${disEdu===e?'selected':''}>${e}</option>`).join('')}</select></div>
      <div class="field"><label>地区</label><select onchange="disRegion=this.value;renderDisability()" style="max-width:120px">${regions.map(r=>`<option ${disRegion===r?'selected':''}>${r}</option>`).join('')}</select></div>
      <div class="field"><label>搜索</label><input id="disQ" placeholder="🔍 搜政策，如：补贴 / 培训 / 创业 / 助学" value="${esc(disQ)}" oninput="disQ=this.value;renderDisList()" style="max-width:220px"></div>
      <div class="spacer"></div>
      <div class="tiny" id="disCount"></div>
    </div>
  </div>
  <div class="res-grid" id="disList"></div>`;
  renderDisList();
}
function renderDisList(){
  const box=$('#disList'); if(!box) return;
  const R=state.resources; if(!R) return;
  const eduRank={'不限':0,'大专':1,'本科':2,'硕士':3,'博士':4};
  const q=(disQ||'').trim().toLowerCase();
  const list=R.disability.filter(b=>{
    const okEdu=b.edu==='不限'||eduRank[b.edu]<=eduRank[disEdu];
    const okRegion=disRegion==='全部'||b.region===disRegion||b.region==='全国';
    const okQ=!q||(b.title+b.note+b.region+b.edu).toLowerCase().includes(q);
    return okEdu&&okRegion&&okQ;
  });
  const c=$('#disCount'); if(c)c.textContent='共 '+list.length+' 项符合条件';
  box.innerHTML=list.length?list.map(b=>`<a class="benefit" href="${esc(b.url)}" target="_blank" rel="noopener">
      <div class="bn-top"><span class="bn-edu">${esc(b.edu)}</span><span class="bn-region">${esc(b.region)}</span></div>
      <div class="bn-title">${esc(b.title)}</div>
      <div class="bn-note">${esc(b.note)}</div>
      <div class="bn-url">${esc(b.url)} ↗</div>
    </a>`).join(''):'<div class="empty">该条件下暂无条目，放宽学历/地区或搜索词试试。</div>';
}

/* ================= 智能匹配 ================= */
async function renderMatch(){
  const v=$('#view-match');
  state.resumes=await api('GET','/api/resumes');
  state.jobs=await api('GET','/api/jobs');
  const def=state.resumes.find(r=>r.is_default)||state.resumes[0];
  const hiN=state.jobs.filter(j=>(j.match_score!=null&&j.match_score>=60)).length;
  v.innerHTML=`
  <h2>🎯 智能匹配</h2>
  <div class="sub">对全部职位计算<b>匹配度</b>——「按自己的条件找岗位」。<b>有简历自动用简历；没简历也能用</b>：在下方手动填专业 / 学历即可筛选。默认本地关键词引擎（离线可用）；设置开启 Ollama 后可调用本机 Qwen 深度分析。</div>
  <div class="panel mb">
    <h3>🎯 我的匹配背景</h3>
    <div class="row">
      <div>${def?`当前背景：<b>简历 · ${esc(def.name)}</b>${def.major?' · '+esc(def.major):''}${def.education?' · '+esc(def.education):''}`
        :(state.profile.manual_major?`当前背景：<b>手动 · ${esc(state.profile.manual_major)}</b>${state.profile.education&&state.profile.education!=='不限'?' · '+esc(state.profile.education):''}`
        :`尚未设置匹配背景`)}</div>
      <div class="spacer"></div>
      <button class="btn primary" onclick="matchAll()">⚡ 一键匹配全部 (${state.jobs.length})</button>
    </div>
    <div class="tiny mt">有简历自动用简历；无简历则用下方手动填的专业 / 学历。<b>两者都行</b>。设置开启 Ollama 后可调用本机 Qwen 深度分析。</div>
  </div>
  <div class="panel mb">
    <h3>📝 手动填写 / 补充背景（无简历也能用）</h3>
    <div class="tiny mb">填「专业」（必填）后点「用我填的专业筛选」，即按你的背景对全部职位算匹配度；学历 / 技能越全越准。已填内容会记住，下次自动带入。</div>
    <div class="row">
      <input id="mMajor" value="${esc(state.profile.manual_major||'')}" placeholder="专业，如：软件工程 / 汉语言文学" style="max-width:230px">
      <select id="mEdu" style="max-width:110px">
        ${["不限","大专","本科","硕士","博士"].map(e=>`<option value="${e}" ${(state.profile.education||'')===e?'selected':''}>${e}</option>`).join('')}
      </select>
      <input id="mSkills" value="${esc(state.profile.manual_skills||'')}" placeholder="技能（逗号分隔，可选）" style="max-width:190px">
      <button class="btn primary" onclick="matchManual()">🔍 用我填的专业筛选</button>
    </div>
    <input id="mKw" placeholder="附加关键词（逗号分隔，可选）" value="${esc(state.profile.manual_keywords||'')}" class="mt" style="max-width:520px">
  </div>
  <div class="match-filter">
    <button class="btn sm ${matchHighOnly?'primary':''}" onclick="toggleMatchHigh()">🔥 只看高匹配(≥60)</button>
    <button class="btn sm primary" onclick="matchBatchDeliver(60)">⚡ 一键投递高匹配(${hiN})</button>
    <span class="tiny">未匹配前先点「一键匹配全部」。点「详情」看命中技能与差距；高匹配岗位可一键投递。</span>
  </div>
  ${state.jobs.length?matchBandSummary(state.jobs):''}
  <div class="panel">
    <h3>职位匹配度排行</h3>
    ${(matchHighOnly?state.jobs.filter(j=>j.match_score!=null&&j.match_score>=60):state.jobs).length?`<table><tr><th>职位</th><th>公司</th><th>平台</th><th>匹配度</th><th></th></tr>
    ${[...(matchHighOnly?state.jobs.filter(j=>j.match_score!=null&&j.match_score>=60):state.jobs)].sort((a,b)=>(b.match_score||0)-(a.match_score||0)).map(j=>`
      <tr><td class="joblink" onclick="showJobDetail(${j.id})">${esc(j.title)}</td><td>${esc(j.company)}</td>
      <td><span class="pfbadge" style="background:${pf(j.platform_key).color}22;color:${pf(j.platform_key).color}">${pf(j.platform_key).icon} ${esc(pf(j.platform_key).name)}</span></td>
      <td><span class="score ${j.match_score>=50?'hi':j.match_score>=30?'mid':'lo'}" style="width:36px;height:36px;font-size:13px">${j.match_score!=null?j.match_score:'–'}</span></td>
      <td><button class="btn sm" onclick="matchOne(${j.id})">详情</button> <button class="btn sm green" onclick="applyJob(${j.id})">🚀 投递</button></td></tr>`).join('')}</table>`
    :'<div class="empty">没有 ≥60 的高匹配职位，放宽筛选或补充简历技能。</div>'}
  </div>`;
}
async function matchAll(){
  if(state.resumes.length){
    toast('匹配中…');
    await api('POST','/api/match_all');
    toast('全部匹配完成','ok');renderMatch();
    return;
  }
  const major=(document.getElementById('mMajor')?.value||'').trim();
  if(!major){toast('请先填写专业（必填），或上传简历后再匹配','err');return;}
  await matchManual();
}
async function matchManual(){
  const major=document.getElementById('mMajor').value.trim();
  if(!major){toast('请先填写专业（必填）','err');return;}
  const edu=document.getElementById('mEdu').value;
  const skills=document.getElementById('mSkills').value.trim();
  const kw=document.getElementById('mKw').value.trim();
  // 记住本次手动背景，跨会话复用（无简历用户的"简历替身"）
  await api('POST','/api/profile',{manual_major:major,manual_skills:skills,manual_keywords:kw,education:edu});
  if(state.profile){state.profile.manual_major=major;state.profile.manual_skills=skills;state.profile.manual_keywords=kw;state.profile.education=edu;}
  toast('匹配中…');
  await api('POST','/api/match_all',{manual:{major,education:edu,skills,keywords:kw}});
  toast('已按【'+major+(edu&&edu!=='不限'?' · '+edu:'')+'】匹配完成','ok');renderMatch();
}
function matchBatchDeliver(threshold=60){
  const top=state.jobs.filter(j=>j.match_score!=null&&j.match_score>=threshold&&!db_delivered(j.id));
  if(!top.length){toast('没有 ≥'+threshold+' 的高匹配岗位可投递，先点「一键匹配全部」','err');return;}
  if(!defaultResumeName()){toast('先去简历库上传并设为默认简历','err');goView('resumes');return;}
  state.selJobs=new Set(top.map(j=>j.id));
  updateSelCnt();
  toast('已选 '+top.length+' 个高匹配岗位，开始一键投递…','ok');
  batchDeliver();
}
function matchBandSummary(jobs){
  const matched=jobs.filter(j=>j.match_score!=null);
  const high=matched.filter(j=>j.match_score>=60).length;
  const mid=matched.filter(j=>j.match_score>=30&&j.match_score<60).length;
  const low=matched.filter(j=>j.match_score<30).length;
  const unmatched=jobs.length-matched.length;
  return `<div class="gap-summary">
    <span class="g" style="background:rgba(79,70,229,.08);border-color:rgba(79,70,229,.3);color:#3730a3">🔥 高匹配 ${high}</span>
    <span class="g" style="background:rgba(245,158,11,.1);border-color:rgba(245,158,11,.4);color:#92600a">⚡ 中匹配 ${mid}</span>
    <span class="g" style="background:rgba(239,68,68,.08);border-color:rgba(239,68,68,.3);color:#c0392b">低匹配 ${low}</span>
    ${unmatched?`<span class="g" style="background:rgba(107,115,135,.1);border-color:rgba(107,115,135,.3);color:#6b7385">未匹配 ${unmatched}</span>`:''}
  </div>`;
}
function toggleMatchHigh(){matchHighOnly=!matchHighOnly;renderMatch();}

/* ================= 备考时间线 ================= */
async function renderTimeline(){
  const v=$('#view-timeline');
  const ms=await api('GET','/api/milestones');
  const cats=TRACKS.map(([nm,ic,cat])=>cat);
  const t0=new Date();t0.setHours(0,0,0,0);
  const withDays=ms.map(m=>{const d=new Date(m.date+'T00:00:00');return {...m,days:Math.round((d-t0)/86400000)};});
  const byCat={};cats.forEach(c=>byCat[c]=(msOnlyUndone?withDays.filter(m=>!m.done):withDays).filter(m=>m.track===c).sort((a,b)=>a.date.localeCompare(b.date)));
  const tm={};TRACKS.forEach(([nm,ic,cat])=>tm[cat]={nm,ic});
  v.innerHTML=`
  <h2>🗓️ 备考时间线</h2>
  <div class="sub">四大赛道的报名 / 笔试 / 考试关键节点，已联网核实 2026-2027 周期（带"预计"的为推测，以官方公告为准）。红=30天内紧迫，橙=90天内，绿=已完成。</div>
  <div class="row mb">
    <button class="btn sm ${msOnlyUndone?'primary':''}" onclick="toggleMsUndone()">👁 ${msOnlyUndone?'显示全部':'只看未完成'}</button>
    <span class="tiny">共 ${withDays.length} 个节点 ${msOnlyUndone?'· 已隐藏已完成':''}</span>
  </div>
  ${monthCalHtml(withDays)}
  <div class="panel mb">
    <h3>➕ 新增节点</h3>
    <div class="field row2">
      <div><label>赛道</label><select id="msTrack">${cats.map(c=>`<option value="${c}">${tm[c].nm}</option>`).join('')}</select></div>
      <div><label>标题</label><input id="msTitle" placeholder="如：2027考研 打印准考证"></div>
    </div>
    <div class="field row2">
      <div><label>日期</label><input id="msDate" type="date"></div>
      <div><label>备注</label><input id="msNote" placeholder="可选，如官方入口/注意事项"></div>
    </div>
    <button class="btn primary" onclick="addMilestone()">添加节点</button>
  </div>
  ${cats.map(c=>`
    <div class="panel mt">
      <h3>${tm[c].ic} ${esc(tm[c].nm)} <span class="tag">${byCat[c].length} 个节点</span></h3>
      ${byCat[c].length?`<div class="ms-list">${byCat[c].map(msCard).join('')}</div>`:'<div class="empty">该赛道暂无节点，上面添加一条</div>'}
    </div>`).join('')}
  `;
}
function msCard(m){
  const cls=m.done?'done':(m.days<0?'past':(m.days<=30?'urg':m.days<=90?'soon':''));
  let tag=m.done?'已完成':(m.days<0?'已过 '+Math.abs(m.days)+' 天':'还有 '+m.days+' 天');
  return `<div class="ms ${cls}">
    <div class="ms-date">${esc(m.date)}</div>
    <div class="ms-body">
      <div class="ms-title">${esc(m.title)}</div>
      ${m.note?`<div class="ms-note">${esc(m.note)}</div>`:''}
    </div>
    <div class="ms-side">
      <div class="ms-tag">${tag}</div>
      <div class="row">
        <button class="btn sm" onclick="toggleMs(${m.id},${m.done?0:1})">${m.done?'↺ 重开':'✓ 完成'}</button>
        <button class="btn sm danger" onclick="delMs(${m.id})">删</button>
      </div>
    </div>
  </div>`;
}
async function addMilestone(){
  const body={track:$('#msTrack').value,title:$('#msTitle').value.trim(),date:$('#msDate').value,note:$('#msNote').value.trim()};
  if(!body.title||!body.date){toast('标题和日期必填','err');return;}
  await api('POST','/api/milestones',body);toast('已添加节点','ok');renderTimeline();
}
async function toggleMs(id,val){await api('POST','/api/milestones/'+id+'/toggle',{value:val});renderTimeline();}
async function delMs(id){if(!confirm('删除该节点？'))return;await api('DELETE','/api/milestones/'+id);toast('已删除');renderTimeline();}
function toggleMsUndone(){msOnlyUndone=!msOnlyUndone;renderTimeline();}
function monthCalHtml(msList){
  const t0=new Date();t0.setHours(0,0,0,0);
  const msByDate={};(msList||[]).forEach(x=>{(msByDate[x.date]=msByDate[x.date]||[]).push(x);});
  const week=['日','一','二','三','四','五','六'];
  let html='';
  for(let mo=0;mo<2;mo++){
    const cm=new Date(t0.getFullYear(),t0.getMonth()+mo,1);
    const yy=cm.getFullYear(),mm=cm.getMonth();
    const first=new Date(yy,mm,1).getDay();
    const days=new Date(yy,mm+1,0).getDate();
    let cells='';
    for(let i=0;i<first;i++)cells+=`<div class="cal-cell muted"></div>`;
    for(let d=1;d<=days;d++){
      const ds=`${yy}-${String(mm+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
      const has=msByDate[ds];
      const isToday=ds===t0.toISOString().slice(0,10);
      const cls=has?'checked':'';
      const title=has?has.map(x=>x.title).join('；'):'';
      cells+=`<div class="cal-cell ${cls} ${isToday?'today':''}" title="${esc(title)}">${d}${has?'<span style="position:absolute;bottom:2px;font-size:6px">'+'•'.repeat(Math.min(has.length,3))+'</span>':''}</div>`;
    }
    html+=`<div class="panel mt">
      <h3>📅 ${yy}年${mm+1}月 · 备考节点</h3>
      <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:5px;margin-bottom:5px">${week.map(w=>`<div class="cal-head">${w}</div>`).join('')}</div>
      <div class="cal-heat">${cells}</div>
      <div class="cal-leg"><span><i class="c2"></i>有节点</span><span><i class="c1"></i>无节点</span>${mo===0?'<span>🟠 今日</span>':''}</div>
    </div>`;
  }
  return html;
}

/* ================= 计划打卡（万能工作台） ================= */
function daysLeft(target){
  if(!target) return null;
  const t=new Date(target.replace(/-/g,'/')).getTime();
  const d=Math.ceil((t-Date.now())/86400000);
  return d;
}
function planCardHtml(p){
  const total=p.total||0, done=p.done||0;
  const pct=total?Math.round(done/total*100):0;
  const dl=daysLeft(p.target_date);
  const dlTxt=dl===null?'':(dl>0?`还剩 ${dl} 天`:(dl===0?'今天截止':'已过期'));
  const fire=p.streak>0?`<span class="fire">🔥 ${p.streak}天</span>`:`<span>未打卡</span>`;
  return `<div class="plan-card">
    <div class="pc-del" title="删除计划" onclick="delPlan(${p.id})">✕</div>
    <div class="pc-top">
      <div class="pc-ic">${p.smart?'🤖':'📌'}</div>
      <div><div class="pc-title">${esc(p.title)}</div>
      ${p.goal?`<div class="pc-goal">🎯 ${esc(p.goal)}</div>`:''}</div>
    </div>
    <div class="pc-prog"><i style="width:${pct}%"></i></div>
    <div class="pc-stats">
      <div class="pc-stat">进度 <b>${done}/${total}</b></div>
      <div class="pc-stat">连续打卡 ${fire}</div>
      ${dlTxt?`<div class="pc-stat">⏳ ${dlTxt}</div>`:''}
    </div>
    <div class="pc-acts">
      <button class="btn primary sm" onclick="openPlan(${p.id})">📂 打开 / 打卡</button>
    </div>
  </div>`;
}
async function renderPlans(){
  const v=$('#view-plans');
  const plans=await api('GET','/api/plans');
  v.innerHTML=`<h2>📅 计划打卡</h2>
    <div class="sub">不论备考、减肥、学技能还是准备任何事，都能自定义或一键智能生成阶段计划，每天来打卡，看着进度条一点点涨。</div>
    <div class="row mb">
      <button class="btn primary" onclick="openGenerateModal()">✨ 智能生成计划</button>
      <button class="btn" onclick="openNewPlanModal()">➕ 新建空白计划</button>
    </div>
    ${plans.length?`<div class="plan-grid">${plans.map(planCardHtml).join('')}</div>`
      :`<div class="empty">还没有计划。点「智能生成计划」填个目标（如：考研 / 教资 / 减肥），马上帮你排好执行表 🚀</div>`}`;
}
async function openPlan(pid){
  const p=await api('GET','/api/plans/'+pid);
  if(!p){toast('计划不存在','err');return;}
  const total=p.total||0, done=p.done||0;
  const pct=total?Math.round(done/total*100):0;
  const dl=daysLeft(p.target_date);
  const dlTxt=dl===null?'':(dl>0?`还剩 ${dl} 天`:(dl===0?'今天截止':'已过期'));
  const today=new Date().toISOString().slice(0,10);
  const checkedToday=p.checkins.some(c=>c.date===today);
  const tasks=p.tasks.map(t=>`
    <div class="task ${t.done?'done':''}">
      <div class="cb ${t.done?'on':''}" onclick="togglePlanTask(${p.id},${t.id})">${t.done?'✓':''}</div>
      <div class="tc">${esc(t.content)}</div>
      <div class="tdue">${t.due_date||''}</div>
      <div class="tdel" title="删除任务" onclick="delPlanTask(${p.id},${t.id})">✕</div>
    </div>`).join('');
  const hist=p.checkins.slice(-12).map(c=>`<span class="checkin-dot ${c.date===today?'today':''}">${c.date.slice(5)}</span>`).join('')||'<span class="tiny">还没有打卡记录</span>';
  openModal(`<div class="plan-detail">
    <div class="pd-head"><span class="pd-title">${esc(p.title)}</span> ${p.smart?'<span class="chip g">智能生成</span>':''}</div>
    <div class="pd-meta">🎯 ${esc(p.goal||'自定义计划')}　·　🗓️ ${p.start_date||'—'} → ${p.target_date||'—'} ${dlTxt?('· '+dlTxt):''}</div>
    <div class="pc-prog" style="margin-bottom:8px"><i style="width:${pct}%"></i></div>
    ${planBadges(p)}
    <div class="task-add">
      <input id="pta" placeholder="添加一项任务，如：做完两套真题" onkeydown="if(event.key==='Enter')addPlanTask(${p.id})">
      <button class="btn primary" onclick="addPlanTask(${p.id})">添加</button>
    </div>
    <div class="tasks">${tasks||'<div class="tiny">暂无任务，上面添加或靠智能生成。</div>'}</div>
    <div class="checkin-bar">
      <div class="cbtn" onclick="doCheckin(${p.id})">${checkedToday?'✅ 今日已打卡':'📍 今日打卡'}</div>
      ${checkedToday?'<span class="cdone">连续 '+p.streak+' 天，稳住！</span>':'<span class="tiny">每天来一下，连续打卡看得见的坚持。</span>'}
    </div>
    <div class="checkin-history">${hist}</div>
    ${planHeatHtml(p)}
    <div style="margin-top:16px;text-align:right"><button class="btn ghost sm" onclick="delPlan(${p.id})">🗑️ 删除整个计划</button></div>
  </div>`);
}
function _pp(){return document.getElementById('pta');}
async function addPlanTask(pid){
  const el=document.getElementById('pta'); if(!el)return;
  const content=el.value.trim(); if(!content){toast('任务内容不能为空');return;}
  await api('POST','/api/plans/'+pid+'/tasks',{content});
  await openPlan(pid);
}
async function togglePlanTask(pid,tid){await api('POST','/api/plans/'+pid+'/tasks/'+tid);await openPlan(pid);}
async function delPlanTask(pid,tid){await api('DELETE','/api/plans/'+pid+'/tasks/'+tid);await openPlan(pid);}
async function doCheckin(pid){await api('POST','/api/plans/'+pid+'/checkin',{note:''});await openPlan(pid);toast('打卡成功 🔥','ok');}
async function delPlan(pid){if(!confirm('删除该计划及其全部任务/打卡？'))return;await api('DELETE','/api/plans/'+pid);toast('已删除');renderPlans();}
function planBadges(p){
  const b=[];
  if(p.streak>=30) b.push({t:'🏆 连续30天',c:'gold'});
  else if(p.streak>=7) b.push({t:'🔥 连续7天',c:''});
  if(p.total>0 && p.done===p.total) b.push({t:'✅ 计划达成',c:'green'});
  if(p.total>=10) b.push({t:'📋 任务满满',c:''});
  if(!b.length) b.push({t:'🌱 刚刚开始',c:''});
  return `<div class="plan-badges">${b.map(x=>`<span class="pbadge ${x.c}">${x.t}</span>`).join('')}</div>`;
}
function planHeatHtml(p){
  const set=new Set((p.checkins||[]).map(c=>c.date));
  const t0=new Date();t0.setHours(0,0,0,0);
  const yy=t0.getFullYear(),mm=t0.getMonth();
  const first=new Date(yy,mm,1).getDay();
  const days=new Date(yy,mm+1,0).getDate();
  const week=['日','一','二','三','四','五','六'];
  let cells='';
  for(let i=0;i<first;i++)cells+=`<div class="cal-cell muted"></div>`;
  for(let d=1;d<=days;d++){
    const ds=`${yy}-${String(mm+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
    const on=set.has(ds);
    const isToday=ds===t0.toISOString().slice(0,10);
    cells+=`<div class="cal-cell ${on?'checked':''} ${isToday?'today':''}" title="${on?'已打卡':''}">${d}</div>`;
  }
  return `<div class="panel" style="padding:14px 16px;margin-top:14px">
    <h3 style="font-size:14px;margin-top:0">📅 ${yy}年${mm+1}月 打卡热力图</h3>
    <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:5px;margin-bottom:5px">${week.map(w=>`<div class="cal-head">${w}</div>`).join('')}</div>
    <div class="cal-heat">${cells}</div>
    <div class="cal-leg"><span><i class="c2"></i>已打卡</span><span><i class="c1"></i>未打卡</span><span>🟠 今日</span></div>
  </div>`;
}
function planFormCommon(extra){
  const today=new Date().toISOString().slice(0,10);
  return `<div class="field"><label>目标 / 主题</label><input id="pfGoal" placeholder="如：考研 / 教资 / 减肥 / 学Python"></div>
    <div class="field row2"><div><label>开始日期</label><input id="pfStart" type="date" value="${today}"></div>
    <div><label>目标日期</label><input id="pfEnd" type="date"></div></div>${extra||''}`;
}
function openNewPlanModal(){
  openModal(`<h3>➕ 新建空白计划</h3>${planFormCommon()}<div class="field"><label>计划名称（可选）</label><input id="pfTitle" placeholder="留空则用目标名"></div>
    <div class="row" style="justify-content:flex-end;margin-top:8px"><button class="btn ghost" onclick="closeModal()">取消</button><button class="btn primary" onclick="createPlan()">创建</button></div>`);
}
function openGenerateModal(){
  openModal(`<h3>✨ 智能生成计划</h3><div class="warn" style="margin-bottom:14px">填写目标与倒计时，系统会按目标类型（考研/考公/教资/语言/会计/法考/医护/健身…）自动拆解成「准备→基础→强化→冲刺→复盘」阶段任务并排好日期。</div>
    ${planFormCommon()}<div class="row" style="justify-content:flex-end;margin-top:8px"><button class="btn ghost" onclick="closeModal()">取消</button><button class="btn primary" onclick="generatePlan()">🤖 智能生成</button></div>`);
}
async function createPlan(){
  const goal=document.getElementById('pfGoal').value.trim();
  if(!goal){toast('请填写目标','err');return;}
  const body={goal,start_date:document.getElementById('pfStart').value,target_date:document.getElementById('pfEnd').value};
  const t=document.getElementById('pfTitle').value.trim(); if(t)body.title=t;
  const r=await api('POST','/api/plans',body);
  closeModal();toast('计划已创建','ok');renderPlans();if(r&&r.id)openPlan(r.id);
}
async function generatePlan(){
  const goal=document.getElementById('pfGoal').value.trim();
  if(!goal){toast('请填写目标','err');return;}
  const body={goal,start_date:document.getElementById('pfStart').value,target_date:document.getElementById('pfEnd').value};
  const r=await api('POST','/api/plans/generate',body);
  closeModal();toast('已智能生成 '+((r&&r.generated)||0)+' 项任务 🚀','ok');renderPlans();if(r&&r.id)openPlan(r.id);
}

/* ================= 设置 ================= */
async function renderSettings(){
  const v=$('#view-settings');
  state.profile=await api('GET','/api/profile');
  const p=state.profile;
  v.innerHTML=`
  <h2>⚙️ 设置</h2>
  <div class="sub">你的求职画像、平台模板、数据与 AI 模型配置都在这儿。</div>
  <div class="grid cards-2">
    <div class="panel">
      <h3>👤 求职画像</h3>
      <div class="field"><label>姓名</label><input id="spName" value="${esc(p.name)}"></div>
      <div class="field"><label>目标方向</label><input id="spTitle" value="${esc(p.target_title)}"></div>
      <div class="field"><label>专业关键词（逗号分隔，用于搜索+匹配）</label><textarea id="spKw" rows="2">${esc(p.keywords)}</textarea></div>
      <div class="field"><label>所在省份</label>
        <select id="spProv">${provOptions()}</select>
      </div>
      <div class="field"><label>搜索城市（云贵川桂四省州市）</label>
        <select id="spCity">${cityOptions()}</select>
        <div class="tiny mt">面向云南/贵州/四川/广西四省；城市码/拼音由系统按州市自动映射；选「全省」则外部搜索以省会为基准，全省真实岗位见「职位看板」。</div>
      </div>
      <div class="field"><label>学历层次（用于无简历时的智能筛选）</label>
        <select id="spEdu">
          ${["不限","大专","本科","硕士","博士"].map(e=>`<option value="${e}" ${p.education===e?'selected':''}>${e}</option>`).join('')}
        </select>
      </div>
      <div class="field"><label>屏蔽公司（逗号分隔）</label><textarea id="spBl" rows="2">${esc(p.blacklist||'')}</textarea></div>
      <button class="btn primary" onclick="saveProfile()">保存画像</button>
    </div>
    <div class="panel">
      <h3>🤖 本地 AI（可选）</h3>
      <div class="warn">调用你本机 Ollama 的 Qwen 模型做深度人岗分析。关闭时自动用本地关键词引擎，零依赖、永不联网。</div>
      <div class="field row2"><div><label>Ollama 地址</label><input id="spOllamaUrl" value="${esc(p.ollama_url)}"></div>
        <div><label>模型名</label><input id="spOllamaModel" value="${esc(p.ollama_model)}"></div></div>
      <div class="field"><label>启用 Ollama 深度匹配</label>
        <div class="switch ${p.ollama_enabled?'on':''}" id="spOllamaOn" onclick="this.classList.toggle('on')" style="margin-top:6px"></div></div>
      <div class="field"><label>🔔 浏览器桌面提醒（临近备考节点）</label>
        <div class="row">
          <div class="switch ${p.notify_enabled?'on':''}" id="spNotify" onclick="this.classList.toggle('on')" style="margin-top:6px"></div>
          <button class="btn sm" onclick="requestNotify()">开启并授权</button>
          <button class="btn sm" onclick="testNotify()">测试</button>
        </div>
        <div class="tiny mt">开启后，临近 30 天内的备考节点会推送到系统通知（需浏览器授权）。</div>
      </div>
      <button class="btn primary" onclick="saveProfile()">保存 AI 配置</button>
    </div>
  </div>
  <div class="panel mt">
    <h3>🛡️ 投递保护（防平台风控）</h3>
    <div class="tiny mb">一键投递太猛容易被 BOSS / 智联等平台判定为机器操作、限流甚至封号。设置每日上限后，超过会自动停下并提示，保护账号安全。</div>
    <div class="field"><label>每日最多投递（个，0 = 不限制）</label><input id="spCap" type="number" min="0" value="${(state.profile&&state.profile.daily_cap)||0}" style="max-width:120px"></div>
    <div class="tiny mt">建议值：新号 / 冷号 10–20，老号 30–50。配合「逐个打开平台页、人工点提交」更稳妥。已在职位看板实时显示「今日已投 X / N」。</div>
    <button class="btn primary" onclick="saveProfile()">保存设置</button>
  </div>
  <div class="panel mt">
    <h3>🗄️ 数据与演示</h3>
    <div class="row">
      <a class="btn" href="/api/export">📤 导出全部数据(JSON)</a>
      <button class="btn" onclick="loadDemo()">✨ 载入演示职位(云贵川广西多行业)</button>
      <button class="btn danger" onclick="resetDemo()">🗑️ 清空职位</button>
    </div>
    <div class="tiny mt">演示数据用于开箱验证；清空后保留简历/平台/画像。</div>
  </div>`;
}
async function saveProfile(){
  const body={
    name:$('#spName').value,target_title:$('#spTitle').value,keywords:$('#spKw').value,
    province:$('#spProv').value,city_name:$('#spCity').value,education:$('#spEdu').value,
    blacklist:$('#spBl').value,
    ollama_url:$('#spOllamaUrl').value,ollama_model:$('#spOllamaModel').value,
    ollama_enabled:$('#spOllamaOn').classList.contains('on'),
    notify_enabled:$('#spNotify')?$('#spNotify').classList.contains('on'):false,
    daily_cap:parseInt($('#spCap').value||'0',10)||0
  };
  await api('POST','/api/profile',body);toast('已保存','ok');init();
}
async function loadDemo(){const r=await api('POST','/api/demo');toast('已载入 '+r.imported+' 条演示职位','ok');renderJobs();}
async function resetDemo(){
  if(!confirm('清空所有职位（保留简历/平台/画像）？'))return;
  await api('POST','/api/reset');
  toast('职位已清空','ok');renderJobs();
}

/* ================= 公开访问（无需登录） ================= */
async function boot(){
  // 公开版：任何人直接进，数据按浏览器访客标识隔离
  await init();
}
async function clearMyData(){
  if(!confirm('清空本浏览器的简历 / 收藏 / 投递记录？此操作不可恢复。'))return;
  const r=await api('DELETE','/api/my_data');
  toast('已清空你的数据（'+ (r.cleared||0) +' 条）','ok');
  await init();
}
boot();
