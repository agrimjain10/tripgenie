"use client";
import {useEffect,useState} from 'react';
import {ImagePlus,Loader2,Sparkles,X} from 'lucide-react';
import {request,Trip} from '@/lib/api';
import {photoFor} from '@/lib/destinations';
type Visual={available:boolean;image:string|null;label:string;state:string};
export default function TripCover({trip}:{trip:Trip}){
 const [visual,setVisual]=useState<Visual|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 useEffect(()=>{let active=true;setVisual(null);setError('');request<Visual>('/api/trips/'+trip.id+'/visual').then(value=>{if(active)setVisual(value);}).catch(()=>{});return()=>{active=false;};},[trip.id]);
 async function create(){setBusy(true);setError('');try{setVisual(await request<Visual>('/api/trips/'+trip.id+'/visual',{method:'POST',signal:AbortSignal.timeout(55000)}));}catch(error){setError(error instanceof Error?error.message:'The image could not be created.');}finally{setBusy(false);}}
 return <><img className="trip-cover-image" src={visual?.image||photoFor(trip.destination)} alt={visual?.image?'AI-generated travel inspiration for '+trip.destination:trip.destination+' — travel inspiration'}/><div className="trip-cover-control">{visual?.image?<span><Sparkles size={12}/>AI-generated inspiration</span>:<button type="button" onClick={create} disabled={busy||visual?.available===false}><span>{busy?<Loader2 size={13} className="spin"/>:<ImagePlus size={13}/>}</span>{busy?'Creating your destination visual…':'Create AI cover'}</button>}</div>{error&&<div className="visual-error" role="status"><span>{error}</span><button aria-label="Dismiss image message" onClick={()=>setError('')}><X size={14}/></button></div>}</>;
}
