"use client";
import {useState} from 'react';
import Link from 'next/link';
import {ArrowUpRight,Search} from 'lucide-react';
import {destinations} from '@/lib/destinations';
import DiscoveryPlanner from '@/components/DiscoveryPlanner';
export default function Explore(){
 const [view,setView]=useState('match');const [search,setSearch]=useState('');
 const filtered=destinations.filter(place=>(place.name+' '+place.region+' '+place.tags.join(' ')).toLowerCase().includes(search.toLowerCase()));
 return <><div className="page-heading"><div><span className="eyebrow">FOLLOW A FEELING. FIND YOUR SOMEWHERE.</span><h1>A little closer to your next escape.</h1><p>Discover India from where you are, with the time and budget you have.</p></div></div><div className="discovery-view-tabs" aria-label="Explore modes"><button className={view==='match'?'active':''} onClick={()=>setView('match')}>Find my escape</button><button className={view==='browse'?'active':''} onClick={()=>setView('browse')}>Browse inspiration</button></div>{view==='match'?<DiscoveryPlanner/>:<><div className="trip-toolbar"><h2>Where would you rather be?</h2><label className="search-input"><Search size={16}/><input aria-label="Search destinations" placeholder="Find a destination" value={search} onChange={event=>setSearch(event.target.value)}/></label></div><div className="explore-grid">{filtered.map(place=><article className="explore-card" key={place.name}><div className="explore-image"><img src={place.image} alt="Destination and landscape inspiration" loading="lazy"/><span>{place.duration}</span></div><div className="explore-body"><span className="eyebrow">{place.region}</span><h2>{place.name}</h2><p>{place.description}</p><div className="tags">{place.tags.map(tag=><span key={tag}>{tag}</span>)}</div><Link href={'/trips/new?destination='+encodeURIComponent(place.name)} className="text-link">Plan a trip here<ArrowUpRight size={16}/></Link></div></article>)}</div>{!filtered.length&&<p className="empty">No destinations match. Try another name, or plan any destination directly.</p>}</>}</>;
}
