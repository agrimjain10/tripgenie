"use client";
import Link from 'next/link';
export default function ErrorPage({reset}:{reset:()=>void}){return <div className="empty"><h1>A little detour.</h1><p>We couldn’t open this part of your workspace. Your saved trips are still there.</p><button className="btn primary" onClick={reset}>Try again</button><Link className="text-link" href="/dashboard">Back to overview</Link></div>;}
