import {collection,deleteDoc,doc,getDoc,getDocs,getFirestore,orderBy,query,serverTimestamp,setDoc} from 'firebase/firestore';
import {auth} from './firebase';
import {annual,stats,Variable} from './analysis';
export type Evidence={title:string;mission:string;region:string;start:string;end:string;answers:Record<string,string>;results:Partial<Record<Variable,ReturnType<typeof annual>&{stats:ReturnType<typeof stats>}>>;source:string;method:string;engine:string};
export type SavedInvestigation={id:string;title:string;createdAt:string;evidence:Evidence};
function db(){const a=auth();if(!a?.currentUser)throw Error('Sign in to save and read your investigations.');return {store:getFirestore(a.app),uid:a.currentUser.uid};}
export function validateEvidence(e:Evidence){
 if(!e||typeof e.title!=='string'||!e.title.trim()||e.title.length>120||typeof e.region!=='string'||typeof e.source!=='string'||typeof e.method!=='string'||typeof e.mission!=='string'||typeof e.engine!=='string'||!e.answers||typeof e.answers!=='object'||!/^\d{4}-\d{2}-\d{2}$/.test(e.start)||!/^\d{4}-\d{2}-\d{2}$/.test(e.end)||e.start>e.end||!e.results||!Object.keys(e.results).length)throw Error('Incomplete investigation. Run the analysis again.');
 for(const [key,r] of Object.entries(e.results)){
  if(!['rainfall','temperature','soil'].includes(key)||!r||!Array.isArray(r.points)||!r.stats||r.points.length<5||!Array.isArray(r.omitted)||!r.points.every(p=>Number.isInteger(p.year)&&Number.isFinite(p.value))||!['slope','sen','p','n'].every(k=>Number.isFinite(r.stats[k]))||r.stats.p<0||r.stats.p>1)throw Error('Invalid analysis results. Run the investigation again.');
 }
 const json=JSON.stringify(e);if(new TextEncoder().encode(json).length>450000)throw Error('This investigation is too large to save.');return json;
}
export async function saveInvestigation(e:Evidence,id:string){const json=validateEvidence(e);const {store,uid}=db();const ref=doc(store,'users',uid,'investigations',id);await setDoc(ref,{title:e.title,evidenceJson:json,schemaVersion:1,createdAt:serverTimestamp()});return id;}
function decode(id:string,data:any):SavedInvestigation {if(data.schemaVersion!==1)throw Error('Unsupported report version.');const evidence=JSON.parse(data.evidenceJson);validateEvidence(evidence);return {id,title:data.title,createdAt:data.createdAt?.toDate().toISOString()||'',evidence};}
export async function listInvestigations(){const {store,uid}=db();const result=await getDocs(query(collection(store,'users',uid,'investigations'),orderBy('createdAt','desc')));return result.docs.map(d=>decode(d.id,d.data()));}
export async function getInvestigation(id:string){if(!/^[a-zA-Z0-9-]{1,80}$/.test(id))throw Error('Invalid report ID.');const {store,uid}=db();const result=await getDoc(doc(store,'users',uid,'investigations',id));if(!result.exists())throw Error('Report not found in your account. It may have been deleted.');return decode(result.id,result.data());}
export async function deleteInvestigation(id:string){const {store,uid}=db();await deleteDoc(doc(store,'users',uid,'investigations',id));}
export function memberError(error:unknown){const e=error as {code?:string;message?:string};const messages:Record<string,string>={
 'auth/configuration-not-found':'Firebase Authentication is not initialized. Open Authentication in Firebase Console and click Get started.',
 'auth/operation-not-allowed':'Enable this sign-in provider in Firebase Authentication → Sign-in method.',
 'auth/unauthorized-domain':'Add localhost to Firebase Authentication → Settings → Authorized domains.',
 'auth/invalid-credential':'The email or password is incorrect.',
 'auth/email-already-in-use':'This email already has an account. Sign in instead.',
 'auth/weak-password':'Choose a stronger password that meets your Firebase password policy.',
 'auth/popup-blocked':'Allow popups, then try again in Chrome.',
 'auth/popup-closed-by-user':'Google sign-in was cancelled. Please try again.',
 'auth/network-request-failed':'Check your internet connection and retry.',
 'auth/too-many-requests':'Too many attempts. Wait a moment before retrying.',
 'permission-denied':'Access denied. Check your sign-in and publish the Member 04 Firestore rules.',
 'unavailable':'Cannot reach Firestore. Check your connection and that the database exists.'};return messages[e?.code||'']||e?.message||'Something went wrong. Please retry.';}
