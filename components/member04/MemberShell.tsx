'use client';
import EarthtraceLogo from '../EarthtraceLogo';
import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {ReactNode} from 'react';
import {Session,useSession} from './Session';
function Shell({children}:{children:ReactNode}){const path=usePathname(),{user}=useSession();return <div className="m4"><header className="m4-nav"><EarthtraceLogo/><nav aria-label="Member pages">{[['/','Explore'],['/ai-detective','AI Detective'],['/history','History'],[user?'/profile':'/login',user?'My profile':'Sign in']].map(([href,label])=><Link key={href} href={href} aria-current={path===href?'page':undefined}>{label}</Link>)}</nav></header><main className="m4-main">{children}</main><footer className="m4-footer">EARTHTRACE · Follow the evidence. Keep asking questions.</footer></div>}
export default function MemberShell({children}:{children:ReactNode}){return <Session><Shell>{children}</Shell></Session>}
