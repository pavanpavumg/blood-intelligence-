import React from 'react';
import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4 text-center">
      <h2 className="text-2xl font-black text-slate-800 mb-2">Page Not Found</h2>
      <p className="text-xs text-slate-500 mb-4">The requested health report page could not be located.</p>
      <Link href="/" className="px-4 py-2 bg-blue-600 text-white font-bold text-xs rounded-xl shadow-xs">
        Return to Report Viewer
      </Link>
    </div>
  );
}
