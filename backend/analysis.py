"""Reference Python analysis, numerically equivalent to the browser implementation."""
from collections import defaultdict,Counter
from calendar import monthrange
from math import sqrt,erfc
from statistics import median

def annual(rows,variable,start,end):
    by=defaultdict(list);months=0
    for r in rows:
        year,month=map(int,r['date'].split('-'));last=monthrange(year,month)[1]
        if r['date']+'-01'<start or f"{r['date']}-{last:02d}">end:continue
        by[year].append(r);months+=1
    points=[];omitted=[]
    for year,rs in sorted(by.items()):
        if len({r['date'] for r in rs})!=12:omitted.append(year);continue
        days=lambda r:monthrange(*map(int,r['date'].split('-')))[1]
        value=sum(r['value'] for r in rs) if variable=='rainfall' else sum(r['value']*days(r) for r in rs)/sum(days(r) for r in rs)
        points.append({'year':year,'value':value})
    return {'points':points,'omitted':omitted,'months':months}

def stats(points):
    n=len(points)
    if n<5:return None
    x=[p['year'] for p in points];y=[p['value'] for p in points];xm=sum(x)/n;ym=sum(y)/n
    slope=sum((a-xm)*(b-ym) for a,b in zip(x,y))/sum((a-xm)**2 for a in x)
    S=0;slopes=[]
    for i in range(n):
        for j in range(i+1,n):
            diff=y[j]-y[i];S+=(diff>0)-(diff<0);slopes.append(diff/(x[j]-x[i]))
    variance=(n*(n-1)*(2*n+5)-sum(t*(t-1)*(2*t+5) for t in Counter(y).values()))/18
    z=((S-1 if S>0 else S+1 if S<0 else 0)/sqrt(variance)) if variance else 0
    p=erfc(abs(z)/sqrt(2));sen=median(slopes)
    residual=[b-(ym+slope*(a-xm)) for a,b in zip(x,y)];den=sum(r*r for r in residual)
    autocorrelation=sum(a*b for a,b in zip(residual,residual[1:]))/den if den else 0
    return dict(n=n,slope=slope,sen=sen,p=p,z=z,S=S,mean=ym,intercept=ym-slope*xm,significant=p<.05,direction='Increasing' if sen>0 else 'Decreasing' if sen<0 else 'Flat',autocorrelation=autocorrelation)
