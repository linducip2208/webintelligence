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
function fmtDT(v){if(v==null||v==='')return'—';let t=null;if(typeof v==='number'){t=v>1e12?v:v*1000;}else{const d=new Date(v);if(!isNaN(d))return d.toLocaleString();return String(v).slice(0,19);}return new Date(t).toLocaleString();}
function ago(v){if(!v)return'—';let t=typeof v==='number'?(v>1e12?v:v*1000):new Date(v).getTime();if(isNaN(t))return'—';const s=Math.max(0,(Date.now()-t)/1000);if(s<60)return Math.floor(s)+'s ago';if(s<3600)return Math.floor(s/60)+'m ago';if(s<86400)return Math.floor(s/3600)+'h ago';return Math.floor(s/86400)+'d ago';}
function badge(status){const m=String(status||'').toLowerCase();
const ok=['success','done','active','enabled','up','healthy','passed','connected','published','resolved','ok'];
const bad=['failed','error','down','disabled','paused','cancelled'];
const warn=['queued','running','planned','pending','running...','unverified','needs_review'];
if(ok.includes(m))return `<span class="status ok">${esc(status)}</span>`;
if(bad.includes(m))return `<span class="status err">${esc(status)}</span>`;
if(warn.includes(m))return `<span class="status warn">${esc(status)}</span>`;
return `<span class="status">${esc(status||'—')}</span>`;}
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
function debounce(fn,ms){let t;return(...a)=>{clearTimeout(t);t=setTimeout(()=>fn(...a),ms);};}
function shortId(id){return esc(String(id||'').slice(0,8));}
