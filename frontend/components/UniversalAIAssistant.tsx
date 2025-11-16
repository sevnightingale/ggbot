"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ConversationMessage {
  role: string;
  content: string;
}

interface UniversalAIAssistantProps {
  configId: string;
  botType: "agent" | "scheduled" | "signal_validation";
  isOpen: boolean;
  onClose: () => void;
  onConfigUpdate: () => void;
}

export function UniversalAIAssistant({
  configId,
  botType,
  isOpen,
  onClose,
  onConfigUpdate,
}: UniversalAIAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationHistory, setConversationHistory] = useState<ConversationMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");
    setLoading(true);

    // Add user message to UI immediately
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    try {
      const response = await fetch("/api/v2/assistant/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          config_id: configId,
          bot_type: botType,
          message: userMessage,
          conversation_history: conversationHistory,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();

      // Add assistant response to UI
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response },
      ]);

      // Update conversation history for next request
      setConversationHistory(data.conversation_history);

      // If config was updated, refresh parent component
      if (data.config_updated) {
        onConfigUpdate();
      }
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${error instanceof Error ? error.message : "Failed to send message"}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
          />

          {/* Bottom Sheet */}
          <motion.div
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed inset-x-0 bottom-0 z-50 flex flex-col bg-[var(--bg-secondary)] border-t border-[var(--border)] shadow-2xl"
            style={{ height: "60vh", maxHeight: "600px" }}
          >
            {/* Header with drag handle */}
            <div className="flex-shrink-0">
              {/* Drag handle */}
              <div className="w-full flex justify-center py-3 cursor-grab active:cursor-grabbing">
                <div className="w-16 h-1 bg-[var(--border)] rounded-full" />
              </div>

              {/* Header bar */}
              <div className="px-4 pb-3 border-b border-[var(--border)] flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-[var(--accent)]" />
                  <h3 className="font-semibold text-[var(--text-primary)]">
                    Strategy Advisor
                  </h3>
                  <span className="text-xs text-[var(--text-muted)]">
                    {botType === "agent"
                      ? "Strategy Builder"
                      : botType === "scheduled"
                      ? "Config Helper"
                      : "Signal Validator"}
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClose}
                  className="hover:bg-[var(--bg-tertiary)]"
                >
                  <ChevronDown className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* Messages area - flex-1 to fill available space */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
              {messages.length === 0 && (
                <div className="text-center text-[var(--text-muted)] mt-8">
                  <Sparkles className="w-12 h-12 mx-auto mb-4 text-[var(--accent)] opacity-50" />
                  <p className="text-sm">
                    Hi! I can help you configure your bot.
                  </p>
                  <p className="text-xs mt-2">
                    Ask me anything about setting up{" "}
                    {botType === "agent"
                      ? "your trading strategy"
                      : "your bot configuration"}
                    .
                  </p>
                </div>
              )}

              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${
                    msg.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-2 ${
                      msg.role === "user"
                        ? "bg-[var(--accent)] text-[var(--bg-primary)]"
                        : "bg-[var(--bg-tertiary)] text-[var(--text-primary)] border border-[var(--border)]"
                    }`}
                  >
                    <div className="text-sm whitespace-pre-wrap">
                      {msg.content}
                    </div>
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex justify-start">
                  <div className="bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg px-4 py-2">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-[var(--accent)] rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-[var(--accent)] rounded-full animate-bounce delay-100" />
                      <div className="w-2 h-2 bg-[var(--accent)] rounded-full animate-bounce delay-200" />
                    </div>
                  </div>
                </div>
              )}

              {/* Scroll anchor */}
              <div ref={messagesEndRef} />
            </div>

            {/* Input area - flex-shrink-0 to prevent collapse */}
            <div className="flex-shrink-0 p-4 border-t border-[var(--border)] bg-[var(--bg-secondary)]">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me anything about your bot configuration..."
                  className="flex-1 px-4 py-2 border border-[var(--border)] rounded-lg bg-[var(--bg-primary)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
                  disabled={loading}
                  autoFocus
                />
                <Button
                  onClick={sendMessage}
                  disabled={loading || !input.trim()}
                  className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] font-medium px-6"
                >
                  Send
                </Button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
