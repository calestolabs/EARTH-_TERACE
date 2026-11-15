// Run from earthtrace: node scripts/install-member03.cjs
// Adds navigation without overwriting Member 04 or your original analysis logic.
const fs=require('node:fs');const path=require('node:path');
const root=path.resolve(__dirname,'..');const file=path.join(root,'app/page.tsx');
let text=fs.readFileSync(file,'utf8');
if(text.includes('MEMBER03_NAV')){console.log('Member 03 navigation already installed.');process.exit(0);}
const nav="<nav className={menu?'nav open':'nav'}>";
const actions='<div className="analysis-actions">';
if(!text.includes(nav)||!text.includes(actions)){console.error('Your app/page.tsx differs from the original ZIP. No changes made. Follow INSTALL_MEMBER03.md to add links manually.');process.exit(1);}
text=text.replace(nav,nav+'{/* MEMBER03_NAV */}<a href="/evidence-board">Evidence Lab</a>');
text=text.replace(actions,actions+'<a className="secondary" href={"/environmental-map?"+new URLSearchParams({district:region,variable:selected[0]||"temperature",from:start.slice(0,4),to:end.slice(0,4)}).toString()}>Maps &amp; comparisons</a>');
const backup=file+'.member03-backup';if(!fs.existsSync(backup))fs.copyFileSync(file,backup);
fs.writeFileSync(file,text);console.log('Added Evidence Lab and Maps & comparisons links. Backup: app/page.tsx.member03-backup');
