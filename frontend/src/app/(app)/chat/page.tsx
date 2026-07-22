"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import {
  MessageSquare,
  Send,
  Plus,
  Trash2,
  Loader2,
  Bot,
  User,
  BookOpen,
  X,
  ChevronDown,
  FileText,
} from "lucide-react";
import { api } from "@/lib/api";
import { ChatSession, Message, Document } from "@/types";
import { ChatMessageContent } from "@/components/chat/ChatMessageContent";

export default function ChatPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [showNewChat, setShowNewChat] = useState(false);
  const [newChatTitle, setNewChatTitle] = useState("");
  const [newChatDocId, setNewChatDocId] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () =>
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    fetchSessions();
    api
      .get<{ documents: Document[] }>("/documents")
      .then((d) => setDocuments(d.documents.filter((doc) => doc.status === "ready")));
  }, []);

  const fetchSessions = async () => {
    try {
      const data = await api.get<ChatSession[]>("/chat/sessions");
      setSessions(data);
    } catch {}
    setLoadingSessions(false);
  };

  const loadSession = async (session: ChatSession) => {
    setActiveSession(session);
    setLoadingMessages(true);
    try {
      const data = await api.get<{ session: ChatSession; messages: Message[] }>(
        `/chat/sessions/${session.id}`
      );
      setMessages(data.messages);
    } catch {
      setMessages([]);
    }
    setLoadingMessages(false);
  };

  const [chatError, setChatError] = useState("");

  const createSession = async () => {
    setChatError("");
    try {
      const session = await api.post<ChatSession>("/chat/sessions", {
        title: newChatTitle || "New Chat",
        document_id: newChatDocId || null,
      });
      setSessions((s) => [session, ...s]);
      setActiveSession(session);
      setMessages([]);
      setShowNewChat(false);
      setNewChatTitle("");
      setNewChatDocId("");
    } catch (err: any) {
      setChatError(err.detail || "Failed to create chat session.");
    }
  };

  const deleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.delete(`/chat/sessions/${sessionId}`);
      setSessions((s) => s.filter((s) => s.id !== sessionId));
      if (activeSession?.id === sessionId) {
        setActiveSession(null);
        setMessages([]);
      }
    } catch {}
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !activeSession || sending) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      source_chunks: null,
      created_at: new Date().toISOString(),
    };

    setMessages((m) => [...m, userMsg]);
    const content = input.trim();
    setInput("");
    setSending(true);

    try {
      const reply = await api.post<Message>(
        `/chat/sessions/${activeSession.id}/messages`,
        { content }
      );
      setMessages((m) => [...m, reply]);
    } catch (err: any) {
      const errorMsg = err.detail || err.message || "Sorry, something went wrong. Please try again.";
      setMessages((m) => [
        ...m,
        {
          id: Date.now().toString(),
          role: "assistant",
          content: `⚠️ Error: ${errorMsg}`,
          source_chunks: null,
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex h-full overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 bg-card border-r border-border/50 flex flex-col shrink-0">
        <div className="p-4 border-b border-border/40">
          <h2 className="font-semibold text-sm mb-3 flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-primary" />
            Doubt Solver
          </h2>
          <button
            onClick={() => setShowNewChat(true)}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-all"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </button>
        </div>

        {/* New Chat Modal */}
        {showNewChat && (
          <div className="absolute inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
            <div className="bg-card border border-border rounded-2xl p-6 w-80 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">New Chat Session</h3>
                <button onClick={() => setShowNewChat(false)}>
                  <X className="h-4 w-4 text-muted-foreground" />
                </button>
              </div>
              <div className="space-y-3">
                {chatError && (
                  <p className="text-xs text-destructive bg-destructive/10 p-2 rounded-lg border border-destructive/20 font-medium">
                    {chatError}
                  </p>
                )}
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Title (optional)</label>
                  <input
                    value={newChatTitle}
                    onChange={(e) => setNewChatTitle(e.target.value)}
                    placeholder="e.g. OS Concepts Doubt"
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Scope to document (optional)</label>
                  <select
                    value={newChatDocId}
                    onChange={(e) => setNewChatDocId(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="">All documents</option>
                    {documents.map((doc) => (
                      <option key={doc.id} value={doc.id}>
                        {doc.title}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  onClick={createSession}
                  className="w-full py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-all"
                >
                  Create Session
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Session list */}
        <div className="flex-1 overflow-y-auto p-2">
          {loadingSessions ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : sessions.length === 0 ? (
            <p className="text-xs text-muted-foreground text-center py-6 px-2">
              No sessions yet. Create one to start chatting!
            </p>
          ) : (
            sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => loadSession(session)}
                className={`w-full text-left px-3 py-2.5 rounded-xl text-sm transition-all group flex items-center justify-between gap-2 mb-1 ${
                  activeSession?.id === session.id
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-accent text-foreground"
                }`}
              >
                <span className="truncate font-medium">{session.title}</span>
                <button
                  onClick={(e) => deleteSession(session.id, e)}
                  className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {!activeSession ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-4 text-muted-foreground p-8">
            <Bot className="h-16 w-16 opacity-20" />
            <div className="text-center">
              <h3 className="text-lg font-semibold text-foreground mb-1">Start a conversation</h3>
              <p className="text-sm">
                Create a new chat session and ask anything about your study materials.
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Chat header */}
            <div className="h-14 border-b border-border/40 flex items-center px-6 gap-3 shrink-0 bg-card/50">
              <MessageSquare className="h-4 w-4 text-primary" />
              <span className="font-semibold text-sm">{activeSession.title}</span>
              {activeSession.document_id && (
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <FileText className="h-3 w-3" />
                  Scoped to document
                </span>
              )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              {loadingMessages ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : messages.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground text-sm">
                  <Bot className="h-8 w-8 mx-auto mb-2 opacity-40" />
                  Ask me anything about your notes!
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
                  >
                    <div
                      className={`h-8 w-8 rounded-xl flex items-center justify-center shrink-0 ${
                        msg.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {msg.role === "user" ? (
                        <User className="h-4 w-4" />
                      ) : (
                        <Bot className="h-4 w-4" />
                      )}
                    </div>
                    <div
                      className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                        msg.role === "user"
                          ? "bg-primary text-primary-foreground rounded-tr-sm"
                          : "bg-card border border-border/50 text-foreground rounded-tl-sm"
                      }`}
                    >
                      <ChatMessageContent content={msg.content} isUser={msg.role === "user"} />
                      {msg.source_chunks && msg.source_chunks.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-border/30 space-y-1">
                          <p className="text-xs opacity-60 font-medium">Sources:</p>
                          {msg.source_chunks.map((chunk, i) => (
                            <p key={i} className="text-xs opacity-70 line-clamp-1">
                              Page {chunk.page_number ?? "?"}: {chunk.excerpt}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
              {sending && (
                <div className="flex gap-3">
                  <div className="h-8 w-8 rounded-xl bg-muted flex items-center justify-center">
                    <Bot className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="bg-card border border-border/50 rounded-2xl rounded-tl-sm px-4 py-3">
                    <div className="flex gap-1 items-center">
                      <span className="h-2 w-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="h-2 w-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="h-2 w-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form
              onSubmit={sendMessage}
              className="border-t border-border/40 px-6 py-4 flex gap-3 bg-card/50 shrink-0"
            >
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about your study material…"
                disabled={sending}
                className="flex-1 px-4 py-2.5 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50 transition-all"
              />
              <button
                type="submit"
                disabled={!input.trim() || sending}
                className="px-4 py-2.5 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-all flex items-center gap-2"
              >
                {sending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
