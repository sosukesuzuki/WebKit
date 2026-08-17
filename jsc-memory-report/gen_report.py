#!/usr/bin/env python3
# Generates the bilingual (EN/JA) HTML report "JSC JIT Memory Ledger" from measured data.
import json, html, os
HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'data', 'data.json')))
SZ = D['sizeof']; MS = D['metaSizes']
MATRIX = D['matrix']; RET = D['retained']
BOPS = D['baselineOps']; DOPS = D['dfgOps']

def esc(s): return html.escape(s, quote=False)
def t(en, ja):
    return f'<span class="en">{en}</span><span class="ja" lang="ja">{ja}</span>'
def T(en, ja):
    return f'<div class="en">{en}</div><div class="ja" lang="ja">{ja}</div>'
def c(s): return f'<code>{esc(s)}</code>'
def kb(b):
    if b >= 1024*1024: return f'{b/1048576:.2f} MB'
    if b >= 1024: return f'{b/1024:.0f} KB'
    return f'{b} B'
def n(x): return f'{x:,}'

def mrow(cfg, test):
    for r in MATRIX:
        if r['cfg']==cfg and r['test']==test: return r
    return {}

TESTS = ["typescript","acorn-wtb","Babylon","pdfjs","gbemu","Air","octane-zlib","ML","raytrace","splay"]
RET_TESTS = [x for x in TESTS if x in RET]
# bytes per retained record, from the sizeof harness
B_DFG_EXIT = SZ['DFG::OSRExit'] + 16   # + JITData::m_exits MacroAssemblerCodeRef
B_EXIT_STUB = 11                       # x86_64 move imm32 + patchable jump
B_EVENT = SZ['DFG::VariableEvent']; B_MINI = SZ['DFG::MinifiedNode']
B_FTL_EXIT = SZ['FTL::OSRExit']; B_DESC = SZ['FTL::OSRExitDescriptor']; B_EXITVAL = SZ['FTL::ExitValue']; B_REP = 16
B_WP = SZ['CodeBlockJettisoningWatchpoint']; B_ASW = SZ['DFG::AdaptiveStructureWatchpoint']; B_AIW = SZ['DFG::AdaptiveInferredPropertyValueWatchpoint']
B_ICF = SZ['InlineCallFrame'] + 8; B_CO = SZ['CodeOrigin']

# ---------- derived numbers used in prose ----------
ts = mrow('default','typescript')
ts_base = ts['lb_Baseline']; ts_dfg = ts['lb_DFG']; ts_ftl = ts['lb_FTL']
R = RET['typescript']['retained']
dfgR, ftlR = R['DFG'], R['FTL']
ftl_exit_values_bytes = ftlR['sumExitValues']*SZ['FTL::ExitValue']
ftl_desc_bytes = ftlR['descriptors']*SZ['FTL::OSRExitDescriptor']
ftl_reps_bytes = ftlR['sumValueReps']*B_REP
ftl_exit_bytes = ftlR['exits']*SZ['FTL::OSRExit']
dfg_events_bytes = dfgR['events']*SZ['DFG::VariableEvent']
dfg_min_bytes = dfgR['minified']*SZ['DFG::MinifiedNode']
dfg_exit_bytes = dfgR['exits']*B_DFG_EXIT
dfg_exit_stub_bytes = dfgR['exits']*B_EXIT_STUB
ftl_exit_stub_bytes = ftlR['exits']*10
bops = {k:(b,cnt,avg) for k,b,cnt,avg in BOPS}
gbi = bops['Baseline_fast_op_get_by_id']
pbi = bops['Baseline_fast_op_put_by_id']
jf = bops['Baseline_fast_op_jfalse']; jt = bops['Baseline_fast_op_jtrue']
pro = bops['Baseline_prologue']; ent = bops['Baseline_fast_op_enter']
dops = {k:(b,cnt,avg) for k,b,cnt,avg in DOPS}
sb = dops['DFG_slow_FencedStoreBarrier']
meta_ts = RET['typescript']['meta']
def meta_family(m, ops):
    return sum(m['per'][o][1] for o in ops if o in m['per']), sum(m['per'][o][0] for o in ops if o in m['per'])
CALL_OPS=['op_call','op_call_ignore_result','op_construct','op_tail_call','op_call_varargs','op_construct_varargs','op_tail_call_varargs','op_super_construct','op_super_construct_varargs','op_call_direct_eval','op_iterator_open','op_iterator_next','op_async_iterator_open','op_async_iterator_next']
ts_call_bytes, ts_call_n = meta_family(meta_ts, CALL_OPS)
ac_meta = RET['acorn-wtb']['meta']; ac_call_bytes, ac_call_n = meta_family(ac_meta, CALL_OPS)

# ---------- HTML pieces ----------
CSS = r"""
:root{--bg:#F4F6F8;--surface:#FFFFFF;--ink:#14202B;--muted:#5B6B7A;--line:#D6DEE6;--accent:#0E6BA8;--accent-soft:#E3F0F9;--good:#1E7F4F;--warn:#B4780A;--bad:#B3261E;--code-bg:#EEF2F5;--shadow:0 1px 2px rgba(20,32,43,.06),0 4px 16px rgba(20,32,43,.05)}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0E1418;--surface:#151C22;--ink:#E3E9EE;--muted:#93A1AE;--line:#263139;--accent:#5FB0EA;--accent-soft:#16283A;--good:#4CC38A;--warn:#E9A23B;--bad:#F0716A;--code-bg:#1B242C;--shadow:0 1px 2px rgba(0,0,0,.4)}}
:root[data-theme="dark"]{--bg:#0E1418;--surface:#151C22;--ink:#E3E9EE;--muted:#93A1AE;--line:#263139;--accent:#5FB0EA;--accent-soft:#16283A;--good:#4CC38A;--warn:#E9A23B;--bad:#F0716A;--code-bg:#1B242C;--shadow:0 1px 2px rgba(0,0,0,.4)}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif;font-size:16px;line-height:1.55;-webkit-font-smoothing:antialiased}
[lang="ja"]{font-family:"IBM Plex Sans JP","IBM Plex Sans","Hiragino Sans","Noto Sans JP",sans-serif}
:root:not([data-lang="ja"]) .ja{display:none!important}
:root[data-lang="ja"] .en{display:none!important}
code,pre,.mono{font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.92em}
code{background:var(--code-bg);padding:.08em .35em;border-radius:4px}
pre{background:var(--code-bg);padding:12px 14px;border-radius:8px;overflow-x:auto;line-height:1.45;font-size:.84rem}
pre code{background:none;padding:0}
a{color:var(--accent)}
h1,h2,h3,h4{line-height:1.2;text-wrap:balance;margin:0}
h2{font-size:1.55rem;font-weight:600;letter-spacing:-.01em;margin:3.2rem 0 1rem;padding-top:.6rem;border-top:1px solid var(--line)}
h3{font-size:1.15rem;font-weight:600;margin:2rem 0 .6rem}
h4{font-size:1rem;font-weight:600;margin:1.2rem 0 .4rem}
p{margin:.6rem 0}
.topbar{position:sticky;top:0;z-index:5;background:var(--surface);border-bottom:1px solid var(--line);display:flex;align-items:center;gap:16px;padding:10px 20px}
.topbar .name{font-weight:600;letter-spacing:.01em}
.topbar .sp{flex:1}
.langsw{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden}
.langsw button{background:transparent;border:0;color:var(--muted);font:inherit;font-size:.85rem;padding:5px 12px;cursor:pointer}
.langsw button[aria-pressed="true"]{background:var(--accent);color:#fff}
.langsw button:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.wrap{max-width:1120px;margin:0 auto;padding:28px 20px 80px}
.mast{padding:24px 0 8px}
.mast .eyebrow{color:var(--accent);font-size:.8rem;letter-spacing:.12em;text-transform:uppercase;font-weight:600}
.mast h1{font-size:2.5rem;font-weight:700;letter-spacing:-.02em;margin:.3rem 0 .6rem}
.mast .sub{color:var(--muted);font-size:1.05rem;max-width:70ch}
.meta{display:flex;flex-wrap:wrap;gap:8px 20px;color:var(--muted);font-size:.85rem;margin-top:14px}
.meta b{color:var(--ink);font-weight:600}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:22px 0}
@media (max-width:900px){.kpis{grid-template-columns:repeat(2,1fr)}}
@media (max-width:560px){.kpis{grid-template-columns:1fr}}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:14px 16px;box-shadow:var(--shadow)}
.kpi .v{font-size:1.7rem;font-weight:700;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.kpi .l{color:var(--muted);font-size:.85rem;margin-top:2px}
.toc{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin:18px 0 8px;columns:2;column-gap:32px}
.toc a{display:block;text-decoration:none;color:var(--ink);padding:3px 0;font-size:.95rem;break-inside:avoid}
.toc a span.num{color:var(--muted);display:inline-block;width:2.2em}
@media (max-width:720px){.toc{columns:1}.mast h1{font-size:1.9rem}}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--surface);margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:.88rem}
th,td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;white-space:nowrap}
th{background:var(--code-bg);font-weight:600;position:sticky;top:0}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:0}
td.txt,th.txt{white-space:normal;min-width:18ch}
.note{border-left:3px solid var(--accent);background:var(--accent-soft);padding:10px 14px;border-radius:0 8px 8px 0;margin:12px 0;font-size:.95rem}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin:18px 0;box-shadow:var(--shadow)}
.card .head{display:flex;gap:14px;align-items:flex-start;flex-wrap:wrap}
.rank{flex:0 0 auto;width:44px;height:44px;border-radius:10px;background:var(--accent);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:1.15rem;font-variant-numeric:tabular-nums}
.card h3{margin:0;font-size:1.2rem;flex:1 1 300px}
.pills{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.pill{font-size:.75rem;border-radius:999px;padding:2px 10px;border:1px solid var(--line);color:var(--muted);white-space:nowrap}
.pill.area{border-color:var(--accent);color:var(--accent)}
.pill.save{background:var(--accent-soft);border-color:transparent;color:var(--ink);font-weight:600}
.pill.risk-low{border-color:var(--good);color:var(--good)}
.pill.risk-med{border-color:var(--warn);color:var(--warn)}
.pill.risk-high{border-color:var(--bad);color:var(--bad)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px 24px;margin-top:12px}
@media (max-width:820px){.grid2{grid-template-columns:1fr}}
.blk h4{margin:0 0 4px;font-size:.78rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.blk p{margin:.35rem 0}
.blk ul{margin:.3rem 0 .3rem 1.1rem;padding:0}
.blk li{margin:.2rem 0}
.ref{color:var(--muted);font-size:.85em}
.diagram{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:14px 0}
.box{border:1px solid var(--line);border-radius:10px;padding:10px 12px;background:var(--surface);font-size:.88rem}
.box .t{font-weight:600;color:var(--accent);margin-bottom:4px}
.box ul{margin:0;padding-left:1.1rem}
.small{font-size:.85rem;color:var(--muted)}
.bar{height:10px;background:var(--code-bg);border-radius:5px;overflow:hidden}
.bar i{display:block;height:100%;background:var(--accent)}
footer{margin-top:60px;color:var(--muted);font-size:.85rem;border-top:1px solid var(--line);padding-top:16px}
@media (prefers-reduced-motion: no-preference){.langsw button{transition:background .15s,color .15s}}
"""

JS = r"""
(function(){
  var root=document.documentElement;
  function setLang(l){root.setAttribute('data-lang',l);try{localStorage.setItem('jscmem-lang',l)}catch(e){}
    document.querySelectorAll('.langsw button').forEach(function(b){b.setAttribute('aria-pressed', b.dataset.lang===l?'true':'false')});}
  var q=new URLSearchParams(location.search).get('lang');var s=null;try{s=localStorage.getItem('jscmem-lang')}catch(e){}
  setLang(q==='ja'||q==='en'?q:(s==='ja'?'ja':'en'));
  document.querySelectorAll('.langsw button').forEach(function(b){b.addEventListener('click',function(){setLang(b.dataset.lang)})});
})();
"""

def pill(cls, en, ja=None):
    return f'<span class="pill {cls}">{t(en, ja) if ja else en}</span>'

def card(rank, title_en, title_ja, area_en, area_ja, save_en, save_ja, risk, risk_en, risk_ja, evidence, measurement, proposal, riskblk):
    riskcls={'low':'risk-low','med':'risk-med','high':'risk-high'}[risk]
    return f'''
<article class="card" id="opp{rank}">
 <div class="head"><div class="rank">{rank}</div><h3>{t(title_en,title_ja)}</h3></div>
 <div class="pills">{pill("area",area_en,area_ja)}{pill("save",save_en,save_ja)}{pill(riskcls,risk_en,risk_ja)}</div>
 <div class="grid2">
  <div class="blk"><h4>{t("Evidence (source)","根拠（ソース）")}</h4>{evidence}</div>
  <div class="blk"><h4>{t("Measurement","計測")}</h4>{measurement}</div>
  <div class="blk"><h4>{t("Proposal","提案")}</h4>{proposal}</div>
  <div class="blk"><h4>{t("Risk / complexity","リスク / 複雑さ")}</h4>{riskblk}</div>
 </div>
</article>'''

# ---------- tables ----------
def sizeof_table():
    rows = [
     ("CodeBlock", "bytecode/CodeBlock.h", "cell = 224 B (IsoSubspace, static_assert ≤ 224)"),
     ("UnlinkedCodeBlock", "bytecode/UnlinkedCodeBlock.h", "shared across realms"),
     ("ValueProfile", "bytecode/ValueProfile.h", "1 bucket + SpeculatedType"),
     ("ArgumentValueProfile", "bytecode/ValueProfile.h", "1 bucket + 1 spec-fail bucket"),
     ("ArrayProfile", "bytecode/ArrayProfile.h", ""),
     ("BinaryArithProfile", "bytecode/ArithProfile.h", "in UnlinkedCodeBlock (shared)"),
     ("PropertyInlineCache", "bytecode/PropertyInlineCache.h", "base (ex-StructureStubInfo)"),
     ("HandlerPropertyInlineCache", "bytecode/PropertyInlineCache.h", "Baseline + DFG, per linked CodeBlock"),
     ("RepatchingPropertyInlineCache", "bytecode/PropertyInlineCache.h", "FTL"),
     ("BaselineUnlinkedPropertyInlineCache", "bytecode/PropertyInlineCache.h", "shared BaselineJITCode"),
     ("InlineCacheHandler", "bytecode/InlineCacheHandler.h", "dsize 96, alignas(64) → 128"),
     ("AccessCase", "bytecode/AccessCase.h", ""),
     ("GetterSetterAccessCase", "bytecode/GetterSetterAccessCase.h", ""),
     ("PolymorphicAccessJITStubRoutine", "jit/GCAwareJITStubRoutine.h", "+ WatchpointSet 24 B always"),
     ("WatchpointSet", "bytecode/Watchpoint.h", ""),
     ("CodeBlockJettisoningWatchpoint", "bytecode/CodeBlockJettisoningWatchpoint.h", "per watched set per DFG/FTL CodeBlock"),
     ("DFG::AdaptiveStructureWatchpoint", "dfg/DFGAdaptiveStructureWatchpoint.h", ""),
     ("DFG::AdaptiveInferredPropertyValueWatchpoint", "dfg/DFGAdaptiveInferredPropertyValueWatchpoint.h", "virtual"),
     ("DataOnlyCallLinkInfo", "bytecode/CallLinkInfo.h", "embedded in op_call metadata"),
     ("OptimizingCallLinkInfo", "bytecode/CallLinkInfo.h", "DFG/FTL; m_callLocation unused"),
     ("DirectCallLinkInfo", "bytecode/CallLinkInfo.h", ""),
     ("PolymorphicCallStubRoutine", "jit/PolymorphicCallStubRoutine.h", "+ 24 B node + 32 B CallSlot each"),
     ("JITAddIC", "jit/JITMathIC.h", "per op_add in Baseline/DFG"),
     ("DFG::Node", "dfg/DFGNode.h", "compile-time; 4 B pad + 16 B scratch"),
     ("DFG::AbstractValue", "dfg/DFGAbstractValue.h", "compile-time"),
     ("DFG::OSRExit", "dfg/DFGOSRExit.h", "retained per exit"),
     ("DFG::VariableEvent", "dfg/DFGVariableEvent.h", "retained per event"),
     ("DFG::MinifiedNode", "dfg/DFGMinifiedNode.h", "retained"),
     ("DFG::JITCode", "dfg/DFGJITCode.h", ""),
     ("DFG::CommonData", "dfg/DFGCommonData.h", ""),
     ("FTL::OSRExit", "ftl/FTLOSRExit.h", "+ FixedVector<ValueRep> 16 B each"),
     ("FTL::OSRExitDescriptor", "ftl/FTLOSRExit.h", "+ 9 B × frame operands"),
     ("FTL::ExitValue", "ftl/FTLExitValue.h", ""),
     ("InlineCallFrame", "bytecode/InlineCallFrame.h", "Bag node"),
     ("CodeOrigin", "bytecode/CodeOrigin.h", "packed"),
     ("BaselineJITCode", "jit/BaselineJITCode.h", "shared per UnlinkedCodeBlock"),
     ("JITCodeMap", "jit/JITCodeMap.h", "+ 12 B per bytecode instruction"),
     ("Structure", "runtime/Structure.h", "cell 112 B (7 atoms)"),
     ("StructureRareData", "runtime/StructureRareData.h", ""),
     ("FunctionRareData", "runtime/FunctionRareData.h", "cell 80 B"),
     ("WeakImpl", "heap/WeakImpl.h", ""),
     ("JSCell", "runtime/JSCell.h", "header"),
    ]
    out=['<div class="tablewrap"><table><thead><tr><th>Type</th><th class="num">sizeof (x86_64)</th><th>File</th><th class="txt">'+t('Note','備考')+'</th></tr></thead><tbody>']
    for name,f,note in rows:
        v = SZ.get(name)
        out.append(f'<tr><td class="mono">{esc(name)}</td><td class="num">{v if v is not None else "—"}</td><td class="mono small">{esc(f)}</td><td class="txt small">{esc(note)}</td></tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)

def meta_table():
    ops = sorted(MS.items(), key=lambda kv:-kv[1])
    out=['<div class="tablewrap"><table><thead><tr><th>Op::Metadata</th><th class="num">bytes</th><th>Op::Metadata</th><th class="num">bytes</th><th>Op::Metadata</th><th class="num">bytes</th></tr></thead><tbody>']
    per=3; rows=(len(ops)+per-1)//per
    for i in range(rows):
        cells=[]
        for j in range(per):
            k=i+j*rows
            if k<len(ops): cells.append(f'<td class="mono">{esc(ops[k][0])}</td><td class="num">{ops[k][1]}</td>')
            else: cells.append('<td></td><td></td>')
        out.append('<tr>'+''.join(cells)+'</tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)

def workload_table():
    hdr = ['Test','Baseline','DFG','FTL','DFG OSR exit','FTL OSR exit','IC stubs','All linked','JIT pool RSS (after GC)','Live CodeBlocks','Unlinked CB']
    out=['<div class="tablewrap"><table><thead><tr>'+''.join(f'<th class="{"num" if i else ""}">{h}</th>' for i,h in enumerate(hdr))+'</tr></thead><tbody>']
    for tname in TESTS:
        r=mrow('default',tname)
        if not r: continue
        out.append(f'<tr><td>{tname}</td><td class="num">{kb(r["lb_Baseline"])}</td><td class="num">{kb(r["lb_DFG"])}</td><td class="num">{kb(r["lb_FTL"])}</td><td class="num">{kb(r.get("lb_DFGOSRExit",0))}</td><td class="num">{kb(r.get("lb_FTLOSRExit",0))}</td><td class="num">{kb(r.get("lb_InlineCache",0))}</td><td class="num">{kb(r["lb_Total"])}</td><td class="num">{kb(r.get("afterGC_jitRss",0))}</td><td class="num">{n(r.get("afterGC_FunctionCodeBlock",0))}</td><td class="num">{n(r.get("afterGC_UnlinkedFunctionCodeBlock",0))}</td></tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)

def config_table():
    cfgs=[('default','default'),('jit2000','thresholdForJITAfterWarmUp=2000'),('jit5000','thresholdForJITAfterWarmUp=5000'),('eagerjettison','forceCodeBlockToJettisonDueToOldAge + eager timing'),('nosharing','useBaselineJITCodeSharing=0'),('noftl','useFTLJIT=0'),('nodfg','useDFGJIT=0')]
    out=['<div class="tablewrap"><table><thead><tr><th>Test</th><th>Config</th><th class="num">Baseline linked</th><th class="num">DFG linked</th><th class="num">FTL linked</th><th class="num">JIT pool RSS after GC</th><th class="num">Live CodeBlocks</th><th class="num">Score</th></tr></thead><tbody>']
    for tname in ['Air','acorn-wtb','typescript','pdfjs','gbemu','octane-zlib']:
        for cfg,label in cfgs:
            r=mrow(cfg,tname)
            if not r or 'lb_Baseline' not in r: continue
            out.append(f'<tr><td>{tname}</td><td class="mono small">{esc(label)}</td><td class="num">{kb(r["lb_Baseline"])}</td><td class="num">{kb(r["lb_DFG"])}</td><td class="num">{kb(r["lb_FTL"])}</td><td class="num">{kb(r.get("afterGC_jitRss",0))}</td><td class="num">{n(r.get("afterGC_FunctionCodeBlock",0))}</td><td class="num">{r.get("score","")}</td></tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)

def ops_table(ops, total, topn=18):
    out=['<div class="tablewrap"><table><thead><tr><th>Marker</th><th class="num">total bytes</th><th class="num">count</th><th class="num">avg B</th><th class="num">% of tier code</th><th></th></tr></thead><tbody>']
    for name,b,cnt,avg in ops[:topn]:
        pct=100.0*b/total
        out.append(f'<tr><td class="mono">{esc(name)}</td><td class="num">{n(b)}</td><td class="num">{n(cnt)}</td><td class="num">{avg:.0f}</td><td class="num">{pct:.1f}%</td><td style="min-width:120px"><div class="bar"><i style="width:{min(100,pct*2.5):.1f}%"></i></div></td></tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)

def metastats_table():
    out=['<div class="tablewrap"><table><thead><tr><th>Test</th><th class="num">metadata bytes (linked, excl. ValueProfiles)</th><th class="num">tables</th><th class="num">extra realm copies</th><th class="num">call-family bytes</th><th class="num">call-family %</th><th class="num">op_get_by_id</th><th class="num">op_put_by_id</th><th class="num">op_get_from_scope</th></tr></thead><tbody>']
    for tname in RET_TESTS:
        m=RET[tname]['meta']
        cb,cn=meta_family(m,CALL_OPS)
        g=m['per'].get('op_get_by_id',(0,0)); p=m['per'].get('op_put_by_id',(0,0)); s=m['per'].get('op_get_from_scope',(0,0))
        out.append(f'<tr><td>{tname}</td><td class="num">{n(m["total"])}</td><td class="num">{n(m["tables"])}</td><td class="num">{n(m["copies"])}</td><td class="num">{n(cb)} ({n(cn)} sites)</td><td class="num">{100.0*cb/m["total"]:.0f}%</td><td class="num">{n(g[1])} ({n(g[0])})</td><td class="num">{n(p[1])} ({n(p[0])})</td><td class="num">{n(s[1])} ({n(s[0])})</td></tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)

def retained_table():
    hdr=['Test','DFG compiles','DFG code','DFG exits',f'OSRExit+m_exits ({B_DFG_EXIT} B)',f'exit stubs in code (~{B_EXIT_STUB} B)','VariableEvents',f'event stream ({B_EVENT} B)','FTL compiles','FTL code (linked)','FTL exits','descriptors','ExitValues',f'descriptor payload ({B_EXITVAL} B)',f'ValueReps ({B_REP} B)',f'FTL OSRExit ({B_FTL_EXIT} B)']
    out=['<div class="tablewrap"><table><thead><tr>'+''.join(f'<th class="{"num" if i else ""}">{h}</th>' for i,h in enumerate(hdr))+'</tr></thead><tbody>']
    for tname in RET_TESTS:
        r=RET[tname]['retained']; d=r['DFG']; f=r['FTL']; mr=mrow('default',tname)
        out.append(f'<tr><td>{tname}</td><td class="num">{d["count"]}</td><td class="num">{kb(mr["lb_DFG"])}</td><td class="num">{n(d["exits"])}</td><td class="num">{kb(d["exits"]*B_DFG_EXIT)}</td><td class="num">{kb(d["exits"]*B_EXIT_STUB)}</td><td class="num">{n(d["events"])}</td><td class="num">{kb(d["events"]*B_EVENT)}</td>'
                   f'<td class="num">{f["count"]}</td><td class="num">{kb(mr["lb_FTL"])}</td><td class="num">{n(f["exits"])}</td><td class="num">{n(f["descriptors"])}</td><td class="num">{n(f["sumExitValues"])}</td><td class="num">{kb(f["sumExitValues"]*B_EXITVAL)}</td><td class="num">{kb(f["sumValueReps"]*B_REP)}</td><td class="num">{kb(f["exits"]*B_FTL_EXIT)}</td></tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)

def watchpoint_table():
    out=[f'<div class="tablewrap"><table><thead><tr><th>Test</th><th class="num">DFG+FTL CodeBlockJettisoningWatchpoint ({B_WP} B)</th><th class="num">AdaptiveStructureWatchpoint ({B_ASW} B)</th><th class="num">AdaptiveInferredPropertyValueWatchpoint ({B_AIW} B)</th><th class="num">total</th><th class="num">InlineCallFrames ({SZ["InlineCallFrame"]} B + Bag)</th><th class="num">CodeOrigins ({B_CO} B)</th></tr></thead><tbody>']
    for tname in RET_TESTS:
        r=RET[tname]['retained']; d=r['DFG']; f=r['FTL']
        w=d['watchpoints']+f['watchpoints']; a=d['adaptiveStructWP']+f['adaptiveStructWP']; i=d['adaptiveInferredWP']+f['adaptiveInferredWP']
        icf=d['inlineCallFrames']+f['inlineCallFrames']; co=d['codeOrigins']+f['codeOrigins']
        out.append(f'<tr><td>{tname}</td><td class="num">{n(w)} ({kb(w*B_WP)})</td><td class="num">{n(a)} ({kb(a*B_ASW)})</td><td class="num">{n(i)} ({kb(i*B_AIW)})</td><td class="num">{kb(w*B_WP+a*B_ASW+i*B_AIW)}</td><td class="num">{n(icf)} ({kb(icf*B_ICF)})</td><td class="num">{n(co)} ({kb(co*B_CO)})</td></tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)

CO = c('CodeOrigin{bytecodeIndex}')
# ---------- opportunity cards ----------
cards = []
def add(*a): cards.append(card(*a))

# 1
add(1, "Cap or size-scale the LLInt→Baseline threshold (giant straight-line functions get MBs of Baseline code)",
 "LLInt→Baseline の閾値をバイトコードサイズで補正／上限を設ける（巨大な直線関数が MB 単位の Baseline コードを生む）",
 "Executable code · Baseline", "実行コード · Baseline",
 f"Air: {kb(mrow('default','Air')['lb_Baseline'])} → {kb(mrow('jit2000','Air')['lb_Baseline'])} of Baseline code (−88%)", f"Air: Baseline コード {kb(mrow('default','Air')['lb_Baseline'])} → {kb(mrow('jit2000','Air')['lb_Baseline'])}（−88%）",
 "med", "medium (tiering policy)", "中（ティアリング方針）",
 T(f"""<p>{c('thresholdForJITAfterWarmUp = 500')}, {c('thresholdForJITSoon = 100')} <span class="ref">(runtime/OptionsList.h:355-356)</span> are applied on the shared LLInt counter with no scaling by bytecode size or code type; the LLInt adds 5 on entry, 10 on return and 1 per loop iteration <span class="ref">(llint/LowLevelInterpreter.asm, LowLevelInterpreter64.asm)</span>. {c('LLIntSlowPaths::shouldJIT')} has no size cap, whereas the DFG refuses functions above {c('maximumOptimizationCandidateBytecodeCost = 100000')} <span class="ref">(OptionsList.h:311)</span> and scales its thresholds with bytecode cost ({c('optimizationThresholdScalingFactor')}, bytecode/CodeBlock.cpp). Baseline machine code is ~14 B per bytecode byte on x86_64 (measured), so a 250 KB-bytecode function becomes ~1.9 MB of code.</p>""",
   f"""<p>{c('thresholdForJITAfterWarmUp = 500')}, {c('thresholdForJITSoon = 100')} <span class="ref">(runtime/OptionsList.h:355-356)</span> は共有 LLInt カウンタに対して、バイトコード量やコード種別で補正されずに適用される（LLInt は入口で +5、return で +10、ループ 1 反復で +1）。{c('LLIntSlowPaths::shouldJIT')} にはサイズ上限がない一方、DFG は {c('maximumOptimizationCandidateBytecodeCost = 100000')} <span class="ref">(OptionsList.h:311)</span> を超える関数を拒否し、閾値もバイトコード量で補正する（{c('optimizationThresholdScalingFactor')}）。x86_64 の Baseline は 1 バイトコードバイトあたり約 14 B の機械語（実測）なので、250 KB のバイトコードは約 1.9 MB のコードになる。</p>"""),
 T(f"""<p>JetStream2 <b>Air</b>: 4 payload builders ({c('createPayloadImagingGaussianBlurGaussianBlur')} bytecode cost 248,984 → 1,874,304 B; {c('createPayloadGbemuExecuteIteration')} 237,892 → 1,703,744 B; {c('createPayloadAirJSACLj8C')} 123,180 → 1,098,080 B; {c('createPayloadTypescriptScanIdentifier')} 135,312 → 1,054,016 B) produce <b>5.7 MB of the 6.5 MB</b> Baseline code and the JIT pool RSS is 7.1 MB. With {c('--thresholdForJITAfterWarmUp=2000 --thresholdForJITSoon=400')} Baseline drops to 756 KB and JIT RSS to 1.37 MB; score 184 → 193 (noise). Other tests at 4× threshold: pdfjs −25%, gbemu −27%, acorn-wtb −27%, Babylon −6%, typescript −3% Baseline bytes.</p><p class="small">Reproduce: {c('jsc --reportBaselineCompileTimes=1 ...')}, {c('$vm.linkBufferStats()')} (see method section).</p>""",
   f"""<p>JetStream2 <b>Air</b>: 4 つのペイロード生成関数（{c('createPayloadImagingGaussianBlurGaussianBlur')} バイトコードコスト 248,984 → 1,874,304 B、{c('createPayloadGbemuExecuteIteration')} 237,892 → 1,703,744 B、{c('createPayloadAirJSACLj8C')} 123,180 → 1,098,080 B、{c('createPayloadTypescriptScanIdentifier')} 135,312 → 1,054,016 B）が Baseline コード 6.5 MB のうち <b>5.7 MB</b> を占め、JIT プールの RSS は 7.1 MB。{c('--thresholdForJITAfterWarmUp=2000 --thresholdForJITSoon=400')} で Baseline は 756 KB、JIT RSS は 1.37 MB に減少し、スコアは 184 → 193（ノイズ範囲）。閾値 4 倍での他テスト: pdfjs −25%、gbemu −27%、acorn-wtb −27%、Babylon −6%、typescript −3%。</p><p class="small">再現: {c('jsc --reportBaselineCompileTimes=1 ...')}、{c('$vm.linkBufferStats()')}（計測方法の節を参照）。</p>"""),
 T("""<p>Scale the LLInt threshold by bytecode cost (reuse the DFG curve or a simple <code>bytecodeCost / K</code>), give Program/Module code a multiplier (today only eval has <code>evalThresholdMultiplier</code>), and add a hard cap: functions above the DFG candidacy limit only get Baseline via loop OSR after a much larger count.</p>""",
   """<p>LLInt 閾値をバイトコードコストで補正し（DFG のカーブか単純な <code>bytecodeCost / K</code>）、Program/Module コードに乗数を与え（現状 eval のみ <code>evalThresholdMultiplier</code>）、さらに上限を設ける: DFG 候補上限を超える関数は、はるかに大きなカウント後のループ OSR でのみ Baseline 化する。</p>"""),
 T("""<p>Medium: giant hot functions stay in LLInt longer (throughput regression risk on code-load style tests); needs benchmarking on JetStream/Speedometer. Implementation is small (UnlinkedCodeBlock.cpp:309-321 <code>thresholdForJIT</code>).</p>""",
   """<p>中: 巨大でホットな関数が LLInt に長く留まる（code-load 系テストでのスループット後退リスク）。JetStream/Speedometer での検証が必要。実装自体は小さい（UnlinkedCodeBlock.cpp:309-321 <code>thresholdForJIT</code>）。</p>"""))

# 2
ej_ac = mrow('eagerjettison','acorn-wtb'); de_ac = mrow('default','acorn-wtb'); ej_ts=mrow('eagerjettison','typescript'); ej_zl=mrow('eagerjettison','octane-zlib'); de_zl=mrow('default','octane-zlib')
add(2, "Release cache-only Baseline code held by UnlinkedCodeBlock::m_unlinkedBaselineCode",
 "UnlinkedCodeBlock::m_unlinkedBaselineCode がキャッシュだけで保持している Baseline コードを解放する",
 "Executable code · Baseline", "実行コード · Baseline",
 "up to 100% of Baseline bytes of dead functions", "死んだ関数の Baseline コードを最大 100% 回収",
 "low", "low", "低",
 T(f"""<p>{c('CodeBlock::setupWithUnlinkedBaselineCode')} caches the shared {c('BaselineJITCode')} on the unlinked block: {c('unlinkedCodeBlock()->m_unlinkedBaselineCode = WTF::move(jitCode)')} <span class="ref">(bytecode/CodeBlock.cpp:848-849)</span>. The only release paths are UnlinkedCodeBlock death or a memory warning: {c('Heap::deleteAllUnlinkedCodeBlocks')} <span class="ref">(heap/Heap.cpp:1188-1204)</span>, whose comment states that a warm UnlinkedCodeBlock "can pin Baseline JIT executable memory across memory warnings indefinitely". Old-age jettison frees CodeBlocks (LLInt 5 s / Baseline 15 s / DFG 20 s / FTL 60 s TTL, CodeBlock.cpp:1263-1308) but not this cache.</p>""",
   f"""<p>{c('CodeBlock::setupWithUnlinkedBaselineCode')} は共有 {c('BaselineJITCode')} を unlinked 側にキャッシュする: {c('unlinkedCodeBlock()->m_unlinkedBaselineCode = WTF::move(jitCode)')} <span class="ref">(bytecode/CodeBlock.cpp:848-849)</span>。解放経路は UnlinkedCodeBlock の死かメモリ警告時の {c('Heap::deleteAllUnlinkedCodeBlocks')} <span class="ref">(heap/Heap.cpp:1188-1204)</span> だけで、そのコメント自体が「warm な UnlinkedCodeBlock は Baseline JIT の実行メモリをメモリ警告をまたいで無期限にピン留めし得る」と述べている。老化 jettison は CodeBlock（TTL: LLInt 5 s / Baseline 15 s / DFG 20 s / FTL 60 s、CodeBlock.cpp:1263-1308）を解放するが、このキャッシュは解放しない。</p>"""),
 T(f"""<p>{c('--forceCodeBlockToJettisonDueToOldAge=1 --useEagerCodeBlockJettisonTiming=1')} kills CodeBlocks aggressively yet the JIT pool RSS does not follow: acorn-wtb live CodeBlocks {n(de_ac['afterGC_FunctionCodeBlock'])} → {n(ej_ac['afterGC_FunctionCodeBlock'])} while JIT RSS after GC {kb(de_ac['afterGC_jitRss'])} → {kb(ej_ac['afterGC_jitRss'])}; octane-zlib {n(de_zl['afterGC_FunctionCodeBlock'])} → {n(ej_zl['afterGC_FunctionCodeBlock'])} CodeBlocks, JIT RSS {kb(de_zl['afterGC_jitRss'])} → {kb(ej_zl['afterGC_jitRss'])}; typescript {n(ts['afterGC_FunctionCodeBlock'])} → {n(ej_ts['afterGC_FunctionCodeBlock'])}, RSS {kb(ts['afterGC_jitRss'])} → {kb(ej_ts['afterGC_jitRss'])}. Baseline is 53% (acorn), 81% (zlib), 44% (typescript) of linked bytes, so the retained cache is most of what remains.</p>""",
   f"""<p>{c('--forceCodeBlockToJettisonDueToOldAge=1 --useEagerCodeBlockJettisonTiming=1')} で CodeBlock を積極的に捨てても JIT プール RSS は追随しない: acorn-wtb の生存 CodeBlock {n(de_ac['afterGC_FunctionCodeBlock'])} → {n(ej_ac['afterGC_FunctionCodeBlock'])} に対し GC 後の JIT RSS は {kb(de_ac['afterGC_jitRss'])} → {kb(ej_ac['afterGC_jitRss'])}。octane-zlib は CodeBlock {n(de_zl['afterGC_FunctionCodeBlock'])} → {n(ej_zl['afterGC_FunctionCodeBlock'])}、JIT RSS {kb(de_zl['afterGC_jitRss'])} → {kb(ej_zl['afterGC_jitRss'])}。typescript は {n(ts['afterGC_FunctionCodeBlock'])} → {n(ej_ts['afterGC_FunctionCodeBlock'])}、RSS {kb(ts['afterGC_jitRss'])} → {kb(ej_ts['afterGC_jitRss'])}。リンク済みバイトのうち Baseline は 53%（acorn）、81%（zlib）、44%（typescript）を占め、残っているものの大半がこのキャッシュ。</p>"""),
 T("""<p>In <code>UnlinkedCodeBlock::visitChildrenImpl</code> (or at GC end) drop <code>m_unlinkedBaselineCode</code> when its refcount is 1 (no linked CodeBlock uses it) and the block is old (reuse the <code>m_age</code> counter used by <code>useUnlinkedCodeBlockJettisoning</code>, or a wall-clock TTL like the CodeBlock TTLs). Recompilation is cheap and profiles live on the UnlinkedCodeBlock.</p>""",
   """<p><code>UnlinkedCodeBlock::visitChildrenImpl</code>（または GC 終了時）で、参照カウントが 1（リンク済み CodeBlock が使っていない）かつ古い（<code>useUnlinkedCodeBlockJettisoning</code> が使う <code>m_age</code>、または CodeBlock と同様の TTL）なら <code>m_unlinkedBaselineCode</code> を捨てる。再コンパイルは安価で、プロファイルは UnlinkedCodeBlock 側に残る。</p>"""),
 T("""<p>Low: the invariant "linked CodeBlocks hold their own ref" is already relied upon by <code>deleteAllUnlinkedCodeBlocks</code>. Perf risk = one recompile when idle code becomes hot again.</p>""",
   """<p>低: 「リンク済み CodeBlock は自前の参照を持つ」という不変条件は <code>deleteAllUnlinkedCodeBlocks</code> がすでに前提にしている。性能面のリスクは、アイドルだったコードが再度ホットになった際の 1 回の再コンパイルのみ。</p>"""))

# 3
add(3, "Baseline: shrink the inline data-IC fast paths (get_by_id ≈ 93 B, put_by_id ≈ 155 B, jtrue/jfalse ≈ 100 B per site)",
 "Baseline: インライン data-IC 高速パスを縮める（get_by_id ≈ 93 B、put_by_id ≈ 155 B、jtrue/jfalse ≈ 100 B/サイト）",
 "Executable code · Baseline", "実行コード · Baseline",
 f"typescript: ≈ {kb(gbi[0]*0.65+pbi[0]*0.7+(jf[0]+jt[0])*0.7)} of {kb(ts_base)} Baseline (≈ 37%)", f"typescript: Baseline {kb(ts_base)} のうち ≈ {kb(gbi[0]*0.65+pbi[0]*0.7+(jf[0]+jt[0])*0.7)}（≈ 37%）",
 "med", "medium (perf trade-off; make it a mode)", "中（性能トレードオフ。モード化が前提）",
 T(f"""<p>{c('JIT::emit_op_get_by_id')} emits {c('generateGetByIdInlineAccessBaselineDataIC')} <span class="ref">(jit/JITInlineCacheGenerator.cpp:152-190)</span>: cell check, structure compare against the IC, offset load, an inline-vs-out-of-line branch (<code>cmp $0x40; jl; neg; movsxd; jmp; lea; movq</code>) and the handler dispatch — 12+ instructions before a single property is loaded (disassembly of a one-line function shows 77 B for the fast path alone). The slow path already is just {c('movq 0x30(%rsi),%rax; callq 0x10(%rax)')} (11 B) into the shared handler chain ({c('PropertyInlineCache::offsetOfHandler')}). {c('emit_op_jfalse')} inlines boolean, int32 and undefined/null tests before the truthiness thunk (99 B in the disassembly).</p>""",
   f"""<p>{c('JIT::emit_op_get_by_id')} は {c('generateGetByIdInlineAccessBaselineDataIC')} <span class="ref">(jit/JITInlineCacheGenerator.cpp:152-190)</span> を出力する: セル判定、IC との structure 比較、オフセット読み込み、インライン/アウトオブライン分岐（<code>cmp $0x40; jl; neg; movsxd; jmp; lea; movq</code>）、そしてハンドラディスパッチ — プロパティ 1 つを読むまでに 12 命令以上（1 行関数の逆アセンブルで高速パスだけで 77 B）。一方スローパスは共有ハンドラチェーンへ飛ぶ {c('movq 0x30(%rsi),%rax; callq 0x10(%rax)')}（11 B）だけである。{c('emit_op_jfalse')} も truthiness サンクの前に boolean / int32 / undefined-null 判定をインライン化する（逆アセンブルで 99 B）。</p>"""),
 T(f"""<p>{c('--dumpBaselineJITSizeStatistics=1')} on typescript: {c('Baseline_fast_op_get_by_id')} {n(gbi[0])} B over {n(gbi[1])} sites (avg {gbi[2]:.0f} B) = <b>{100*gbi[0]/ts_base:.0f}% of all Baseline code</b>; {c('Baseline_fast_op_put_by_id')} {n(pbi[0])} B ({n(pbi[1])} sites, avg {pbi[2]:.0f} B); {c('jfalse')}+{c('jtrue')} {n(jf[0]+jt[0])} B ({n(jf[1]+jt[1])} sites, avg ≈ 100 B); the matching slow paths are 22 B (get_by_id) each. Total Baseline for typescript: {kb(ts_base)} in 608 functions.</p>""",
   f"""<p>typescript で {c('--dumpBaselineJITSizeStatistics=1')}: {c('Baseline_fast_op_get_by_id')} は {n(gbi[1])} サイトで {n(gbi[0])} B（平均 {gbi[2]:.0f} B）= <b>Baseline 全コードの {100*gbi[0]/ts_base:.0f}%</b>。{c('Baseline_fast_op_put_by_id')} {n(pbi[0])} B（{n(pbi[1])} サイト、平均 {pbi[2]:.0f} B）。{c('jfalse')}+{c('jtrue')} {n(jf[0]+jt[0])} B（{n(jf[1]+jt[1])} サイト、平均 ≈ 100 B）。対応するスローパスは get_by_id で各 22 B。typescript の Baseline 総量は 608 関数で {kb(ts_base)}。</p>"""),
 T("""<p>Add a compact emission mode (per-VM option, per-function for large/cold functions, or under memory pressure) that emits only cell check + handler dispatch for get/put_by_id (≈ 30 B) and only the boolean fast path + thunk for jtrue/jfalse (≈ 30 B). Since handler ICs already do the structure check inside shared thunks, the semantic path is unchanged; the cost is one extra indirect call per monomorphic access.</p>""",
   """<p>コンパクト出力モード（VM オプション、巨大/コールド関数単位、またはメモリ逼迫時）を追加し、get/put_by_id はセル判定 + ハンドラディスパッチのみ（≈ 30 B）、jtrue/jfalse は boolean 高速パス + サンクのみ（≈ 30 B）を出力する。ハンドラ IC は共有サンク内で structure 判定を行うので意味論は変わらず、コストはモノモーフィックアクセス 1 回あたりの間接呼び出し 1 つ。</p>"""),
 T("""<p>Medium: measurable throughput cost on property-heavy micro-benchmarks; hence a mode rather than the default. Code change is localized to <code>JITPropertyAccess.cpp</code>/<code>JITOpcodes.cpp</code>.</p>""",
   """<p>中: プロパティアクセス中心のマイクロベンチでは計測可能なスループット低下があるため、既定ではなくモードとする。変更は <code>JITPropertyAccess.cpp</code>/<code>JITOpcodes.cpp</code> に局所化される。</p>"""))

# 4
add(4, "Baseline: shared function entry (prologue + op_enter + arity/stack-overflow trailer ≈ 270 B per function)",
 "Baseline: 関数入口の共通化（prologue + op_enter + arity/スタックオーバーフロー trailer ≈ 270 B/関数）",
 "Executable code · Baseline", "実行コード · Baseline",
 f"≈ 200 B × functions (typescript: ≈ {kb(200*607)}, 3.5%)", f"≈ 200 B × 関数数（typescript: ≈ {kb(200*607)}、3.5%）",
 "med", "medium", "中",
 T(f"""<p>Every Baseline function emits its own stack check against an absolute address, callee-save stores, tag-register setup <span class="ref">(jit/JIT.cpp:766-798)</span>, then after the slow cases an arity-fixup trailer ({c('getArityPadding')}, jit/AssemblyHelpers.cpp:1780-1805, + {c('nearCallThunk(LLInt::arityFixup())')}) and a second prologue that jumps to {c('ThrowStackOverflowAtPrologue')} <span class="ref">(JIT.cpp:822-864)</span>. {c('op_enter')} additionally stores argument value profiles and checks traps.</p>""",
   f"""<p>各 Baseline 関数は絶対アドレスに対するスタックチェック、callee-save の保存、タグレジスタ設定 <span class="ref">(jit/JIT.cpp:766-798)</span> を自前で出力し、スローケースの後に arity 修正 trailer（{c('getArityPadding')}、jit/AssemblyHelpers.cpp:1780-1805、+ {c('nearCallThunk(LLInt::arityFixup())')}）と {c('ThrowStackOverflowAtPrologue')} へ飛ぶ第 2 プロローグ <span class="ref">(JIT.cpp:822-864)</span> を持つ。{c('op_enter')} はさらに引数の value profile 保存とトラップ検査を行う。</p>"""),
 T(f"""<p>typescript size statistics: {c('Baseline_prologue')} {n(pro[0])} B / {n(pro[1])} functions (avg {pro[2]:.0f} B), {c('Baseline_fast_op_enter')} {n(ent[0])} B (avg {ent[2]:.0f} B), {c('Baseline_slow_op_enter')} 10 B; the arity trailer (~70 B, not covered by a marker; visible in {c('--dumpDisassembly')}) brings the fixed per-function overhead to ≈ 275 B, i.e. ≈ {kb(275*607)} of {kb(ts_base)} (4.9%). For the many tiny functions typical of frameworks (avg Baseline function here is 5.6 KB) the ratio is higher.</p>""",
   f"""<p>typescript のサイズ統計: {c('Baseline_prologue')} {n(pro[0])} B / {n(pro[1])} 関数（平均 {pro[2]:.0f} B）、{c('Baseline_fast_op_enter')} {n(ent[0])} B（平均 {ent[2]:.0f} B）、{c('Baseline_slow_op_enter')} 10 B。arity trailer（約 70 B、マーカー対象外だが {c('--dumpDisassembly')} で確認可能）を含めると関数あたり固定 ≈ 275 B、すなわち {kb(ts_base)} のうち ≈ {kb(275*607)}（4.9%）。フレームワークに多い小さな関数（ここでは平均 5.6 KB）ではこの比率はさらに高い。</p>"""),
 T("""<p>A per-VM entry thunk (like <code>llint_function_for_call_arity_check</code>) that reads frame size / parameter count from <code>CallFrame::codeBlock()</code>, performs the stack check via the VM pointer already reachable from the CodeBlock, and jumps to the function body; the arity path becomes a shared thunk parameterised by CodeBlock.</p>""",
   """<p><code>llint_function_for_call_arity_check</code> のような VM ごとの入口サンクを用意し、<code>CallFrame::codeBlock()</code> からフレームサイズ/引数数を読み、CodeBlock から到達可能な VM ポインタ経由でスタックチェックを行い本体へジャンプする。arity パスは CodeBlock をパラメータとする共有サンクにする。</p>"""),
 T("""<p>Medium: one extra call/ret on the arity path (or per entry if the whole prologue is shared); PAC/return-address tagging on ARM64 needs care.</p>""",
   """<p>中: arity パス（プロローグ全体を共有する場合は各エントリ）で call/ret が 1 組増える。ARM64 の PAC / リターンアドレス署名に注意が必要。</p>"""))

# 5
add(5, "DFG/FTL: replace the per-exit OSR-exit stubs in the code body with a table dispatch",
 "DFG/FTL: コード本体内の OSR exit スタブ（1 exit ごと）をテーブルディスパッチに置き換える",
 "Executable code · DFG/FTL", "実行コード · DFG/FTL",
 f"typescript: ≈ {kb(dfg_exit_stub_bytes)} of DFG ({100*dfg_exit_stub_bytes/ts_dfg:.0f}%) + ≈ {kb(ftl_exit_stub_bytes)} of FTL", f"typescript: DFG の ≈ {kb(dfg_exit_stub_bytes)}（{100*dfg_exit_stub_bytes/ts_dfg:.0f}%）+ FTL の ≈ {kb(ftl_exit_stub_bytes)}",
 "med", "medium (repatch protocol)", "中（リパッチ手順）",
 T(f"""<p>For every OSR exit the DFG emits {c('move(TrustedImm32(i), numberTagRegister); patchableJump()')} <span class="ref">(dfg/DFGJITCompiler.cpp:102-109)</span> (~11 B on x86_64, 12-16 B on ARM64) and the FTL emits {c('pushToSaveImmediateWithoutTouchingRegisters(m_index); patchableJump')} <span class="ref">(ftl/FTLOSRExitHandle.cpp:44-46)</span>; both then jump to the shared {c('osrExitGenerationThunkGenerator')}. Only ~0.3% of exits ever fire ({c('osrExitCountForReoptimization = 100')}, OptionsList.h:382), and when they do the stub is repatched to the lazily compiled exit ({c('dfg/DFGOSRExit.cpp:209-221')}).</p>""",
   f"""<p>DFG は OSR exit ごとに {c('move(TrustedImm32(i), numberTagRegister); patchableJump()')} <span class="ref">(dfg/DFGJITCompiler.cpp:102-109)</span>（x86_64 で約 11 B、ARM64 で 12-16 B）を、FTL は {c('pushToSaveImmediateWithoutTouchingRegisters(m_index); patchableJump')} <span class="ref">(ftl/FTLOSRExitHandle.cpp:44-46)</span> を出力し、いずれも共有 {c('osrExitGenerationThunkGenerator')} へ飛ぶ。実際に発火する exit はごく一部（{c('osrExitCountForReoptimization = 100')}、OptionsList.h:382）で、発火時にスタブは遅延コンパイルされた exit へリパッチされる（{c('dfg/DFGOSRExit.cpp:209-221')}）。</p>"""),
 T(f"""<p>Instrumented finalizer counts (typescript): DFG {n(dfgR['exits'])} exits in {dfgR['count']} compiles → ≈ {kb(dfg_exit_stub_bytes)} of the {kb(ts_dfg)} DFG code ({100*dfg_exit_stub_bytes/ts_dfg:.0f}%); FTL {n(ftlR['exits'])} exits → ≈ {kb(ftl_exit_stub_bytes)} of {kb(ts_ftl)}. acorn-wtb: {n(RET['acorn-wtb']['retained']['DFG']['exits'])} DFG exits (≈ {kb(RET['acorn-wtb']['retained']['DFG']['exits']*11)}), gbemu {n(RET['gbemu']['retained']['DFG']['exits'])}. Compiled exit stubs (LinkBuffer profile {c('DFGOSRExit')}/{c('FTLOSRExit')}) are separately {kb(ts.get('lb_DFGOSRExit',0))} + {kb(ts.get('lb_FTLOSRExit',0))} for typescript, each its own 32 B-rounded allocation.</p>""",
   f"""<p>ファイナライザ計測（typescript）: DFG は {dfgR['count']} コンパイルで {n(dfgR['exits'])} exit → DFG コード {kb(ts_dfg)} のうち ≈ {kb(dfg_exit_stub_bytes)}（{100*dfg_exit_stub_bytes/ts_dfg:.0f}%）。FTL は {n(ftlR['exits'])} exit → {kb(ts_ftl)} のうち ≈ {kb(ftl_exit_stub_bytes)}。acorn-wtb: DFG exit {n(RET['acorn-wtb']['retained']['DFG']['exits'])}（≈ {kb(RET['acorn-wtb']['retained']['DFG']['exits']*11)}）、gbemu {n(RET['gbemu']['retained']['DFG']['exits'])}。コンパイル済み exit スタブ（LinkBuffer プロファイル {c('DFGOSRExit')}/{c('FTLOSRExit')}）は typescript で別途 {kb(ts.get('lb_DFGOSRExit',0))} + {kb(ts.get('lb_FTLOSRExit',0))} あり、各々が 32 B 単位の独立割り当て。</p>"""),
 T("""<p>Emit a 5-byte <code>call</code> (x86_64) / <code>bl</code> (ARM64) into a per-CodeBlock exit thunk that derives the exit index from the return address via a sorted table (or from a compact per-exit index table in <code>JITData</code>), and repatch by writing the table entry instead of the code. This also lets <code>OSRExit::m_patchableJumpLocation</code> (8 B/exit) go away.</p>""",
   """<p>5 バイトの <code>call</code>（x86_64）/ <code>bl</code>（ARM64）で CodeBlock ごとの exit サンクに入り、リターンアドレスからソート済みテーブル（または <code>JITData</code> 内のコンパクトな exit インデックス表）で exit 番号を求める。リパッチはコードではなくテーブルの書き換えで行う。これにより <code>OSRExit::m_patchableJumpLocation</code>（8 B/exit）も不要になる。</p>"""),
 T("""<p>Medium: touches the exit-thunk ABI (<code>osrExitGenerationThunkGenerator</code>) and the repatch path in <code>DFGOSRExit.cpp</code>/<code>FTLOSRExitCompiler.cpp</code>; slight cost on the (rare) exit path.</p>""",
   """<p>中: exit サンク ABI（<code>osrExitGenerationThunkGenerator</code>）と <code>DFGOSRExit.cpp</code>/<code>FTLOSRExitCompiler.cpp</code> のリパッチ経路に触れる。（稀な）exit 経路がわずかに遅くなる。</p>"""))

# 6
add(6, "Thunk-ify inline C-call slow paths: DFG store barrier (87 B/site), Baseline math/compare slow paths (55-110 B/site)",
 "インライン C 呼び出しスローパスのサンク化: DFG ストアバリア（87 B/サイト）、Baseline の算術/比較スローパス（55-110 B/サイト）",
 "Executable code · DFG + Baseline", "実行コード · DFG + Baseline",
 f"typescript: ≈ {kb(sb[0]*0.85)} of DFG (7%) + ≈ 60 KB Baseline", f"typescript: DFG の ≈ {kb(sb[0]*0.85)}（7%）+ Baseline ≈ 60 KB",
 "low", "low-medium", "低〜中",
 T(f"""<p>{c('SpeculativeJIT::compileStoreBarrier')} registers a slow-path lambda that does {c('silentSpill(savePlans); callOperationWithoutExceptionCheck(operationWriteBarrierSlowPath, ...); silentFill(savePlans)')} inline per site <span class="ref">(dfg/DFGSpeculativeJIT.cpp:13079-13092)</span>; the FTL emits a {c('vmCall(operationWriteBarrierSlowPath)')} block per barrier <span class="ref">(ftl/FTLLowerDFGToB3.cpp:26754)</span>. Baseline math ICs and compares still use inline {c('callOperation')} (far call 13 B x86_64 / 20 B ARM64 + argument setup + exception check) <span class="ref">(jit/JITArithmetic.cpp:998-1004, JITOpcodes.cpp:1053-1064)</span>, unlike the generic slow ops that already go through {c('JITSlowPathCall')} thunks (8-10 B).</p>""",
   f"""<p>{c('SpeculativeJIT::compileStoreBarrier')} はサイトごとに {c('silentSpill(savePlans); callOperationWithoutExceptionCheck(operationWriteBarrierSlowPath, ...); silentFill(savePlans)')} をインラインで行うスローパスを登録する <span class="ref">(dfg/DFGSpeculativeJIT.cpp:13079-13092)</span>。FTL もバリアごとに {c('vmCall(operationWriteBarrierSlowPath)')} ブロックを出力する <span class="ref">(ftl/FTLLowerDFGToB3.cpp:26754)</span>。Baseline の算術 IC と比較は、汎用スロー op が既に {c('JITSlowPathCall')} サンク（8-10 B）を使うのに対し、依然インラインの {c('callOperation')}（far call 13 B x86_64 / 20 B ARM64 + 引数設定 + 例外チェック）を使う <span class="ref">(jit/JITArithmetic.cpp:998-1004, JITOpcodes.cpp:1053-1064)</span>。</p>"""),
 T(f"""<p>{c('--dumpDFGJITSizeStatistics=1')} typescript: {c('DFG_slow_FencedStoreBarrier')} {n(sb[0])} B / {n(sb[1])} sites (avg {sb[2]:.0f} B) = {100*sb[0]/ts_dfg:.1f}% of DFG code, plus {c('DFG_slow_CheckTierUpAtReturn')} 42 KB (1,043 × 40 B). Baseline: {c('Baseline_slow_op_jneq')} 55 B, {c('slow_op_jnless')}/{c('jless')} 110 B, {c('slow_op_add')}/{c('sub')} 55 B per site.</p>""",
   f"""<p>typescript で {c('--dumpDFGJITSizeStatistics=1')}: {c('DFG_slow_FencedStoreBarrier')} は {n(sb[1])} サイトで {n(sb[0])} B（平均 {sb[2]:.0f} B）= DFG コードの {100*sb[0]/ts_dfg:.1f}%。加えて {c('DFG_slow_CheckTierUpAtReturn')} 42 KB（1,043 × 40 B）。Baseline: {c('Baseline_slow_op_jneq')} 55 B、{c('slow_op_jnless')}/{c('jless')} 110 B、{c('slow_op_add')}/{c('sub')} 55 B/サイト。</p>"""),
 T("""<p>A shared write-barrier slow-path thunk that saves/restores all caller-save registers itself (the DFG barrier only needs the base cell in a register), reducing each site to <code>call thunk</code> + <code>jmp back</code> (~10 B); Baseline math/compare slow paths become <code>JITSlowPathCall</code>-style thunks with the ArithProfile/MathIC pointer passed in a register loaded from metadata.</p>""",
   """<p>すべての caller-save レジスタを自ら退避/復元する共有ライトバリア・スローパスサンクを用意し（DFG のバリアはベースセルがレジスタにあれば十分）、各サイトを <code>call thunk</code> + <code>jmp back</code>（約 10 B）にする。Baseline の算術/比較スローパスは、メタデータから読んだ ArithProfile/MathIC ポインタをレジスタで渡す <code>JITSlowPathCall</code> 型のサンクにする。</p>"""),
 T("""<p>Low-medium: the barrier thunk spills more registers than the precise <code>savePlans</code> do (slow path only); math IC repatching (<code>generateOutOfLine</code>) must move to the thunk-dispatch design already used by <code>InlineCacheCompiler::generateSlowPathCode</code>.</p>""",
   """<p>低〜中: バリアサンクは精密な <code>savePlans</code> より多くのレジスタを退避する（スローパスのみ）。MathIC のリパッチ（<code>generateOutOfLine</code>）は <code>InlineCacheCompiler::generateSlowPathCode</code> がすでに使うサンクディスパッチ方式へ移す必要がある。</p>"""))

# 7
add(7, "Executable allocator: 16-byte granule, compaction-before-allocation on ARM64, tighter libpas size classes",
 "実行メモリアロケータ: 16 B グラニュール、ARM64 での割り当て前圧縮、libpas サイズクラスの締め付け",
 "Executable code · allocator", "実行コード · アロケータ",
 "≈ 3-9% of JIT pool RSS", "JIT プール RSS の ≈ 3-9%",
 "low", "low", "低",
 T(f"""<p>{c('LinkBuffer::allocate')} pads the assembler buffer with breakpoints up to a multiple of {c('jitAllocationGranule = 32')} <span class="ref">(assembler/LinkBuffer.cpp:519-533, jit/ExecutableAllocator.h:60)</span> although the libpas JIT heap's minimum alignment is 16 B <span class="ref">(bmalloc/libpas/src/libpas/jit_heap_config.h:38-39)</span>. On ARM64 the branch-compacted size is only applied afterwards via {c('m_executableMemory->shrink(m_size)')} <span class="ref">(LinkBuffer.cpp:424-438)</span>, and {c('jit_heap_shrink')} is a no-op for segregated (≤ 2000 B) allocations <span class="ref">(jit_heap.c:90-99)</span>, so small functions and stubs keep their pre-compaction size class; size classes may be reused up to {c('PAS_SIZE_CLASS_PROGRESSION = 1.3')}×.</p>""",
   f"""<p>{c('LinkBuffer::allocate')} は libpas JIT ヒープの最小アラインが 16 B <span class="ref">(bmalloc/libpas/src/libpas/jit_heap_config.h:38-39)</span> であるにもかかわらず、アセンブラバッファを {c('jitAllocationGranule = 32')} <span class="ref">(assembler/LinkBuffer.cpp:519-533, jit/ExecutableAllocator.h:60)</span> の倍数までブレークポイントで埋める。ARM64 では分岐圧縮後のサイズが {c('m_executableMemory->shrink(m_size)')} <span class="ref">(LinkBuffer.cpp:424-438)</span> で後から適用されるが、{c('jit_heap_shrink')} は segregated（≤ 2000 B）割り当てでは no-op <span class="ref">(jit_heap.c:90-99)</span> なので、小さな関数やスタブは圧縮前のサイズクラスに留まる。サイズクラスは最大 {c('PAS_SIZE_CLASS_PROGRESSION = 1.3')} 倍まで流用される。</p>"""),
 T("""<p>Synthetic workload with all code alive: N=1000 functions → linked (already granule-padded) 3,565,034 B vs JIT-pool RSS 3,903,488 B (+9.5%); N=4000 → 14,076,746 B vs 15,126,528 B (+7.5%). IC stubs average 103-125 B (typescript: 736 stubs), so 32-B rounding alone wastes up to ~15% on them; DFG/FTL OSR-exit stubs are separate 32-B-rounded allocations (typescript: 310 + 64).</p>""",
   """<p>全コードが生存する合成ワークロード: N=1000 関数でリンク済み（すでにグラニュール込み）3,565,034 B に対し JIT プール RSS 3,903,488 B（+9.5%）。N=4000 で 14,076,746 B 対 15,126,528 B（+7.5%）。IC スタブは平均 103-125 B（typescript: 736 個）なので 32 B 丸めだけで最大約 15% を浪費。DFG/FTL の OSR exit スタブも 32 B 単位の個別割り当て（typescript: 310 + 64）。</p>"""),
 T("""<p>Lower the granule to 16 B on libpas builds (the sorted <code>JITStubRoutineSet</code> no longer needs <code>addressStep()</code>), compute the compacted size before allocating on ARM64 (compaction into a scratch buffer, then exact-size allocation), and tune the JIT heap's size-class progression / segregated cutoff.</p>""",
   """<p>libpas ビルドではグラニュールを 16 B に下げ（ソート済み <code>JITStubRoutineSet</code> はもう <code>addressStep()</code> を必要としない）、ARM64 では割り当て前に圧縮サイズを求め（スクラッチバッファに圧縮してから正確なサイズで割り当て）、JIT ヒープのサイズクラス進行率 / segregated 上限を調整する。</p>"""),
 T("""<p>Low for the granule; medium for libpas tuning (page sharing / scavenger behaviour). Measure with <code>$vm.linkBufferStats()</code> vs pool RSS (smaps), <code>--verboseExecutablePoolAllocation</code>, <code>DUMP_LINK_STATISTICS</code>.</p>""",
   """<p>グラニュールは低、libpas 調整は中（ページ共有 / スカベンジャ挙動）。<code>$vm.linkBufferStats()</code> とプール RSS（smaps）、<code>--verboseExecutablePoolAllocation</code>、<code>DUMP_LINK_STATISTICS</code> で計測。</p>"""))

# 8
add(8, "Slim DataOnlyCallLinkInfo in call metadata (80 B → 64 B) and drop the dead OptimizingCallLinkInfo::m_callLocation (96 → 80 B)",
 "呼び出しメタデータの DataOnlyCallLinkInfo をスリム化（80 B → 64 B）し、未使用の OptimizingCallLinkInfo::m_callLocation を削除（96 → 80 B）",
 "Metadata · calls", "メタデータ · 呼び出し",
 f"acorn-wtb: −{kb(ac_call_n*16)} of {kb(ac_meta['total'])} metadata; typescript −{kb(ts_call_n*16)}", f"acorn-wtb: メタデータ {kb(ac_meta['total'])} のうち −{kb(ac_call_n*16)}、typescript −{kb(ts_call_n*16)}",
 "med", "medium", "中",
 T(f"""<p>{c('OpCall::Metadata')} = {MS['OpCall']} B ({c('DataOnlyCallLinkInfo')} 80 B + {c('ArrayProfile')} 16 B), {c('OpIteratorNext::Metadata')} = {MS['OpIteratorNext']} B (record layout dump). Inside the 80 B: {c('m_owner')} (8 B) is always the CodeBlock that owns the metadata table and {c('m_codeOrigin')} (8 B) is always {CO} ({c('CodeBlock.cpp:469-472')} {c('link_callLinkInfo')}); {c('m_slowPathCount')} is a full uint32; ICs already derive the owner ({c('ownerForSlowPath')}, CallLinkInfo.h:466-475 "This is a hack only for now"). {c('OptimizingCallLinkInfo::m_callLocation')} <span class="ref">(CallLinkInfo.h:461)</span> is only ever written for {c('DirectCallLinkInfo')} (CallLinkInfo.cpp:467, 501) — for the optimizing data-IC variant it is dead but pads the object to 96 B.</p>""",
   f"""<p>{c('OpCall::Metadata')} = {MS['OpCall']} B（{c('DataOnlyCallLinkInfo')} 80 B + {c('ArrayProfile')} 16 B）、{c('OpIteratorNext::Metadata')} = {MS['OpIteratorNext']} B（レコードレイアウトダンプ）。80 B の内訳で、{c('m_owner')}（8 B）は常にそのメタデータ表を持つ CodeBlock、{c('m_codeOrigin')}（8 B）は常に {CO}（{c('CodeBlock.cpp:469-472')} {c('link_callLinkInfo')}）。{c('m_slowPathCount')} はフル uint32。IC 側はすでに owner を導出している（{c('ownerForSlowPath')}、CallLinkInfo.h:466-475「This is a hack only for now」）。{c('OptimizingCallLinkInfo::m_callLocation')} <span class="ref">(CallLinkInfo.h:461)</span> への書き込みは {c('DirectCallLinkInfo')} のみ（CallLinkInfo.cpp:467, 501）で、optimizing data-IC 版では未使用のままオブジェクトを 96 B に膨らませている。</p>"""),
 T(f"""<p>{c('ENABLE(METADATA_STATISTICS)')} build: call-family opcodes (call, call_ignore_result, construct, tail_call, varargs, iterator_open/next…) are <b>{n(ac_call_bytes)} B of {n(ac_meta['total'])} B ({100*ac_call_bytes/ac_meta['total']:.0f}%)</b> of linked metadata in acorn-wtb ({n(ac_call_n)} sites; op_call alone {n(ac_meta['per']['op_call'][1])} B) and {n(ts_call_bytes)} B of {n(meta_ts['total'])} B ({100*ts_call_bytes/meta_ts['total']:.0f}%) in typescript ({n(ts_call_n)} sites). Removing 16 B per site: acorn −{kb(ac_call_n*16)}, typescript −{kb(ts_call_n*16)}. DFG/FTL {c('OptimizingCallLinkInfo')}: typescript {n(dfgR['callLinkBag']+ftlR['callLinkBag'])} (Bag) + unlinked; −16 B each.</p>""",
   f"""<p>{c('ENABLE(METADATA_STATISTICS)')} ビルド: 呼び出し系 opcode（call, call_ignore_result, construct, tail_call, varargs, iterator_open/next…）はリンク済みメタデータのうち acorn-wtb で <b>{n(ac_meta['total'])} B 中 {n(ac_call_bytes)} B（{100*ac_call_bytes/ac_meta['total']:.0f}%）</b>（{n(ac_call_n)} サイト、op_call 単独で {n(ac_meta['per']['op_call'][1])} B）、typescript で {n(meta_ts['total'])} B 中 {n(ts_call_bytes)} B（{100*ts_call_bytes/meta_ts['total']:.0f}%、{n(ts_call_n)} サイト）。サイトあたり 16 B 削減で acorn −{kb(ac_call_n*16)}、typescript −{kb(ts_call_n*16)}。DFG/FTL の {c('OptimizingCallLinkInfo')}: typescript で {n(dfgR['callLinkBag']+ftlR['callLinkBag'])}（Bag）+ unlinked、各 −16 B。</p>"""),
 T("""<p>Store a 4-byte <code>BytecodeIndex</code> instead of <code>CodeOrigin</code> in the data-only variant, shrink <code>m_slowPathCount</code> to 16 bits so it fits in the header word, and derive the owner from the metadata table (or pass it from the LLInt/Baseline slow paths); delete <code>OptimizingCallLinkInfo::m_callLocation</code> outright.</p>""",
   """<p>data-only 版では <code>CodeOrigin</code> の代わりに 4 B の <code>BytecodeIndex</code> を持ち、<code>m_slowPathCount</code> を 16 bit にしてヘッダ語に収め、owner はメタデータ表から導出（または LLInt/Baseline スローパスから渡す）。<code>OptimizingCallLinkInfo::m_callLocation</code> は単純に削除する。</p>"""),
 T("""<p>Medium for the data-only split (generic repatch/GC code uses <code>owner()</code>/<code>codeOrigin()</code>; LLInt offsets change); trivial for the dead field.</p>""",
   """<p>data-only 分離は中（汎用のリパッチ/GC コードが <code>owner()</code>/<code>codeOrigin()</code> を使い、LLInt のオフセットも変わる）。未使用フィールド削除は自明。</p>"""))

# 9
add(9, "HandlerPropertyInlineCache 112 → ≈ 88 B: derive doneLocation, m_slowOperation and (Baseline) codeOrigin",
 "HandlerPropertyInlineCache 112 → ≈ 88 B: doneLocation、m_slowOperation、（Baseline の）codeOrigin を導出値にする",
 "Metadata · inline caches", "メタデータ · インラインキャッシュ",
 "≈ 24 B × IC sites (typescript ≈ 17.8K sites → ≈ 420 KB)", "≈ 24 B × IC サイト（typescript ≈ 17.8K サイト → ≈ 420 KB）",
 "low", "low-medium", "低〜中",
 T(f"""<p>Record layout: {c('HandlerPropertyInlineCache')} = 112 B <span class="ref">(bytecode/PropertyInlineCache.h:398-443, 549-570)</span>. {c('doneLocation')} (8 B) is copied from the unlinked IC ({c('PropertyInlineCache.cpp:774, 802')}) but is never read by handler-IC machine code: in {c('InlineCacheCompiler::succeed()')} the {c('farJump(... offsetOfDoneLocation())')} branch sits behind an identical {c('isHandlerIC()')} test that already returned <span class="ref">(bytecode/InlineCacheCompiler.cpp:1141-1153, dead code)</span>; the only reader is DFG OSR exit ({c('DFGOSRExitCompilerCommon.cpp:267')}), which can consult the unlinked table like calls do ({c('BaselineJITCode::getCallLinkDoneLocationForBytecodeIndex')}). {c('m_slowOperation')} (8 B) is a pure function of {c('accessType')} ({c('slowOperationFromUnlinkedPropertyInlineCache')}, PropertyInlineCache.cpp:591-650). Baseline sets {c('codeOrigin')} = {c('callSiteIndex')} = bytecode index (:775-778).</p>""",
   f"""<p>レコードレイアウト: {c('HandlerPropertyInlineCache')} = 112 B <span class="ref">(bytecode/PropertyInlineCache.h:398-443, 549-570)</span>。{c('doneLocation')}（8 B）は unlinked IC からコピーされる（{c('PropertyInlineCache.cpp:774, 802')}）が、ハンドラ IC の機械語からは読まれない: {c('InlineCacheCompiler::succeed()')} の {c('farJump(... offsetOfDoneLocation())')} は、その直前で return する同一の {c('isHandlerIC()')} 判定の後ろにあり到達不能 <span class="ref">(bytecode/InlineCacheCompiler.cpp:1141-1153)</span>。唯一の読み手は DFG OSR exit（{c('DFGOSRExitCompilerCommon.cpp:267')}）で、呼び出しと同様に unlinked 表を引ける（{c('BaselineJITCode::getCallLinkDoneLocationForBytecodeIndex')}）。{c('m_slowOperation')}（8 B）は {c('accessType')} の純関数（{c('slowOperationFromUnlinkedPropertyInlineCache')}、PropertyInlineCache.cpp:591-650）。Baseline では {c('codeOrigin')} = {c('callSiteIndex')} = bytecode index（:775-778）。</p>"""),
 T(f"""<p>Recent commit b00e0c35f8 ("Move repatching-only fields out of HandlerPropertyInlineCache") reports 16,500 Baseline + 1,700 DFG IC sites on Octane typescript and 465 KB saved by 16 B/site; the same population × 24 B ≈ 430 KB. Metadata statistics here: typescript has {n(meta_ts['per']['op_get_by_id'][0])} op_get_by_id + {n(meta_ts['per']['op_put_by_id'][0])} op_put_by_id entries; DFG allocates a 112 B handler IC for every {c('UnlinkedPropertyInlineCache')} ({n(dfgR['unlinkedPIC'])} in typescript) whether or not the site executes.</p>""",
   f"""<p>直近のコミット b00e0c35f8（"Move repatching-only fields out of HandlerPropertyInlineCache"）は Octane typescript で Baseline 16,500 + DFG 1,700 IC サイト、16 B/サイトで 465 KB 削減と報告している。同じ母数 × 24 B ≈ 430 KB。ここでのメタデータ統計: typescript は op_get_by_id {n(meta_ts['per']['op_get_by_id'][0])} + op_put_by_id {n(meta_ts['per']['op_put_by_id'][0])} エントリ。DFG は各 {c('UnlinkedPropertyInlineCache')}（typescript で {n(dfgR['unlinkedPIC'])}）に対し、実行の有無にかかわらず 112 B のハンドラ IC を確保する。</p>"""),
 T("""<p>Recover the IC index by pointer arithmetic in the <code>ButterflyArray</code> leading span (<code>BaselineJITData::propertyCache(index)</code>), look up <code>doneLocation</code>/<code>bytecodeIndex</code> in the unlinked vector on the OSR-exit path only, and select the slow operation in the slow-path thunk from <code>accessType</code> (one thunk per AccessType or a small table).</p>""",
   """<p><code>ButterflyArray</code> 先頭スパン内のポインタ演算で IC インデックスを復元し（<code>BaselineJITData::propertyCache(index)</code>）、OSR exit 経路でのみ unlinked ベクタから <code>doneLocation</code>/<code>bytecodeIndex</code> を引き、slow operation はスローパスサンク内で <code>accessType</code> から選ぶ（AccessType ごとのサンク、または小さな表）。</p>"""),
 T("""<p>Low-medium: needs an IC→JITCode back-reference on the exit path; +30 tiny thunks (a few KB) or one table load in the slow-path thunk.</p>""",
   """<p>低〜中: exit 経路で IC→JITCode の逆参照が必要。約 30 個の小さなサンク（数 KB）か、スローパスサンク内の表参照 1 回が増える。</p>"""))

# 10
add(10, "PropertyInlineCache::m_bufferedStructures Variant (24 B) + lock live in every IC but are used only while buffering",
 "PropertyInlineCache::m_bufferedStructures の Variant（24 B）+ ロックは全 IC にあるがバッファリング中しか使われない",
 "Metadata · inline caches", "メタデータ · インラインキャッシュ",
 "−16 B × IC sites (typescript ≈ 285 KB)", "−16 B × IC サイト（typescript ≈ 285 KB）",
 "low", "low", "低",
 T(f"""<p>{c('Variant<monostate, Vector<StructureID>, Vector<tuple<StructureID, CacheableIdentifier>>> m_bufferedStructures')} occupies offsets 56-79 of the 96 B base <span class="ref">(bytecode/PropertyInlineCache.h:415; record layout)</span> plus a 1-byte {c('Lock')} (:432). It is filled only in {c('considerRepatchingCacheImpl')} (PropertyInlineCache.cpp:250-315) and cleared by {c('clearBufferedStructures')} (:319-329) whenever code is generated; monomorphic ICs (the majority) never leave {c('monostate')}. The other data-IC state ({c('byIdSelfOffset')}, {c('m_inlineAccessBaseStructureID')}, {c('m_inlineHolder')}, 24 B) is only meaningful for {c('preconfiguredCacheType != Unset')} (self get/put/in), i.e. dead space for by-val/instanceof/delete/private-brand ICs.</p>""",
   f"""<p>{c('Variant<monostate, Vector<StructureID>, Vector<tuple<StructureID, CacheableIdentifier>>> m_bufferedStructures')} は 96 B ベースのオフセット 56-79 を占め <span class="ref">(bytecode/PropertyInlineCache.h:415; レイアウトダンプ)</span>、さらに 1 B の {c('Lock')}（:432）。書き込みは {c('considerRepatchingCacheImpl')}（PropertyInlineCache.cpp:250-315）のみで、コード生成のたびに {c('clearBufferedStructures')}（:319-329）で空になる。大多数のモノモーフィック IC は {c('monostate')} のまま。もう一組の data-IC 状態（{c('byIdSelfOffset')}、{c('m_inlineAccessBaseStructureID')}、{c('m_inlineHolder')}、24 B）は {c('preconfiguredCacheType != Unset')}（self の get/put/in）でしか意味を持たず、by-val / instanceof / delete / private-brand IC では死領域。</p>"""),
 T("""<p>Layout dump: <code>PropertyInlineCache</code> sizeof 96, dsize 94; the Variant is 16 B storage + 8 B index. With ≈ 17.8K linked handler ICs (typescript, see #9) → −16 B × 17.8K ≈ 285 KB; making the 24 B inline-access group a second leading type in the ButterflyArray for non-preconfigured sites saves a further ~24 B × 30-40% of sites (≈ 130-170 KB).</p>""",
   """<p>レイアウトダンプ: <code>PropertyInlineCache</code> sizeof 96、dsize 94。Variant は 16 B のストレージ + 8 B のインデックス。リンク済みハンドラ IC ≈ 17.8K（typescript、#9 参照）→ −16 B × 17.8K ≈ 285 KB。24 B のインラインアクセス群を非 preconfigured サイト向けの別の先頭型にすれば、さらにサイトの 30-40% × ~24 B（≈ 130-170 KB）。</p>"""),
 T("""<p>Replace the Variant with a <code>std::unique_ptr&lt;BufferedStructures&gt;</code> (8 B) holding the vectors and the lock, allocated on first buffering and freed on <code>clearBufferedStructures</code>.</p>""",
   """<p>Variant を、ベクタとロックを保持する <code>std::unique_ptr&lt;BufferedStructures&gt;</code>（8 B）に置き換え、初回バッファリング時に確保し <code>clearBufferedStructures</code> で解放する。</p>"""),
 T("""<p>Low: concurrent-JS readers already take the lock; JIT code never touches these fields.</p>""",
   """<p>低: 並行 JS の読み手はすでにロックを取っており、JIT コードはこれらのフィールドに触れない。</p>"""))

# 11
add(11, "InlineCacheHandler is alignas(64): 32 B of padding per handler (25%), plus a separate 40 B clearing-watchpoint object",
 "InlineCacheHandler は alignas(64): ハンドラごとに 32 B のパディング（25%）と、別確保の 40 B クリア用ウォッチポイント",
 "Metadata · inline caches", "メタデータ · インラインキャッシュ",
 "−32…−80 B per live handler (≈ 0.3-1 MB on typescript-class pages)", "生存ハンドラあたり −32…−80 B（typescript 級のページで ≈ 0.3-1 MB）",
 "low", "low-medium", "低〜中",
 T(f"""<p>{c('class JSC_CACHE_LINE_ALIGNED InlineCacheHandler')} <span class="ref">(bytecode/InlineCacheHandler.h:55)</span> with {c('JSC_CACHE_LINE_ALIGNED = alignas(64)')} (assembler/CPU.h:183-184): the layout dump shows dsize 96, sizeof 128. Each watched handler also allocates a {c('PropertyInlineCacheClearingWatchpoint')} (40 B: Watchpoint 24 + PackedCellPtr owner + {c('PropertyInlineCache&')}) through {c('unique_ptr m_watchpoint')} (:172; created at InlineCacheCompiler.cpp:7204-7205, 7226-7227). The hot fields fit in the first 48 B ({c('static_assert(offsetOfUid() == 40)')}).</p>""",
   f"""<p>{c('class JSC_CACHE_LINE_ALIGNED InlineCacheHandler')} <span class="ref">(bytecode/InlineCacheHandler.h:55)</span>、{c('JSC_CACHE_LINE_ALIGNED = alignas(64)')}（assembler/CPU.h:183-184）: レイアウトダンプでは dsize 96、sizeof 128。監視対象を持つハンドラは {c('PropertyInlineCacheClearingWatchpoint')}（40 B: Watchpoint 24 + PackedCellPtr owner + {c('PropertyInlineCache&')}）を {c('unique_ptr m_watchpoint')}（:172; InlineCacheCompiler.cpp:7204-7205, 7226-7227 で生成）で別途確保する。ホットなフィールドは先頭 48 B に収まる（{c('static_assert(offsetOfUid() == 40)')}）。</p>"""),
 T("""<p>sizeof harness: <code>InlineCacheHandler</code> 128 (payload 96), <code>InlineCacheHandlerWithJSCall</code> 192 (payload 176), <code>PropertyInlineCacheClearingWatchpoint</code> 32-40. Handler count ≈ number of IC sites that executed at least once (order 10<sup>4</sup> on typescript-class code, see #9), so 32-80 B each ≈ 0.3-1 MB.</p>""",
   """<p>sizeof ハーネス: <code>InlineCacheHandler</code> 128（ペイロード 96）、<code>InlineCacheHandlerWithJSCall</code> 192（ペイロード 176）、<code>PropertyInlineCacheClearingWatchpoint</code> 32-40。ハンドラ数 ≈ 一度でも実行された IC サイト数（typescript 級コードで 10<sup>4</sup> オーダー、#9 参照）なので、各 32-80 B ≈ 0.3-1 MB。</p>"""),
 T("""<p>Either drop the 64-byte alignment (keep hot fields first; a 96 B object straddles a line at most once) or use the padding: embed the clearing watchpoint (24 B Watchpoint base + owner) inside the handler and reach the IC through <code>m_next</code>/back-pointer, removing the extra malloc.</p>""",
   """<p>64 B アラインを外す（ホットなフィールドを先頭に保てば 96 B オブジェクトがラインをまたぐのは高々 1 回）か、パディングを活用する: クリア用ウォッチポイント（24 B の Watchpoint 基底 + owner）をハンドラ内に埋め込み、IC へは <code>m_next</code>/逆ポインタで到達させ、余分な malloc をなくす。</p>"""),
 T("""<p>Low for the alignment (perf to be validated), medium for embedding (<code>fireInternal</code> must locate the <code>PropertyInlineCache</code>).</p>""",
   """<p>アラインは低（性能検証が必要）、埋め込みは中（<code>fireInternal</code> が <code>PropertyInlineCache</code> を特定できる必要がある）。</p>"""))

# 12
add(12, "Pre-compiled handler thunks still allocate a per-handler PolymorphicAccessJITStubRoutine (96 B) + WatchpointSet (24 B)",
 "事前コンパイル済みハンドラサンクでも、ハンドラごとに PolymorphicAccessJITStubRoutine（96 B）+ WatchpointSet（24 B）を確保している",
 "Metadata · inline caches", "メタデータ · インラインキャッシュ",
 "−120 B per handler without watchpoints (≈ 0.5-1.5 MB on typescript-class pages)", "ウォッチポイントのないハンドラあたり −120 B（typescript 級ページで ≈ 0.5-1.5 MB）",
 "low", "low-medium", "低〜中",
 T(f"""<p>{c('compileOneAccessCaseHandler')} selects one of ~99 shared thunks (e.g. {c('CommonJITThunkID::GetByIdLoadOwnPropertyHandler')}) but wraps it in a fresh {c('createPreCompiledICJITStubRoutine(code, vm, codeBlock)')} at 26 call sites <span class="ref">(bytecode/InlineCacheCompiler.cpp:7283, 7296, …)</span>, and {c('PolymorphicAccessJITStubRoutine')}'s constructor unconditionally does {c('m_watchpointSet(WatchpointSet::create(IsWatched))')} <span class="ref">(jit/GCAwareJITStubRoutine.cpp:112-118)</span> even when {c('watchedConditions')} is empty (GetByIdSelf, PutByIdReplace, InByIdSelf, Miss, indexed loads…). The stateless path already shows the alternative: one routine per key in {c('SharedJITStubSet::m_statelessStubs')} (:7246-7252, 8078-8082).</p>""",
   f"""<p>{c('compileOneAccessCaseHandler')} は約 99 個の共有サンク（例: {c('CommonJITThunkID::GetByIdLoadOwnPropertyHandler')}）を選ぶが、26 箇所で毎回新しい {c('createPreCompiledICJITStubRoutine(code, vm, codeBlock)')} に包む <span class="ref">(bytecode/InlineCacheCompiler.cpp:7283, 7296, …)</span>。しかも {c('PolymorphicAccessJITStubRoutine')} のコンストラクタは {c('watchedConditions')} が空（GetByIdSelf、PutByIdReplace、InByIdSelf、Miss、インデックス読み出し…）でも無条件に {c('m_watchpointSet(WatchpointSet::create(IsWatched))')} を行う <span class="ref">(jit/GCAwareJITStubRoutine.cpp:112-118)</span>。stateless 経路は代替案をすでに示している: {c('SharedJITStubSet::m_statelessStubs')} にキーごと 1 ルーチン（:7246-7252, 8078-8082）。</p>"""),
 T("""<p>sizeof: <code>PolymorphicAccessJITStubRoutine</code> 96 B (+ malloc rounding), <code>WatchpointSet</code> 24 B; both per handler. With H ≈ 10<sup>4</sup> executed monomorphic sites (typescript: 14,417 get_by_id + 1,907 put_by_id Baseline sites compiled), 120 B × H ≈ 1.2 MB upper bound; the <code>InlineCache</code> LinkBuffer profile shows only 736 bespoke stubs were actually compiled for typescript, i.e. the vast majority of handlers are pre-compiled-thunk wrappers.</p>""",
   """<p>sizeof: <code>PolymorphicAccessJITStubRoutine</code> 96 B（+ malloc 丸め）、<code>WatchpointSet</code> 24 B。いずれもハンドラごと。実行されたモノモーフィックサイト H ≈ 10<sup>4</sup>（typescript: Baseline でコンパイルされた get_by_id 14,417 + put_by_id 1,907 サイト）とすると 120 B × H ≈ 1.2 MB が上限。<code>InlineCache</code> LinkBuffer プロファイルでは typescript で実際にコンパイルされた個別スタブは 736 個だけで、ハンドラの大半は事前コンパイル済みサンクのラッパである。</p>"""),
 T("""<p>Share one immortal <code>PolymorphicAccessJITStubRoutine</code> per <code>CommonJITThunkID</code> when there are no watched conditions / additional watchpoint sets (extend <code>m_statelessStubs</code>), or let <code>InlineCacheHandler</code> hold a bare <code>MacroAssemblerCodeRef</code> and allocate a routine only when watchpoints are needed; make <code>m_watchpointSet</code> lazy in all cases (<code>isStillValid()</code> already tolerates null).</p>""",
   """<p>監視条件 / 追加ウォッチポイント集合がない場合は <code>CommonJITThunkID</code> ごとに不滅の <code>PolymorphicAccessJITStubRoutine</code> を 1 つ共有する（<code>m_statelessStubs</code> の拡張）か、<code>InlineCacheHandler</code> が生の <code>MacroAssemblerCodeRef</code> を持ち、ウォッチポイントが必要な時だけルーチンを確保する。<code>m_watchpointSet</code> はすべての場合で遅延確保にする（<code>isStillValid()</code> は null を許容済み）。</p>"""),
 T("""<p>Low-medium: <code>containsPC</code>/GC-aware bookkeeping uses the routine's start address; <code>reconcileWeakReferencesAtGCEnd</code> paths must handle shared routines (they already do for stateless stubs).</p>""",
   """<p>低〜中: <code>containsPC</code> / GC 対応の管理はルーチンの開始アドレスを使う。<code>reconcileWeakReferencesAtGCEnd</code> 経路は共有ルーチンを扱える必要がある（stateless スタブでは既に対応済み）。</p>"""))

# 13
add(13, "Prototype-load handlers bypass SharedJITStubSet: per-site condition sets and watchpoints (≈ 370 + 136·N B per site)",
 "プロトタイプ読み出しハンドラは SharedJITStubSet を迂回: サイトごとの条件集合とウォッチポイント（≈ 370 + 136·N B/サイト）",
 "Metadata · inline caches", "メタデータ · インラインキャッシュ",
 "≈ 0.5-1 KB per monomorphic o.method() site → 1-3 MB on large apps", "モノモーフィックな o.method() サイトあたり ≈ 0.5-1 KB → 大規模アプリで 1-3 MB",
 "med", "medium", "中",
 T(f"""<p>For {c('Load')}/{c('GetGetter')}/{c('Miss')} with a non-empty watched condition set, {c('compileOneAccessCaseHandler')} builds a fresh routine and installs a fresh {c('StructureTransitionPropertyInlineCacheClearingWatchpoint')} per condition ({c('connectWatchpointSets')} → {c('addWatchpoint')}, InlineCacheCompiler.cpp:7185-7197, 4656-4667; 112 B per Bag node incl. the Variant with the 96 B adaptive variant) and returns before the {c('SharedJITStubSet::Searcher')} lookup at :7979 that would share an equal {c('AccessCase')} ({c('canBeShared')} compares {c('m_conditionSet')}, AccessCase.cpp:1643). Each site's AccessCase owns its own {c('ObjectPropertyConditionSet')} (8 + 24·N B, {c('generateConditionsForPrototypePropertyHit')}, ObjectPropertyConditionSet.cpp:404).</p>""",
   f"""<p>監視条件集合が空でない {c('Load')}/{c('GetGetter')}/{c('Miss')} では、{c('compileOneAccessCaseHandler')} が新しいルーチンを作り、条件ごとに新しい {c('StructureTransitionPropertyInlineCacheClearingWatchpoint')} を設置し（{c('connectWatchpointSets')} → {c('addWatchpoint')}、InlineCacheCompiler.cpp:7185-7197, 4656-4667; Bag ノードあたり 112 B、96 B の adaptive 版を含む Variant）、同一 {c('AccessCase')} を共有するはずの :7979 の {c('SharedJITStubSet::Searcher')} 探索より前に return する（{c('canBeShared')} は {c('m_conditionSet')} を比較、AccessCase.cpp:1643）。各サイトの AccessCase は自前の {c('ObjectPropertyConditionSet')}（8 + 24·N B、{c('generateConditionsForPrototypePropertyHit')}、ObjectPropertyConditionSet.cpp:404）を持つ。</p>"""),
 T("""<p>Per monomorphic prototype-method site with N conditions: handler 128 + AccessCase 48 + routine 96 + WatchpointSet 24 + N × 112 watchpoint nodes + 40 clearing watchpoint + condition set (8 + 24 N) ≈ 340 + 136·N B (sizeof harness values); N = 2 → ≈ 610 B, N = 4 → ≈ 880 B. DFG-side <code>GetById</code> sites in typescript: 1,002 (<code>DFG_fast_GetById</code>) + 499 megamorphic; Baseline get_by_id sites 14,417 — a few thousand of which are prototype hits.</p>""",
   """<p>N 条件のモノモーフィックなプロトタイプメソッドサイトあたり: ハンドラ 128 + AccessCase 48 + ルーチン 96 + WatchpointSet 24 + N × 112 ウォッチポイントノード + クリア用 40 + 条件集合（8 + 24 N）≈ 340 + 136·N B（sizeof ハーネス値）。N = 2 → ≈ 610 B、N = 4 → ≈ 880 B。typescript の DFG 側 <code>GetById</code> サイト: 1,002（<code>DFG_fast_GetById</code>）+ 499 megamorphic。Baseline の get_by_id サイトは 14,417 で、うち数千がプロトタイプヒット。</p>"""),
 T("""<p>Route pre-compiled-thunk handlers with conditions through the same <code>SharedJITStubSet::find(Searcher)</code> (key = IC key + <code>AccessCase::hash</code>) so equal shapes across sites share routine, watchpoints and condition set; optionally intern <code>ObjectPropertyConditionSet</code>s.</p>""",
   """<p>条件付きの事前コンパイル済みサンクハンドラも同じ <code>SharedJITStubSet::find(Searcher)</code>（キー = IC キー + <code>AccessCase::hash</code>）を通し、同一形状のサイト間でルーチン・ウォッチポイント・条件集合を共有する。必要なら <code>ObjectPropertyConditionSet</code> をインターン化する。</p>"""),
 T("""<p>Medium: owner tracking via <code>m_owners</code> and <code>isStillValid</code> invalidation semantics for shared routines; the bespoke path already does this.</p>""",
   """<p>中: 共有ルーチンに対する <code>m_owners</code> による所有者追跡と <code>isStillValid</code> の無効化セマンティクス。個別スタブ経路ではすでに実現されている。</p>"""))

# 14
add(14, "FTL OSRExitDescriptor::m_values: a dense 9-byte-per-operand copy of the whole frame for every exit (≈ 8× the FTL code size)",
 "FTL OSRExitDescriptor::m_values: exit ごとにフレーム全体を 9 B/オペランドで密にコピー（FTL コードサイズの ≈ 8 倍）",
 "Retained metadata · FTL", "保持メタデータ · FTL",
 f"typescript: {kb(ftl_exit_values_bytes)} payload (+ {kb(ftl_desc_bytes)} descriptors) vs {kb(ts_ftl)} FTL code; −70% possible", f"typescript: ペイロード {kb(ftl_exit_values_bytes)}（+ 記述子 {kb(ftl_desc_bytes)}）対 FTL コード {kb(ts_ftl)}。−70% が可能",
 "med", "medium", "中",
 T(f"""<p>{c('appendOSRExitDescriptor')} allocates {c('FixedOperands<ExitValue> m_values')} sized {c('numberOfArguments + numberOfLocals + numberOfTmps')} of the whole machine frame and fills every slot, dead operands included <span class="ref">(ftl/FTLLowerDFGToB3.cpp:27030-27034, 27174-27191)</span>; nothing shares or delta-encodes across descriptors, unlike the DFG's event-stream reconstruction. Descriptors are kept for the life of the code in {c('SegmentedVector<OSRExitDescriptor, 8> osrExitDescriptors')} <span class="ref">(ftl/FTLJITCode.h:89)</span>, and descriptors whose {c('CheckValue')} B3 later eliminates are never removed ({c('prepareOSRExitHandle')} only appends an {c('OSRExit')} for surviving checks, ftl/FTLOSRExit.cpp:93-94). {c('sizeof(ExitValue) = 9')}, {c('sizeof(OSRExitDescriptor) = 48')}.</p>""",
   f"""<p>{c('appendOSRExitDescriptor')} は機械フレーム全体の {c('numberOfArguments + numberOfLocals + numberOfTmps')} 個分の {c('FixedOperands<ExitValue> m_values')} を確保し、死んだオペランドも含め全スロットを埋める <span class="ref">(ftl/FTLLowerDFGToB3.cpp:27030-27034, 27174-27191)</span>。DFG のイベントストリーム再構成と異なり、記述子間で共有も差分符号化もされない。記述子はコードの寿命の間 {c('SegmentedVector<OSRExitDescriptor, 8> osrExitDescriptors')} <span class="ref">(ftl/FTLJITCode.h:89)</span> に保持され、B3 が後で {c('CheckValue')} を消した記述子も削除されない（{c('prepareOSRExitHandle')} は生き残ったチェックにだけ {c('OSRExit')} を追加、ftl/FTLOSRExit.cpp:93-94）。{c('sizeof(ExitValue) = 9')}、{c('sizeof(OSRExitDescriptor) = 48')}。</p>"""),
 T(f"""<p>Instrumented {c('Plan::finalizeInThread')} (patch in appendix), typescript: {ftlR['count']} FTL compiles, {n(ftlR['descriptors'])} descriptors, {n(ftlR['sumExitValues'])} ExitValues → <b>{kb(ftl_exit_values_bytes)}</b> of {c('m_values')} + {kb(ftl_desc_bytes)} of descriptor headers, versus {kb(ts_ftl)} of FTL machine code (LinkBuffer). acorn-wtb {kb(RET['acorn-wtb']['retained']['FTL']['sumExitValues']*9)}, Babylon {kb(RET['Babylon']['retained']['FTL']['sumExitValues']*9)}, gbemu {kb(RET['gbemu']['retained']['FTL']['sumExitValues']*9)}, pdfjs {kb(RET['pdfjs']['retained']['FTL']['sumExitValues']*9)}. Average operands per descriptor in typescript: {ftlR['sumExitValues']/ftlR['descriptors']:.0f}.</p>""",
   f"""<p>{c('Plan::finalizeInThread')} の計測（付録のパッチ）、typescript: FTL コンパイル {ftlR['count']} 回、記述子 {n(ftlR['descriptors'])}、ExitValue {n(ftlR['sumExitValues'])} → {c('m_values')} が <b>{kb(ftl_exit_values_bytes)}</b> + 記述子ヘッダ {kb(ftl_desc_bytes)}。対する FTL 機械語は {kb(ts_ftl)}（LinkBuffer）。acorn-wtb {kb(RET['acorn-wtb']['retained']['FTL']['sumExitValues']*9)}、Babylon {kb(RET['Babylon']['retained']['FTL']['sumExitValues']*9)}、gbemu {kb(RET['gbemu']['retained']['FTL']['sumExitValues']*9)}、pdfjs {kb(RET['pdfjs']['retained']['FTL']['sumExitValues']*9)}。typescript の記述子あたり平均オペランド数: {ftlR['sumExitValues']/ftlR['descriptors']:.0f}。</p>"""),
 T("""<p>(a) At <code>FTL::link</code>, compact <code>osrExitDescriptors</code> to those referenced by an <code>OSRExit</code>; (b) encode <code>m_values</code> sparsely (skip <code>Dead</code> runs, varint the common in-JS-stack/constant forms) or intern identical descriptors by hash; decode on the (rare) lazy exit compile. (c) Same for <code>OSRExit::m_valueReps</code>: 16 B <code>ValueRep</code> → 8 B packed for register/stack/constant kinds.</p>""",
   """<p>(a) <code>FTL::link</code> 時に <code>osrExitDescriptors</code> を <code>OSRExit</code> から参照されるものだけに圧縮。(b) <code>m_values</code> を疎に符号化（<code>Dead</code> の連続をスキップ、一般的な in-JS-stack/定数形式を varint 化）するか、同一記述子をハッシュでインターン化し、（稀な）遅延 exit コンパイル時に復号。(c) <code>OSRExit::m_valueReps</code> も同様: 16 B の <code>ValueRep</code> をレジスタ/スタック/定数種別向けに 8 B へパック。</p>"""),
 T("""<p>Medium: the exit compiler (<code>FTLOSRExitCompiler.cpp</code>) random-accesses <code>m_values</code>; a decode step into a stack buffer at exit-compile time is cheap. Descriptor compaction is low risk.</p>""",
   """<p>中: exit コンパイラ（<code>FTLOSRExitCompiler.cpp</code>）は <code>m_values</code> をランダムアクセスするが、exit コンパイル時にスタックバッファへ復号するのは安価。記述子の圧縮は低リスク。</p>"""))

# 15
add(15, "DFG VariableEventStream + MinifiedGraph retained uncompressed (≈ 1.7× the DFG code size)",
 "DFG の VariableEventStream + MinifiedGraph が非圧縮で保持される（DFG コードサイズの ≈ 1.7 倍）",
 "Retained metadata · DFG", "保持メタデータ · DFG",
 f"typescript: {kb(dfg_events_bytes)} events + {kb(dfg_min_bytes)} minified vs {kb(ts_dfg)} code; −50-70%", f"typescript: イベント {kb(dfg_events_bytes)} + minified {kb(dfg_min_bytes)} 対コード {kb(ts_dfg)}。−50-70%",
 "med", "medium", "中",
 T(f"""<p>{c('FixedVector<VariableEvent> m_stream')} (14 B/event, {c('dfg/DFGVariableEventStream.h:65')}, {c('DFGVariableEvent.h:255-268')}) records every MovHint/SetLocal/fill/spill/death during codegen ({c('DFGSpeculativeJIT.cpp:2068, 2115, 2136')}); {c('MinifiedGraph::m_list')} holds 13 B/node for constants and phantom arguments ({c('DFGMinifiedNode.h:39')}). Both live in {c('DFG::JITCode')} <span class="ref">(dfg/DFGJITCode.h:293-294)</span> for the life of the code so that {c('operationCompileOSRExit')} can reconstruct recoveries ({c('DFGOSRExit.cpp:174-175')}); reconstruction scans back only to the previous {c('Reset')} event ({c('DFGVariableEventStream.cpp:176-185')}), so the stream is naturally block-segmented.</p>""",
   f"""<p>{c('FixedVector<VariableEvent> m_stream')}（14 B/イベント、{c('dfg/DFGVariableEventStream.h:65')}、{c('DFGVariableEvent.h:255-268')}）はコード生成中の MovHint/SetLocal/fill/spill/death をすべて記録し（{c('DFGSpeculativeJIT.cpp:2068, 2115, 2136')}）、{c('MinifiedGraph::m_list')} は定数と phantom 引数を 13 B/ノードで保持する（{c('DFGMinifiedNode.h:39')}）。どちらも {c('operationCompileOSRExit')} が復元情報を再構成できるように（{c('DFGOSRExit.cpp:174-175')}）{c('DFG::JITCode')} <span class="ref">(dfg/DFGJITCode.h:293-294)</span> にコードの寿命の間置かれる。再構成は直前の {c('Reset')} イベントまでしか遡らない（{c('DFGVariableEventStream.cpp:176-185')}）ので、ストリームは自然にブロック単位に分割できる。</p>"""),
 T(f"""<p>Instrumented finalizer, typescript: {n(dfgR['events'])} events × 14 B = <b>{kb(dfg_events_bytes)}</b> + {n(dfgR['minified'])} minified nodes × 13 B = {kb(dfg_min_bytes)}, for {kb(ts_dfg)} of DFG machine code ({dfgR['count']} compiles). acorn-wtb {kb(RET['acorn-wtb']['retained']['DFG']['events']*14)}, gbemu {kb(RET['gbemu']['retained']['DFG']['events']*14)}, pdfjs {kb(RET['pdfjs']['retained']['DFG']['events']*14)}, Babylon {kb(RET['Babylon']['retained']['DFG']['events']*14)}. Ratio events/exit ≈ {dfgR['events']/dfgR['exits']:.1f}.</p>""",
   f"""<p>ファイナライザ計測、typescript: イベント {n(dfgR['events'])} × 14 B = <b>{kb(dfg_events_bytes)}</b> + minified ノード {n(dfgR['minified'])} × 13 B = {kb(dfg_min_bytes)}。対する DFG 機械語は {kb(ts_dfg)}（{dfgR['count']} コンパイル）。acorn-wtb {kb(RET['acorn-wtb']['retained']['DFG']['events']*14)}、gbemu {kb(RET['gbemu']['retained']['DFG']['events']*14)}、pdfjs {kb(RET['pdfjs']['retained']['DFG']['events']*14)}、Babylon {kb(RET['Babylon']['retained']['DFG']['events']*14)}。exit あたりイベント数 ≈ {dfgR['events']/dfgR['exits']:.1f}。</p>"""),
 T("""<p>Delta/varint-encode the stream per <code>Reset</code> segment (operands and register/stack numbers are small integers; kind+format fit a byte), drop segments belonging to blocks with no exits, and shrink <code>MinifiedNode</code> to a (id, packed constant/argument) pair; decode into a scratch vector at exit-compile time.</p>""",
   """<p>ストリームを <code>Reset</code> セグメント単位で差分/varint 符号化し（オペランドやレジスタ/スタック番号は小さな整数、kind+format は 1 B に収まる）、exit を持たないブロックのセグメントは捨て、<code>MinifiedNode</code> を（id, パック済み定数/引数）の対に縮める。exit コンパイル時にスクラッチベクタへ復号する。</p>"""),
 T("""<p>Medium: also used by <code>JITCode::reconstruct</code> for debugging/<code>$vm</code>; exit compile becomes slightly slower (it is already lazy and cached in <code>JITData::m_exits</code>).</p>""",
   """<p>中: デバッグ/<code>$vm</code> 用の <code>JITCode::reconstruct</code> も利用者。exit コンパイルがわずかに遅くなる（すでに遅延で <code>JITData::m_exits</code> にキャッシュされる）。</p>"""))

# 16
add(16, "Per-exit records: DFG::OSRExit 80 B + JITData::m_exits 16 B, FTL::OSRExit 80 B + ValueReps — split hot/cold, pack",
 "exit ごとのレコード: DFG::OSRExit 80 B + JITData::m_exits 16 B、FTL::OSRExit 80 B + ValueReps — hot/cold 分離とパック",
 "Retained metadata · DFG/FTL", "保持メタデータ · DFG/FTL",
 f"typescript: {kb(dfg_exit_bytes)} DFG + {kb(ftl_exit_bytes+ftl_reps_bytes)} FTL retained; ≈ −40%", f"typescript: DFG {kb(dfg_exit_bytes)} + FTL {kb(ftl_exit_bytes+ftl_reps_bytes)} を保持。≈ −40%",
 "low", "low", "低",
 T(f"""<p>{c('DFG::OSRExit')} = 80 B: base 40 ({c('m_count, m_kind, 2×CodeOrigin, 2×CallSiteIndex, m_dfgNodeIndex')}) + {c('m_patchableJumpLocation')} 8 + {c('m_jsValueSource')} 8 + {c('MethodOfGettingAValueProfile')} 16 + {c('m_recoveryIndex')}/{c('m_streamIndex')} <span class="ref">(dfg/DFGOSRExitBase.h:53-61, DFGOSRExit.h:119-128)</span>. Only {c('m_count/m_kind/origins/call-site indices/jump location')} are needed at run time; the rest is read once inside {c('operationCompileOSRExit')} (DFGOSRExit.cpp:168-217). {c('JITData::m_exits')} pre-populates a 16 B {c('MacroAssemblerCodeRef')} per exit with the shared thunk <span class="ref">(dfg/DFGPlan.cpp:740-745)</span>. {c('FTL::OSRExit')} = 80 B + {c('FixedVector<B3::ValueRep> m_valueReps')} at 16 B each (ftl/FTLOSRExit.cpp:86-89) although most reps are a kind + register/stack offset.</p>""",
   f"""<p>{c('DFG::OSRExit')} = 80 B: 基底 40（{c('m_count, m_kind, 2×CodeOrigin, 2×CallSiteIndex, m_dfgNodeIndex')}）+ {c('m_patchableJumpLocation')} 8 + {c('m_jsValueSource')} 8 + {c('MethodOfGettingAValueProfile')} 16 + {c('m_recoveryIndex')}/{c('m_streamIndex')} <span class="ref">(dfg/DFGOSRExitBase.h:53-61, DFGOSRExit.h:119-128)</span>。実行時に必要なのは {c('m_count/m_kind/origins/call-site indices/jump location')} だけで、残りは {c('operationCompileOSRExit')}（DFGOSRExit.cpp:168-217）内で一度読まれるだけ。{c('JITData::m_exits')} は exit ごとに 16 B の {c('MacroAssemblerCodeRef')} を共有サンクで事前に埋める <span class="ref">(dfg/DFGPlan.cpp:740-745)</span>。{c('FTL::OSRExit')} = 80 B + 各 16 B の {c('FixedVector<B3::ValueRep> m_valueReps')}（ftl/FTLOSRExit.cpp:86-89）で、大半の rep は種別 + レジスタ/スタックオフセットに過ぎない。</p>"""),
 T(f"""<p>typescript: DFG {n(dfgR['exits'])} exits × (80 + 16) B = <b>{kb(dfg_exit_bytes)}</b>; FTL {n(ftlR['exits'])} exits × 80 B = {kb(ftl_exit_bytes)} + {n(ftlR['sumValueReps'])} ValueReps × 16 B = {kb(ftl_reps_bytes)}. Only ~0.3% of exits ever compile ({c('osrExitCountForReoptimization=100')}), so a hot record of ≈ 40-48 B + cold side table + 8 B CodePtr in {c('m_exits')} saves ≈ 40 B/exit in DFG ({kb(dfgR['exits']*40)}) and ≈ 8 B/rep in FTL ({kb(ftlR['sumValueReps']*8)}).</p>""",
   f"""<p>typescript: DFG exit {n(dfgR['exits'])} × (80 + 16) B = <b>{kb(dfg_exit_bytes)}</b>。FTL exit {n(ftlR['exits'])} × 80 B = {kb(ftl_exit_bytes)} + ValueRep {n(ftlR['sumValueReps'])} × 16 B = {kb(ftl_reps_bytes)}。コンパイルされる exit は約 0.3%（{c('osrExitCountForReoptimization=100')}）に過ぎないので、≈ 40-48 B のホットレコード + コールド側表 + {c('m_exits')} の 8 B CodePtr にすれば DFG で exit あたり ≈ 40 B（{kb(dfgR['exits']*40)}）、FTL で rep あたり ≈ 8 B（{kb(ftlR['sumValueReps']*8)}）節約。</p>"""),
 T("""<p>Split <code>OSRExit</code> into a hot 40-48 B record and a cold <code>FixedVector</code> indexed by exit number; store only a <code>CodePtr</code> (8 B) in <code>m_exits</code> and keep compiled stub handles in a lazily allocated side <code>Bag</code>; pack <code>ValueRep</code> to 8 B for the register/stack/constant kinds.</p>""",
   """<p><code>OSRExit</code> を 40-48 B のホットレコードと exit 番号で引くコールドな <code>FixedVector</code> に分け、<code>m_exits</code> には <code>CodePtr</code>（8 B）だけを置き、コンパイル済みスタブのハンドルは遅延確保の <code>Bag</code> に保持。<code>ValueRep</code> はレジスタ/スタック/定数種別向けに 8 B へパックする。</p>"""),
 T("""<p>Low: mechanical; <code>exitCode(index)</code> is read from JIT code via <code>offsetOfExits</code>, so the representation must stay a simple array.</p>""",
   """<p>低: 機械的な変更。<code>exitCode(index)</code> は JIT コードから <code>offsetOfExits</code> 経由で読まれるので、表現は単純な配列のままにする必要がある。</p>"""))

# 17
add(17, "Freeze Bag<> side tables (InlineCallFrameSet, IC/CallLinkInfo bags) into FixedVectors and drop RecordedStatuses copies after link",
 "Bag<> の補助表（InlineCallFrameSet、IC/CallLinkInfo の Bag）を FixedVector に固定化し、リンク後は RecordedStatuses のコピーを捨てる",
 "Retained metadata · DFG/FTL", "保持メタデータ · DFG/FTL",
 "≈ 8-16 B + 1 malloc per element; ≈ 0.3-0.6 MB on typescript", "要素あたり ≈ 8-16 B + malloc 1 回。typescript で ≈ 0.3-0.6 MB",
 "low", "low", "低",
 T(f"""<p>{c('WTF::Bag')} is a singly linked list of individually malloc'd nodes ({c('wtf/Bag.h:54-65')}). {c('DFG::CommonData')} keeps {c('Bag<HandlerPropertyInlineCache>')}, {c('Bag<RepatchingPropertyInlineCache>')}, {c('Bag<OptimizingCallLinkInfo>')}, {c('Bag<DirectCallLinkInfo>')} <span class="ref">(dfg/DFGCommonData.h:136-139, with the FIXME "These seem like they should be FixedVectors")</span>, {c('InlineCallFrameSet')} is a {c('Bag<InlineCallFrame>')} (bytecode/InlineCallFrameSet.h:44,50), and {c('RecordedStatuses')} holds heap copies of every {c('GetByStatus')}/{c('PutByStatus')}/{c('CallLinkStatus')} used during parsing (~88 B + variants each, RecordedStatuses.cpp:39-45) solely for GC marking. {c('DFG::JITCode')} also carries three {c('HashMap')}s for tier-up bookkeeping (DFGJITCode.h:376-392) that are empty for loop-free functions.</p>""",
   f"""<p>{c('WTF::Bag')} は個別に malloc されたノードの単方向リスト（{c('wtf/Bag.h:54-65')}）。{c('DFG::CommonData')} は {c('Bag<HandlerPropertyInlineCache>')}、{c('Bag<RepatchingPropertyInlineCache>')}、{c('Bag<OptimizingCallLinkInfo>')}、{c('Bag<DirectCallLinkInfo>')} <span class="ref">(dfg/DFGCommonData.h:136-139、FIXME「These seem like they should be FixedVectors」付き)</span> を持ち、{c('InlineCallFrameSet')} は {c('Bag<InlineCallFrame>')}（bytecode/InlineCallFrameSet.h:44,50）、{c('RecordedStatuses')} は解析中に使った全 {c('GetByStatus')}/{c('PutByStatus')}/{c('CallLinkStatus')} のヒープコピー（各 ~88 B + variant、RecordedStatuses.cpp:39-45）を GC マーキングのためだけに保持する。{c('DFG::JITCode')} はさらに tier-up 管理用の {c('HashMap')} を 3 つ持つ（DFGJITCode.h:376-392）が、ループのない関数では空。</p>"""),
 T(f"""<p>typescript finalizer counts: InlineCallFrames {n(dfgR['inlineCallFrames']+ftlR['inlineCallFrames'])} (56 B + 8 B node + malloc header each ≈ {kb((dfgR['inlineCallFrames']+ftlR['inlineCallFrames'])*72)}), DirectCallLinkInfo {n(dfgR['directCallBag']+ftlR['directCallBag'])} (104 B + node), OptimizingCallLinkInfo {n(dfgR['callLinkBag']+ftlR['callLinkBag'])}, RepatchingPropertyInlineCache {n(ftlR['repatchPICBag'])} (144 B + node), CodeOrigins {n(dfgR['codeOrigins']+ftlR['codeOrigins'])} × 8 B. sizeof: {c('DFG::JITCode')} 416, {c('CommonData')} 248, {c('FTL::JITCode')} 392 per compile.</p>""",
   f"""<p>typescript のファイナライザ計数: InlineCallFrame {n(dfgR['inlineCallFrames']+ftlR['inlineCallFrames'])}（56 B + 8 B ノード + malloc ヘッダで各 ≈ 72 B、計 ≈ {kb((dfgR['inlineCallFrames']+ftlR['inlineCallFrames'])*72)}）、DirectCallLinkInfo {n(dfgR['directCallBag']+ftlR['directCallBag'])}（104 B + ノード）、OptimizingCallLinkInfo {n(dfgR['callLinkBag']+ftlR['callLinkBag'])}、RepatchingPropertyInlineCache {n(ftlR['repatchPICBag'])}（144 B + ノード）、CodeOrigin {n(dfgR['codeOrigins']+ftlR['codeOrigins'])} × 8 B。sizeof: {c('DFG::JITCode')} 416、{c('CommonData')} 248、{c('FTL::JITCode')} 392（コンパイルごと）。</p>"""),
 T("""<p>At <code>finalizeInThread</code>, move Bag contents into <code>FixedVector</code>s (addresses only need stability during link) and replace <code>RecordedStatuses</code> by the compact set of cells/structures it keeps alive (<code>StructureSet</code>s, condition-set cells, callee cells); allocate the tier-up maps lazily.</p>""",
   """<p><code>finalizeInThread</code> で Bag の内容を <code>FixedVector</code> に移し（アドレスの安定性はリンク中だけ必要）、<code>RecordedStatuses</code> は生かしておくべきセル/structure のコンパクトな集合（<code>StructureSet</code>、条件集合のセル、callee セル）に置き換える。tier-up 用マップは遅延確保にする。</p>"""),
 T("""<p>Low: retained sets are frozen after link; <code>RecordedStatuses</code> replacement must keep exactly the same GC roots.</p>""",
   """<p>低: 保持集合はリンク後に固定される。<code>RecordedStatuses</code> の置き換えでは GC ルートを厳密に同一に保つ必要がある。</p>"""))

# 18
add(18, "Linked ValueProfile: keep the 8 B bucket, move the merged 8 B prediction to the shared UnlinkedValueProfile",
 "リンク済み ValueProfile: 8 B のバケットだけ残し、統合された 8 B の予測は共有 UnlinkedValueProfile 側に置く",
 "Metadata · profiling", "メタデータ · プロファイリング",
 "−8 B × value profiles (typescript ≈ 30K → ≈ 240 KB) per linked table", "value profile あたり −8 B（typescript ≈ 30K → リンク済み表あたり ≈ 240 KB）",
 "high", "high (concurrency semantics)", "高（並行性のセマンティクス）",
 T(f"""<p>{c('ValueProfile')} = 16 B ({c('EncodedJSValue m_buckets[1]')} + {c('SpeculatedType m_prediction')}, bytecode/ValueProfile.h:44-146) is stored per linked {c('MetadataTable')} in the negative-indexed prefix ({c('MetadataTable.h:74-84')}); {c('UnlinkedValueProfile')} (8 B, ValueProfile.h:225-247) already aggregates the prediction across realms and {c('CodeBlock::updateAllNonLazyValueProfilePredictionsAndCountLiveness')} sets the linked prediction to {c('unlinked | local')} (CodeBlock.cpp:3020-3041). {c('ArgumentValueProfile')} is 24 B. The METADATA_STATISTICS "total memory" excludes value profiles, so they sit on top of the numbers in the metadata table.</p>""",
   f"""<p>{c('ValueProfile')} = 16 B（{c('EncodedJSValue m_buckets[1]')} + {c('SpeculatedType m_prediction')}、bytecode/ValueProfile.h:44-146）はリンク済み {c('MetadataTable')} ごとに負インデックスの前置領域に置かれる（{c('MetadataTable.h:74-84')}）。{c('UnlinkedValueProfile')}（8 B、ValueProfile.h:225-247）はすでに realm 横断で予測を集約し、{c('CodeBlock::updateAllNonLazyValueProfilePredictionsAndCountLiveness')} はリンク済み予測を {c('unlinked | local')} に設定する（CodeBlock.cpp:3020-3041）。{c('ArgumentValueProfile')} は 24 B。METADATA_STATISTICS の「total memory」は value profile を含まないので、これらは表の数値の上乗せになる。</p>"""),
 T("""<p><code>--dumpGeneratedBytecodes</code> on typescript: 29,862 <code>valueProfile:</code> operands across 1,104 code blocks (+ one ArgumentValueProfile per parameter) → ≈ 478 KB of linked ValueProfiles for 1.36 MB of other metadata (+35%). Halving them saves ≈ 240 KB per realm; the metadata table copies per extra realm (113 KB in typescript) shrink proportionally.</p>""",
   """<p>typescript で <code>--dumpGeneratedBytecodes</code>: 1,104 コードブロックに 29,862 個の <code>valueProfile:</code> オペランド（+ 引数ごとの ArgumentValueProfile）→ 他のメタデータ 1.36 MB に対しリンク済み ValueProfile ≈ 478 KB（+35%）。半減で realm あたり ≈ 240 KB 節約。realm 追加ごとのメタデータ表コピー（typescript で 113 KB）も比例して縮む。</p>"""),
 T("""<p>Make the linked profile the 8 B bucket only and read/merge predictions from the <code>UnlinkedValueProfile</code> array (already sized <code>numParameters + numValueProfiles</code>, UnlinkedCodeBlock.cpp:324-348); builtins (which never update unlinked profiles) keep a per-CodeBlock prediction side array.</p>""",
   """<p>リンク済みプロファイルを 8 B のバケットだけにし、予測は <code>UnlinkedValueProfile</code> 配列（すでに <code>numParameters + numValueProfiles</code> 分確保、UnlinkedCodeBlock.cpp:324-348）から読んで統合する。unlinked プロファイルを更新しない builtin は CodeBlock ごとの予測補助配列を持つ。</p>"""),
 T("""<p>High: changes what concurrent DFG compilations of different realms observe, and touches LLInt/Baseline profile stores (<code>valueProfile</code> macro, LowLevelInterpreter64.asm:77-81) and <code>MinimalValueProfile</code>/lazy variants. Flagged as a direction, not a quick win.</p>""",
   """<p>高: 異なる realm の並行 DFG コンパイルが観測する内容が変わり、LLInt/Baseline のプロファイル格納（<code>valueProfile</code> マクロ、LowLevelInterpreter64.asm:77-81）や <code>MinimalValueProfile</code>/lazy 版にも触れる。即効性のある案ではなく方向性として提示。</p>"""))

# 19
add(19, "BaselineJITCode::JITCodeMap: 12 B per bytecode instruction (≈ 14% of the machine code size) — pack to 8 B or make sparse",
 "BaselineJITCode::JITCodeMap: バイトコード命令あたり 12 B（機械語サイズの ≈ 14%）— 8 B にパックするか疎にする",
 "Metadata · Baseline", "メタデータ · Baseline",
 f"typescript: ≈ {kb(240488/5.9*12)} → −33% (offsets) or −80% (sparse)", f"typescript: ≈ {kb(240488/5.9*12)} → −33%（オフセット化）/ −80%（疎化）",
 "low", "low", "低",
 T(f"""<p>{c('JIT::link')} appends one entry per set label ({c('jit/JIT.cpp:944-948')}) and every bytecode instruction sets one ({c('m_labels[m_bytecodeIndex.offset()] = label()')}, JIT.cpp:196); {c('JITCodeMap')} stores a {c('CodeLocationLabel')} (8 B) + {c('BytecodeIndex')} (4 B) per entry <span class="ref">(jit/JITCodeMap.h:44-82)</span>. Consumers are rare paths only: exception-handler linking (CodeBlock.cpp:794-799), LLInt→Baseline OSR entry (LLIntSlowPaths.cpp:506, 2667, 2689) and DFG OSR exit (DFGOSRExitCompilerCommon.cpp:494).</p>""",
   f"""<p>{c('JIT::link')} は設定されたラベルごとに 1 エントリを追加し（{c('jit/JIT.cpp:944-948')}）、全バイトコード命令がラベルを設定する（{c('m_labels[m_bytecodeIndex.offset()] = label()')}、JIT.cpp:196）。{c('JITCodeMap')} はエントリごとに {c('CodeLocationLabel')}（8 B）+ {c('BytecodeIndex')}（4 B）を持つ <span class="ref">(jit/JITCodeMap.h:44-82)</span>。利用者は稀な経路のみ: 例外ハンドラのリンク（CodeBlock.cpp:794-799）、LLInt→Baseline の OSR entry（LLIntSlowPaths.cpp:506, 2667, 2689）、DFG OSR exit（DFGOSRExitCompilerCommon.cpp:494）。</p>"""),
 T("""<p>typescript: Baseline compiled 240,488 bytecode bytes into 3,430,048 B of machine code (<code>--reportBaselineCompileTimes</code>; 14.3 B/bytecode byte); average instruction length from <code>--dumpGeneratedBytecodes</code> is 5.9 B → ≈ 40,700 instructions → JITCodeMap ≈ 489 KB of malloc per BaselineJITCode set (≈ 14% of the code size, kept alive with the shared code, see #2).</p>""",
   """<p>typescript: Baseline はバイトコード 240,488 B を機械語 3,430,048 B にコンパイル（<code>--reportBaselineCompileTimes</code>; 14.3 B/バイトコードバイト）。<code>--dumpGeneratedBytecodes</code> による平均命令長は 5.9 B → ≈ 40,700 命令 → JITCodeMap ≈ 489 KB の malloc（コードサイズの ≈ 14%。共有コードと共に生存、#2 参照）。</p>"""),
 T("""<p>Store 4-byte code offsets relative to the code start (code &lt; 4 GB is already assumed) + 4-byte bytecode offsets, or delta/varint both and keep only entries needed by consumers (loop hints, catch, exception targets, and exit origins) with lazy expansion for OSR exit.</p>""",
   """<p>コード先頭からの 4 B オフセット（コード &lt; 4 GB は既に前提）+ 4 B のバイトコードオフセットで持つか、両方を差分/varint 化し、利用者が必要とするエントリ（loop hint、catch、例外ターゲット、exit 起点）だけを保持して OSR exit 時に遅延展開する。</p>"""),
 T("""<p>Low: a pure data-structure change; binary search remains.</p>""",
   """<p>低: 純粋なデータ構造変更。二分探索は維持。</p>"""))

# 20
wp_ts = dfgR['watchpoints']+ftlR['watchpoints']; as_ts=dfgR['adaptiveStructWP']+ftlR['adaptiveStructWP']; ai_ts=dfgR['adaptiveInferredWP']+ftlR['adaptiveInferredWP']
add(20, "GC-side JIT metadata: devirtualise AdaptiveInferredPropertyValueWatchpoint (88 → ≈ 72 B) and drop the per-watchpoint owner (24 → 16 B)",
 "GC 側の JIT メタデータ: AdaptiveInferredPropertyValueWatchpoint の非仮想化（88 → ≈ 72 B）とウォッチポイントごとの owner 削除（24 → 16 B）",
 "GC-side metadata · watchpoints", "GC 側メタデータ · ウォッチポイント",
 f"typescript: {kb(wp_ts*24+as_ts*48+ai_ts*88)} of DFG/FTL watchpoints → −{kb(wp_ts*8+ai_ts*16)} (≈ 18%)", f"typescript: DFG/FTL ウォッチポイント {kb(wp_ts*24+as_ts*48+ai_ts*88)} → −{kb(wp_ts*8+ai_ts*16)}（≈ 18%）",
 "low", "low-medium", "低〜中",
 T(f"""<p>Per optimized CodeBlock, {c('DFG::CommonData')} materialises {c('FixedVector<CodeBlockJettisoningWatchpoint>')} (24 B: Watchpoint 17 + {c('PackedCellPtr<CodeBlock> m_owner')}), {c('FixedVector<AdaptiveStructureWatchpoint>')} (48 B) and {c('FixedVector<AdaptiveInferredPropertyValueWatchpoint>')} (88 B) <span class="ref">(dfg/DFGCommonData.h:127-129, DFGDesiredWatchpoints.cpp:166-168)</span>. {c('AdaptiveInferredPropertyValueWatchpointBase')} is virtual ({c('virtual ~, isValid, handleFire')}, bytecode/AdaptiveInferredPropertyValueWatchpointBase.h:43-56) and its DFG subclass keeps a full {c('CodeBlock* m_codeBlock')} (dfg/DFGAdaptiveInferredPropertyValueWatchpoint.h:50) while {c('AdaptiveStructureWatchpoint')} uses a 6 B {c('PackedCellPtr')}; {c('Watchpoint')} itself is already vtable-free ({c('Type')} tag + {c('runWithDowncast')}, Watchpoint.h:86-149). Every jettisoning watchpoint of one CodeBlock stores the same owner.</p>""",
   f"""<p>最適化 CodeBlock ごとに {c('DFG::CommonData')} は {c('FixedVector<CodeBlockJettisoningWatchpoint>')}（24 B: Watchpoint 17 + {c('PackedCellPtr<CodeBlock> m_owner')}）、{c('FixedVector<AdaptiveStructureWatchpoint>')}（48 B）、{c('FixedVector<AdaptiveInferredPropertyValueWatchpoint>')}（88 B）を実体化する <span class="ref">(dfg/DFGCommonData.h:127-129, DFGDesiredWatchpoints.cpp:166-168)</span>。{c('AdaptiveInferredPropertyValueWatchpointBase')} は仮想（{c('virtual ~, isValid, handleFire')}、bytecode/AdaptiveInferredPropertyValueWatchpointBase.h:43-56）で、DFG サブクラスはフルの {c('CodeBlock* m_codeBlock')}（dfg/DFGAdaptiveInferredPropertyValueWatchpoint.h:50）を持つ一方、{c('AdaptiveStructureWatchpoint')} は 6 B の {c('PackedCellPtr')} を使う。{c('Watchpoint')} 自体は既に vtable なし（{c('Type')} タグ + {c('runWithDowncast')}、Watchpoint.h:86-149）。1 つの CodeBlock の jettisoning ウォッチポイントはすべて同じ owner を格納している。</p>"""),
 T(f"""<p>Instrumented finalizer, typescript (DFG+FTL): {n(wp_ts)} CodeBlockJettisoningWatchpoints ({kb(wp_ts*24)}), {n(as_ts)} AdaptiveStructureWatchpoints ({kb(as_ts*48)}), {n(ai_ts)} AdaptiveInferredPropertyValueWatchpoints ({kb(ai_ts*88)}) = {kb(wp_ts*24+as_ts*48+ai_ts*88)}; acorn-wtb {kb((RET['acorn-wtb']['retained']['DFG']['watchpoints']+RET['acorn-wtb']['retained']['FTL']['watchpoints'])*24 + (RET['acorn-wtb']['retained']['DFG']['adaptiveStructWP']+RET['acorn-wtb']['retained']['FTL']['adaptiveStructWP'])*48 + (RET['acorn-wtb']['retained']['DFG']['adaptiveInferredWP']+RET['acorn-wtb']['retained']['FTL']['adaptiveInferredWP'])*88)}. Each watched Structure also inflates its thin {c('m_transitionWatchpointSet')} into a 24 B {c('WatchpointSet')} (Watchpoint.cpp:209-217).</p>""",
   f"""<p>ファイナライザ計測、typescript（DFG+FTL）: CodeBlockJettisoningWatchpoint {n(wp_ts)}（{kb(wp_ts*24)}）、AdaptiveStructureWatchpoint {n(as_ts)}（{kb(as_ts*48)}）、AdaptiveInferredPropertyValueWatchpoint {n(ai_ts)}（{kb(ai_ts*88)}）= {kb(wp_ts*24+as_ts*48+ai_ts*88)}。acorn-wtb {kb((RET['acorn-wtb']['retained']['DFG']['watchpoints']+RET['acorn-wtb']['retained']['FTL']['watchpoints'])*24 + (RET['acorn-wtb']['retained']['DFG']['adaptiveStructWP']+RET['acorn-wtb']['retained']['FTL']['adaptiveStructWP'])*48 + (RET['acorn-wtb']['retained']['DFG']['adaptiveInferredWP']+RET['acorn-wtb']['retained']['FTL']['adaptiveInferredWP'])*88)}。監視される各 Structure は薄い {c('m_transitionWatchpointSet')} を 24 B の {c('WatchpointSet')} に膨らませる（Watchpoint.cpp:209-217）。</p>"""),
 T("""<p>Replace the virtual base with the <code>Watchpoint::Type</code> tag pattern (only two subclasses exist), use <code>PackedCellPtr</code> for the CodeBlock, and recover the owner of a <code>CodeBlockJettisoningWatchpoint</code> from its <code>FixedVector</code> (a small header before the array, or a per-CommonData back-pointer) instead of storing it in every element.</p>""",
   """<p>仮想基底を <code>Watchpoint::Type</code> タグ方式に置き換え（サブクラスは 2 つのみ）、CodeBlock には <code>PackedCellPtr</code> を使い、<code>CodeBlockJettisoningWatchpoint</code> の owner は各要素に格納する代わりに所属 <code>FixedVector</code>（配列前の小さなヘッダ、または CommonData への逆ポインタ）から復元する。</p>"""),
 T("""<p>Low for devirtualisation/packing (TZone bucket changes); medium for the owner recovery (<code>fireInternal</code> must find the CodeBlock from the element address).</p>""",
   """<p>非仮想化/パックは低（TZone バケットが変わる）。owner 復元は中（<code>fireInternal</code> が要素アドレスから CodeBlock を見つける必要がある）。</p>"""))

# ---------- summary table of the 20 ----------
SUMMARY = [
 (1, 'Size-scale / cap LLInt→Baseline threshold', 'LLInt→Baseline 閾値のサイズ補正/上限', 'code', 'Air −5.7 MB (−88%); others −3…−27%', 'Air −5.7 MB（−88%）、他 −3…−27%', 'med'),
 (2, 'Release cache-only unlinked Baseline code', 'キャッシュ専用 unlinked Baseline コードの解放', 'code', 'up to all Baseline bytes of dead functions', '死んだ関数の Baseline 全バイトまで', 'low'),
 (3, 'Compact inline data-IC / truthiness sequences', 'インライン data-IC / truthiness 列の短縮', 'code', '≈ 37% of Baseline (typescript)', 'Baseline の ≈ 37%（typescript）', 'med'),
 (4, 'Shared prologue / arity trailer', 'プロローグ / arity trailer の共有', 'code', '≈ 200 B × function (3.5%)', '≈ 200 B × 関数（3.5%）', 'med'),
 (5, 'OSR-exit stubs → table dispatch', 'OSR exit スタブ → テーブルディスパッチ', 'code', '≈ 14% of DFG/FTL code', 'DFG/FTL コードの ≈ 14%', 'med'),
 (6, 'Thunk-ify barrier / math slow paths', 'バリア・算術スローパスのサンク化', 'code', '≈ 7% of DFG code + Baseline', 'DFG コードの ≈ 7% + Baseline', 'low'),
 (7, '16 B granule, compaction-before-alloc', '16 B グラニュール、割り当て前圧縮', 'code', '3-9% of JIT RSS', 'JIT RSS の 3-9%', 'low'),
 (8, 'Slim DataOnlyCallLinkInfo (80→64)', 'DataOnlyCallLinkInfo のスリム化（80→64）', 'meta', '≈ 30-40% of call metadata ×0.2', '呼び出しメタデータ（全体の 30-40%）の 20%', 'med'),
 (9, 'HandlerPropertyInlineCache 112→88', 'HandlerPropertyInlineCache 112→88', 'meta', '≈ 24 B × IC site', '≈ 24 B × IC サイト', 'low'),
 (10, 'm_bufferedStructures out-of-line', 'm_bufferedStructures の外出し', 'meta', '−16 B × IC site', '−16 B × IC サイト', 'low'),
 (11, 'InlineCacheHandler padding / embedded watchpoint', 'InlineCacheHandler のパディング / 埋め込みウォッチポイント', 'meta', '−32…−80 B × handler', '−32…−80 B × ハンドラ', 'low'),
 (12, 'Share routines for pre-compiled handlers', '事前コンパイル済みハンドラのルーチン共有', 'meta', '−120 B × handler', '−120 B × ハンドラ', 'low'),
 (13, 'Share prototype-load handlers + condition sets', 'プロトタイプ読み出しハンドラ・条件集合の共有', 'meta', '≈ 0.5-1 KB × site', '≈ 0.5-1 KB × サイト', 'med'),
 (14, 'FTL exit descriptors: sparse/interned values', 'FTL exit 記述子: 疎化/インターン', 'retained', '≈ 8× FTL code today; −70%', '現状 FTL コードの ≈ 8 倍。−70%', 'med'),
 (15, 'Compress DFG event stream / minified graph', 'DFG イベントストリーム / minified graph の圧縮', 'retained', '≈ 1.7× DFG code today; −50-70%', '現状 DFG コードの ≈ 1.7 倍。−50-70%', 'med'),
 (16, 'Hot/cold split of OSRExit records, packed reps', 'OSRExit レコードの hot/cold 分離、rep のパック', 'retained', '≈ −40% of exit records', 'exit レコードの ≈ −40%', 'low'),
 (17, 'Bag<> → FixedVector, drop RecordedStatuses', 'Bag<> → FixedVector、RecordedStatuses 廃止', 'retained', '≈ 0.3-0.6 MB (typescript)', '≈ 0.3-0.6 MB（typescript）', 'low'),
 (18, '8 B linked ValueProfile', '8 B のリンク済み ValueProfile', 'meta', '−8 B × value profile', '−8 B × value profile', 'high'),
 (19, 'Pack / sparsify JITCodeMap', 'JITCodeMap のパック / 疎化', 'meta', '−33…−80% of ≈ 14% of code size', 'コードサイズの ≈ 14% のうち −33…−80%', 'low'),
 (20, 'Devirtualise / de-owner DFG watchpoints', 'DFG ウォッチポイントの非仮想化 / owner 削除', 'gc', '≈ 18% of watchpoint bytes', 'ウォッチポイントバイトの ≈ 18%', 'low'),
]
def summary_table():
    out=['<div class="tablewrap"><table><thead><tr><th>#</th><th class="txt">'+t('Opportunity','施策')+'</th><th>'+t('Area','領域')+'</th><th class="txt">'+t('Estimated saving','推定削減量')+'</th><th>'+t('Risk','リスク')+'</th></tr></thead><tbody>']
    areas={'code':t('executable code','実行コード'),'meta':t('metadata','メタデータ'),'retained':t('retained DFG/FTL data','DFG/FTL 保持データ'),'gc':t('GC-side','GC 側')}
    risks={'low':('risk-low',t('low','低')),'med':('risk-med',t('medium','中')),'high':('risk-high',t('high','高'))}
    for i,en,ja,area,save,save_ja,risk in SUMMARY:
        rc,rl=risks[risk]
        out.append(f'<tr><td><a href="#opp{i}">{i}</a></td><td class="txt">{t(en,ja)}</td><td>{areas[area]}</td><td class="txt">{t(esc(save), esc(save_ja))}</td><td><span class="pill {rc}">{rl}</span></td></tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)

# ---------- page ----------
def section(id_, title_en, title_ja, body):
    return f'<section id="{id_}"><h2>{t(title_en,title_ja)}</h2>{body}</section>'

toc_items = [
 ("summary","Executive summary","要旨"),
 ("method","Method & measurement setup","方法と計測環境"),
 ("arch","Deep dive: how the JIT tiers own memory","深掘り: JIT ティアとメモリ所有関係"),
 ("objmodel","Object model & GC facts the JIT depends on","JIT が依拠するオブジェクトモデルと GC"),
 ("data","Measured data","計測データ"),
 ("opps","The 20 opportunities","20 の削減施策"),
 ("prio","Prioritisation","優先度"),
 ("appendix","Appendix: reproduction & instrumentation","付録: 再現手順と計測パッチ"),
]
toc = '<nav class="toc">'+''.join(f'<a href="#{i}"><span class="num">{k+1}.</span>{t(en,ja)}</a>' for k,(i,en,ja) in enumerate(toc_items))+'</nav>'

kpis = f'''
<div class="kpis">
 <div class="kpi"><div class="v">20</div><div class="l">{t("evidence-backed reductions, each with a measurement","根拠と計測を伴う削減施策")}</div></div>
 <div class="kpi"><div class="v">{kb(ftl_exit_values_bytes+ftl_desc_bytes+ftl_reps_bytes+ftl_exit_bytes)}</div><div class="l">{t(f"FTL OSR-exit metadata retained for {kb(ts_ftl)} of FTL code (typescript)",f"FTL コード {kb(ts_ftl)} に対して保持される FTL OSR exit メタデータ（typescript）")}</div></div>
 <div class="kpi"><div class="v">{100*gbi[0]/ts_base:.0f}%</div><div class="l">{t("of Baseline machine code is get_by_id inline fast paths (typescript)","Baseline 機械語のうち get_by_id インライン高速パスの割合（typescript）")}</div></div>
 <div class="kpi"><div class="v">5.7 MB</div><div class="l">{t("Baseline code from 4 straight-line payload functions in Air (of 6.5 MB)","Air の直線的なペイロード関数 4 つが生む Baseline コード（6.5 MB 中）")}</div></div>
 <div class="kpi"><div class="v">{100*ac_call_bytes/ac_meta['total']:.0f}%</div><div class="l">{t("of linked bytecode metadata is call-site DataOnlyCallLinkInfo (acorn-wtb)","リンク済みバイトコードメタデータのうち呼び出しサイトの DataOnlyCallLinkInfo（acorn-wtb）")}</div></div>
 <div class="kpi"><div class="v">{kb(dfg_events_bytes)}</div><div class="l">{t(f"DFG variable-event stream kept for {kb(ts_dfg)} of DFG code (typescript)",f"DFG コード {kb(ts_dfg)} に対して保持される DFG 変数イベントストリーム（typescript）")}</div></div>
</div>'''

summary_body = kpis + T(
f"""<p>This report is a source-level deep dive into JavaScriptCore's JIT tiers (LLInt → Baseline → DFG → FTL), inline caches, garbage collector and object model, focused on one question: <b>where does memory attributable to JIT compilation — machine code and its metadata — go, and how could it be reduced?</b> The tree is WebKit {c('7375405d8e')} (2026-08-16), built as JSCOnly Release on x86_64 Linux (clang 18, libpas JIT heap). Every number below was either measured on that build (a {c('sizeof')}/record-layout harness compiled against the real headers, {c('jsc')} shell runs of JetStream2 sub-tests with {c('$vm.linkBufferStats()')}, JIT-pool RSS from {c('/proc/pid/smaps')}, {c('--dumpBaselineJITSizeStatistics')}/{c('--dumpDFGJITSizeStatistics')}, an {c('ENABLE(METADATA_STATISTICS)')} build, and a small temporary finalizer probe for retained DFG/FTL data) or is a static estimate derived from those measurements, and it is labelled as such.</p>
<p>The headline findings: (1) retained <b>OSR-exit metadata</b> dwarfs optimized machine code — for JetStream2 typescript the FTL keeps {kb(ftl_exit_values_bytes)} of exit-value payload for {kb(ts_ftl)} of FTL code and the DFG keeps a {kb(dfg_events_bytes)} event stream for {kb(ts_dfg)} of DFG code; (2) <b>Baseline code volume</b> is dominated by generic inline IC sequences (get_by_id ≈ 93 B/site, {100*gbi[0]/ts_base:.0f}% of the tier) and by giant straight-line functions that the size-blind LLInt threshold compiles anyway (Air: 5.7 MB of 6.5 MB), and it is pinned by the unlinked-baseline cache after CodeBlocks die; (3) <b>bytecode metadata</b> is dominated by the 80-byte {c('DataOnlyCallLinkInfo')} embedded in every call site (30-40% of metadata bytes) and by IC objects that carry derivable or padding bytes ({c('HandlerPropertyInlineCache')} 112 B, {c('InlineCacheHandler')} 128 B with 32 B padding, a 96 B stub routine + 24 B watchpoint set per handler).</p>
<p>The 20 opportunities are ranked by (estimated saving ÷ risk); items 1-7 target executable memory, 8-13 and 18-19 metadata, 14-17 retained DFG/FTL data, 20 GC-side watchpoints. Existing savings mechanisms (unlinked Baseline sharing, handler ICs with ~99 shared thunks, 16-bit metadata offset tables, lazy OSR-exit compilation, {c('shrinkToFit')} passes, old-age jettison, thin {c('InlineWatchpointSet')}s, 32-bit {c('StructureID')}s…) are catalogued in the deep-dive so that none of the proposals duplicates them.</p>""",
f"""<p>本レポートは JavaScriptCore の JIT ティア（LLInt → Baseline → DFG → FTL）、インラインキャッシュ、GC、オブジェクトモデルをソースレベルで深掘りし、「<b>JIT コンパイルに起因するメモリ — 機械語とそのメタデータ — はどこに消費され、どう減らせるか</b>」という一点に焦点を当てたものである。対象ツリーは WebKit {c('7375405d8e')}（2026-08-16）、x86_64 Linux 上の JSCOnly Release ビルド（clang 18、libpas JIT ヒープ）。以下の数値はすべて、そのビルド上での実測（実ヘッダに対してコンパイルした {c('sizeof')}/レコードレイアウトハーネス、JetStream2 サブテストを {c('jsc')} シェルで走らせて得た {c('$vm.linkBufferStats()')}、{c('/proc/pid/smaps')} による JIT プール RSS、{c('--dumpBaselineJITSizeStatistics')}/{c('--dumpDFGJITSizeStatistics')}、{c('ENABLE(METADATA_STATISTICS)')} ビルド、DFG/FTL の保持データを数える一時的なファイナライザプローブ）か、それらから導いた静的推定であり、その旨を明記している。</p>
<p>主要な発見: (1) 保持される <b>OSR exit メタデータ</b>が最適化コードを圧倒する — JetStream2 typescript では FTL コード {kb(ts_ftl)} に対して exit 値ペイロード {kb(ftl_exit_values_bytes)}、DFG コード {kb(ts_dfg)} に対してイベントストリーム {kb(dfg_events_bytes)} が保持される。(2) <b>Baseline コード量</b>は汎用のインライン IC 列（get_by_id ≈ 93 B/サイト、ティア全体の {100*gbi[0]/ts_base:.0f}%）と、サイズを見ない LLInt 閾値がそのままコンパイルしてしまう巨大な直線関数（Air: 6.5 MB 中 5.7 MB）に支配され、CodeBlock の死後も unlinked-baseline キャッシュにピン留めされる。(3) <b>バイトコードメタデータ</b>は全呼び出しサイトに埋め込まれる 80 B の {c('DataOnlyCallLinkInfo')}（メタデータの 30-40%）と、導出可能な値やパディングを抱える IC オブジェクト（{c('HandlerPropertyInlineCache')} 112 B、32 B のパディングを含む {c('InlineCacheHandler')} 128 B、ハンドラごとの 96 B スタブルーチン + 24 B ウォッチポイント集合）に支配される。</p>
<p>20 の施策は（推定削減量 ÷ リスク）で順位付けした。1-7 は実行メモリ、8-13 と 18-19 はメタデータ、14-17 は DFG/FTL の保持データ、20 は GC 側のウォッチポイントを対象とする。既存の削減機構（unlinked Baseline 共有、約 99 個の共有サンクを持つハンドラ IC、16 bit メタデータオフセット表、OSR exit の遅延コンパイル、{c('shrinkToFit')}、老化 jettison、薄い {c('InlineWatchpointSet')}、32 bit {c('StructureID')} など）は深掘り節で整理し、提案が重複しないようにした。</p>""")

method_body = T(
f"""<h3>Build</h3><p>{c('cmake -DPORT=JSCOnly -DCMAKE_BUILD_TYPE=Release -DDEVELOPER_MODE=ON -DENABLE_STATIC_JSC=ON')} with clang 18 on a 4-vCPU Linux VM (16 min). A second build added {c('-DENABLE_METADATA_STATISTICS=1')} (the counters in {c('bytecode/UnlinkedMetadataTable.cpp')} exist upstream but are not wired to any option; they self-report at {c('atexit')}) plus a 40-line, env-gated {c('dataLog')} in {c('DFG::Plan::finalizeInThread')} that counts retained per-compilation structures (patch in the appendix; reverted from the tree).</p>
<h3>Static sizes</h3><p>A translation unit including the real headers prints {c('sizeof')} for ~115 types and {c('-Xclang -fdump-record-layouts')} gives field offsets and padding (all sizes in this report are x86_64; Apple arm64 with 36-bit addresses shrinks a few {c('CompactPtr')} fields).</p>
<h3>Workloads</h3><p>JetStream2 sub-tests run one at a time in the {c('jsc')} shell through the JetStream driver in RAMification mode ({c('typescript, acorn-wtb, Babylon, pdfjs, gbemu, Air, octane-zlib, ML, raytrace, splay')}) plus a synthetic 1-4K-function workload. After each run: two {c('$vm.gc()')}, {c('$vm.linkBufferStats()')} (cumulative linked bytes per LinkBuffer profile: Baseline/DFG/FTL/OSR exits/IC stubs/thunks), {c('memoryUsageStatistics()')} (heap size, per-class cell counts), {c('MemoryFootprint()')}, and — from a Python driver reading {c('/proc/&lt;pid&gt;/smaps')} while the shell blocks on {c('readline()')} — the RSS of the fixed 1 GB executable pool (sum of its contiguous anonymous {c('rwxp')} VMAs). Configurations: default, {c('--thresholdForJITAfterWarmUp=2000/5000')}, {c('--forceCodeBlockToJettisonDueToOldAge=1 --useEagerCodeBlockJettisonTiming=1')}, {c('--useBaselineJITCodeSharing=0')}, {c('--useDFGJIT=0')}, {c('--useFTLJIT=0')}, {c('--useJIT=0')}.</p>
<h3>Caveats</h3><ul><li>LinkBuffer statistics are cumulative allocations (jettisoned code included); pool RSS is the live figure.</li><li>Scores on this VM vary by ±10% run to run; they are shown only to flag gross regressions.</li><li>Retained-metadata counts are summed over all compilations of a run (some CodeBlocks were later jettisoned), i.e. they are the peak-ish population, not the end-of-run live set.</li><li>Machine-code sizes are x86_64; ARM64 code is generally 10-30% larger for the same sequences.</li></ul>""",
f"""<h3>ビルド</h3><p>4 vCPU の Linux VM 上で {c('cmake -DPORT=JSCOnly -DCMAKE_BUILD_TYPE=Release -DDEVELOPER_MODE=ON -DENABLE_STATIC_JSC=ON')}、clang 18（16 分）。2 つ目のビルドでは {c('-DENABLE_METADATA_STATISTICS=1')}（{c('bytecode/UnlinkedMetadataTable.cpp')} のカウンタは upstream に存在するがオプションに接続されておらず、{c('atexit')} で自己報告する）と、コンパイルごとの保持構造を数える 40 行の環境変数ゲート付き {c('dataLog')} を {c('DFG::Plan::finalizeInThread')} に追加した（付録にパッチ。ツリーからは戻し済み）。</p>
<h3>静的サイズ</h3><p>実ヘッダをインクルードする翻訳単位で約 115 型の {c('sizeof')} を出力し、{c('-Xclang -fdump-record-layouts')} でフィールドオフセットとパディングを得た（本レポートのサイズはすべて x86_64。36 bit アドレスの Apple arm64 ではいくつかの {c('CompactPtr')} フィールドが縮む）。</p>
<h3>ワークロード</h3><p>JetStream2 のサブテストを RAMification モードの JetStream ドライバ経由で {c('jsc')} シェル上で 1 つずつ実行（{c('typescript, acorn-wtb, Babylon, pdfjs, gbemu, Air, octane-zlib, ML, raytrace, splay')}）し、加えて 1-4K 関数の合成ワークロード。各実行後に {c('$vm.gc()')} を 2 回、{c('$vm.linkBufferStats()')}（LinkBuffer プロファイルごとの累積リンク済みバイト: Baseline/DFG/FTL/OSR exit/IC スタブ/サンク）、{c('memoryUsageStatistics()')}（ヒープサイズ、クラス別セル数）、{c('MemoryFootprint()')}、そしてシェルが {c('readline()')} でブロックしている間に Python ドライバが {c('/proc/&lt;pid&gt;/smaps')} を読んで得た固定 1 GB 実行プールの RSS（連続する匿名 {c('rwxp')} VMA の合計）。構成: default、{c('--thresholdForJITAfterWarmUp=2000/5000')}、{c('--forceCodeBlockToJettisonDueToOldAge=1 --useEagerCodeBlockJettisonTiming=1')}、{c('--useBaselineJITCodeSharing=0')}、{c('--useDFGJIT=0')}、{c('--useFTLJIT=0')}、{c('--useJIT=0')}。</p>
<h3>注意点</h3><ul><li>LinkBuffer 統計は累積の割り当て量（jettison 済みコードを含む）。プール RSS が生存量。</li><li>この VM ではスコアが実行ごとに ±10% ばらつく。大きな後退を検出する目的でのみ示す。</li><li>保持メタデータの計数は実行中の全コンパイルの合計（後に jettison された CodeBlock も含む）。すなわちピークに近い母集団であり、実行終了時の生存集合ではない。</li><li>機械語サイズは x86_64。ARM64 は同じ列でも一般に 10-30% 大きい。</li></ul>""")

arch_body = T(
f"""<h3>Tiers and who owns the code</h3>
<div class="diagram">
 <div class="box"><div class="t">UnlinkedCodeBlock (shared per source)</div><ul><li>bytecode stream, {c('UnlinkedMetadataTable')} (+ first linked buffer)</li><li>{c('m_unlinkedBaselineCode')}: shared {c('BaselineJITCode')} = machine code + {c('JITCodeMap')} + unlinked IC/call descriptors + math IC bags</li><li>LLInt tier-up counter, arith profiles, unlinked value/array profiles</li></ul></div>
 <div class="box"><div class="t">CodeBlock (per realm, per tier)</div><ul><li>216 B cell (224 B slot); {c('MetadataTable')} copy (16 B/ValueProfile + per-op metadata)</li><li>{c('BaselineJITData')}: one 112 B {c('HandlerPropertyInlineCache')} per IC + constant pool</li><li>{c('DFG::JITData')}: same handler ICs + {c('m_exits')} (16 B/exit) + call link infos + watchpoints</li></ul></div>
 <div class="box"><div class="t">DFG::JITCode / FTL::JITCode</div><ul><li>{c('CommonData')}: watchpoints, weak refs, code origins, inline call frames, IC/CLI bags</li><li>DFG: {c('m_osrExit')} (80 B), event stream (14 B/event), minified graph</li><li>FTL: {c('m_osrExit')} (80 B + reps), {c('osrExitDescriptors')} (48 B + 9 B × frame operands), lazy slow paths, B3 byproducts</li></ul></div>
 <div class="box"><div class="t">Executable pool (1 GB reserved on x86_64)</div><ul><li>Baseline / DFG / FTL bodies, per-exit stubs, IC stubs (bespoke), thunks (per VM + process-wide)</li><li>32 B granule, libpas size classes ≤ 2000 B, medium bitfit above</li></ul></div>
</div>
<p><b>LLInt → Baseline.</b> The LLInt counts on the shared {c('UnlinkedCodeBlock')} counter (+5 entry / +10 return / +1 loop iteration; {c('thresholdForJITAfterWarmUp = 500')}). Baseline compiles on the concurrent {c('JITWorklist')} keyed by UnlinkedCodeBlock; {c('JIT::link')} produces a {c('BaselineJITCode')} that is cached on the unlinked block and reused by every later CodeBlock ({c('useBaselineJITCodeSharing')}); the per-CodeBlock part is only {c('BaselineJITData')} (handler ICs, 112 B each, allocated eagerly per unlinked IC). Property/call/scope/truthiness slow paths are per-VM or process-wide thunks; math ICs, compares and a few others still call C inline. Machine code per bytecode byte on x86_64 measured at 14.3 B (typescript).</p>
<p><b>Baseline → DFG → FTL.</b> The DFG is gated by bytecode cost ({c('maximumOptimizationCandidateBytecodeCost = 100000')}), thresholds scaled by cost, and {c('thresholdForOptimizeAfterWarmUp = 1000')}; the FTL at {c('thresholdForFTLOptimizeAfterWarmUp = 64000')} and cost ≤ 60000. Compile-time memory (Graph, ~104 B {c('DFG::Node')}s individually malloc'd, 32 B {c('AbstractValue')}s ×(2 per node + 3 per block), B3 {c('Value')} 40 B, Air {c('Inst')} 64 B) is stack-scoped to {c('Plan::compileInThreadImpl')} and freed; what stays is {c('DFG::JITCode')}/{c('FTL::JITCode')} plus the CodeBlock's {c('JITData')}. Up to 2-3 plans are compiling concurrently ({c('numberOfDFGCompilerThreads')}, {c('numberOfFTLCompilerThreads')}). OSR exits are compiled lazily on first hit; the DFG reconstructs value recoveries from the event stream, the FTL reads a per-exit dense descriptor.</p>
<p><b>Inline caches.</b> {c('StructureStubInfo')} became {c('PropertyInlineCache')} (96 B base) with {c('HandlerPropertyInlineCache')} (Baseline/DFG, 112 B: data-driven chain of {c('InlineCacheHandler')}s, each 128 B) and {c('RepatchingPropertyInlineCache')} (FTL, 144 B, code patching + {c('PolymorphicAccess')}). Handler code comes from ~99 pre-compiled thunks or bespoke stubs shared through {c('SharedJITStubSet')}; each handler references a {c('PolymorphicAccessJITStubRoutine')} (96 B) that owns cases, weak structures, a {c('WatchpointSet')} and a Bag of clearing watchpoints (112 B/node). Calls use {c('DataOnlyCallLinkInfo')} (80 B) embedded in bytecode metadata for LLInt+Baseline and {c('OptimizingCallLinkInfo')} (96 B) in DFG/FTL; polymorphic calls are shared thunks over a {c('CallSlot')} array (32 B each).</p>
<p><b>Metadata table.</b> One linked {c('MetadataTable')} per CodeBlock: {c('[ValueProfile × N][LinkingData 16][offset16 table 104 (+offset32 208)][per-op metadata]')}; the first link reuses the unlinked buffer, later realms copy. 50 opcodes carry metadata (sizes in the table below); DFG/FTL CodeBlocks share the Baseline table but deep-copy constants/decls/exprs. Arith profiles (2 B) live in the unlinked block; value profiles are 16 B linked + 8 B unlinked.</p>
<h3>Existing memory-saving mechanisms (do not re-propose)</h3>
<ul>
<li>Unlinked Baseline code sharing across CodeBlocks/realms; static shared LLInt entry stubs; process-wide VM-independent thunks and handler-IC thunks; {c('SharedJITStubSet')} for stateless/bespoke stubs; polymorphic call thunks over data slots.</li>
<li>Metadata: 16-bit offset table (32-bit only above 64 KB), value profiles packed into a prefix, {c('MetadataTable')} shared between tiers, arith profiles/LLInt counter on the unlinked block, {c('RareData')} on both CodeBlock kinds, lazy catch/lazy-value-profile buffers, compressed {c('ExpressionInfo')}, {c('static_assert(sizeof(CodeBlock) <= 224)')}.</li>
<li>DFG/FTL: lazy OSR-exit compilation with per-exit caching, no per-exit recoveries in DFG (event stream), {c('FixedVector')}s + {c('shrinkToFit')} at finalize, packed {c('CodeOrigin')}/{c('ValueRecovery')}/{c('VariableEvent')}/{c('ExitValue')}, {c('PCToCodeOriginMap')} only when profiling, Graph/B3 freed after compile, jettison on exit counts and old age, gating by bytecode cost.</li>
<li>Executable memory: branch compaction + shrink on ARM64, exact-size allocation on x86_64, libpas page sharing/decommit, {c('deleteAllCode')} on memory warnings, unlinked-code-block jettison in mini mode.</li>
<li>GC/object model: thin {c('InlineWatchpointSet')} (1 word until first add), vtable-free {c('Watchpoint')} + {c('PackedCellPtr')} owners, DFG weak references as {c('WriteBarrier')}/{c('StructureID')} arrays (no {c('Weak<>')} handles), single-slot transition tables, lazily created {c('StructureRareData')} (≤ 96 B), GC-time dropping of unpinned {c('PropertyTable')}s, IsoSubspace lower-tier precise cells.</li>
</ul>""",
f"""<h3>ティアとコードの所有者</h3>
<div class="diagram">
 <div class="box"><div class="t">UnlinkedCodeBlock（ソースごとに共有）</div><ul><li>バイトコード列、{c('UnlinkedMetadataTable')}（+ 最初のリンク済みバッファ）</li><li>{c('m_unlinkedBaselineCode')}: 共有 {c('BaselineJITCode')} = 機械語 + {c('JITCodeMap')} + unlinked IC/呼び出し記述子 + math IC の Bag</li><li>LLInt tier-up カウンタ、算術プロファイル、unlinked value/array プロファイル</li></ul></div>
 <div class="box"><div class="t">CodeBlock（realm ごと・ティアごと）</div><ul><li>216 B セル（224 B スロット）。{c('MetadataTable')} コピー（16 B/ValueProfile + op ごとのメタデータ）</li><li>{c('BaselineJITData')}: IC ごとに 112 B の {c('HandlerPropertyInlineCache')} + 定数プール</li><li>{c('DFG::JITData')}: 同じハンドラ IC + {c('m_exits')}（16 B/exit）+ call link info + ウォッチポイント</li></ul></div>
 <div class="box"><div class="t">DFG::JITCode / FTL::JITCode</div><ul><li>{c('CommonData')}: ウォッチポイント、弱参照、code origin、inline call frame、IC/CLI の Bag</li><li>DFG: {c('m_osrExit')}（80 B）、イベントストリーム（14 B/イベント）、minified graph</li><li>FTL: {c('m_osrExit')}（80 B + rep）、{c('osrExitDescriptors')}（48 B + 9 B × フレームオペランド）、lazy slow path、B3 副産物</li></ul></div>
 <div class="box"><div class="t">実行プール（x86_64 で 1 GB 予約）</div><ul><li>Baseline / DFG / FTL 本体、exit ごとのスタブ、IC スタブ（個別）、サンク（VM ごと + プロセス共通）</li><li>32 B グラニュール、≤ 2000 B は libpas サイズクラス、それ以上は medium bitfit</li></ul></div>
</div>
<p><b>LLInt → Baseline。</b>LLInt は共有 {c('UnlinkedCodeBlock')} のカウンタで数える（入口 +5 / return +10 / ループ 1 反復 +1、{c('thresholdForJITAfterWarmUp = 500')}）。Baseline は UnlinkedCodeBlock をキーとする並行 {c('JITWorklist')} でコンパイルされ、{c('JIT::link')} が生成する {c('BaselineJITCode')} は unlinked 側にキャッシュされ以後の全 CodeBlock で再利用される（{c('useBaselineJITCodeSharing')}）。CodeBlock ごとの部分は {c('BaselineJITData')}（unlinked IC ごとに 112 B のハンドラ IC を先行確保）だけ。プロパティ/呼び出し/スコープ/truthiness のスローパスは VM ごと・プロセス共通のサンクだが、math IC や比較などはまだインラインで C を呼ぶ。x86_64 のバイトコード 1 B あたり機械語は 14.3 B（typescript 実測）。</p>
<p><b>Baseline → DFG → FTL。</b>DFG はバイトコードコスト（{c('maximumOptimizationCandidateBytecodeCost = 100000')}）でゲートされ、閾値はコストで補正、{c('thresholdForOptimizeAfterWarmUp = 1000')}。FTL は {c('thresholdForFTLOptimizeAfterWarmUp = 64000')} かつコスト ≤ 60000。コンパイル時メモリ（Graph、個別 malloc の約 104 B {c('DFG::Node')}、32 B {c('AbstractValue')} ×（ノードごと 2 + ブロックごと 3）、B3 {c('Value')} 40 B、Air {c('Inst')} 64 B）は {c('Plan::compileInThreadImpl')} のスタックスコープで解放され、残るのは {c('DFG::JITCode')}/{c('FTL::JITCode')} と CodeBlock の {c('JITData')}。同時に 2-3 プランがコンパイル中になり得る（{c('numberOfDFGCompilerThreads')}、{c('numberOfFTLCompilerThreads')}）。OSR exit は初回発火時に遅延コンパイルされ、DFG はイベントストリームから復元情報を再構成し、FTL は exit ごとの密な記述子を読む。</p>
<p><b>インラインキャッシュ。</b>{c('StructureStubInfo')} は {c('PropertyInlineCache')}（96 B 基底）となり、{c('HandlerPropertyInlineCache')}（Baseline/DFG、112 B: 各 128 B の {c('InlineCacheHandler')} をデータ駆動で連鎖）と {c('RepatchingPropertyInlineCache')}（FTL、144 B、コードパッチ + {c('PolymorphicAccess')}）がある。ハンドラコードは約 99 個の事前コンパイル済みサンクか {c('SharedJITStubSet')} 経由で共有される個別スタブ。各ハンドラは case、弱 structure、{c('WatchpointSet')}、クリア用ウォッチポイントの Bag（112 B/ノード）を持つ {c('PolymorphicAccessJITStubRoutine')}（96 B）を参照する。呼び出しは LLInt+Baseline ではバイトコードメタデータに埋め込まれた {c('DataOnlyCallLinkInfo')}（80 B）、DFG/FTL では {c('OptimizingCallLinkInfo')}（96 B）。ポリモーフィック呼び出しは {c('CallSlot')} 配列（各 32 B）上の共有サンク。</p>
<p><b>メタデータ表。</b>CodeBlock ごとに 1 つのリンク済み {c('MetadataTable')}: {c('[ValueProfile × N][LinkingData 16][offset16 表 104 (+offset32 208)][op ごとのメタデータ]')}。最初のリンクは unlinked バッファを再利用し、以降の realm はコピーする。50 opcode がメタデータを持つ（サイズは下表）。DFG/FTL の CodeBlock は Baseline の表を共有するが、定数/decl/expr は深いコピー。算術プロファイル（2 B）は unlinked 側、value profile はリンク済み 16 B + unlinked 8 B。</p>
<h3>既存の削減機構（再提案しない）</h3>
<ul>
<li>CodeBlock/realm 横断の unlinked Baseline コード共有。静的共有の LLInt エントリスタブ。プロセス共通の VM 非依存サンクとハンドラ IC サンク。stateless/個別スタブ用の {c('SharedJITStubSet')}。データスロット上のポリモーフィック呼び出しサンク。</li>
<li>メタデータ: 16 bit オフセット表（64 KB 超のみ 32 bit）、前置領域にパックされた value profile、ティア間で共有される {c('MetadataTable')}、unlinked 側の算術プロファイル/LLInt カウンタ、両 CodeBlock 種の {c('RareData')}、遅延の catch/lazy value profile バッファ、圧縮 {c('ExpressionInfo')}、{c('static_assert(sizeof(CodeBlock) <= 224)')}。</li>
<li>DFG/FTL: exit ごとにキャッシュする遅延 OSR exit コンパイル、DFG では exit ごとの recovery を持たない（イベントストリーム）、finalize 時の {c('FixedVector')} + {c('shrinkToFit')}、パックされた {c('CodeOrigin')}/{c('ValueRecovery')}/{c('VariableEvent')}/{c('ExitValue')}、プロファイル時のみの {c('PCToCodeOriginMap')}、コンパイル後の Graph/B3 解放、exit 回数と老化による jettison、バイトコードコストによるゲート。</li>
<li>実行メモリ: ARM64 の分岐圧縮 + shrink、x86_64 の正確サイズ割り当て、libpas のページ共有/decommit、メモリ警告時の {c('deleteAllCode')}、mini モードでの unlinked code block jettison。</li>
<li>GC/オブジェクトモデル: 薄い {c('InlineWatchpointSet')}（初回 add まで 1 語）、vtable なしの {c('Watchpoint')} + {c('PackedCellPtr')} owner、DFG 弱参照は {c('WriteBarrier')}/{c('StructureID')} 配列（{c('Weak<>')} ハンドル不使用）、単一スロット遷移表、遅延生成の {c('StructureRareData')}（≤ 96 B）、GC 時の未ピン {c('PropertyTable')} 破棄、IsoSubspace の lower-tier precise セル。</li>
</ul>""")

objmodel_body = T(
f"""<p>Facts the JIT bakes into code: the 8-byte {c('JSCell')} header ({c('StructureID')} 32-bit + indexingType/type/flags/cellState; {c('runtime/JSCell.h:293-300')}); {c('StructureID')} decodes as {c('base + 32-bit offset')} because all Structures live in a 4 GB-aligned reservation ({c('heap/StructureAlignedMemoryAllocator.cpp:106-121')}) — this is why so much JIT metadata can hold 4-byte {c('WriteBarrierStructureID')}s instead of pointers; {c('JSObject')} = header + butterfly pointer, default inline capacity 6, out-of-line offsets ≥ 64; {c('Structure')} = 112 B (fields read by generated code: prototype, classInfo, outOfLineTypeFlags, indexingMode, propertyTable, inlineCapacity, previousOrRareData, bitField, propertyHash, seenProperties; fields used only by C++: {c('m_cachedPrototypeChain')}, {c('m_transitionTable')}, {c('m_transitionPropertyName')}, {c('m_transitionWatchpointSet')}), {c('StructureRareData')} = 96 B (created by ICs via {c('startWatchingPropertyForReplacements')} on every prototype-chain hit), {c('FunctionRareData')} = 72 B (80 B cell; the {c('ObjectAllocationProfile')} the JIT reads for {c('new F')}).</p>
<p>GC interplay: {c('CodeBlock::visitChildren')} reports metadata size and non-shared JIT code as extra memory (so N realms over-count shared Baseline code N× while cache-only code counts 0×, and no DFG/FTL side tables are reported at all — {c('CodeBlock.cpp:1213-1219')}); liveness of optimized code goes through {c('shouldVisitStrongly → shouldJettisonDueToOldAge')} with 5/15/20/60 s TTLs; DFG code registers 24 B {c('CodeBlockJettisoningWatchpoint')}s in every watched set (inflating each Structure's thin transition set to a 24 B {c('WatchpointSet')}), and stub routines are freed by {c('Heap::deleteUnmarkedCompiledCode')}. Weak references from the JIT are arrays of {c('WriteBarrier')}/{c('StructureID')} reconciled at GC end, not {c('Weak<>')} handles (24 B {c('WeakImpl')} each), which is why the WeakBlock cost is dominated by transition maps and VM string maps, not by JIT metadata.</p>""",
f"""<p>JIT がコードに焼き込む事実: 8 B の {c('JSCell')} ヘッダ（32 bit の {c('StructureID')} + indexingType/type/flags/cellState、{c('runtime/JSCell.h:293-300')}）。{c('StructureID')} は全 Structure が 4 GB 境界の予約領域に置かれる（{c('heap/StructureAlignedMemoryAllocator.cpp:106-121')}）ため {c('base + 32 bit オフセット')} で復号でき、多くの JIT メタデータがポインタの代わりに 4 B の {c('WriteBarrierStructureID')} を持てる理由になっている。{c('JSObject')} = ヘッダ + butterfly ポインタ、既定インライン容量 6、アウトオブラインオフセット ≥ 64。{c('Structure')} = 112 B（生成コードが読むフィールド: prototype、classInfo、outOfLineTypeFlags、indexingMode、propertyTable、inlineCapacity、previousOrRareData、bitField、propertyHash、seenProperties。C++ だけが使うフィールド: {c('m_cachedPrototypeChain')}、{c('m_transitionTable')}、{c('m_transitionPropertyName')}、{c('m_transitionWatchpointSet')}）。{c('StructureRareData')} = 96 B（IC がプロトタイプチェーンヒットのたびに {c('startWatchingPropertyForReplacements')} で生成）。{c('FunctionRareData')} = 72 B（80 B セル。JIT が {c('new F')} で読む {c('ObjectAllocationProfile')}）。</p>
<p>GC との相互作用: {c('CodeBlock::visitChildren')} はメタデータサイズと非共有 JIT コードを extra memory として報告する（そのため N realm では共有 Baseline コードが N 倍に数えられ、キャッシュ専用コードは 0 倍、DFG/FTL の補助表は一切報告されない — {c('CodeBlock.cpp:1213-1219')}）。最適化コードの生存判定は {c('shouldVisitStrongly → shouldJettisonDueToOldAge')}（TTL 5/15/20/60 s）。DFG コードは監視する各集合に 24 B の {c('CodeBlockJettisoningWatchpoint')} を登録し（各 Structure の薄い遷移集合を 24 B の {c('WatchpointSet')} に膨らませる）、スタブルーチンは {c('Heap::deleteUnmarkedCompiledCode')} で解放される。JIT からの弱参照は GC 終了時に照合される {c('WriteBarrier')}/{c('StructureID')} 配列であり {c('Weak<>')} ハンドル（各 24 B の {c('WeakImpl')}）ではないため、WeakBlock のコストは JIT メタデータではなく遷移マップや VM の文字列マップに支配される。</p>""")

data_body = (
 f'<h3>{t("Static sizes (sizeof, x86_64, this build)","静的サイズ（sizeof、x86_64、本ビルド）")}</h3>' + sizeof_table() +
 f'<h3>{t("Per-opcode metadata sizes (generated BytecodeStructs.h)","opcode ごとのメタデータサイズ（生成された BytecodeStructs.h）")}</h3>' + meta_table() +
 f'<h3>{t("Workloads: linked machine code per tier and live executable pool","ワークロード: ティア別リンク済み機械語と生存実行プール")}</h3>' + workload_table() +
 T("<p class='small'>Cumulative LinkBuffer bytes per profile (<code>$vm.linkBufferStats()</code>) after the test; JIT pool RSS from smaps after two GCs. Live CodeBlocks/Unlinked from <code>memoryUsageStatistics().objectTypeCounts</code>.</p>","<p class='small'>テスト後のプロファイル別 LinkBuffer 累積バイト（<code>$vm.linkBufferStats()</code>）。JIT プール RSS は GC 2 回後の smaps。生存 CodeBlock/Unlinked は <code>memoryUsageStatistics().objectTypeCounts</code>。</p>") +
 f'<h3>{t("Configuration sweeps","構成比較")}</h3>' + config_table() +
 f'<h3>{t("Baseline code composition (typescript, --dumpBaselineJITSizeStatistics)","Baseline コードの内訳（typescript、--dumpBaselineJITSizeStatistics）")}</h3>' + ops_table(BOPS, ts_base) +
 f'<h3>{t("DFG code composition (typescript, --dumpDFGJITSizeStatistics)","DFG コードの内訳（typescript、--dumpDFGJITSizeStatistics）")}</h3>' + ops_table(DOPS, ts_dfg) +
 f'<h3>{t("Linked bytecode metadata (ENABLE(METADATA_STATISTICS) build)","リンク済みバイトコードメタデータ（ENABLE(METADATA_STATISTICS) ビルド）")}</h3>' + metastats_table() +
 f'<h3>{t("Retained DFG/FTL per-compilation data (finalizer probe; summed over all compiles in the run)","保持される DFG/FTL のコンパイルごとデータ（ファイナライザプローブ。実行中の全コンパイルの合計）")}</h3>' + retained_table() +
 f'<h3>{t("Watchpoints and other CommonData retained per compile","コンパイルごとに保持されるウォッチポイントほか CommonData")}</h3>' + watchpoint_table()
)

prio_body = summary_table() + T(
"""<p><b>Do first (low risk, measured, large):</b> #2 (release cache-only Baseline code), #16/#17 (mechanical DFG/FTL record diets), #9/#10/#12 (IC object diets), #19 (JITCodeMap), #7 (granule). <b>Biggest wins needing design work:</b> #14 (FTL exit descriptors — the single largest retained item), #15 (event stream), #1 (size-aware Baseline threshold — trivial patch, needs benchmarking), #3 (compact Baseline IC mode), #5 (exit stub dispatch). <b>Longer-term:</b> #8/#13/#18.</p>""",
"""<p><b>まず着手（低リスク・実測済み・効果大）:</b> #2（キャッシュ専用 Baseline コードの解放）、#16/#17（DFG/FTL レコードの機械的なダイエット）、#9/#10/#12（IC オブジェクトのダイエット）、#19（JITCodeMap）、#7（グラニュール）。<b>設計を要する最大級の効果:</b> #14（FTL exit 記述子 — 保持データ中最大）、#15（イベントストリーム）、#1（サイズを考慮した Baseline 閾値 — パッチは自明だがベンチマーク必須）、#3（コンパクト Baseline IC モード）、#5（exit スタブディスパッチ）。<b>長期:</b> #8/#13/#18。</p>""")

PATCH = open(os.path.join(HERE,'measurement-instrumentation.patch')).read()
appendix_body = T(
f"""<h4>Reproduce the measurements</h4>
<pre><code># build
cmake -G Ninja -DPORT=JSCOnly -DCMAKE_BUILD_TYPE=Release -DDEVELOPER_MODE=ON -DENABLE_STATIC_JSC=ON \\
      -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ ../.. &amp;&amp; ninja jsc
# per-tier linked bytes + IC stubs + thunks (after a workload)
jsc --useDollarVM=1 workload.js -e 'print($vm.linkBufferStats())'
# per-opcode machine code composition
jsc --dumpBaselineJITSizeStatistics=1 workload.js ; jsc --dumpDFGJITSizeStatistics=1 workload.js
# what compiled to Baseline and how big
jsc --reportBaselineCompileTimes=1 workload.js
# metadata bytes per opcode: rebuild with -DENABLE_METADATA_STATISTICS=1 (self-reports at exit)
# retained DFG/FTL data: apply the finalizer probe below, run with WKMEAS_DUMP_RETAINED=1
# JetStream2 sub-test in-process: cd PerformanceTests/JetStream2 &amp;&amp; jsc -e "testList='typescript'" cli-mem.js
# live JIT pool: read /proc/&lt;pid&gt;/smaps while the shell blocks on readline(); sum RSS of the contiguous rwxp VMAs</code></pre>
<h4>Temporary finalizer probe (not committed; reverted from the tree)</h4>""",
f"""<h4>計測の再現</h4>
<pre><code># ビルド
cmake -G Ninja -DPORT=JSCOnly -DCMAKE_BUILD_TYPE=Release -DDEVELOPER_MODE=ON -DENABLE_STATIC_JSC=ON \\
      -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ ../.. &amp;&amp; ninja jsc
# ティア別リンク済みバイト + IC スタブ + サンク（ワークロード後）
jsc --useDollarVM=1 workload.js -e 'print($vm.linkBufferStats())'
# opcode ごとの機械語内訳
jsc --dumpBaselineJITSizeStatistics=1 workload.js ; jsc --dumpDFGJITSizeStatistics=1 workload.js
# 何が Baseline 化され、どれだけ大きいか
jsc --reportBaselineCompileTimes=1 workload.js
# opcode ごとのメタデータバイト: -DENABLE_METADATA_STATISTICS=1 で再ビルド（終了時に自己報告）
# 保持される DFG/FTL データ: 下のプローブを当て、WKMEAS_DUMP_RETAINED=1 で実行
# JetStream2 サブテストをインプロセスで: cd PerformanceTests/JetStream2 &amp;&amp; jsc -e "testList='typescript'" cli-mem.js
# 生存 JIT プール: シェルが readline() でブロック中に /proc/&lt;pid&gt;/smaps を読み、連続する rwxp VMA の RSS を合計</code></pre>
<h4>一時的なファイナライザプローブ（コミットせず、ツリーから戻し済み）</h4>""") + f'<pre><code>{esc(PATCH)}</code></pre>'

def build():
    parts=[]
    parts.append('<title>JSC JIT Memory Ledger</title>')
    parts.append('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+JP:wght@400;500;600;700&display=swap">')
    parts.append(f'<style>{CSS}</style>')
    parts.append(f'''<div class="topbar"><span class="name">JSC JIT Memory Ledger</span><span class="sp"></span>
<div class="langsw" role="group" aria-label="Language"><button type="button" data-lang="en" aria-pressed="true">English</button><button type="button" data-lang="ja" aria-pressed="false" lang="ja">日本語</button></div></div>''')
    parts.append('<div class="wrap">')
    parts.append(f'''<header class="mast"><div class="eyebrow">{t("JavaScriptCore · JIT · GC · IC · object model","JavaScriptCore · JIT · GC · IC · オブジェクトモデル")}</div>
<h1>JSC JIT Memory Ledger</h1>
<p class="sub">{t("A deep dive into where JIT-compiled code and its metadata spend memory in JavaScriptCore, and 20 evidence-backed, measured ways to spend less.","JavaScriptCore の JIT コンパイル済みコードとメタデータがメモリをどこで消費しているかの深掘りと、根拠と計測を伴う 20 の削減策。")}</p>
<div class="meta"><span>{t("Tree","対象ツリー")}: <b>WebKit 7375405d8e</b> (2026-08-16)</span><span>{t("Build","ビルド")}: <b>JSCOnly Release, x86_64 Linux, clang 18</b></span><span>{t("Workloads","ワークロード")}: <b>JetStream2 sub-tests + synthetic</b></span><span>{t("Date","日付")}: <b>2026-08-17</b></span></div></header>''')
    parts.append(toc)
    parts.append(section("summary","Executive summary","要旨",summary_body))
    parts.append(section("method","Method & measurement setup","方法と計測環境",method_body))
    parts.append(section("arch","Deep dive: how the JIT tiers own memory","深掘り: JIT ティアとメモリ所有関係",arch_body))
    parts.append(section("objmodel","Object model & GC facts the JIT depends on","JIT が依拠するオブジェクトモデルと GC",objmodel_body))
    parts.append(section("data","Measured data","計測データ",data_body))
    parts.append(section("opps","The 20 opportunities","20 の削減施策", T("<p>Ranked by estimated saving ÷ risk. Each card cites the source lines behind the claim, the measurement that sizes it, a proposal and its risk. Savings are for the measured x86_64 build; multiply code-size items by ~1.2 for ARM64.</p>","<p>推定削減量 ÷ リスクで順位付け。各カードは主張の根拠となるソース行、規模を示す計測、提案、リスクを記す。削減量は計測した x86_64 ビルド基準で、コードサイズ系は ARM64 では約 1.2 倍。</p>") + ''.join(cards)))
    parts.append(section("prio","Prioritisation","優先度",prio_body))
    parts.append(section("appendix","Appendix: reproduction & instrumentation","付録: 再現手順と計測パッチ",appendix_body))
    parts.append(f'<footer>{t("All file:line references are relative to Source/JavaScriptCore/ at 7375405d8e. Sizes are sizeof on x86_64 Linux; counts are from the runs described in the method section.","file:line 参照はすべて 7375405d8e の Source/JavaScriptCore/ 相対。サイズは x86_64 Linux の sizeof、件数は方法の節で述べた実行から得たもの。")}</footer>')
    parts.append('</div>')
    parts.append(f'<script>{JS}</script>')
    return '\n'.join(parts)

if __name__=='__main__':
    out=build()
    p=os.path.join(HERE,'index.html')
    open(p,'w').write(out)
    print(p, len(out))
