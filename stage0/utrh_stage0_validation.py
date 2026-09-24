#!/usr/bin/env python3
import json, math, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats, optimize
from statsmodels.tools.numdiff import approx_hess
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

SEED = 20260924
rng = np.random.default_rng(SEED)
OUT = Path('/mnt/data')

# ---------- Generic parametric AFT likelihood ----------

def _dist_fns(name, shape):
    if name == 'weibull':
        d = stats.weibull_min(c=shape, scale=1.0)
    elif name == 'lognormal':
        d = stats.lognorm(s=shape, scale=1.0)  # median 1
    elif name == 'loglogistic':
        d = stats.fisk(c=shape, scale=1.0)
    elif name == 'gamma':
        d = stats.gamma(a=shape, scale=1.0/shape)  # mean 1
    else:
        raise ValueError(name)
    return d

SHAPE_BOUNDS = {
    'weibull': (0.35, 5.0),
    'lognormal': (0.12, 1.8),
    'loglogistic': (1.2, 8.0),
    'gamma': (0.5, 12.0),
}
SHAPE_INIT = {'weibull':1.5,'lognormal':0.55,'loglogistic':3.0,'gamma':3.0}
TRUE_SHAPE = {'weibull':1.6,'lognormal':0.55,'loglogistic':3.2,'gamma':3.0}


def sim_aft_dataset(dist_name, tstars, n=180, shape=None, shape_by_module=None, exact_frac=0.55, grid_frac=0.12):
    rows=[]
    shape = TRUE_SHAPE[dist_name] if shape is None else shape
    for m,a in enumerate(tstars):
        sh = shape_by_module[m] if shape_by_module is not None else shape
        d = _dist_fns(dist_name, sh)
        z = d.rvs(size=n, random_state=rng)
        t = a*z
        # independent right censoring, scaled to module so censoring burden is comparable
        c = rng.uniform(0.75*a, 2.25*a, size=n)
        for ti,ci in zip(t,c):
            if ti > ci:
                rows.append((m,'right',ci,np.inf))
            else:
                if rng.random() < exact_frac:
                    rows.append((m,'exact',ti,ti))
                else:
                    h = grid_frac*a
                    lo = math.floor(ti/h)*h
                    hi = lo+h
                    lo = max(lo, 1e-10)
                    rows.append((m,'interval',lo,hi))
    return pd.DataFrame(rows, columns=['module','type','L','R'])


def _dist_vals(dist_name, x, shape, kind):
    # shape may be scalar or vector
    if dist_name == 'weibull':
        if kind=='pdf': return stats.weibull_min.pdf(x, c=shape, scale=1.0)
        if kind=='cdf': return stats.weibull_min.cdf(x, c=shape, scale=1.0)
        return stats.weibull_min.sf(x, c=shape, scale=1.0)
    elif dist_name == 'lognormal':
        if kind=='pdf': return stats.lognorm.pdf(x, s=shape, scale=1.0)
        if kind=='cdf': return stats.lognorm.cdf(x, s=shape, scale=1.0)
        return stats.lognorm.sf(x, s=shape, scale=1.0)
    elif dist_name == 'loglogistic':
        if kind=='pdf': return stats.fisk.pdf(x, c=shape, scale=1.0)
        if kind=='cdf': return stats.fisk.cdf(x, c=shape, scale=1.0)
        return stats.fisk.sf(x, c=shape, scale=1.0)
    elif dist_name == 'gamma':
        sc=1.0/np.asarray(shape)
        if kind=='pdf': return stats.gamma.pdf(x, a=shape, scale=sc)
        if kind=='cdf': return stats.gamma.cdf(x, a=shape, scale=sc)
        return stats.gamma.sf(x, a=shape, scale=sc)
    raise ValueError(dist_name)


def _arrays(df):
    m=df.module.to_numpy(dtype=int)
    typ=df.type.to_numpy()
    L=df.L.to_numpy(float); R=df.R.to_numpy(float)
    return m,typ,L,R


def nll_shared(params, df, dist_name, M):
    loga=np.zeros(M)
    if M>1: loga[1:]=params[:M-1]
    sh=float(np.exp(params[M-1]))
    lo_b,hi_b=SHAPE_BOUNDS[dist_name]
    if not (lo_b < sh < hi_b): return 1e12
    m,typ,L,R=_arrays(df); a=np.exp(loga[m])
    vals=np.empty(len(df),float)
    ex=typ=='exact'; ri=typ=='right'; it=typ=='interval'
    if np.any(ex): vals[ex]=_dist_vals(dist_name,L[ex]/a[ex],sh,'pdf')/a[ex]
    if np.any(ri): vals[ri]=_dist_vals(dist_name,L[ri]/a[ri],sh,'sf')
    if np.any(it):
        vals[it]=_dist_vals(dist_name,R[it]/a[it],sh,'cdf')-_dist_vals(dist_name,L[it]/a[it],sh,'cdf')
    if np.any(~np.isfinite(vals)) or np.any(vals<=0): return 1e12
    return -float(np.sum(np.log(np.maximum(vals,1e-14))))


def nll_sep_shape(params, df, dist_name, M):
    loga=np.zeros(M)
    if M>1: loga[1:]=params[:M-1]
    shapes=np.exp(params[M-1:M-1+M])
    lo_b,hi_b=SHAPE_BOUNDS[dist_name]
    if np.any(shapes<=lo_b) or np.any(shapes>=hi_b): return 1e12
    m,typ,L,R=_arrays(df); a=np.exp(loga[m]); sh=shapes[m]
    vals=np.empty(len(df),float)
    ex=typ=='exact'; ri=typ=='right'; it=typ=='interval'
    if np.any(ex): vals[ex]=_dist_vals(dist_name,L[ex]/a[ex],sh[ex],'pdf')/a[ex]
    if np.any(ri): vals[ri]=_dist_vals(dist_name,L[ri]/a[ri],sh[ri],'sf')
    if np.any(it):
        vals[it]=_dist_vals(dist_name,R[it]/a[it],sh[it],'cdf')-_dist_vals(dist_name,L[it]/a[it],sh[it],'cdf')
    if np.any(~np.isfinite(vals)) or np.any(vals<=0): return 1e12
    return -float(np.sum(np.log(np.maximum(vals,1e-14))))

def fit_shared(df, dist_name, M):
    x0=np.r_[np.zeros(M-1), np.log(SHAPE_INIT[dist_name])]
    bshape=(np.log(SHAPE_BOUNDS[dist_name][0]), np.log(SHAPE_BOUNDS[dist_name][1]))
    bounds=[(-3,3)]*(M-1)+[bshape]
    res=optimize.minimize(nll_shared,x0,args=(df,dist_name,M),method='L-BFGS-B',bounds=bounds,
                          options={'maxiter':500,'ftol':1e-10})
    # observed Hessian at optimum
    try:
        H=approx_hess(res.x, lambda p:nll_shared(p,df,dist_name,M), epsilon=1e-4)
        cov=np.linalg.pinv(H)
    except Exception:
        cov=np.full((len(res.x),len(res.x)),np.nan)
    return res,cov


def fit_sep(df, dist_name, M):
    x0=np.r_[np.zeros(M-1), np.repeat(np.log(SHAPE_INIT[dist_name]),M)]
    bshape=(np.log(SHAPE_BOUNDS[dist_name][0]), np.log(SHAPE_BOUNDS[dist_name][1]))
    bounds=[(-3,3)]*(M-1)+[bshape]*M
    res=optimize.minimize(nll_sep_shape,x0,args=(df,dist_name,M),method='L-BFGS-B',bounds=bounds,
                          options={'maxiter':600,'ftol':1e-10})
    return res


def loglik_on(df, dist_name, M, params, separate=False):
    return -(nll_sep_shape(params,df,dist_name,M) if separate else nll_shared(params,df,dist_name,M))

# ---------- S0.1 ----------
def run_s01(R=12):
    records=[]
    tstars=np.array([1.0,1.45,2.3])
    true_logs=np.log(tstars[1:])
    for dist in ['weibull','lognormal','loglogistic','gamma']:
        est=[]; cover=[]; sep_reject=[]; fails=0
        for r in range(R):
            df=sim_aft_dataset(dist,tstars,n=140)
            rs,cov=fit_shared(df,dist,3)
            if not rs.success or not np.all(np.isfinite(rs.x)):
                fails+=1; continue
            e=rs.x[:2]
            est.append(e)
            se=np.sqrt(np.maximum(np.diag(cov)[:2],0))
            cover.append((np.abs(e-true_logs)<=1.96*se).astype(float))
            rp=fit_sep(df,dist,3)
            if rp.success:
                LR=2*((-rp.fun)-(-rs.fun))
                p=stats.chi2.sf(max(LR,0),df=2)
                sep_reject.append(p<0.05)
        est=np.array(est); cover=np.array(cover)
        records.append({
            'test':'S0.1','scenario':dist,'replicates_ok':len(est),'fit_failures':fails,
            'bias_logscale_m1':float(np.mean(est[:,0]-true_logs[0])),'bias_logscale_m2':float(np.mean(est[:,1]-true_logs[1])),
            'rmse_logscale':float(np.sqrt(np.mean((est-true_logs)**2))),
            'coverage95':float(np.mean(cover)),'spurious_shape_reject_rate':float(np.mean(sep_reject)),
        })
    return records

# ---------- S0.2 ----------
def split_df(df, frac=.7):
    idx=rng.permutation(len(df)); k=int(frac*len(df));
    return df.iloc[idx[:k]].copy(), df.iloc[idx[k:]].copy()

def run_s02(R=20):
    detects=[]; gains=[]; lrtps=[]
    for r in range(R):
        df=sim_aft_dataset('weibull',[1.0,1.8],n=220,shape_by_module=[1.05,2.2],exact_frac=.7,grid_frac=.08)
        tr,te=split_df(df,.7)
        s,_=fit_shared(tr,'weibull',2); a=fit_sep(tr,'weibull',2)
        if not (s.success and a.success): continue
        LR=2*((-a.fun)-(-s.fun)); p=stats.chi2.sf(max(LR,0),df=1)
        gain=(loglik_on(te,'weibull',2,a.x,True)-loglik_on(te,'weibull',2,s.x,False))/len(te)
        lrtps.append(p); gains.append(gain); detects.append((p<.05) and (gain>0))
    return [{'test':'S0.2','scenario':'weibull shape 1.05 vs 2.20','replicates_ok':len(detects),
             'detection_rate_LRT_and_testLL':float(np.mean(detects)),
             'LRT_reject_rate':float(np.mean(np.array(lrtps)<.05)),
             'median_test_loglik_gain_per_obs':float(np.median(gains)),
             'fraction_alt_better_testLL':float(np.mean(np.array(gains)>0))}]

# ---------- S0.3 ----------
def lognorm_phase(mu, sigma, n, factor):
    return factor*np.exp(rng.normal(mu,sigma,size=n))

def fit_phase_models(df_train, df_test):
    # long data columns logdur, group, phase(0 early 1 late)
    def design(d, interaction):
        X=pd.DataFrame({'const':1.0,'phase':d.phase.values,'group':d.group.values})
        if interaction: X['interaction']=d.phase.values*d.group.values
        return X
    out=[]
    for inter in [False,True]:
        X=design(df_train,inter); model=sm.OLS(df_train.logdur.values,X.values).fit()
        Xt=design(df_test,inter).values
        pred=Xt@model.params
        sig=np.sqrt(np.mean(model.resid**2))
        ll=np.sum(stats.norm.logpdf(df_test.logdur.values,loc=pred,scale=sig))
        out.append((model,ll))
    return out

def run_s03(R=40):
    pvals=[]; gains=[]
    for r in range(R):
        rows=[]
        for g,(ae,al) in enumerate([(1,1),(.60,1.40)]):
            n=260
            e=lognorm_phase(2.1,.32,n,ae); l=lognorm_phase(2.4,.32,n,al)
            for x in e: rows.append((g,0,math.log(x)))
            for x in l: rows.append((g,1,math.log(x)))
        df=pd.DataFrame(rows,columns=['group','phase','logdur'])
        idx=rng.permutation(len(df)); k=int(.7*len(df)); tr=df.iloc[idx[:k]]; te=df.iloc[idx[k:]]
        (m0,ll0),(m1,ll1)=fit_phase_models(tr,te)
        # interaction p-value is last coefficient
        pvals.append(m1.pvalues[-1]); gains.append((ll1-ll0)/len(te))
    return [{'test':'S0.3','scenario':'early factor 0.60, late factor 1.40',
             'interaction_reject_rate':float(np.mean(np.array(pvals)<.05)),
             'median_test_loglik_gain_per_obs':float(np.median(gains)),
             'fraction_phase_specific_better':float(np.mean(np.array(gains)>0))}]

# ---------- S0.4 ----------
def sim_mix(n, w, scale):
    comp=rng.random(n)>w  # False comp1 with weight w
    mu=np.where(comp,3.55,2.55)
    logt=rng.normal(mu,.22,size=n)+math.log(scale)
    return np.exp(logt)

def run_s04(R=40):
    pks=[]; cvps=[]; qdiff=[]
    for r in range(R):
        t0=sim_mix(300,.80,1.0); t1=sim_mix(300,.30,1.55)
        # estimate scalar shift robustly by log-median and remove it
        shift=np.median(np.log(t1))-np.median(np.log(t0))
        z0=np.log(t0); z1=np.log(t1)-shift
        pks.append(stats.ks_2samp(z0,z1).pvalue)
        # Levene-like difference in dimensionless CV via bootstrap-independent delta method is not needed; record magnitude
        cv0=np.std(t0,ddof=1)/np.mean(t0); cv1=np.std(t1,ddof=1)/np.mean(t1)
        cvps.append(abs(math.log(cv1/cv0)))
        q0=np.quantile(t0,.75)/np.quantile(t0,.25); q1=np.quantile(t1,.75)/np.quantile(t1,.25)
        qdiff.append(abs(math.log(q1/q0)))
    return [{'test':'S0.4','scenario':'mixture weights 0.80/0.20 vs 0.30/0.70',
             'KS_reject_after_scale_alignment':float(np.mean(np.array(pks)<.05)),
             'median_abs_log_CV_ratio':float(np.median(cvps)),
             'median_abs_log_IQRratio_ratio':float(np.median(qdiff))}]

# ---------- S0.5 ----------
def run_s05(R=24):
    est=[]; excludes=[]; fails=0
    for r in range(R):
        df=sim_aft_dataset('weibull',[1.0,1.0],n=180)
        rs,cov=fit_shared(df,'weibull',2)
        if not rs.success: fails+=1; continue
        e=rs.x[0]; se=math.sqrt(max(cov[0,0],0)); est.append(e); excludes.append(abs(e)>1.96*se)
    return [{'test':'S0.5','scenario':'equal Weibull modules', 'replicates_ok':len(est),'fit_failures':fails,
             'mean_logscale_estimate':float(np.mean(est)),'sd_logscale_estimate':float(np.std(est,ddof=1)),
             'false_nonzero_rate_95CI':float(np.mean(excludes))}]

# ---------- S0.6 ----------
def cv_summary(times):
    return np.mean(times),np.std(times,ddof=1)/np.mean(times)

def one_s06(vary_delta=False, M=40, n=8):
    # log t* span corresponding roughly to 25--200 day means
    logt=np.linspace(math.log(.125),0,M)
    rng.shuffle(logt)
    x=(-logt - np.mean(-logt))/np.std(-logt,ddof=1) # larger x = faster modifier
    if vary_delta:
        # independent schedules with enough spread to break x-g collinearity
        deltas=rng.choice([2.,4.,7.,10.,14.],size=M,replace=True)
    else:
        deltas=np.repeat(7.,M)
    ys=[]; gs=[]
    # low biological CV typical of tight incubation distributions
    sigma=math.sqrt(math.log(1+.045**2))
    mu=-.5*sigma*sigma # mean Z=1
    for lt,delta in zip(logt,deltas):
        mean_target=200*np.exp(lt)
        z=np.exp(rng.normal(mu,sigma,size=n))
        true=mean_target*z
        obs=np.ceil(true/delta)*delta
        mean,cv=cv_summary(obs)
        # avoid exact zero SD under coarse grid; continuity floor reflects unresolved dispersion
        cv=max(cv,1e-4)
        ys.append(math.log(cv)); gs.append(math.log(delta/mean))
    y=np.array(ys); g=np.array(gs)
    X0=sm.add_constant(x)
    m0=sm.OLS(y,X0).fit()
    X1=np.column_stack([np.ones(M),x,g])
    m1=sm.OLS(y,X1).fit()
    # VIF for x and g (without intercept indexing 1,2)
    vif_x=variance_inflation_factor(X1,1); vif_g=variance_inflation_factor(X1,2)
    return {'p_unadj':m0.pvalues[1],'b_unadj':m0.params[1],
            'p_adj':m1.pvalues[1],'b_adj':m1.params[1],
            'vif':max(vif_x,vif_g),'corr_xg':np.corrcoef(x,g)[0,1]}

def run_s06(R=80):
    recs=[]
    for varying in [False,True]:
        arr=[one_s06(varying) for _ in range(R)]
        df=pd.DataFrame(arr)
        identifiable=df.vif<=5
        recs.append({'test':'S0.6','scenario':'varying grid' if varying else 'fixed common grid',
                     'unadjusted_spurious_reject_rate':float(np.mean(df.p_unadj<.05)),
                     'median_unadjusted_beta1':float(df.b_unadj.median()),
                     'median_VIF':float(df.vif.median()),
                     'fraction_VIF_le_5':float(np.mean(identifiable)),
                     'median_corr_x_g':float(df.corr_xg.median()),
                     'adjusted_reject_rate_all':float(np.mean(df.p_adj<.05)),
                     'adjusted_reject_rate_if_identifiable':float(np.mean(df.loc[identifiable,'p_adj']<.05)) if identifiable.any() else np.nan,
                     'median_adjusted_beta1_if_identifiable':float(df.loc[identifiable,'b_adj'].median()) if identifiable.any() else np.nan,
                     'replicates':R})
    return recs

# ---------- Main ----------
records=[]
records += run_s01()
records += run_s02()
records += run_s03()
records += run_s04()
records += run_s05()
records += run_s06()
res=pd.DataFrame(records)
res.to_csv(OUT/'UTRH_Stage0_results.csv',index=False)

# Pass/fail engineering interpretation
status=[]
for _,r in res.iterrows():
    t=r['test']; sc=r['scenario']; st='PASS'; note=''
    if t=='S0.1':
        ok=(abs(r.bias_logscale_m1)<0.06 and abs(r.bias_logscale_m2)<0.06 and r.rmse_logscale<0.12 and 0.88<=r.coverage95<=1.0 and r.spurious_shape_reject_rate<=0.12)
        st='PASS' if ok else 'REVIEW'
        note='Engineering tolerance: |bias|<0.06, RMSE<0.12, coverage>=0.88, false shape rejection<=0.12.'
    elif t=='S0.2':
        ok=(r.detection_rate_LRT_and_testLL>=0.85 and r.fraction_alt_better_testLL>=0.90 and r.median_test_loglik_gain_per_obs>0)
        st='PASS' if ok else 'REVIEW'
        note='Prespecified simulation effect 1.05 vs 2.20; engineering detection target >=0.85.'
    elif t=='S0.3':
        ok=(r.interaction_reject_rate>=0.90 and r.fraction_phase_specific_better>=0.90)
        st='PASS' if ok else 'REVIEW'
        note='Phase-specific interaction must be reproducibly detected.'
    elif t=='S0.4':
        ok=(r.KS_reject_after_scale_alignment>=0.90)
        st='PASS' if ok else 'REVIEW'
        note='After scalar alignment, changing mixture weights must remain detectable.'
    elif t=='S0.5':
        ok=(abs(r.mean_logscale_estimate)<0.03 and r.false_nonzero_rate_95CI<=0.09)
        st='PASS' if ok else 'REVIEW'
        note='Null log-scale near 0; false nonzero rate <=0.09.'
    elif t=='S0.6':
        if sc=='fixed common grid':
            # Under plan's VIF rule this is expected to be non-identifiable; requirement as written cannot be met.
            st='PLAN_CONFLICT' if r.fraction_VIF_le_5<0.5 else ('PASS' if r.adjusted_reject_rate_if_identifiable<=0.10 else 'REVIEW')
            note='With fixed Delta, x and g are structurally collinear; §8.2 VIF>5 gate conflicts with S0.6 demand for adjusted beta1≈0.'
        else:
            ok=(r.fraction_VIF_le_5>=0.70 and r.unadjusted_spurious_reject_rate>=0.50 and r.adjusted_reject_rate_if_identifiable<=0.12)
            st='PASS' if ok else 'REVIEW'
            note='Varying schedules should permit separation; adjustment should restore nominal false-positive behavior.'
    status.append({'test':t,'scenario':sc,'status':st,'note':note})
status=pd.DataFrame(status)
status.to_csv(OUT/'UTRH_Stage0_status.csv',index=False)

bundle={'seed':SEED,'results':records,'status':status.to_dict(orient='records')}
(OUT/'UTRH_Stage0_results.json').write_text(json.dumps(bundle,indent=2),encoding='utf-8')

print(res.to_string(index=False))
print('\nSTATUS')
print(status.to_string(index=False))
