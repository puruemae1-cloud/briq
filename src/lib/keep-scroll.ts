/**
 * Keep the scroll position across a full-document navigation (shop filter
 * chips hard-assign the next URL, which would otherwise land at the top).
 *
 * Client: call {@link rememberScrollFor} right before `location.assign`.
 * Server: inline {@link KEEP_SCROLL_RESTORE_SCRIPT} in `<head>` so the target
 * page restores while its HTML streams in, before hydration.
 */
export const KEEP_SCROLL_KEY = "briq:keep-scroll";

export function rememberScrollFor(href: string): void {
  try {
    const target = new URL(href, window.location.href);
    sessionStorage.setItem(
      KEEP_SCROLL_KEY,
      JSON.stringify({ path: target.pathname, y: window.scrollY, t: Date.now() }),
    );
  } catch {
    /* storage disabled — fall back to default navigation */
  }
}

export const KEEP_SCROLL_RESTORE_SCRIPT = `(function(){try{
var k=${JSON.stringify(KEEP_SCROLL_KEY)},raw=sessionStorage.getItem(k);if(!raw)return;
sessionStorage.removeItem(k);var s=JSON.parse(raw);
if(!s||typeof s.y!=="number"||Date.now()-s.t>60000||s.path!==location.pathname)return;
var y=s.y,stop=false,end=Date.now()+8000,settle=Date.now()+1500;
function cancel(){stop=true}
["wheel","touchstart","keydown","mousedown"].forEach(function(e){addEventListener(e,cancel,{passive:true,once:true})});
function go(){try{scrollTo({top:y,left:0,behavior:"instant"})}catch(_){scrollTo(0,y)}}
(function tick(){if(stop)return;var d=document.documentElement;
if(d&&d.scrollHeight-innerHeight>=y-1){if(Math.abs(scrollY-y)>1)go();
if(document.readyState==="complete"&&Date.now()>settle&&Math.abs(scrollY-y)<=1)return;}
if(Date.now()<end)requestAnimationFrame(tick);})();
}catch(_){}})();`;
