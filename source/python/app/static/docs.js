/* Docs portal behavior (vanilla, no framework). Tokens __MOUNT__, __LANG__,
   __ACTIVE__, __EMPTY__ are replaced server-side per request. */
(function(){
var cfg=document.currentScript&&document.currentScript.dataset?document.currentScript.dataset:{};
var MOUNT=cfg.mount||'', LANG=cfg.lang||'en', ACTIVE=cfg.active||'index', EMPTY=cfg.empty||'No results.';
var q=document.getElementById('docs-q'), box=document.getElementById('docs-results'),
    body=document.getElementById('docs-results-body'), t=null;
function esc(s){return String(s||'').replace(/[<>&]/g,function(c){return {'<':'&lt;','>':'&gt;','&':'&amp;'}[c];}).slice(0,300);}
async function run(){
var v=(q.value||'').trim();if(v.length<2){box.style.display='none';return;}
try{
var r=await fetch(MOUNT+'/api/v1/docs/search?q='+encodeURIComponent(v)+'&lang='+LANG);
var j=await r.json();var items=j.results||[];
body.innerHTML=items.length?items.map(function(x){return '<a class="dropdown-item" href="'+MOUNT+'/docs/'+LANG+'/'+x.slug+'"><b>'+esc(x.title)+'</b><div class="text-muted small">'+esc(x.section)+' — '+esc((x.excerpt||'').slice(0,120))+'</div></a>';}).join(''):'<div class="p-2 text-muted small">'+esc(EMPTY)+'</div>';
box.style.display='block';
}catch(e){box.style.display='none';}
}
if(q){
q.addEventListener('input',function(){clearTimeout(t);t=setTimeout(run,250);});
q.addEventListener('keydown',function(e){if(e.key==='Escape'){box.style.display='none';}});
document.addEventListener('keydown',function(e){if((e.ctrlKey||e.metaKey)&&String(e.key).toLowerCase()==='k'&&document.activeElement!==q){e.preventDefault();q.focus();q.select();}});
}
var langSel=document.getElementById('docs-lang');
if(langSel){langSel.addEventListener('change',function(){location.href=MOUNT+'/docs/'+this.value+'/'+ACTIVE;});}
var themeBtn=document.getElementById('docs-theme');
if(themeBtn){themeBtn.addEventListener('click',function(){try{var t=localStorage.getItem('wi-theme')||'light';t=t==='light'?'dark':t==='dark'?'system':'light';localStorage.setItem('wi-theme',t);var dark=t==='dark'||(t==='system'&&window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches);document.documentElement.setAttribute('data-bs-theme',dark?'dark':'light');}catch(e){}});}
var navBtn=document.getElementById('docs-navbtn');
if(navBtn){navBtn.addEventListener('click',function(){document.getElementById('docs-side').classList.toggle('open');});}
document.querySelectorAll('pre').forEach(function(pre){if(pre.querySelector('.code-copy'))return;var b=document.createElement('button');b.className='btn btn-sm code-copy';b.textContent='Copy';b.setAttribute('aria-label','Copy code');b.addEventListener('click',function(){try{navigator.clipboard.writeText(pre.innerText);b.textContent='Copied';setTimeout(function(){b.textContent='Copy';},1500);}catch(e){}});pre.appendChild(b);});
})();
