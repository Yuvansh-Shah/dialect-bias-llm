"""Three figures for the manuscript. Every value comes from figures.json or is
recomputed here from scores.csv by a named computation. Each figure must clear the
label-overlap gate in figstyle.save() before it is written."""
import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
ITEMS_DIR = ROOT / "items"
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"
FIG_DIR = ROOT / "figures"
ANALYSIS_DIR = ROOT / "analysis"
import csv, json
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
import figstyle as F
F.use_style()

RUN=str(DATA_DIR)+"/"
sc=[r for r in csv.DictReader([l for l in open(str(DATA_DIR/"scores.csv"),encoding='utf-8') if not l.startswith('#')])]
akey={r['item_id']:r for r in csv.DictReader(open(str(ITEMS_DIR/"arm_mapping.csv"),encoding='utf-8'))}
loc={r['item_id']:r['locale_class'] for r in csv.DictReader(
     [l for l in open(str(ITEMS_DIR/"item_locale_classification.csv"),encoding='utf-8') if not l.startswith('#')])}
for r in sc:
    r['cond']='SAE' if r['arm']==akey[r['item_id']]['sae_arm'] else 'DIALECT'
    r['track']='AAE' if r['item_id'].startswith('AAE') else 'IndE'
    r['loc']=loc[r['item_id']]
MODELS=['google/gemma-4-31b-it','meta/llama-3.3-70b-instruct','z-ai/glm-5.2']
SHORT={'google/gemma-4-31b-it':'gemma-4-31b','meta/llama-3.3-70b-instruct':'llama-3.3-70b',
       'z-ai/glm-5.2':'glm-5.2'}
EXCL={'AAE08'}

def cells(field,pred=lambda r:True):
    d=defaultdict(list)
    for r in sc:
        if r['item_id'] in EXCL or not pred(r): continue
        v=r.get(field)
        if v=='' or v is None: continue
        d[(r['item_id'],r['model'],r['cond'])].append(float(v))
    return d

# ============================================================ Figure 1
def fig1():
    cv=cells('correct')
    rows=[]
    for m in MODELS:
        ids=sorted(set(k[0] for k in cv if k[1]==m))
        for meth in ('Binary','Graded'):
            vals={}
            for c in ('SAE','DIALECT'):
                if meth=='Binary':
                    v=[1 if sum(cv[(i,m,c)])>len(cv[(i,m,c)])/2 else 0 for i in ids]
                else:
                    v=[np.mean(cv[(i,m,c)]) for i in ids]
                vals[c]=100*np.mean(v)
            rows.append((SHORT[m],meth,vals['SAE'],vals['DIALECT']))
    fig,ax=plt.subplots(figsize=(F.TEXTWIDTH,2.9))
    ys=[]; labs=[]
    y=0
    for i,(mn,meth,s,d) in enumerate(rows):
        ys.append(y); labs.append(meth)
        ax.plot([s,d],[y,y],color=F.GRAY,lw=0.7,zorder=1)
        # dialect drawn as an OPEN square so a coinciding SAE circle stays visible
        ax.plot([d],[y],'s',ms=7.0,mfc='none',mec=F.DIA_C,mew=1.4,zorder=3,
                label='Dialect arm' if i==0 else None)
        ax.plot([s],[y],'o',ms=4.6,color=F.SAE_C,zorder=4,
                label='SAE arm' if i==0 else None)
        y-=1
        if meth=='Graded': y-=0.6
    ax.set_yticks(ys); ax.set_yticklabels(labs)
    # model names as left-hand group labels, placed outside the data area
    for gi,m in enumerate(MODELS):
        ymid=-(gi*2.6)-0.5
        ax.text(-0.185,ymid,SHORT[m],transform=ax.get_yaxis_transform(),
                ha='left',va='center',fontsize=8.5,color=F.INK,fontweight='bold')
    ax.set_xlabel('Per-arm accuracy (per cent of the 51 scored items)')
    ax.set_xlim(92,101)
    ax.set_ylim(min(ys)-0.8,max(ys)+0.8)
    h,l=ax.get_legend_handles_labels()
    o=[l.index('SAE arm'),l.index('Dialect arm')]
    ax.legend([h[i] for i in o],[l[i] for i in o],loc='lower left',bbox_to_anchor=(0.0,1.02),ncol=2)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='y',length=0)
    fig.subplots_adjust(left=0.30,right=0.985,top=0.86,bottom=0.17)
    F.save(fig,str(FIG_DIR/"fig1_accuracy.pdf"),name='Figure 1 (accuracy, binary vs graded)')
    plt.close(fig)

# ============================================================ Figure 2
def fig2():
    cv=cells('word_count',pred=lambda r: r['track']=='AAE')
    fig,axes=plt.subplots(1,3,figsize=(F.TEXTWIDTH,3.1),sharey=True)
    for ax,m in zip(axes,MODELS):
        ids=sorted(set(k[0] for k in cv if k[1]==m))
        sh=lo=ti=0
        for i in ids:
            s=np.mean(cv[(i,m,'SAE')]); d=np.mean(cv[(i,m,'DIALECT')])
            if d<s: col,z,a=F.SAE_C,2,0.85; sh+=1
            elif d>s: col,z,a=F.RUST,3,0.9; lo+=1
            else: col,z,a=F.GRAY,2,0.7; ti+=1
            ax.plot([0,1],[s,d],'-o',color=col,lw=0.8,ms=2.6,alpha=a,zorder=z)
        ax.set_xlim(-0.28,1.28); ax.set_xticks([0,1])
        ax.set_xticklabels(['SAE','Dialect'])
        ax.set_title(f'{SHORT[m]}\n{sh} shorter, {lo} longer, {ti} tied',fontsize=8.5)
        ax.spines['bottom'].set_visible(True)
    axes[0].set_ylabel('Mean response length (words)\nover three repeats')
    fig.subplots_adjust(left=0.115,right=0.99,top=0.80,bottom=0.10,wspace=0.16)
    F.save(fig,str(FIG_DIR/"fig2_aae_slope.pdf"),name='Figure 2 (AAE paired slopes)')
    plt.close(fig)

# ============================================================ Figure 3
def fig3():
    out={}
    for lab,pred in [('Locale-sensitive\n(4 items)',lambda r: r['track']=='IndE' and r['loc']=='locale-sensitive'),
                     ('Locale-invariant\n(28 items)',lambda r: r['track']=='IndE' and r['loc']=='locale-invariant')]:
        cv=cells('word_count',pred=pred); d=[]
        for (iid,mm) in sorted(set((k[0],k[1]) for k in cv)):
            s=cv.get((iid,mm,'SAE')); dd=cv.get((iid,mm,'DIALECT'))
            if s and dd: d.append(np.mean(dd)-np.mean(s))
        out[lab]=np.array(d)
    fig,ax=plt.subplots(figsize=(F.TEXTWIDTH,2.6))
    rng=np.random.default_rng(20260725)
    ypos={list(out)[0]:1.0,list(out)[1]:0.0}
    for lab,d in out.items():
        y=ypos[lab]+rng.uniform(-0.13,0.13,len(d))
        cols=[F.SAE_C if v<0 else (F.RUST if v>0 else F.GRAY) for v in d]
        ax.scatter(d,y,s=17,c=cols,alpha=0.85,linewidths=0,zorder=3)
        ax.plot([np.median(d),np.median(d)],[ypos[lab]-0.24,ypos[lab]+0.24],
                color=F.INK,lw=1.5,zorder=4)
    ax.axvline(0,color=F.GRAY,lw=0.7,zorder=1)
    ax.set_yticks(list(ypos.values())); ax.set_yticklabels(list(ypos.keys()))
    ax.set_ylim(-0.5,1.5)
    ax.set_xlabel('Dialect minus SAE mean response length (words), one point per item and model')
    ax.spines['left'].set_visible(False); ax.tick_params(axis='y',length=0)
    ax.text(0.985,0.90,'vertical rule = median',transform=ax.transAxes,
            ha='right',va='top',fontsize=7.5,color=F.GRAY)
    fig.subplots_adjust(left=0.20,right=0.985,top=0.95,bottom=0.20)
    F.save(fig,str(FIG_DIR/"fig3_locale_split.pdf"),name='Figure 3 (locale split)')
    plt.close(fig)

fig1(); fig2(); fig3()
