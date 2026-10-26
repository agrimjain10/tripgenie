"use client";
import Link from 'next/link';
import {ArrowUpRight,CalendarDays,MapPin,Users} from 'lucide-react';
import {Trip,niceDate,money,titleOf} from '@/lib/api';
import {photoFor} from '@/lib/destinations';
export default function TripCard({trip}:{trip:Trip}){return <Link className="trip-card" href={'/trips/'+trip.id}><div className="trip-card-cover"><img src={photoFor(trip.destination)} alt={trip.destination}/><span className={'status-badge '+trip.status}>{trip.status==='generating'?'Planning':trip.status==='updating'?'Updating':trip.status==='planned'?'Ready to go':trip.status==='archived'?'Archived':'Draft'}</span><span className="trip-arrow"><ArrowUpRight size={18}/></span></div><div className="trip-card-body"><span className="trip-place"><MapPin size={12}/>{trip.destination}</span><h3>{titleOf(trip)}</h3><p><CalendarDays size={13}/>{niceDate(trip.start_date)} – {niceDate(trip.end_date)}</p><div className="trip-card-bottom"><span><Users size={13}/>{trip.travelers} traveler{trip.travelers!==1?'s':''}</span><strong>{money(trip.budget)}</strong></div></div></Link>;}
