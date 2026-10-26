import Link from 'next/link';
export default function NotFound(){return <div className="empty"><h1>This path leads somewhere else.</h1><p>The page you’re looking for isn’t here.</p><Link className="btn primary" href="/dashboard">Back to your workspace</Link></div>;}
