"""Clean the supplied Giovanni exports. Run: python scripts/prepare_data.py PATH_TO_CSV_FOLDER"""
import csv,json,sys,calendar,re,datetime
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=Path(sys.argv[1])
districts=['Ampara','Anuradhapura','Badulla','Batticaloa','Colombo','Galle','Gampaha','Hambantota','Jaffna','Kalutara','Kandy','Kegalle','Kilinochchi','Kurunegala','Mannar','Matale','Matara','Monaragala','Mullaitivu','Nuwara Eliya','Polonnaruwa','Puttalam','Ratnapura','Trincomalee','Vavuniya']
alias={'kaluthara':'Kalutara','hambanthota':'Hambantota','hambana10c301tota':'Hambantota','atale':'Matale','mullativu':'Mullaitivu','puththlamnorth':'Puttalam','rathnapura':'Ratnapura','vauniya':'Vavuniya'}
lookup={re.sub('[^a-z]','',n.lower()):n for n in districts}
files={'rainfall':'Rainfall Sri Lanka.csv','temperature':'temperature_srilanka.csv','soil':'SOILMOISTURE_srilanka.CSV'}
out={d:{v:[] for v in files} for d in districts}; report={'excluded':[],'renamed':{},'duplicates':[],'sources':files}
for variable,name in files.items():
 seen=set()
 for line,r in enumerate(csv.reader(open(source/name,encoding='utf-8-sig')),1):
  try:d=datetime.datetime.strptime(r[1],'%m/%d/%Y %H:%M');v=float(r[2])
  except (ValueError,IndexError):continue
  raw=r[0].strip();key=re.sub('[^a-z0-9]','',raw.lower().split('_')[0])
  if raw.lower().startswith('nuwara'):key='nuwaraeliya'
  district=lookup.get(key) or alias.get(key)
  if not district or v==-9999 or d.date()>datetime.date(2026,11,15):
   report['excluded'].append({'file':name,'line':line,'region':raw,'date':str(d.date()),'reason':'unknown region or invalid/future value'});continue
  if raw!=district:report['renamed'][raw]=district
  stamp=d.strftime('%Y-%m');ident=(district,stamp)
  if ident in seen: report['duplicates'].append({'file':name,'district':district,'month':stamp});continue
  seen.add(ident)
  days=calendar.monthrange(d.year,d.month)[1]
  if variable=='temperature':v-=273.15
  if variable=='rainfall':v*=86400*days
  out[district][variable].append({'date':stamp,'value':round(v,6)})
for d in out:
 for v in out[d]:out[d][v].sort(key=lambda x:x['date'])
(root/'public/data/climate.json').write_text(json.dumps(out,separators=(',',':')))
(root/'public/data/quality-report.json').write_text(json.dumps(report,indent=2))
print('Saved',sum(len(a) for d in out.values() for a in d.values()),'observations;',len(report['excluded']),'excluded;',len(report['duplicates']),'duplicates')
