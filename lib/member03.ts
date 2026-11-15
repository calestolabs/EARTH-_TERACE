import {annual,stats,Point,Variable} from './analysis';
export const variableKeys:Variable[]=['rainfall','temperature','soil'];
export type AnnualResult=ReturnType<typeof annual>;
export function standardize(points:Point[]){
 const n=points.length,mean=n?points.reduce((s,p)=>s+p.value,0)/n:0;
 const sd=n>1?Math.sqrt(points.reduce((s,p)=>s+(p.value-mean)**2,0)/(n-1)):0;
 return {n,mean,sd,points:points.map(p=>({...p,z:sd?(p.value-mean)/sd:0}))};
}
export function anomalies(points:Point[],threshold:number){
 if(!Number.isFinite(threshold)||threshold<1)throw Error('Invalid anomaly threshold');
 const baseline=standardize(points);
 return {...baseline,eligible:baseline.n>=5,flags:baseline.n>=5&&baseline.sd>0?baseline.points.filter(p=>Math.abs(p.z)>=threshold):[]};
}
export function yearChange(points:Point[],a:number,b:number){const first=points.find(p=>p.year===a),last=points.find(p=>p.year===b);return first&&last?{first:first.value,last:last.value,difference:last.value-first.value}:null;}
export function compareRows(series:Partial<Record<Variable,Point[]>>,normalized:boolean){
 const years=[...new Set(Object.values(series).flatMap(p=>p.map(x=>x.year)))].sort((a,b)=>a-b);
 const standardized=Object.fromEntries(Object.entries(series).map(([v,p])=>[v,standardize(p).points]));
 return years.map(year=>Object.fromEntries([['year',year],...Object.keys(series).map(v=>{const p=standardized[v].find(p=>p.year===year);return [v,p?(normalized?p.z:p.value):null]})]));
}
export function trendClass(points:Point[]){const s=stats(points);return !s?'insufficient':!s.significant?'uncertain':s.sen>0?'increasing':s.sen<0?'decreasing':'uncertain';}
export const fmt=(n:number|null|undefined)=>n==null||!Number.isFinite(n)?'—':n.toLocaleString('en-US',{maximumFractionDigits:3});
