from pathlib import Path
import json, sys, numpy as np
src=Path('/mnt/data/utrh_stage0_validation.py').read_text()
pre=src.split('# ---------- Main ----------')[0]
ns={}
exec(pre,ns)
name=sys.argv[1]; R=int(sys.argv[2]); seed=int(sys.argv[3])
ns['rng']=np.random.default_rng(seed)
if name.startswith('S01_'):
    dist=name.split('_',1)[1]
    # clone run_s01 logic for one distribution only
    tstars=np.array([1.0,1.45,2.3]); true_logs=np.log(tstars[1:])
    est=[]; cover=[]; sep_reject=[]; fails=0
    stats=ns['stats']
    for r in range(R):
        df=ns['sim_aft_dataset'](dist,tstars,n=140)
        rs,cov=ns['fit_shared'](df,dist,3)
        if not rs.success or not np.all(np.isfinite(rs.x)):
            fails+=1; continue
        e=rs.x[:2]; est.append(e)
        se=np.sqrt(np.maximum(np.diag(cov)[:2],0)); cover.append((np.abs(e-true_logs)<=1.96*se).astype(float))
        rp=ns['fit_sep'](df,dist,3)
        if rp.success:
            LR=2*((-rp.fun)-(-rs.fun)); p=stats.chi2.sf(max(LR,0),df=2); sep_reject.append(p<0.05)
    est=np.array(est); cover=np.array(cover)
    out={'test':'S0.1','scenario':dist,'R_requested':R,'replicates_ok':len(est),'fit_failures':fails,
         'bias_logscale_m1':float(np.mean(est[:,0]-true_logs[0])),'bias_logscale_m2':float(np.mean(est[:,1]-true_logs[1])),
         'rmse_logscale':float(np.sqrt(np.mean((est-true_logs)**2))), 'coverage95':float(np.mean(cover)),
         'spurious_shape_reject_rate':float(np.mean(sep_reject)), 'seed':seed}
else:
    fn={'S02':'run_s02','S03':'run_s03','S04':'run_s04','S05':'run_s05','S06':'run_s06'}[name]
    out=ns[fn](R=R)
    out={'seed':seed,'R_requested':R,'results':out}
Path(f'/mnt/data/highpower_{name}.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
