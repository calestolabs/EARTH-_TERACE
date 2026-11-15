import {initializeApp,getApps} from 'firebase/app';
import {getAuth,GoogleAuthProvider,signInWithPopup} from 'firebase/auth';
export function configured(){return !!process.env.NEXT_PUBLIC_FIREBASE_API_KEY && !!process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN && !!process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;}
export function auth(){if(!configured())return null;const app=getApps()[0]||initializeApp({apiKey:process.env.NEXT_PUBLIC_FIREBASE_API_KEY,authDomain:process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,projectId:process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,appId:process.env.NEXT_PUBLIC_FIREBASE_APP_ID});return getAuth(app);}
export async function googleSignIn(){const a=auth();if(!a)throw new Error('Google sign-in needs your Firebase project configuration. Use the demo to explore, or follow README.md to connect your project.');return signInWithPopup(a,new GoogleAuthProvider());}
