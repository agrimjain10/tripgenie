"use client";
import { ReactNode, useEffect, useRef } from 'react';
import { ArrowUpRight, Compass, Loader2, X } from 'lucide-react';
import Link from 'next/link';
export function notify(message:string,kind:'success'|'error'='success'){window.dispatchEvent(new CustomEvent('trip-toast',{detail:{message,kind}}));}
export function Spinner({label='Loading'}:{label?:string}){return <div className="loading"><Loader2 className="spin" size={22}/><span>{label}</span></div>;}
export function Empty({title,text,href,label='Plan a trip'}:{title:string;text:string;href?:string;label?:string}){return <div className="empty"><span className="empty-icon"><Compass size={27}/></span><h2>{title}</h2><p>{text}</p>{href&&<Link href={href} className="btn primary">{label}<ArrowUpRight size={16}/></Link>}</div>;}
export function Modal({title,open,onClose,children}:{title:string;open:boolean;onClose:()=>void;children:ReactNode}){const ref=useRef<HTMLDialogElement>(null);useEffect(()=>{if(open)ref.current?.showModal();else ref.current?.close();},[open]);return <dialog ref={ref} className="modal" onCancel={onClose} onClick={e=>{if(e.target===e.currentTarget)onClose();}}><div className="modal-head"><h2>{title}</h2><button className="icon-btn" onClick={onClose} aria-label="Close dialog"><X size={19}/></button></div>{children}</dialog>;}
export function SectionTitle({label,title,children}:{label?:string;title:string;children?:ReactNode}){return <div className="section-heading"><div>{label&&<span className="eyebrow">{label}</span>}<h2>{title}</h2></div>{children}</div>;}
