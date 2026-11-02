"use client";
import {useEffect,useState} from 'react';
import {Palette} from 'lucide-react';
export default function ThemePicker(){
  const [theme,setTheme]=useState('sand');
  useEffect(()=>{try{const saved=localStorage.getItem('wandiamo.theme');if(saved&&['sand','forest','night'].includes(saved)){setTheme(saved);document.documentElement.dataset.theme=saved;}}catch{}},[]);
  function change(value:string){setTheme(value);document.documentElement.dataset.theme=value;try{localStorage.setItem('wandiamo.theme',value);}catch{}}
  return <label className="theme-picker"><Palette size={15}/><span className="sr-only">Color theme</span><select aria-label="Color theme" value={theme} onChange={event=>change(event.target.value)}><option value="sand">Warm sand</option><option value="forest">Forest green</option><option value="night">After dark</option></select></label>;
}
