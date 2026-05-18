import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata = {
  title: "Axiom AI – Intelligent Rule-Based Chatbot",
  description: "Axiom AI is a professional full-stack conversational AI built on NLP logic, Flask, MongoDB, and Next.js. Powered by the DecodeLabs training program.",
  keywords: "Axiom AI, chatbot, NLP, rule-based, Flask, Next.js, MongoDB",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${inter.variable} h-screen max-h-screen overflow-hidden antialiased`} suppressHydrationWarning>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
      </head>
      <body className="h-screen max-h-screen overflow-hidden flex flex-col font-sans" suppressHydrationWarning>{children}</body>
    </html>
  );
}
