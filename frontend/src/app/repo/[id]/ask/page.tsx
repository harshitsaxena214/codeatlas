"use client";

import { useState, useRef, useEffect } from "react";
import { useParams } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import {
  MessageSquare,
  Send,
  Loader2,
  ExternalLink,
  Sparkles,
} from "lucide-react";
import { api, QAResponse } from "@/lib/api";
import { GlassCard } from "@/components/GlassCard";
import { FeedbackButtons } from "@/components/FeedbackButtons";

interface Message {
  role: "user" | "assistant";
  content: string;
  data?: QAResponse;
}

export default function AskPage() {
  const params = useParams();
  const repoId = params.id as string;
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  const mutation = useMutation({
    mutationFn: (q: string) => api.askQuestion(repoId, q),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, data },
      ]);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || mutation.isPending) return;
    const q = question.trim();
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setQuestion("");
    mutation.mutate(q);
  };

  const handleFollowUp = (q: string) => {
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    mutation.mutate(q);
  };

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div
        className="flex items-center gap-3 px-6 py-4"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: "hsla(190, 80%, 55%, 0.15)", color: "var(--accent-cyan)" }}
        >
          <MessageSquare size={16} />
        </div>
        <div>
          <h1 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
            Repository Q&A
          </h1>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            Ask anything — answers backed by real repo data
          </p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto px-6 py-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center animate-fade-in">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
              style={{ background: "var(--bg-tertiary)" }}
            >
              <Sparkles size={24} style={{ color: "var(--text-tertiary)" }} />
            </div>
            <h2 className="text-lg font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
              Ask a question
            </h2>
            <p className="text-sm max-w-md" style={{ color: "var(--text-secondary)" }}>
              Ask about architecture, coding patterns, contribution guidelines,
              or anything else about this repository.
            </p>
            <div className="flex flex-wrap justify-center gap-2 mt-6 max-w-md">
              {[
                "How is the codebase structured?",
                "What testing framework is used?",
                "How do I set up the dev environment?",
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => {
                    setQuestion(q);
                  }}
                  className="badge py-2 px-3 text-xs cursor-pointer"
                  style={{
                    background: "var(--bg-tertiary)",
                    color: "var(--text-secondary)",
                    border: "1px solid var(--border)",
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="flex flex-col gap-4 max-w-3xl mx-auto">
          {messages.map((msg, i) => (
            <div key={i} className="animate-fade-in-up">
              {msg.role === "user" ? (
                <div className="flex justify-end">
                  <div
                    className="max-w-[80%] px-4 py-2.5 rounded-2xl rounded-br-sm text-sm"
                    style={{
                      background: "var(--accent-blue)",
                      color: "white",
                    }}
                  >
                    {msg.content}
                  </div>
                </div>
              ) : (
                <div className="flex flex-col gap-3">
                  <GlassCard padding="p-4">
                    <p
                      className="text-sm leading-relaxed whitespace-pre-wrap"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      {msg.content}
                    </p>

                    {/* Citations */}
                    {msg.data?.citations && msg.data.citations.length > 0 && (
                      <div className="mt-3 pt-3" style={{ borderTop: "1px solid var(--border)" }}>
                        <div className="text-xs font-medium mb-2" style={{ color: "var(--text-tertiary)" }}>
                          Sources
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.data.citations.map((cite, j) => (
                            <a
                              key={j}
                              href={cite.source_url || "#"}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 badge text-xs"
                              style={{
                                background: "var(--bg-secondary)",
                                color: "var(--accent-blue)",
                                border: "1px solid var(--border)",
                              }}
                              title={cite.relevant_excerpt}
                            >
                              {cite.source_type}: {cite.source_title.slice(0, 30)}
                              <ExternalLink size={10} />
                            </a>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Confidence */}
                    {msg.data?.confidence !== undefined && (
                      <div className="mt-2 text-xs" style={{ color: "var(--text-tertiary)" }}>
                        Confidence: {Math.round(msg.data.confidence * 100)}%
                      </div>
                    )}
                  </GlassCard>

                  {/* Follow-up questions */}
                  {msg.data?.follow_up_questions && msg.data.follow_up_questions.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {msg.data.follow_up_questions.map((fq) => (
                        <button
                          key={fq}
                          onClick={() => handleFollowUp(fq)}
                          className="badge py-1.5 px-3 text-xs cursor-pointer transition-all"
                          style={{
                            background: "var(--bg-tertiary)",
                            color: "var(--text-secondary)",
                            border: "1px solid var(--border)",
                          }}
                        >
                          {fq}
                        </button>
                      ))}
                    </div>
                  )}

                  <FeedbackButtons
                    repoId={repoId}
                    feature="qa"
                    query={messages[i - 1]?.content || ""}
                    responseSummary={msg.content.slice(0, 300)}
                  />
                </div>
              )}
            </div>
          ))}

          {mutation.isPending && (
            <div className="flex items-center gap-2 text-sm animate-fade-in" style={{ color: "var(--text-secondary)" }}>
              <Loader2 size={14} className="animate-spin" />
              Thinking...
            </div>
          )}

          <div ref={scrollRef} />
        </div>
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="px-6 py-4"
        style={{ borderTop: "1px solid var(--border)" }}
      >
        <div className="flex gap-2 max-w-3xl mx-auto">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about this repository..."
            className="input-field flex-1"
            disabled={mutation.isPending}
          />
          <button
            type="submit"
            disabled={!question.trim() || mutation.isPending}
            className="btn-primary px-4"
          >
            <Send size={16} />
          </button>
        </div>
      </form>
    </div>
  );
}
