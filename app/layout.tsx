import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Webook Ingestion Platform | Console",
  description:
    "High-fidelity Webook inventory harvesting, taxonomy derivation, and reservation orchestration.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=IBM+Plex+Sans+Arabic:wght@400;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-[#0b0f19] text-[#e2e8f0] font-['Outfit',sans-serif] antialiased selection:bg-blue-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
