import React from 'react';
import './globals.css';

export const metadata = {
  title: 'Tez SmartApp - Smart Health Report Viewer',
  description: 'Interactive patient-friendly health report viewer with organ map, wellness score, and plain language explanations.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-100 text-slate-900 antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
