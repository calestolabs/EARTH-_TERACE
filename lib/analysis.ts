export type Variable = 'rainfall'|'temperature'|'soil';
export type Observation = {date:string,value:number};
export type Dataset = Record<string, Record<Variable,Observation[]>>;
export type Point = {year:number,value:number};
export const variables: Record<Variable,{name:string;unit:string;color:string;definition:string;layer:string}> = {
 rainfall:{name:'Rainfall',unit:'mm',color:'#66b7ff',definition:'Rain accumulated over a year, converted from the monthly precipitation rate.',layer:'Rainf_tavg'},
 temperature:{name:'Temperature',unit:'°C',color:'#f0bd72',definition:'Near-surface air temperature. Monthly Kelvin values are converted to Celsius.',layer:'Tair_f_inst'},
 soil:{name:'Soil moisture',unit:'kg/m²',color:'#65d5ad',definition:'Water stored in the upper 10 cm of soil, expressed as mass per unit area.',layer:'SoilMoi0_10cm_inst'}
};
export function annual(rows:Observation[],v:Variable,start:string,end:string) {
 const by:Record<number,Observation[]>={};let months=0;
 for(const r of rows){const [y,m]=r.date.split('-').map(Number); const last=new Date(Date.UTC(y,m,0)).getUTCDate();if(r.date+'-01'<start||r.date+'-'+last>end)continue;(by[y]??=[]).push(r);months++;}
 const points:Point[]=[]; const omitted:number[]=[];
 for(const [year,rs] of Object.entries(by)) {if(new Set(rs.map(r=>r.date)).size!==12){omitted.push(+year);continue;}
 const days=(r:Observation)=>{const [y,m]=r.date.split('-').map(Number);return new Date(Date.UTC(y,m,0)).getUTCDate()};
 points.push({year:+year,value:v==='rainfall'?rs.reduce((s,r)=>s+r.value,0):rs.reduce((s,r)=>s+r.value*days(r),0)/rs.reduce((s,r)=>s+days(r),0)});}
 return {points:points.sort((a,b)=>a.year-b.year),omitted,months};
}
function erfc(x:number){const z=Math.abs(x),t=1/(1+z/2);const r=t*Math.exp(-z*z-1.26551223+t*(1.00002368+t*(.37409196+t*(.09678418+t*(-.18628806+t*(.27886807+t*(-1.13520398+t*(1.48851587+t*(-.82215223+t*.17087277)))))))));return x>=0?r:2-r;}
export function stats(p:Point[]){const n=p.length;if(n<5)return null;
 const xm=p.reduce((s,p)=>s+p.year,0)/n,ym=p.reduce((s,p)=>s+p.value,0)/n;
 const slope=p.reduce((s,p)=>s+(p.year-xm)*(p.value-ym),0)/p.reduce((s,p)=>s+(p.year-xm)**2,0);
 let S=0;const slopes:number[]=[];const ties:Record<string,number>={};
 for(let i=0;i<n;i++){ties[p[i].value]=(ties[p[i].value]||0)+1;for(let j=i+1;j<n;j++){S+=Math.sign(p[j].value-p[i].value);slopes.push((p[j].value-p[i].value)/(p[j].year-p[i].year));}}
 const variance=(n*(n-1)*(2*n+5)-Object.values(ties).reduce((s,t)=>s+t*(t-1)*(2*t+5),0))/18;
 const z=variance===0?0:(S>0?S-1:S<0?S+1:0)/Math.sqrt(variance);
 const pvalue=Math.min(1,erfc(Math.abs(z)/Math.sqrt(2)));slopes.sort((a,b)=>a-b);const mid=Math.floor(slopes.length/2);const sen=slopes.length%2?slopes[mid]:(slopes[mid-1]+slopes[mid])/2;
 const residual=p.map(a=>a.value-(ym+slope*(a.year-xm)));const den=residual.reduce((s,r)=>s+r*r,0);let lag=0;for(let i=1;i<n;i++)lag+=residual[i]*residual[i-1];
 return {n,slope,sen,p:pvalue,z,S,mean:ym,intercept:ym-slope*xm,significant:pvalue<.05,direction:sen>0?'Increasing':sen<0?'Decreasing':'Flat',autocorrelation:den?lag/den:0};
}
export function correlation(a:Point[],b:Point[]){const pairs=a.flatMap(x=>{const y=b.find(p=>p.year===x.year);return y?[[x.value,y.value]]:[]});if(pairs.length<5)return null;const n=pairs.length,mx=pairs.reduce((s,p)=>s+p[0],0)/n,my=pairs.reduce((s,p)=>s+p[1],0)/n;const d=Math.sqrt(pairs.reduce((s,p)=>s+(p[0]-mx)**2,0)*pairs.reduce((s,p)=>s+(p[1]-my)**2,0));return d?{r:pairs.reduce((s,p)=>s+(p[0]-mx)*(p[1]-my),0)/d,n}:null;}
