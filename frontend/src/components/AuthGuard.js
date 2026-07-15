"use client";
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function AuthGuard({ children }) {
    const router = useRouter();
    const [isAuthed, setIsAuthed] = useState(false);
    
    useEffect(() => {
        const userStr = localStorage.getItem('gc_user');
        if (!userStr) {
            router.push('/login');
        } else {
            const t = setTimeout(() => setIsAuthed(true), 0);
            return () => clearTimeout(t);
        }
    }, [router]);
    
    if (!isAuthed) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-white text-[#111111]">
                <div className="w-8 h-8 border-4 border-[#111111] border-t-transparent rounded-full animate-spin mb-4"></div>
                <div className="animate-pulse font-bold tracking-widest uppercase text-[10px] text-[#666666]">
                    Authenticating...
                </div>
            </div>
        );
    }
    
    return <>{children}</>;
}
