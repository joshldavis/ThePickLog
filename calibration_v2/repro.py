import os,sys,json,csv,random,hashlib,time
sys.path.insert(0,'.')
import calibration_run  # loads jev.env
import filing_lens as fl
C=sorted(csv.DictReader(open('cal/candidates.csv')),key=lambda r:r['cal_id'])
pick=sorted(random.Random(2028).sample([r['cal_id'] for r in C],30))
rd='cal/run_jev-1.13.0_v2'; os.makedirs(rd+'/repro',exist_ok=True)
out=[]
for r in C:
    if r['cal_id'] not in pick: continue
    p=rd+'/repro/'+r['cal_id']+'.json'
    if not os.path.exists(p):
        text=open('cal/'+r['text_file']).read()
        f={"form":r["form"],"items":r["items"],"filingDate":r["filing_date"],"accession":r["accession"],"primaryDocument":""}
        resp=fl.call_jev(fl.build_request(f,text,fl.JEV_MODEL)); json.dump(resp,open(p,'w')); time.sleep(0.1)
    a=fl.parse_answers(json.load(open(rd+'/responses/'+r['cal_id']+'.json')),expected_model=fl.JEV_MODEL)
    b=fl.parse_answers(json.load(open(p)),expected_model=fl.JEV_MODEL)
    out.append({'cal_id':r['cal_id'],**{f'{q}_changed':int(a[q]['value']!=b[q]['value']) for q in fl.QUESTION_ORDER},
      'rs_first':a['reverse_split']['value'],'rs_p1':a['reverse_split']['p'],'rs_p2':b['reverse_split']['p'],
      'max_dp':round(max(abs(a[q]['p']-b[q]['p']) for q in fl.QUESTION_ORDER),3)})
json.dump({'seed':2028,'ids':pick,'rows':out,'reverse_split_changed':sum(o['reverse_split_changed'] for o in out),
 'any_changed':sum(sum(v for k,v in o.items() if k.endswith('_changed')) for o in out),'max_dp':max(o['max_dp'] for o in out)},open(rd+'/repro.json','w'),indent=1)
print(json.dumps({k:v for k,v in json.load(open(rd+'/repro.json')).items() if k!='rows'}))
