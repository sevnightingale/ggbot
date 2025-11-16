"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, X, Minimize2, Maximize2 } from "lucide-react";
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
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationHistory, setConversationHistory] = useState<ConversationMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

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
        <motion.div
          initial={{ y: "100%" }}
          animate={{ y: isMinimized ? "calc(100% - 60px)" : "20%" }}
          exit={{ y: "100%" }}
          drag="y"
          dragConstraints={{ top: 0, bottom: 0 }}
          dragElastic={0.1}
          onDragEnd={(_e, info) => {
            if (info.offset.y > 100) setIsMinimized(true);
            if (info.offset.y < -100) setIsMinimized(false);
          }}
          className="fixed inset-x-0 bottom-0 bg-white dark:bg-gray-900 rounded-t-2xl shadow-2xl border-t border-gray-200 dark:border-gray-700"
          style={{ height: "80vh", zIndex: 50 }}
        >
          {/* Drag handle */}
          <div className="w-full flex justify-center py-2 cursor-grab active:cursor-grabbing">
            <div className="w-12 h-1.5 bg-gray-300 dark:bg-gray-600 rounded-full" />
          </div>

          {/* Header */}
          <div className="px-4 pb-3 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-brass" />
              <h3 className="font-semibold text-gray-900 dark:text-ivory">
                AI Assistant
              </h3>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {botType === "agent"
                  ? "Strategy Builder"
                  : botType === "scheduled"
                  ? "Config Helper"
                  : "Signal Validator"}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsMinimized(!isMinimized)}
              >
                {isMinimized ? (
                  <Maximize2 className="w-4 h-4" />
                ) : (
                  <Minimize2 className="w-4 h-4" />
                )}
              </Button>
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Chat content */}
          {!isMinimized && (
            <div className="flex flex-col h-full">
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                  <div className="text-center text-gray-500 dark:text-gray-400 mt-8">
                    <Sparkles className="w-12 h-12 mx-auto mb-4 text-brass opacity-50" />
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
                          ? "bg-brass text-obsidian"
                          : "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-ivory"
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
                    <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-2">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-brass rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-brass rounded-full animate-bounce delay-100" />
                        <div className="w-2 h-2 bg-brass rounded-full animate-bounce delay-200" />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Input */}
              <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask me anything about configuring your bot..."
                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-ivory placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brass"
                    disabled={loading}
                  />
                  <Button
                    onClick={sendMessage}
                    disabled={loading || !input.trim()}
                    className="bg-brass hover:bg-brass/90 text-obsidian"
                  >
                    Send
                  </Button>
                </div>
              </div>
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
