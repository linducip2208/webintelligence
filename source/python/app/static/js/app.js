/* WebIntel shared frontend utils (globals). No framework, Tabler CSS only. */
const $=s=>document.querySelector(s);
const $$=s=>Array.from(document.querySelectorAll(s));
function H(){const t=($('#tok')&&$('#tok').value||'').trim();if(!t)return{'Content-Type':'application/json'};
return t.startsWith('wi_')?{'X-API-Key':t,'Content-Type':'application/json'}:{'Authorization':'Bearer '+t,'Content-Type':'application/json'};}
async function api(p,o={}){o.headers={...H(),...(o.headers||{})};const r=await fetch(p,o);if(!r.ok)throw new Error(r.status+' '+(await r.text()).slice(0,300));const t=await r.text();try{return JSON.parse(t)}catch{return t}}
async function post(p,b){return api(p,{method:'POST',body:JSON.stringify(b)})}
async function put(p,b){return api(p,{method:'PUT',body:JSON.stringify(b)})}
async function del(p){return api(p,{method:'DELETE'})}
function esc(s){return String(s??'').replace(/[<>&]/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;'}[c])).slice(0,500)}
function toast(m){const box=$('#toasts');if(!box)return;const d=document.createElement('div');d.className='toast';d.textContent=m;box.appendChild(d);setTimeout(()=>d.remove(),4500);}
function fmtDT(v){if(v==null||v==='')return'—';let t=null;if(typeof v==='number'){t=v>1e12?v:v*1000;}else{const ms=Date.parse(v);if(!isNaN(ms))t=ms;else return String(v).slice(0,19);}try{const s=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Jakarta',day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(t));return s.replace(',','')+' WIB';}catch(e){return new Date(t).toLocaleString();}}
function ago(v){if(!v)return'—';let t=typeof v==='number'?(v>1e12?v:v*1000):new Date(v).getTime();if(isNaN(t))return'—';const s=Math.max(0,(Date.now()-t)/1000);if(s<60)return Math.floor(s)+'s ago';if(s<3600)return Math.floor(s/60)+'m ago';if(s<86400)return Math.floor(s/3600)+'h ago';return Math.floor(s/86400)+'d ago';}
/* Semantic badges: Tabler tinted badges, always icon-dot + text label (never color alone). */
const SEVMAP={critical:'red',high:'orange',medium:'yellow',low:'green',info:'cyan',informational:'cyan'};
function badge(status){const m=String(status||'').toLowerCase();
if(SEVMAP[m])return `<span class="badge bg-${SEVMAP[m]}-lt"><span class="bi">●</span>${esc(status)}</span>`;
const ok=['success','done','active','enabled','up','healthy','passed','connected','published','resolved','confirmed','ready','ok','open'];
const bad=['failed','error','down','disabled','paused','cancelled','false_positive','dismissed'];
const warn2=['queued','running','planned','pending','planned...','running...','unverified','needs_review','generating','acked','acknowledged','draft'];
const intel=['investigating','accepted','reviewing','personal','threat','finding'];
if(ok.includes(m))return `<span class="badge bg-green-lt"><span class="bi">●</span>${esc(status)}</span>`;
if(bad.includes(m))return `<span class="badge bg-red-lt"><span class="bi">●</span>${esc(status)}</span>`;
if(warn2.includes(m))return `<span class="badge bg-azure-lt"><span class="bi spin-pulse">●</span>${esc(status)}</span>`;
if(intel.includes(m))return `<span class="badge bg-purple-lt"><span class="bi">●</span>${esc(status)}</span>`;
return `<span class="badge bg-blue-lt">${esc(status||'—')}</span>`;}
function sevClass(s){s=String(s||'info').toLowerCase();return 'sev-'+(SEVMAP[s]?s:'info');}
/* ---- modal ---- */
function openModal(html){let m=$('#modal-root');if(!m){m=document.createElement('div');m.id='modal-root';document.body.appendChild(m);}
m.innerHTML=`<div style="position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:2000;display:flex;align-items:flex-start;justify-content:center;overflow:auto;padding:2rem 1rem" onclick="if(event.target===this)closeModal()"><div class="card" style="width:100%;max-width:680px" role="dialog" aria-modal="true"><div class="card-body">${html}</div></div></div>`;
const f=m.querySelector('input,select,textarea,button');if(f)f.focus();}
function closeModal(){const m=$('#modal-root');if(m)m.innerHTML='';}
document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeModal();if(typeof aiModalClose==='function')aiModalClose();}});
function confirmDlg(msg){return Promise.resolve(confirm(msg));}
function field(label,name,value='',opts={}){const t=opts.type||'text';const extra=opts.extra||'';
if(opts.options)return `<label class="form-label">${esc(label)}</label><select name="${name}" class="form-select mb-2" ${extra}>${opts.options.map(o=>{const v=Array.isArray(o)?o[0]:o,l=Array.isArray(o)?o[1]:o;return `<option value="${esc(v)}" ${String(value)===String(v)?'selected':''}>${esc(l)}</option>`}).join('')}</select>`;
if(t==='textarea')return `<label class="form-label">${esc(label)}</label><textarea name="${name}" class="form-control mb-2" rows="${opts.rows||3}" ${extra}>${esc(value)}</textarea>`;
return `<label class="form-label">${esc(label)}</label><input name="${name}" type="${t}" value="${esc(value)}" class="form-control mb-2" ${extra}>`;}
function formVals(form){const o={};new FormData(form).forEach((v,k)=>{o[k]=v});return o;}
/* ---- generic searchable/sortable/paginated table state ---- */
function pgState(key,per=20){const st={q:'',sort:'',order:'asc',page:1,per,sel:new Set()};
st.apply=rows=>{let r=rows;
if(st.q){const q=st.q.toLowerCase();r=r.filter(x=>JSON.stringify(x).toLowerCase().includes(q));}
if(st.sort){const k=st.sort,rev=st.order==='desc';r=[...r].sort((a,b)=>{const x=a[k],y=b[k];if(x==null&&y==null)return 0;if(x==null)return 1;if(y==null)return-1;const c=(typeof x==='number'&&typeof y==='number')?x-y:String(x).localeCompare(String(y));return rev?-c:c;});}
st.total=r.length;const pages=Math.max(1,Math.ceil(r.length/st.per));if(st.page>pages)st.page=pages;
return r.slice((st.page-1)*st.per,st.page*st.per);};
return st;}
function pgSearch(stName,v){const st=window[stName];if(!st)return;st.q=v;st.page=1;window._pgFocus=true;_debRefresh();}
const _debRefresh=debounce(()=>{refreshView();if(window._pgFocus){window._pgFocus=false;const q=$('#qsearch');if(q){try{q.focus();q.setSelectionRange(q.value.length,q.value.length);}catch(e){}}}},350);
function pgBar(stName){const st=window[stName];const pages=Math.max(1,Math.ceil((st.total||0)/st.per));
return `<div class="d-flex align-items-center gap-2 mt-2 flex-wrap"><input id="qsearch" class="form-control form-control-sm" style="max-width:220px" placeholder="Search…" value="${esc(st.q)}" oninput="pgSearch('${esc(stName)}',this.value)" aria-label="search">
<span class="text-muted small">${st.total||0} rows · page ${st.page}/${pages}</span>
<button class="btn btn-sm" ${st.page<=1?'disabled':''} onclick="window['${esc(stName)}'].page--;refreshView()">‹ Prev</button>
<button class="btn btn-sm" ${st.page>=pages?'disabled':''} onclick="window['${esc(stName)}'].page++;refreshView()">Next ›</button></div>`;}
function th(label,key,stName){return `<th data-sort="${esc(key)}" data-st="${esc(stName)}" style="cursor:pointer;white-space:nowrap" onclick="pgSort('${esc(stName)}','${esc(key)}')">${esc(label)}<span data-sort-arrow></span></th>`;}
function pgSort(stName,key){const st=window[stName];if(!st)return;if(st.sort===key){st.order=st.order==='asc'?'desc':'asc';}else{st.sort=key;st.order='asc';}refreshView();}
function paintArrows(){$$('th[data-sort]').forEach(h=>{const st=window[h.dataset.st];const a=h.querySelector('[data-sort-arrow]');if(!a)return;a.textContent=(st&&st.sort===h.dataset.sort)?(st.order==='asc'?' ▲':' ▼'):'';});}
function downloadCSV(name,rows,cols){const q=v=>`"${String(v??'').replace(/"/g,'""')}"`;
const csv=[cols.join(',')].concat(rows.map(r=>cols.map(c=>q(typeof c==='string'?r[c]:c(r))).join(','))).join('\n');
const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),5000);}
function downloadJSON(name,obj){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(obj,null,1)],{type:'application/json'}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),5000);}
const SEV_COLORS={critical:'#e5484d',high:'#f76b15',medium:'#ffb224',low:'#46a758',info:'#8e8e93'};
function barChart(rows,{w=560,h=120,colors=null}={}){if(!rows.length)return '<div class="empty">No data.</div>';
const mx=Math.max(...rows.map(r=>r[1]),1);const bw=Math.max(2,(w-40)/rows.length);
const bars=rows.map(([l,v],i)=>{const bh=Math.max(2,(h-30)*v/mx);const x=40+i*bw;
const fill=(colors&&(colors[l]||colors[String(l).toLowerCase()]))||'#206bc4';
return `<rect x="${x.toFixed(1)}" y="${(h-20-bh).toFixed(1)}" width="${(bw-2).toFixed(1)}" height="${bh.toFixed(1)}" fill="${fill}"><title>${esc(l)}: ${v}</title></rect>`;}).join('');
return `<svg viewBox="0 0 ${w} ${h}" style="width:100%" role="img">${bars}<line x1="40" y1="${h-20}" x2="${w}" y2="${h-20}" stroke="currentColor" opacity=".3"/></svg>`;}
function debounce(fn,ms){let t;return(...a)=>{clearTimeout(t);t=setTimeout(()=>fn(...a),ms);};}
function shortId(id){return esc(String(id||'').slice(0,8));}
/* ---- long-operation button feedback: spinner + live elapsed timer ---- */
function busy(btn,label){if(!btn||btn.disabled)return()=>{};const orig=btn.innerHTML;btn.disabled=true;const t0=Date.now();
btn.innerHTML=`<span class="spinner-border spinner-border-sm me-1" role="status"></span>${esc(label||'Working…')} <span data-elapsed class="text-muted">0s</span>`;
const iv=setInterval(()=>{const el=btn.querySelector('[data-elapsed]');if(el)el.textContent=Math.floor((Date.now()-t0)/1000)+'s';},500);
return ()=>{clearInterval(iv);if(btn.isConnected){btn.disabled=false;btn.innerHTML=orig;}};}
/* ---- session (memory-only token; never localStorage) ---- */
function getToken(){return window._wiToken||'';}
function setToken(t){window._wiToken=t||'';const chip=$('#userchip');if(chip)chip.innerHTML=t?'<span class="status ok">● signed in</span>':'<span class="text-muted small">anonymous</span>';}
function H(){const t=getToken()||($('#tok')&&$('#tok').value||'').trim();if(!t)return{'Content-Type':'application/json'};
return t.startsWith('wi_')?{'X-API-Key':t,'Content-Type':'application/json'}:{'Authorization':'Bearer '+t,'Content-Type':'application/json'};}
/* ---- hardened API client: timeout, offline, slow-notice, request ids ---- */
function _rid(){return Math.random().toString(36).slice(2,10);}
async function api(p,o={}){
if(!navigator.onLine)throw new Error('offline: connection lost. Reconnect and retry.');
const ctl=new AbortController();const to=setTimeout(()=>ctl.abort(),o.timeout||60000);
let slow=null;const slowMs=o.slowAfter||10000;
slow=setTimeout(()=>{try{toast('Taking longer than expected… you can keep waiting.');}catch(e){}},slowMs);
try{
o.headers={...H(),...(o.headers||{}),'X-Request-ID':_rid()};
const r=await fetch(p,{...o,signal:ctl.signal});
const rid=r.headers.get('X-Request-ID')||'';
if(!r.ok){const txt=(await r.text()).slice(0,500);const err=new Error(`${r.status} ${txt}`);err.requestId=rid;err.status=r.status;throw err;}
const t=await r.text();try{return JSON.parse(t)}catch{return t}
}catch(e){
if(e.name==='AbortError'){const err=new Error('timeout: no response within 60s');err.requestId='';throw err;}
if(String(e.message||'').startsWith('offline'))throw e;
throw e;
}finally{clearTimeout(to);clearTimeout(slow);}}
/* ---- global error boundary ---- */
(function(){let last=0;
function report(msg,src){const now=Date.now();if(now-last<3000)return;last=now;
try{toast('Something went wrong. '+(msg||'').slice(0,160));}catch(e){}
try{console.error('[webintel]',msg,src||'');}catch(e){}}
window.addEventListener('error',e=>report(e.message,e.filename+':'+e.lineno));
window.addEventListener('unhandledrejection',e=>report((e.reason&&(e.reason.message||e.reason))||'request failed','promise'));})();
/* ---- runAction: try → staged operation → request → success/failure ---- */
async function runAction({btn,title,stages,fn,onDone}={}){
const done=busy(btn,(stages&&stages[0])||title||'Working…');
const op=opStart(title||'Operation');
try{
if(stages&&stages.length>1){let i=0;op._stageIv=setInterval(()=>{i=Math.min(i+1,stages.length-1);opStage(op.id,stages[i]);},1500);}
const out=await fn(op);
opDone(op.id,out&&out.link);
if(onDone)onDone(out);
return out;
}catch(e){opFail(op.id,e);throw e;
}finally{done();clearInterval(op._stageIv);if(btn&&btn.isConnected){/* restored by done() */}}}
/* ---- global operation center (drawer, polling, toasts w/ links) ---- */
window._ops={};
function opStart(title){const id='op'+Date.now().toString(36)+Math.floor(Math.random()*99);
window._ops[id]={id,title: title||'Operation',stage:'starting',t0:Date.now(),status:'running'};
opRender();return window._ops[id];}
function opStage(id,stage){const o=window._ops[id];if(!o||o.status!=='running')return;o.stage=stage;o.t=(o.t||0)+1;opRender();}
function opDone(id,link){const o=window._ops[id];if(!o)return;o.status='success';o.ms=Date.now()-o.t0;opRender();
toast(`✓ ${o.title} (${(o.ms/1000).toFixed(1)}s)`);setTimeout(()=>{delete window._ops[id];opRender();},30000);}
function opFail(id,e){const o=window._ops[id];if(!o)return;o.status='failed';o.ms=Date.now()-o.t0;
o.error=String((e&&(e.message||e))||'failed').slice(0,300);o.requestId=e&&e.requestId?e.requestId:'';opRender();
toast(`✕ ${o.title}: ${o.error.slice(0,160)}`);}
function opToggle(force){const d=$('#opsdrawer');if(!d)return;const show=force!=null?force:d.style.display==='none';
d.style.display=show?'block':'none';if(show)opRefresh();}
async function opRefresh(){try{const r=await api('/api/v1/operations?size=10');window._opsServer=r.items||[];}catch(e){window._opsServer=[];}opRender();}
function opRender(){const host=$('#opslist');if(!host)return;const live=Object.values(window._ops);
const items=live.concat((window._opsServer||[]).map(s=>({id:String(s.id),title:s.title,stage:s.status,stale:true})));
host.innerHTML=items.length?items.slice(0,12).map(o=>`<div class="d-flex gap-2 align-items-center mb-1"><span class="status ${o.status==='success'?'ok':o.status==='failed'?'err':'warn'}">${esc(o.status||o.stage||'running')}</span><span class="text-truncate" style="max-width:220px">${esc(o.title||o.id)}</span><span class="text-muted small ms-auto">${o.ms!=null?(o.ms/1000).toFixed(1)+'s':''}</span></div>`).join(''):'<div class="text-muted small">No operations yet.</div>';
const n=live.filter(o=>o.status==='running').length;const b=$('#opsbadge');if(b){b.textContent=n||'';b.style.display=n?'inline-block':'none';}}
setInterval(()=>{const d=$('#opsdrawer');if(d&&d.style.display==='block')opRefresh();},5000);
/* Note: dropdown/collapse/modal behavior comes from the Bootstrap JS bundled
   inside /static/vendor/tabler/tabler.min.js (it auto-wires
   [data-bs-toggle="dropdown"|"collapse"]). Do NOT add a second toggle
   handler here — double toggles instantly close menus. */
