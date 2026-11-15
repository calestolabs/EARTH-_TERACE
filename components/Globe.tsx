'use client';
import {useEffect,useRef,useState} from 'react';
import {geoContains,geoArea} from 'd3-geo';
// Orthographic sphere renderer: works without WebGL, including mobile and restricted GPUs.
export default function Globe({onCountry,small=false}:{onCountry?:(name:string)=>void;small?:boolean}){
 const canvas=useRef<HTMLCanvasElement>(null),callback=useRef(onCountry),pause=useRef(false);callback.current=onCountry;
 const [country,setCountry]=useState('Sri Lanka'),[paused,setPaused]=useState(false),[failed,setFailed]=useState(false);
 useEffect(()=>{const el=canvas.current;if(!el)return;const ctx=el.getContext('2d',{alpha:true});if(!ctx){setFailed(true);return;}
 const size=420,radius=192,center=size/2;el.width=size;el.height=size;let disposed=false,frame=0,longitude=80*Math.PI/180,pitch=0,down=false,moved=false,lastX=0,lastY=0,last=0,features:any[]=[];
 const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;const image=new Image();image.src='/assets/earth.jpg';image.onerror=()=>setFailed(true);
 const vectors:{index:number;x:number;y:number;z:number;shade:number}[]=[];
 for(let y=0;y<size;y++)for(let x=0;x<size;x++){const nx=(x-center)/radius,ny=(center-y)/radius,d=nx*nx+ny*ny;if(d<=1){const z=Math.sqrt(1-d);vectors.push({index:(y*size+x)*4,x:nx,y:ny,z,shade:Math.min(1.16,.42+.78*Math.max(0,-nx*.32+ny*.24+z*.91))});}}
 const buffer=ctx.createImageData(size,size);let pixels:Uint8ClampedArray|null=null,tw=0,th=0;
 image.onload=()=>{const tex=document.createElement('canvas');tex.width=image.width;tex.height=image.height;const tc=tex.getContext('2d')!;tc.drawImage(image,0,0);pixels=tc.getImageData(0,0,image.width,image.height).data;tw=image.width;th=image.height;};
 fetch('/assets/countries.json').then(r=>r.json()).then(d=>{if(disposed)return;features=d.features;for(const f of features){const polys=f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates;for(const p of polys){if(geoArea({type:'Polygon',coordinates:p})>2*Math.PI)p.forEach((r:any)=>r.reverse());}}}).catch(()=>{});
 const point=(x:number,y:number,z:number)=>{const ry=y*Math.cos(pitch)+z*Math.sin(pitch),rz=z*Math.cos(pitch)-y*Math.sin(pitch);return{lat:Math.asin(Math.max(-1,Math.min(1,ry))),lon:longitude+Math.atan2(x,rz)}};
 const draw=(time:number)=>{if(disposed)return;frame=requestAnimationFrame(draw);if(time-last<70)return;const delta=Math.min((time-last)/1000,.1);last=time;if(!down&&!pause.current&&!reduced)longitude+=delta*.035;
 if(!pixels)return;
 for(const v of vectors){const p=point(v.x,v.y,v.z);const u=((p.lon/(Math.PI*2)+.5)%1+1)%1;const tx=Math.min(tw-1,Math.floor(u*tw)),ty=Math.min(th-1,Math.max(0,Math.floor((.5-p.lat/Math.PI)*th)));const k=(ty*tw+tx)*4;buffer.data[v.index]=pixels[k]*v.shade;buffer.data[v.index+1]=pixels[k+1]*v.shade;buffer.data[v.index+2]=pixels[k+2]*v.shade;buffer.data[v.index+3]=255;}
 ctx.putImageData(buffer,0,0);
 const glow=ctx.createRadialGradient(center,center,radius*.92,center,center,radius+5);glow.addColorStop(0,'rgba(70,170,205,0)');glow.addColorStop(.8,'rgba(83,166,200,.13)');glow.addColorStop(1,'rgba(83,166,200,0)');ctx.fillStyle=glow;ctx.beginPath();ctx.arc(center,center,radius+5,0,2*Math.PI);ctx.fill();
 const lat=7.87*Math.PI/180,lon=80.77*Math.PI/180-longitude;const z=Math.cos(lat)*Math.cos(lon),y=Math.sin(lat);const rz=z*Math.cos(pitch)+y*Math.sin(pitch),ry=y*Math.cos(pitch)-z*Math.sin(pitch);if(rz>0){const px=center+radius*Math.cos(lat)*Math.sin(lon),py=center-radius*ry;ctx.fillStyle='#b8f4c4';ctx.shadowColor='#b8f4c4';ctx.shadowBlur=9;ctx.beginPath();ctx.arc(px,py,2.5,0,2*Math.PI);ctx.fill();ctx.shadowBlur=0;}
 };frame=requestAnimationFrame(draw);
 const start=(e:PointerEvent)=>{down=true;moved=false;lastX=e.clientX;lastY=e.clientY;el.setPointerCapture(e.pointerId)};
 const move=(e:PointerEvent)=>{if(!down)return;const dx=e.clientX-lastX,dy=e.clientY-lastY;if(Math.abs(dx)+Math.abs(dy)>2)moved=true;longitude-=dx*.007;pitch=Math.max(-1,Math.min(1,pitch+dy*.004));lastX=e.clientX;lastY=e.clientY};
 const end=(e:PointerEvent)=>{down=false;if(moved)return;const rect=el.getBoundingClientRect();const x=((e.clientX-rect.left)/rect.width*size-center)/radius,y=(center-(e.clientY-rect.top)/rect.height*size)/radius;if(x*x+y*y>1)return;const p=point(x,y,Math.sqrt(1-x*x-y*y));const lng=((p.lon*180/Math.PI+180)%360+360)%360-180;const f=features.find(f=>geoContains(f,[lng,p.lat*180/Math.PI]));const name=f?.properties.name||'Ocean';setCountry(name);callback.current?.(name)};
 el.addEventListener('pointerdown',start);el.addEventListener('pointermove',move);el.addEventListener('pointerup',end);el.addEventListener('pointercancel',()=>down=false);
 return()=>{disposed=true;cancelAnimationFrame(frame);image.onload=null;el.removeEventListener('pointerdown',start);el.removeEventListener('pointermove',move);el.removeEventListener('pointerup',end)};
 },[]);
 return <div className={'globe-shell '+(small?'small':'')}><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="globe-render software"><canvas ref={canvas} role="img" aria-label="Interactive satellite Earth. Drag to rotate and click to identify a country. Sri Lanka is available for investigations."/></div>{failed&&<div className="globe-fallback" style={{backgroundImage:'url(/assets/earth.jpg)'}}/>}<div className="globe-label"><i/>{country}<span>{country==='Sri Lanka'?'FIELD SITE · 25 DISTRICTS':'SELECTED ON EARTH'}</span></div><div className="globe-controls"><button aria-label={paused?'Resume globe rotation':'Pause globe rotation'} onClick={()=>{pause.current=!paused;setPaused(!paused)}}>{paused?'▶':'Ⅱ'}</button><span>DRAG TO EXPLORE · CLICK TO DISCOVER</span></div></div>
}
