import { ImageResponse } from "@vercel/og";
export const config = { runtime: "edge" };

const C = { bg:"#0c0f14", panel:"#0e1420", line:"#2a3240", text:"#e8e8e8",
  muted:"#8b98a8", a:"#1f6f6b", green:"#2ec27e", red:"#f0506e", amber:"#f5b14c", blue:"#5aa0ff" };

const pct = (v)=>{const n=Number(v);return isFinite(n)?((n>0?"+":"")+n.toFixed(1)+"%"):"—";};
const col = (n)=> Number(n)>0?C.green:Number(n)<0?C.red:C.text;
const fmtDate=(s)=>{if(!s)return"—";const d=new Date(s);return isNaN(d)?String(s):d.toLocaleDateString("en-US",{year:"numeric",month:"short",day:"numeric",timeZone:"America/New_York"});};

const h=(type,style,children)=>({type,props:{style,...(children!==undefined?{children}:{})}});
const flex=(style,children)=>h("div",{display:"flex",...style},children);

function parseCSV(text){
  const rows=[];let row=[],f="",q=false;
  for(let i=0;i<text.length;i++){const c=text[i];
    if(q){if(c==='"'){if(text[i+1]==='"'){f+='"';i++;}else q=false;}else f+=c;}
    else{if(c==='"')q=true;else if(c===","){row.push(f);f="";}
      else if(c==="\n"){row.push(f);rows.push(row);row=[];f="";}
      else if(c==="\r"){}else f+=c;}}
  if(f.length||row.length){row.push(f);rows.push(row);}
  const hd=rows.shift()||[];
  return rows.filter(r=>r.some(x=>x!=="")).map(r=>{const o={};hd.forEach((k,i)=>o[k]=r[i]);return o;});
}

const stat=(k,v,c)=>flex({flexDirection:"column",background:"#0b1119",border:`1px solid ${C.line}`,
  borderRadius:16,padding:"16px 24px",flex:1},[
  h("div",{color:C.muted,fontSize:22},k),
  h("div",{color:c||C.text,fontSize:42,fontWeight:800,marginTop:4},v),
]);

function shell(badge,titleTop,titleSub,center,stamps){
  return flex({width:"100%",height:"100%",flexDirection:"column",background:C.bg,color:C.text,
    padding:"44px 60px",fontFamily:"sans-serif"},[
    flex({alignItems:"center"},[
      h("div",{fontSize:30,fontWeight:800,letterSpacing:2},"THEPICKLOG"),
      h("div",{color:C.muted,fontSize:24,marginLeft:14},"thepicklog.com"),
      flex({marginLeft:"auto",border:`1px solid ${C.line}`,borderRadius:999,padding:"8px 20px",
        color:C.muted,fontSize:22,fontWeight:800,letterSpacing:2},[badge]),
    ]),
    flex({flexDirection:"column",marginTop:22},[
      h("div",{fontSize:60,fontWeight:800,lineHeight:1.05},titleTop),
      h("div",{color:C.muted,fontSize:26,marginTop:10},titleSub),
    ]),
    center,
    flex({marginTop:"auto",flexDirection:"column"},[
      h("div",{color:C.text,fontSize:22},stamps),
      h("div",{color:C.muted,fontSize:20,marginTop:10},"Simulated (paper) - research, not advice - verify at thepicklog.com"),
    ]),
  ]);
}

function pickCard(pick,oc){
  const graded=oc&&oc.graded_at;
  const ticker=pick.ticker||(oc&&oc.ticker)||"—";
  let center;
  if(graded){
    center=flex({flexDirection:"column",marginTop:20},[
      flex({alignItems:"baseline"},[
        h("div",{fontSize:80,fontWeight:800,color:col(oc.ret_open_close_net)},pct(oc.ret_open_close_net)),
        h("div",{color:C.muted,fontSize:24,marginLeft:18},"same-day open close (net) - graded result"),
      ]),
      flex({marginTop:20,gap:16},[
        stat("Peaked at (5d)",pct(oc.mfe_5d),col(oc.mfe_5d)),
        stat("If held 5 days",pct(oc.ret_open_5dclose_net),col(oc.ret_open_5dclose_net)),
        stat("Worst dip (5d)",pct(oc.mae_5d),col(oc.mae_5d)),
      ]),
    ]);
  }else{
    center=flex({flexDirection:"column",marginTop:40},[
      flex({background:"#2a2410",border:"1px solid #5a4a22",borderRadius:999,padding:"12px 26px",
        color:C.amber,fontSize:30,fontWeight:800,alignSelf:"flex-start"},["LIVE - grading pending"]),
      h("div",{color:C.muted,fontSize:26,marginTop:24},"Frozen before the outcome is known. Graded in the open, win or lose."),
    ]);
  }
  const stamps=graded
    ? `Frozen ${fmtDate(pick.published_at)} - graded ${fmtDate(oc.graded_at)} - nobody can edit this`
    : `Frozen ${fmtDate(pick.published_at)} - nobody can edit this`;
  return shell("PICK",ticker,`low-float ignition - tier ${pick.tier||"?"} - score ${pick.score||"?"}`,center,stamps);
}

function ruleCard(row,lb){
  const baseAvg=(row.baseline_avg_post!=null)?row.baseline_avg_post:(lb&&lb.baseline&&lb.baseline.avg_post);
  const center=flex({flexDirection:"column",marginTop:18},[
    flex({alignItems:"baseline"},[
      h("div",{fontSize:80,fontWeight:800,color:col(row.delta_post)},pct(row.delta_post)),
      h("div",{color:C.muted,fontSize:24,marginLeft:18},"vs baseline, out-of-sample"),
    ]),
    flex({marginTop:18,gap:16},[
      stat("OOS picks",String(row.n_post),C.text),
      stat("Win rate",row.win_post+"%",C.text),
      stat("Expectancy",pct(row.avg_post),col(row.avg_post)),
    ]),
    h("div",{color:row.significant?C.blue:C.amber,fontSize:22,marginTop:14},
      row.significant?"95% interval clears zero.":"Directional, not proven - 95% interval still spans zero."),
  ]);
  return shell("RULE",row.title,`${row.rule_str||""} - by ${row.author||"—"}`,center,
    `Registered ${fmtDate(row.registered_at)} - graded through ${fmtDate(lb&&lb.generated_at)}`);
}

export default async function handler(request){
  try{
    const url=new URL(request.url);
    const origin=url.origin;
    let raw=(url.searchParams.get("id")||"").trim();
    if(!raw) return new Response("missing id",{status:400});
    const cleaned=raw.replace(/^([pch])-/i,"");
    const opts={width:1200,height:630};

    const lbRes=await fetch(`${origin}/leaderboard.json`).catch(()=>null);
    const lb=lbRes&&lbRes.ok?await lbRes.json():null;
    if(lb&&Array.isArray(lb.rows)){
      const row=lb.rows.find(r=>String(r.id).toLowerCase()===raw.toLowerCase()||String(r.id).toLowerCase()===cleaned.toLowerCase());
      if(row) return new ImageResponse(ruleCard(row,lb),opts);
    }
    const picksRes=await fetch(`${origin}/picks.csv`);
    const picks=parseCSV(await picksRes.text());
    const pick=picks.find(p=>p.pick_id===raw||p.pick_id===cleaned);
    if(pick){
      const ocRes=await fetch(`${origin}/outcomes.csv`).catch(()=>null);
      const ocs=ocRes&&ocRes.ok?parseCSV(await ocRes.text()):[];
      const oc=ocs.find(o=>o.pick_id===pick.pick_id)||null;
      return new ImageResponse(pickCard(pick,oc),opts);
    }
    return new Response("not found",{status:404});
  }catch(e){ return new Response("og failed: "+e.message,{status:502}); }
}
