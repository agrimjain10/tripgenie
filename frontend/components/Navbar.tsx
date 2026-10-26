"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export default function Navbar() {
  const [loggedIn, setLoggedIn] = useState(false);
  useEffect(() => {
    setLoggedIn(Boolean(localStorage.getItem("token")));
    const sync = () => setLoggedIn(Boolean(localStorage.getItem("token")));
    window.addEventListener("storage", sync);
    return () => window.removeEventListener("storage", sync);
  }, []);

  function logout() {
    localStorage.removeItem("token");
    setLoggedIn(false);
    window.location.href = "/";
  }

  return <header className="navbar"><div className="nav-inner">
    <Link href="/" className="brand"><span className="brand-mark">T</span><span>tripgenie</span></Link>
    <nav className="nav-links" aria-label="Main navigation">
      {loggedIn ? <><Link href="/dashboard">My trips</Link><Link href="/trips/new" className="nav-plan-link">Plan a trip <span aria-hidden="true">→</span></Link><button className="nav-button" onClick={logout}>Log out</button></> : <><Link href="/login">Log in</Link><Link href="/register" className="nav-plan-link">Get started <span aria-hidden="true">→</span></Link></>}
    </nav>
  </div></header>;
}

