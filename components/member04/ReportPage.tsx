'use client';
import {useEffect,useState} from 'react';
import {getInvestigation,memberError,SavedInvestigation} from '../../lib/investigations';
import InvestigationReport from './ReportSummary';
export default function ReportPage(){const [report,setReport]=useState<SavedInvestigation|null>(null),[error,setError]=useState(''),[retry,setRetry]=useState(0);useEffect(()=>{let active=true;setError('');const id=new URLSearchParams(window.location.search).get('id');if(!id){setError('Choose a report from your investigation history.');return}getInvestigation(id).then(r=>{if(active)setReport(r)}).catch(e=>{if(active)setError(memberError(e))});return()=>{active=false}},[retry]);if(error)return <section className="m4-card" role="alert"><p>{error}</p><a href="/history">Open history</a> <button onClick={()=>setRetry(n=>n+1)}>Retry</button></section>;if(!report)return <p role="status">Loading report…</p>;return <InvestigationReport report={report}/>}
