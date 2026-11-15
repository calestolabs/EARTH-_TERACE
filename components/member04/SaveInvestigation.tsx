'use client';
import {useRef,useState} from 'react';
import {Evidence,saveInvestigation,memberError} from '../../lib/investigations';
export default function SaveInvestigation({evidence}:{evidence:Evidence}){
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[saved,setSaved]=useState<{key:string;id:string}|null>(null);
 const pending=useRef<{key:string;id:string}|null>(null),lock=useRef(false);const key=JSON.stringify(evidence);
 async function save(){if(lock.current)return;lock.current=true;setBusy(true);setError('');try{if(pending.current?.key!==key)pending.current={key,id:crypto.randomUUID()};const id=await saveInvestigation(evidence,pending.current.id);setSaved({key,id});}catch(e){setError(memberError(e))}finally{lock.current=false;setBusy(false)}}
 return <div>{saved?.key===key?<a className="secondary" href={'/report?id='+saved.id}>Open saved report →</a>:<button className="secondary" disabled={busy} onClick={save}>{busy?'Saving…':'Save investigation'}</button>}{error&&<p role="alert" style={{maxWidth:300,color:'#f4c58d'}}>{error} <a href="/login">Sign in</a></p>}</div>;
}
