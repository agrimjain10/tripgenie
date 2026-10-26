import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import AppShell from '@/components/AppShell';
const inter=Inter({subsets:['latin'],display:'swap'});
export const metadata:Metadata={title:'TripGenie — More moments. Less planning.',description:'Your personal travel workspace. Plan thoughtful itineraries, organize expenses, and keep every detail together.'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en" suppressHydrationWarning data-scroll-behavior="smooth"><body className={inter.className}><AppShell>{children}</AppShell></body></html>;}
