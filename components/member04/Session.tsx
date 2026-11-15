'use client';
import {createContext,useContext,useEffect,useState,ReactNode} from 'react';
import {onAuthStateChanged,User} from 'firebase/auth';
import {auth} from '../../lib/firebase';
import {memberError} from '../../lib/investigations';
const Context=createContext<{user:User|null;loading:boolean;error:string}>({user:null,loading:true,error:''});
export function Session({children}:{children:ReactNode}){const [user,setUser]=useState<User|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState('');useEffect(()=>{try{const a=auth();if(!a){setError('Firebase configuration is missing. Fill the four NEXT_PUBLIC_FIREBASE values in .env.local and restart Next.js.');setLoading(false);return}return onAuthStateChanged(a,u=>{setUser(u);setLoading(false)},e=>{setError(memberError(e));setLoading(false)})}catch(e){setError(memberError(e));setLoading(false)}},[]);return <Context.Provider value={{user,loading,error}}>{children}</Context.Provider>}
export const useSession=()=>useContext(Context);
export function RequireUser({children}:{children:ReactNode}){const {user,loading,error}=useSession();if(loading)return <p role="status">Checking your account…</p>;if(error)return <p className="m4-alert" role="alert">{error}</p>;if(!user)return <section className="m4-card"><h1>Your detective workspace</h1><p>Sign in to access your profile, assistant and saved investigations.</p><a className="m4-button" href="/login">Sign in</a></section>;return <div key={user.uid}>{children}</div>}
