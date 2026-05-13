"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import {
  FaRobot, FaUser, FaPaperPlane, FaHistory, FaTrash,
  FaThumbsUp, FaThumbsDown, FaMicrophone, FaDownload,
  FaSun, FaMoon, FaChevronLeft, FaPlus, FaLightbulb,
  FaMagic, FaCog, FaInfoCircle, FaShieldAlt, FaBrain, FaCheckCircle
} from "react-icons/fa";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { v4 as uuidv4 } from "uuid";

// Utility: strip markdown syntax for plain-text export
const stripMarkdown = (text) => {
  if (!text) return "";
  return text
    .replace(/\*\*(.+?)\*\*/g, "$1")   // bold
    .replace(/\*(.+?)\*/g, "$1")       // italic
    .replace(/`{3}[\s\S]*?`{3}/g, "")  // code blocks
    .replace(/`(.+?)`/g, "$1")         // inline code
    .replace(/#{1,6}\s/g, "")          // headings
    .replace(/!\[.*?\]\(.*?\)/g, "")   // images
    .replace(/\[(.+?)\]\(.*?\)/g, "$1") // links
    .replace(/^[>\-\*]\s/gm, "")       // blockquotes & lists
    .replace(/\n{3,}/g, "\n\n")        // excess newlines
    .trim();
};

/* ─────────────────────────  Sub-Components  ───────────────────────── */

function TypingEffect({ text, onComplete }) {
  const [displayed, setDisplayed] = useState("");
  const [i, setI] = useState(0);
  useEffect(() => {
    if (text && i < text.length) {
      const t = setTimeout(() => {
        setDisplayed((p) => p + text.charAt(i));
        setI((p) => p + 1);
      }, 4);
      return () => clearTimeout(t);
    } else if (onComplete) onComplete();
  }, [i, text, onComplete]);
  return (
    <div className="prose dark:prose-invert max-w-none prose-p:leading-relaxed">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayed}</ReactMarkdown>
    </div>
  );
}

/* ─────────────────────────  Suggested Prompts  ────────────────────── */
const SUGGESTED = [
  { icon: "💬", label: "Who are you?", sub: "Learn about Axiom AI" },
  { icon: "⚡", label: "What are your features?", sub: "Explore capabilities" },
  { icon: "😄", label: "Tell me a joke", sub: "Lighten the mood" },
  { icon: "🧠", label: "How do rules work?", sub: "Understand the engine" },
];

/* ─────────────────────────  Main Component  ───────────────────────── */
export default function Home() {
  const [messages, setMessages]     = useState([]);
  const [input, setInput]           = useState("");
  const [isLoading, setIsLoading]   = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isDark, setIsDark]         = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showInfo, setShowInfo]     = useState(false);
  const [showAlert, setShowAlert]   = useState(null);
  const [sessions, setSessions]     = useState([]);
  const [sessionId, setSessionId]   = useState("");
  const [sessionToDelete, setSessionToDelete] = useState(null);
  const [dbStatus, setDbStatus]     = useState("checking");
  const bottomRef = useRef(null);

  /* ── Init ── */
  useEffect(() => {
    let sid = localStorage.getItem("axiom_sid");
    if (!sid) { sid = uuidv4(); localStorage.setItem("axiom_sid", sid); }
    setSessionId(sid);
    if (localStorage.getItem("axiom_theme") === "light") setIsDark(false);
    if (window.innerWidth < 1024) setSidebarOpen(false);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
    localStorage.setItem("axiom_theme", isDark ? "dark" : "light");
  }, [isDark]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  /* ── API helpers ── */
  const fetchSessions = useCallback(async () => {
    try { 
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
      const r = await axios.get(`${API_URL}/sessions`); 
      setSessions(r.data);
      setDbStatus("connected");
    }
    catch (e) { 
      console.warn("Sessions unavailable", e); 
      setDbStatus("disconnected");
    }
  }, []);

  useEffect(() => { if (sessionId) fetchSessions(); }, [sessionId, fetchSessions]);

  const loadSession = async (sid) => {
    try {
      setIsLoading(true);
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
      const r = await axios.get(`${API_URL}/history?session_id=${sid}`);
      setSessionId(sid);
      localStorage.setItem("axiom_sid", sid);
      const msgs = r.data.flatMap((m) => [
        { role: "user", text: m.message, id: m._id + "_u" },
        { role: "bot",  text: m.response, id: m._id + "_b", userQuery: m.message, feedback: m.feedback },
      ]);
      setMessages(msgs);
    } catch (e) { console.error("Load session failed", e); }
    finally { setIsLoading(false); }
  };

  const deleteSession = (e, sid) => {
    e.stopPropagation();
    setSessionToDelete(sid);
  };

  const confirmDelete = async () => {
    if (!sessionToDelete) return;
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
      await axios.delete(`${API_URL}/sessions/${sessionToDelete}`);
      if (sessionId === sessionToDelete) startNewChat(false);
      fetchSessions();
    } catch (e) { console.error("Delete failed", e); }
    finally { setSessionToDelete(null); }
  };

  const handleFeedback = async (query, type, idx) => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
      await axios.post(`${API_URL}/feedback`, { message: query, session_id: sessionId, feedback: type });
      setMessages((prev) => { const n = [...prev]; n[idx] = { ...n[idx], feedback: type }; return n; });
    } catch (e) { console.error("Feedback failed", e); }
  };

  /* ── Actions ── */
  const exportChat = () => {
    if (!messages.length) {
      setShowAlert("No messages to export! Start a conversation first.");
      return;
    }
    
    // Build the text content
    const dateStr = new Date().toLocaleString();
    let content = `AXIOM AI CHAT EXPORT\n`;
    content += `Generated: ${dateStr}\n`;
    content += `Session ID: ${sessionId}\n`;
    content += `==========================================\n\n`;
    
    messages.forEach((m) => {
      const role = m.role === "user" ? "USER" : "AXIOM AI";
      const cleanText = stripMarkdown(m.text);
      content += `[${role}]\n${cleanText}\n\n`;
    });
    
    content += `==========================================\n`;
    content += `End of Export - ${messages.length} message(s) exported`;
    
    // Standard filename without complex characters
    const filename = `Axiom_Export_${new Date().getTime()}.txt`;
    
    // Create blob with BOM for Windows encoding recognition
    const blob = new Blob(["\ufeff", content], { type: 'text/plain;charset=utf-8' });
    
    // Create a temporary link and trigger download
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.style.display = 'none';
    link.href = url;
    link.download = filename;
    
    document.body.appendChild(link);
    link.click();
    
    // Cleanup
    setTimeout(() => {
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    }, 100);
    
    setShowAlert("Exported! Check your downloads folder for '" + filename + "'.");
  };

  const startListening = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return alert("Voice input not supported.");
    const r = new SR();
    r.onstart = () => setIsListening(true);
    r.onend   = () => setIsListening(false);
    r.onresult = (e) => setInput(e.results[0][0].transcript);
    r.start();
  };

  const startNewChat = (andFetch = true) => {
    const sid = uuidv4();
    setSessionId(sid);
    localStorage.setItem("axiom_sid", sid);
    setMessages([]);
    if (andFetch) fetchSessions();
  };

  const sendMessage = async (e, override) => {
    if (e) e.preventDefault();
    const text = (override || input).trim();
    if (!text || isLoading) return;
    setMessages((p) => [...p, { role: "user", text, id: uuidv4() }]);
    setInput("");
    setIsLoading(true);
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
      const res = await axios.post(`${API_URL}/chat`, { message: text, session_id: sessionId });
      setMessages((p) => [...p, { 
        role: "bot", 
        text: res.data.response, 
        id: uuidv4(), 
        isNew: true, 
        userQuery: text,
        source: res.data.source 
      }]);
      fetchSessions();
    } catch {
      setMessages((p) => [...p, { role: "bot", text: "⚠️ Could not reach the server. Please try again.", id: uuidv4(), isNew: true }]);
    } finally {
      setIsLoading(false);
    }
  };

  /* ── Styles ── */
  const bg  = isDark ? "bg-slate-950 text-slate-100" : "bg-slate-50 text-slate-900";
  const sb  = isDark ? "bg-slate-900/60 border-slate-800" : "bg-white border-slate-200";
  const hdr = isDark ? "border-slate-800/30 bg-slate-950/50" : "border-slate-200/50 bg-white/60";
  const inp = isDark ? "bg-slate-900 border-slate-800 focus-within:border-indigo-500/60" : "bg-white border-slate-200 focus-within:border-indigo-400";
  const ftr = isDark ? "bg-slate-950/80 border-slate-800/30" : "bg-white/90 border-slate-200/50";
  const bot = isDark ? "bg-slate-900 border border-slate-800 text-slate-100 rounded-2xl rounded-tl-none shadow-2xl" : "bg-slate-100/80 border border-slate-200 shadow-xl shadow-slate-200/30 text-slate-900 rounded-2xl rounded-tl-none";
  const card = isDark ? "bg-slate-900/50 border-slate-800 hover:border-indigo-500/40 hover:bg-slate-800/60" : "bg-white border-slate-200 hover:border-indigo-300 hover:shadow-lg";

  /* ──────────────────────────  RENDER  ─────────────────────────────── */
  return (
    <div className={`flex h-screen overflow-hidden font-sans transition-colors duration-500 ${bg}`}>

      {/* ── Sidebar ── */}
      <motion.aside
        initial={false}
        animate={{ 
          width: sidebarOpen ? 290 : 0, 
          opacity: sidebarOpen ? 1 : 0,
          x: mobileMenuOpen ? 0 : (window.innerWidth < 1024 ? -290 : 0)
        }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className={`fixed lg:relative h-full border-r shrink-0 overflow-hidden flex flex-col z-40 ${sb}`}
      >
        <div className="p-5 flex flex-col h-full min-w-[290px]">

          {/* Logo */}
          <div className="flex items-center gap-3 mb-7 cursor-pointer" onClick={() => startNewChat()}>
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-500 to-fuchsia-600 flex items-center justify-center shadow-lg shadow-indigo-600/25 animate-glow">
              <FaRobot className="text-white text-lg" />
            </div>
            <div>
              <div className="font-black text-base leading-none tracking-tight">Axiom AI</div>
              <div className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-500 mt-1">Intelligence Engine</div>
            </div>
          </div>

          {/* New Chat */}
          <button
            onClick={() => startNewChat()}
            className="w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl mb-6 font-bold text-sm bg-indigo-600 text-white shadow-lg shadow-indigo-600/25 hover:bg-indigo-700 hover:scale-[1.02] active:scale-[0.97] transition-all"
          >
            <FaPlus size={11} /> New Conversation
          </button>

          {/* Sessions list */}
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            <p className="text-[9px] uppercase font-black tracking-[0.25em] text-slate-500 mb-3 ml-1 opacity-60">Conversations</p>
            <div className="space-y-1">
              {sessions.length === 0
                ? <p className="text-xs text-slate-500 italic ml-1 opacity-50 mt-2">No chats yet. Start one!</p>
                : sessions.map((s) => (
                  <motion.div
                    layout key={s.session_id}
                    onClick={() => loadSession(s.session_id)}
                    className={`group flex items-center gap-3 p-3 rounded-2xl text-xs cursor-pointer transition-all border ${
                      sessionId === s.session_id
                        ? (isDark ? "sidebar-item-active text-indigo-300" : "bg-indigo-50 border-indigo-200 text-indigo-700")
                        : (isDark ? "border-transparent text-slate-400 hover:bg-slate-800/50" : "border-transparent text-slate-600 hover:bg-slate-100")
                    }`}
                  >
                    <FaHistory className={`shrink-0 ${sessionId === s.session_id ? "text-indigo-400" : "text-slate-500"}`} size={10} />
                    <span className="truncate flex-1 font-medium">{s.title}</span>
                    <button
                      onClick={(e) => deleteSession(e, s.session_id)}
                      className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-rose-500/10 hover:text-rose-500 transition-all"
                    >
                      <FaTrash size={9} />
                    </button>
                  </motion.div>
                ))
              }
            </div>
          </div>

          {/* Footer buttons */}
          <div className="mt-4 pt-4 border-t border-slate-800/30 space-y-1">
            <button
              onClick={() => { setIsDark(!isDark); setMobileMenuOpen(false); }}
              className="flex items-center gap-3 w-full p-3 rounded-2xl hover:bg-slate-500/10 text-xs font-bold transition-colors"
            >
              {isDark ? <><FaSun className="text-yellow-400" /> Light Mode</> : <><FaMoon className="text-indigo-500" /> Dark Mode</>}
            </button>
            <button 
              onClick={() => { setShowSettings(true); setMobileMenuOpen(false); }}
              className="flex items-center gap-3 w-full p-3 rounded-2xl hover:bg-slate-500/10 text-xs font-bold transition-colors"
            >
              <FaCog className="text-slate-500" /> Settings
            </button>
          </div>
        </div>
      </motion.aside>

      {/* ── Mobile Overlay ── */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setMobileMenuOpen(false)}
            className="fixed inset-0 bg-black/60 z-30 lg:hidden backdrop-blur-sm"
          />
        )}
      </AnimatePresence>

      {/* ── Main Area ── */}
      <main className="flex-1 flex flex-col relative overflow-hidden">

        {/* Ambient glow orbs */}
        <div className="absolute top-0 right-0 w-[700px] h-[700px] bg-indigo-600/5 blur-[160px] rounded-full -translate-y-1/2 translate-x-1/3 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-[700px] h-[700px] bg-fuchsia-600/5 blur-[160px] rounded-full translate-y-1/2 -translate-x-1/3 pointer-events-none" />

        {/* Header */}
        <header className={`h-[72px] border-b flex items-center justify-between px-8 z-10 backdrop-blur-xl ${hdr}`}>
          <div className="flex items-center gap-5">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className={`hidden lg:block p-2.5 rounded-xl border transition-all ${isDark ? "border-slate-800 hover:bg-slate-800" : "border-slate-200 hover:bg-slate-100"}`}
            >
              <FaChevronLeft className={`transition-transform duration-500 text-sm ${!sidebarOpen ? "rotate-180" : ""}`} />
            </button>
            <button
              onClick={() => setMobileMenuOpen(true)}
              className={`lg:hidden p-2.5 rounded-xl border transition-all ${isDark ? "border-slate-800 hover:bg-slate-800" : "border-slate-200 hover:bg-slate-100"}`}
            >
              <FaRobot className="text-indigo-500 text-sm" />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-black text-sm tracking-tight">Axiom AI  v4.2</span>
                <span className="px-2 py-0.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[8px] font-black uppercase tracking-widest">Alpha</span>
              </div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse inline-block" />
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">System Online</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button 
              onClick={() => setShowInfo(true)}
              className={`p-2.5 rounded-xl transition-all ${isDark ? "text-slate-500 hover:text-white hover:bg-slate-800" : "text-slate-400 hover:text-slate-900 hover:bg-slate-100"}`}
            >
              <FaInfoCircle size={15} />
            </button>
            <div className={`w-px h-5 ${isDark ? "bg-slate-800" : "bg-slate-200"}`} />
            <button
              onClick={exportChat}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-[11px] font-black uppercase tracking-widest transition-all active:scale-95 bg-slate-800 text-white hover:bg-slate-700 shadow-md"
            >
              <FaDownload size={11} /> Export
            </button>
          </div>
        </header>

        {/* Chat / Empty state */}
        <div className="flex-1 overflow-y-auto custom-scrollbar px-6 md:px-12">
          <div className="max-w-4xl mx-auto min-h-full flex flex-col">
            {messages.length === 0 ? (
              /* ── Empty / Welcome ── */
              <div
                className="flex-1 flex flex-col items-center justify-center text-center py-16 space-y-10 animate-in fade-in zoom-in duration-500"
              >
                  {/* Floating robot icon */}
                  <div className="relative">
                    <div className="absolute inset-0 bg-indigo-500/20 blur-3xl rounded-full animate-pulse" />
                    <div className="relative w-24 h-24 rounded-[2rem] bg-gradient-to-br from-indigo-500 to-fuchsia-600 flex items-center justify-center shadow-2xl shadow-indigo-600/30 border border-white/10 animate-float">
                      <FaRobot className="text-white text-4xl" />
                    </div>
                  </div>

                  <div className="max-w-lg space-y-3">
                    <h1 className="text-4xl font-black tracking-tight leading-tight">
                      Hybrid <span className="text-gradient">Intelligence.</span>
                    </h1>
                    <p className={`text-sm leading-relaxed font-medium ${isDark ? "text-slate-400" : "text-slate-500"}`}>
                      Project 1: The Safety of Rule-Based Logic merged with the Power of Google Gemini AI. 
                      Axiom provides deterministic answers for known rules and intelligent fallback for everything else.
                    </p>
                  </div>

                  {/* Suggestion cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl">
                    {SUGGESTED.map((q, i) => (
                      <button
                        key={i}
                        onClick={() => sendMessage(null, q.label)}
                        className={`flex items-start gap-4 p-5 rounded-3xl text-left border transition-all group ${card}`}
                      >
                        <span className="text-2xl mt-0.5 group-hover:scale-110 transition-transform">{q.icon}</span>
                        <div>
                          <div className="text-[9px] font-black uppercase tracking-widest text-indigo-400 mb-1">{q.sub}</div>
                          <div className="text-[13px] font-bold opacity-80 group-hover:opacity-100 transition-opacity">{q.label}</div>
                        </div>
                      </button>
                    ))}
                  </div>
              </div>
            ) : (
                <div className="space-y-10 py-10 w-full flex-1">
                  {messages.map((msg, idx) => (
                    <motion.div
                      key={msg.id || idx}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, ease: "easeOut" }}
                      className={`flex items-start gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
                    >
                      {/* Avatar */}
                      <div className={`w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 shadow-lg border ${
                        msg.role === "bot"
                          ? "bg-gradient-to-br from-indigo-600 to-fuchsia-600 border-white/10 text-white"
                          : isDark ? "bg-slate-800 border-slate-700 text-slate-300" : "bg-white border-slate-200 text-slate-500"
                      }`}>
                        {msg.role === "bot" ? <FaRobot size={16} /> : <FaUser size={14} />}
                      </div>

                      {/* Bubble */}
                      <div className={`flex flex-col gap-2 max-w-[82%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
                        <div className={`p-5 rounded-[1.75rem] text-[15px] leading-relaxed relative group ${
                          msg.role === "user"
                            ? "message-bubble-user text-white rounded-tr-none"
                            : `${bot}`
                        }`}>
                          {msg.role === "bot" && msg.source === "gemini" && (
                            <div className="absolute -top-3 right-4 px-2 py-0.5 bg-indigo-600 text-[8px] font-black text-white rounded-full flex items-center gap-1 shadow-lg border border-white/20">
                              <FaBrain size={8} /> AI ASSISTED
                            </div>
                          )}
                          {msg.role === "bot"
                            ? msg.isNew
                              ? <TypingEffect text={msg.text} />
                              : <div className="prose dark:prose-invert max-w-none"><ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown></div>
                            : <span className="font-medium">{msg.text}</span>
                          }
                        </div>

                        {/* Feedback */}
                        {msg.role === "bot" && msg.userQuery && (
                          <div className="flex items-center gap-2 px-2">
                            <button
                              onClick={() => handleFeedback(msg.userQuery, "up", idx)}
                              className={`p-2 rounded-lg transition-all ${msg.feedback === "up" ? "text-emerald-500 bg-emerald-500/10" : "text-slate-500 hover:text-emerald-500 hover:bg-emerald-500/5"}`}
                            ><FaThumbsUp size={11} /></button>
                            <button
                              onClick={() => handleFeedback(msg.userQuery, "down", idx)}
                              className={`p-2 rounded-lg transition-all ${msg.feedback === "down" ? "text-rose-500 bg-rose-500/10" : "text-slate-500 hover:text-rose-500 hover:bg-rose-500/5"}`}
                            ><FaThumbsDown size={11} /></button>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}

                  {/* Typing indicator */}
                  {isLoading && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-start gap-5">
                      <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-600 to-fuchsia-600 flex items-center justify-center shrink-0 border border-white/10">
                        <FaRobot className="text-white" size={16} />
                      </div>
                      <div className={`px-6 py-4 rounded-[1.75rem] rounded-tl-none flex items-center gap-2 ${isDark ? "bg-slate-900/60 border border-slate-800" : "bg-white border border-slate-200 shadow-lg"}`}>
                        {["-0.3s", "-0.15s", "0s"].map((d, i) => (
                          <div key={i} className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: d }} />
                        ))}
                      </div>
                    </motion.div>
                  )}
                  <div className="h-10 shrink-0" />
                  <div ref={bottomRef} />
                </div>
            )}
          </div>
        </div>

        {/* Input Dock */}
        <div className={`border-t backdrop-blur-2xl z-10 p-6 md:px-12 md:py-6 ${ftr}`}>
          <div className="max-w-3xl mx-auto">
            <form onSubmit={sendMessage}>
              <div className={`flex items-center rounded-3xl border p-2 transition-all shadow-xl focus-within:ring-4 focus-within:ring-indigo-500/10 ${inp}`}>
                <button
                  type="button" onClick={startListening}
                  className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 transition-all ${
                    isListening ? "bg-rose-500 text-white animate-pulse shadow-lg shadow-rose-500/25" : "text-slate-500 hover:text-indigo-400 hover:bg-indigo-500/5"
                  }`}
                >
                  <FaMicrophone size={17} />
                </button>

                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask Axiom AI anything…"
                  className="flex-1 bg-transparent border-none py-4 px-4 focus:outline-none text-[15px] font-medium placeholder:text-slate-600"
                />

                <button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 transition-all ${
                    !input.trim() || isLoading
                      ? "bg-slate-700/30 text-slate-600 cursor-not-allowed"
                      : "bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg shadow-indigo-600/30 hover:scale-105 active:scale-95"
                  }`}
                >
                  <FaPaperPlane size={15} />
                </button>
              </div>
            </form>

            <div className={`flex items-center justify-center gap-5 mt-4 opacity-30 text-[9px] font-black uppercase tracking-[0.2em] ${isDark ? "text-slate-400" : "text-slate-500"}`}>
              <span>NLP Core</span>
              <span className="w-1 h-1 rounded-full bg-current inline-block" />
              <span>MongoDB Atlas</span>
              <span className="w-1 h-1 rounded-full bg-current inline-block" />
              <span>Flask REST</span>
              <span className="w-1 h-1 rounded-full bg-current inline-block" />
              <span>Next.js 15</span>
            </div>
          </div>
        </div>
      </main>

      {/* ── Settings Modal ── */}
      <AnimatePresence>
        {showSettings && (
          <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setShowSettings(false)} className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm" />
            <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }} className={`relative w-full max-w-md p-8 rounded-[2.5rem] shadow-2xl border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`}>
              <h2 className="text-2xl font-black mb-6">System Settings</h2>
              <div className="space-y-6">
                <div className="flex items-center justify-between p-4 rounded-2xl bg-indigo-500/5 border border-indigo-500/10">
                  <div>
                    <div className="text-xs font-black uppercase tracking-widest text-indigo-400 mb-1">Database Status</div>
                    <div className={`text-sm font-bold ${dbStatus === 'connected' ? 'text-emerald-500' : 'text-rose-500'}`}>
                      {dbStatus === 'connected' ? 'MongoDB Atlas Connected' : 'Database Offline (Local Fallback)'}
                    </div>
                  </div>
                  <div className={`w-3 h-3 rounded-full ${dbStatus === 'connected' ? 'bg-emerald-500 shadow-lg shadow-emerald-500/50' : 'bg-rose-500'} animate-pulse`} />
                </div>
                <div className="space-y-4">
                   <div className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Preferences</div>
                   <label className="flex items-center justify-between cursor-pointer group">
                     <span className="text-sm font-bold opacity-70 group-hover:opacity-100 transition-opacity">Dark Mode</span>
                     <input type="checkbox" checked={isDark} onChange={() => setIsDark(!isDark)} className="w-10 h-5 rounded-full appearance-none bg-slate-700 checked:bg-indigo-600 relative transition-all cursor-pointer before:content-[''] before:absolute before:w-3 before:h-3 before:bg-white before:rounded-full before:top-1 before:left-1 checked:before:left-6 before:transition-all" />
                   </label>
                </div>
              </div>
              <button onClick={() => setShowSettings(false)} className="w-full mt-8 py-4 rounded-2xl bg-indigo-600 text-white font-black text-sm shadow-xl shadow-indigo-600/20 hover:bg-indigo-700 transition-all">Close Settings</button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ── Info Modal ── */}
      <AnimatePresence>
        {showInfo && (
          <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setShowInfo(false)} className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm" />
            <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }} className={`relative w-full max-w-lg p-8 rounded-[2.5rem] shadow-2xl border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`}>
              <div className="flex items-center gap-4 mb-6">
                <div className="w-14 h-14 rounded-2xl bg-indigo-600 flex items-center justify-center shadow-xl shadow-indigo-600/20">
                  <FaInfoCircle className="text-white text-2xl" />
                </div>
                <div>
                  <h2 className="text-2xl font-black">About Axiom AI</h2>
                  <p className="text-[10px] font-black uppercase tracking-widest text-indigo-400">Project Version 4.2.0</p>
                </div>
              </div>
              <div className={`text-sm leading-relaxed space-y-4 mb-8 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                <p>Axiom AI is a **Hybrid Intelligence System** that prioritizes safety and accuracy.</p>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { l: 'Rules (Safety)', i: <FaShieldAlt /> },
                    { l: 'Gemini (Depth)', i: <FaBrain /> },
                    { l: 'Deterministic', i: <FaCheckCircle /> },
                    { l: 'Context Aware', i: <FaMagic /> }
                  ].map(f => (
                    <div key={f.l} className="flex items-center gap-2 p-3 rounded-xl bg-slate-500/5 border border-slate-500/10 text-[11px] font-bold">
                      <span className="text-indigo-500">{f.i}</span> {f.l}
                    </div>
                  ))}
                </div>
                <p className="text-[11px] italic opacity-70 border-l-2 border-indigo-500 pl-4 py-1">When a specific rule isn't found, Axiom intelligently leverages the Google Gemini LLM to provide the most helpful response possible.</p>
              </div>
              <button onClick={() => setShowInfo(false)} className="w-full py-4 rounded-2xl bg-slate-800 text-white font-black text-sm hover:bg-slate-700 transition-all">Understood</button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ── Notification Alert Modal ── */}
      <AnimatePresence>
        {showAlert && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center px-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setShowAlert(null)} className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm" />
            <motion.div initial={{ scale: 0.9, opacity: 0, y: 20 }} animate={{ scale: 1, opacity: 1, y: 0 }} exit={{ scale: 0.9, opacity: 0, y: 20 }} className={`relative w-full max-w-sm p-8 rounded-[2rem] shadow-2xl border text-center ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`}>
              <div className="w-16 h-16 rounded-full bg-indigo-500/10 flex items-center justify-center mx-auto mb-5 text-indigo-500">
                <FaInfoCircle size={28} />
              </div>
              <h3 className="text-xl font-black mb-2">Notice</h3>
              <p className={`text-sm mb-8 leading-relaxed ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{showAlert}</p>
              <button onClick={() => setShowAlert(null)} className="w-full py-4 rounded-2xl bg-indigo-600 text-white font-black text-sm hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-600/20 active:scale-95">Dismiss</button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ── Custom Delete Modal ── */}
      <AnimatePresence>
        {sessionToDelete && (
          <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
            <motion.div 
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setSessionToDelete(null)}
              className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm"
            />
            <motion.div 
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              className={`relative w-full max-w-sm p-6 rounded-3xl shadow-2xl border z-10 ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`}
            >
              <div className="w-12 h-12 rounded-full bg-rose-500/10 flex items-center justify-center mb-4 text-rose-500">
                <FaTrash size={20} />
              </div>
              <h3 className="text-xl font-bold mb-2">Delete Conversation</h3>
              <p className={`text-sm mb-6 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                Are you sure you want to permanently delete this chat? This action cannot be undone.
              </p>
              <div className="flex items-center justify-end gap-3">
                <button 
                  onClick={() => setSessionToDelete(null)}
                  className={`px-5 py-2.5 rounded-xl font-bold text-sm transition-all ${isDark ? 'hover:bg-slate-800 text-slate-300' : 'hover:bg-slate-100 text-slate-600'}`}
                >
                  Cancel
                </button>
                <button 
                  onClick={confirmDelete}
                  className="px-5 py-2.5 rounded-xl font-bold text-sm bg-rose-500 text-white hover:bg-rose-600 transition-all shadow-lg shadow-rose-500/25 active:scale-95"
                >
                  Delete
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
