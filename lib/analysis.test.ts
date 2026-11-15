import {test} from 'node:test';
import assert from 'node:assert/strict';
import {annual,stats,correlation} from './analysis.ts';
test('Mann–Kendall known monotonic series and slope',()=>{const r=stats(Array.from({length:10},(_,i)=>({year:2000+i,value:2*i})))!;assert.equal(r.slope,2);assert.equal(r.sen,2);assert.equal(r.S,45);assert.ok(Math.abs(r.p-.00008303070332645)<1e-7);assert.equal(r.significant,true)});
test('Ties and constant series do not produce a false trend',()=>{const r=stats(Array.from({length:10},(_,i)=>({year:2000+i,value:20})))!;assert.ok(Math.abs(r.p-1)<1e-6);assert.equal(r.sen,0);assert.equal(r.significant,false)});
test('Incomplete years and partial boundary months excluded',()=>{const rows=Array.from({length:12},(_,i)=>({date:`2000-${String(i+1).padStart(2,'0')}`,value:1}));assert.deepEqual(annual([...rows,{date:'2001-01',value:99}],'rainfall','2000-01-01','2001-12-31').points,[{year:2000,value:12}]);assert.equal(annual(rows,'rainfall','2000-01-02','2000-12-31').points.length,0)});
test('Day weighted leap-year mean',()=>{const rows=Array.from({length:12},(_,i)=>({date:`2000-${String(i+1).padStart(2,'0')}`,value:i===1?29:0}));assert.equal(annual(rows,'temperature','2000-01-01','2000-12-31').points[0].value,841/366)});
test('Correlation matches only common years',()=>{const a=Array.from({length:10},(_,i)=>({year:2000+i,value:i}));assert.equal(correlation(a,a.slice(3))?.n,7);assert.equal(correlation(a,a)?.r,1);assert.equal(correlation(a,a.slice(8)),null)});
