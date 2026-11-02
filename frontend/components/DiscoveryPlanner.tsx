"use client";

import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowUpRight, Check, Clock3, Compass, LocateFixed, MapPin, Route, Users, Wallet, X } from 'lucide-react';
import { money, request } from '@/lib/api';
import { useUser } from '@/components/AppShell';

type Inputs = { origin:string; days:number; travelers:number; budget:number; travel_mode:string; interests:string[]; start_date:string; pace:string; language:string };
type Escape = { name:string;region:string;image:string;tags:string[];highlights:string[];distance_km:number;one_way_hours:number;usable_hours:number;estimated_total:number;cost_range:number[];within_budget:boolean;match_reasons:string[];score:number;railhead:string;budget_breakdown:Record<string,number> };
type Matches = { origin:string;results:Escape[];message:string;within_budget_count:number;estimate_note:string };
const styles=['Nature','Food','History','Adventure','Beaches','Culture','Photography','Wellness','Markets','Nightlife'];
const initial:Inputs={origin:'',days:3,travelers:2,budget:15000,travel_mode:'Flexible',interests:['Nature','Food'],start_date:'',pace:'Balanced',language:'English'};
function startDate(){const date=new Date();date.setDate(date.getDate()+1);return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;}
export default function DiscoveryPlanner(){
  const {user}=useUser();
  const [form,setForm]=useState<Inputs>(initial);
  const [origins,setOrigins]=useState<string[]>([]);
  const [matches,setMatches]=useState<Matches|null>(null);
  const [submitted,setSubmitted]=useState<Inputs|null>(null);
  const [busy,setBusy]=useState(false);
  const [locating,setLocating]=useState(false);
  const [error,setError]=useState('');
  const [locationNote,setLocationNote]=useState('');
  const [sort,setSort]=useState('match');
  const [compare,setCompare]=useState<string[]>([]);
  useEffect(()=>{
    setForm(previous=>({...previous,start_date:startDate()}));
    request<{origins:string[]}>('/api/discovery/catalog').then(c=>setOrigins(c.origins)).catch(()=>{});
  },[]);
  useEffect(()=>{if(user?.preferences)setForm(previous=>({...previous,pace:user.preferences.pace||previous.pace}));},[user]);
  function change<K extends keyof Inputs>(key:K,value:Inputs[K]){setForm(previous=>({...previous,[key]:value}));setError('');}
  async function locate(){
    setError('');setLocationNote('');
    if(!navigator.geolocation){setError('Location is unavailable in this browser. Enter your starting city.');return;}
    setLocating(true);
    navigator.geolocation.getCurrentPosition(async position=>{
      try{
        const result=await request<{name:string;message:string}>('/api/discovery/location',{method:'POST',body:JSON.stringify({latitude:Math.round(position.coords.latitude*10)/10,longitude:Math.round(position.coords.longitude*10)/10})});
        change('origin',result.name);setLocationNote(result.message);
      }catch(e){setError(e instanceof Error?e.message:'Enter your city manually.');}finally{setLocating(false);}
    },()=>{setLocating(false);setError('Location was not shared or could not be found. You can enter your city manually.');},{enableHighAccuracy:false,timeout:10000,maximumAge:300000});
  }
  async function find(e:FormEvent){
    e.preventDefault();setBusy(true);setError('');
    const input={...form,interests:[...form.interests]};
    try{const result=await request<Matches>('/api/discovery/suggest',{method:'POST',body:JSON.stringify(input)});setMatches(result);setSubmitted({...input,origin:result.origin});setCompare([]);}
    catch(e){setError(e instanceof Error?e.message:'Could not find getaways. Please try again.');}
    finally{setBusy(false);}
  }
  function planUrl(place:Escape){
    if(!submitted)return '/trips/new';
    const end=new Date(submitted.start_date+'T12:00:00');end.setDate(end.getDate()+submitted.days-1);
    const endDate=`${end.getFullYear()}-${String(end.getMonth()+1).padStart(2,'0')}-${String(end.getDate()).padStart(2,'0')}`;
    return '/trips/new?'+new URLSearchParams({destination:place.name,origin:submitted.origin,start_date:submitted.start_date,end_date:endDate,travelers:String(submitted.travelers),budget:String(submitted.budget),travel_mode:submitted.travel_mode,pace:submitted.pace,language:submitted.language,interests:submitted.interests.map(value=>value==='Food'?'Local food':value).join(', '),trip_brief:`${submitted.travelers===1?'Solo travel':'Group trip'}. Discovery shortlist: ${place.highlights.join(', ')}. Preferred mode: ${submitted.travel_mode}. Include realistic return travel, meal/rest stops, hotel-night accounting and local transfers. Match the ${submitted.days}-day total window; do not add travel outside these dates.`});
  }
  const results=matches?[...matches.results].sort((a,b)=>sort==='cost'?a.estimated_total-b.estimated_total:sort==='time'?a.one_way_hours-b.one_way_hours:b.score-a.score):[];
  const compared=results.filter(item=>compare.includes(item.name));
  return <section className="discovery-planner" id="find-my-escape">
    <div className="discovery-intro"><span className="eyebrow">A LITTLE TIME. A WORLD OF POSSIBILITIES.</span><h2>Tell us what you have.<br/><em>We’ll find where it can take you.</em></h2><p>A free weekend, a few friends, a budget. That’s enough to start.</p></div>
    <form className="escape-form panel" onSubmit={find}>
      <div className="escape-form-top"><span className="section-kicker"><Compass size={18}/>Find my escape</span><Link className="text-link" href="/trips/new">Already know where?<ArrowUpRight size={15}/></Link></div>
      <div className="escape-inputs">
        <label className="field escape-origin">Starting city<div className="location-input"><MapPin size={17}/><input list="escape-cities" value={form.origin} onChange={e=>change('origin',e.target.value)} placeholder="Delhi, Jalandhar, Bengaluru…" required minLength={2} maxLength={120}/><button type="button" onClick={locate} disabled={locating} aria-label="Use my approximate current location" title="Use my approximate current location"><LocateFixed className={locating?'spin':''} size={18}/></button></div></label>
        <datalist id="escape-cities">{origins.map(city=><option key={city} value={city}/>)}</datalist>
        <label className="field">Leaving on<input type="date" required value={form.start_date} onChange={e=>change('start_date',e.target.value)}/></label>
        <label className="field">Days available<input type="number" min={1} max={21} required value={form.days} onChange={e=>change('days',Number(e.target.value))}/></label>
        <label className="field">Travelers<input type="number" min={1} max={20} required value={form.travelers} onChange={e=>change('travelers',Number(e.target.value))}/><small>{form.travelers===1?'A little time for yourself.':'Total people, including you.'}</small></label>
        <label className="field">Group budget · INR<input type="number" min={500} max={100000000} step={100} required value={form.budget} onChange={e=>change('budget',Number(e.target.value))}/><small>{money(form.budget/Math.max(form.travelers,1))} per person</small></label>
        <label className="field">How you’ll travel<select value={form.travel_mode} onChange={e=>change('travel_mode',e.target.value)}>{['Flexible','Train','Bus','Car','Bike','Flight'].map(mode=><option key={mode}>{mode}</option>)}</select></label>
      </div>
      <p className="field-note">Current location is optional: only rounded coordinates reach our server to find a nearby city. They are not saved or sent to a map provider. Edit the city any time.</p>
      {locationNote&&<p className="location-note" role="status"><LocateFixed size={15}/>{locationNote}</p>}
      <div className="escape-preferences"><div><label className="field">What sounds like you?</label><div className="interest-options">{styles.map(style=><button key={style} type="button" aria-pressed={form.interests.includes(style)} className={form.interests.includes(style)?'selected':''} onClick={()=>change('interests',form.interests.includes(style)?form.interests.filter(i=>i!==style):[...form.interests,style])}>{form.interests.includes(style)&&<Check size={12}/>} {style}</button>)}</div></div><div className="escape-small-fields"><label className="field">Your pace<select value={form.pace} onChange={e=>change('pace',e.target.value)}>{['Easygoing','Balanced','Full of adventure'].map(p=><option key={p}>{p}</option>)}</select></label><label className="field">Plan language<select value={form.language} onChange={e=>change('language',e.target.value)}><option>English</option><option>Hinglish (Roman Hindi)</option></select></label></div></div>
      {error&&<div className="alert error" role="alert">{error}</div>}
      <div className="escape-submit"><p><Clock3 size={15}/>Your days include getting there and coming home.</p><button className="btn primary large" disabled={busy||locating}>{busy?'Finding your kind of somewhere…':'Show my escapes'}<ArrowUpRight size={18}/></button></div>
    </form>
    {matches&&submitted&&<div className="escape-results" aria-live="polite"><div className="escape-results-heading"><div><span className="eyebrow">YOUR SHORTLIST · {submitted.origin.toUpperCase()}</span><h2>{matches.within_budget_count?'Good places. Within reach.':'A little adjustment could open more doors.'}</h2><p>{submitted.days} days · {submitted.travelers===1?'Solo':submitted.travelers+' travelers'} · {money(submitted.budget)} · {submitted.travel_mode}</p></div><label className="field compact-field">Sort by<select value={sort} onChange={e=>setSort(e.target.value)}><option value="match">Best match</option><option value="cost">Lowest estimate</option><option value="time">Least travel</option></select></label></div><p className={matches.within_budget_count?'field-note':'alert'}>{matches.message}</p>
      <div className="escape-grid">{results.map((place,index)=><article className="escape-card" key={place.name}><div className="escape-card-photo"><img src={place.image} loading="lazy" alt="Travel landscape inspiration"/><span className="escape-label">{!place.within_budget?'Stretch option':index===0&&sort==='match'?'Our first pick':'Within reach'}</span><button type="button" className={'compare-btn '+(compare.includes(place.name)?'selected':'')} aria-pressed={compare.includes(place.name)} disabled={compare.length>=3&&!compare.includes(place.name)} onClick={()=>setCompare(previous=>previous.includes(place.name)?previous.filter(n=>n!==place.name):[...previous,place.name])}>{compare.includes(place.name)?<Check size={13}/>:null}Compare</button></div><div className="escape-card-body"><span className="eyebrow">{place.region}</span><h3>{place.name}</h3><div className="escape-metrics"><span><Route size={14}/>{place.one_way_hours}h each way</span><span><Clock3 size={14}/>{place.usable_hours}h to explore</span></div><p className="escape-highlights">{place.highlights.join(' · ')}</p><ul className="match-reasons">{place.match_reasons.map(reason=><li key={reason}><Check size={12}/>{reason}</li>)}</ul><div className="escape-price"><div><small>Estimated group trip</small><strong>{money(place.cost_range[0])}–{money(place.cost_range[1])}</strong><span>Travel, stay, food & buffer · rough range</span></div></div><Link className="btn primary full" href={planUrl(place)}>Make this our trip<ArrowUpRight size={16}/></Link></div></article>)}</div>
      {compared.length>0&&<section className="escape-compare panel"><div className="escape-form-top"><h3>Your side-by-side shortlist</h3><button className="text-link" onClick={()=>setCompare([])}><X size={14}/>Clear</button></div><div className="comparison-scroll"><table><thead><tr><th>Destination</th><th>One-way travel</th><th>Time to explore</th><th>Group estimate</th><th/></tr></thead><tbody>{compared.map(place=><tr key={place.name}><th>{place.name}</th><td>{place.one_way_hours} hours</td><td>{place.usable_hours} daytime hours</td><td>{money(place.estimated_total)}</td><td><Link className="text-link" href={planUrl(place)}>Choose<ArrowUpRight size={14}/></Link></td></tr>)}</tbody></table></div></section>}
      <p className="estimate-note"><Wallet size={17}/>{matches.estimate_note} Photographs are destination or landscape inspiration.</p>
    </div>}
  </section>;
}
