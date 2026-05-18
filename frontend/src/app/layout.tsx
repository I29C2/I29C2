// frontend/src/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Navigation } from "@/components/Navigation";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "BetBot AI — AI-Powered Sports Betting Analysis",
  description:
    "Advanced AI football predictions, value bets, integrity monitoring, and bankroll management.",
  keywords: ["sports betting", "football predictions", "AI analysis", "value bets"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} font-sans bg-slate-900 text-white min-h-screen flex flex-col`}
      >
        <Providers>
          <Navigation />
          <main className="flex-1">{children}</main>
          <footer className="border-t border-slate-800 py-6 mt-12">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-blue-400 font-bold text-lg">BetBot AI</span>
                  <span className="text-slate-500 text-sm">
                    &copy; {new Date().getFullYear()}
                  </span>
                </div>
                <div className="flex gap-6 text-sm text-slate-500">
                  <a href="/privacy" className="hover:text-slate-300 transition-colors">
                    Privacy Policy
                  </a>
                  <a href="/terms" className="hover:text-slate-300 transition-colors">
                    Terms of Service
                  </a>
                  <a href="/responsible-gambling" className="hover:text-slate-300 transition-colors">
                    Responsible Gambling
                  </a>
                </div>
              </div>
              <div className="mt-4 text-center text-xs text-slate-600">
                ⚠️{" "}
                <strong className="text-slate-500">18+ only.</strong> This platform
                provides AI-generated analysis for informational purposes only. It does
                not constitute financial or betting advice. Please gamble responsibly.
                If gambling is affecting you or someone you know, visit{" "}
                <a
                  href="https://www.begambleaware.org"
                  className="text-blue-600 hover:underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  BeGambleAware.org
                </a>
                .
              </div>
            </div>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
