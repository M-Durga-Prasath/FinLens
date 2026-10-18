"use client";

import { useState, useCallback, useEffect } from "react";
import { useSession } from "next-auth/react";
import Sidebar from "../components/Sidebar";
import ChatArea from "../components/ChatArea";
import ChatInput from "../components/ChatInput";
import { getBackendToken } from "@/lib/backendToken";

const BACKEND_URL = "http://localhost:8000";

export default function ChatPage() {
  const [largeFiles, SetLargeFiles] = useState(false);
  const { data: session } = useSession();
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState({});
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoadingChats, setIsLoadingChats] = useState(true);
  const [isStreaming, setIsStreaming] = useState(false);

  // Fetch initial chat sessions from DB
  const fetchSessions = useCallback(async () => {
    try {
      setIsLoadingChats(true);
      const res = await fetch("/api/sessions");
      if (res.ok) {
        const data = await res.json();
        setChats(data);
        if (data.length > 0) {
          setActiveChatId((prev) => prev || data[0].id);
        }
      }
    } catch (err) {
      console.error("Failed to load chat sessions:", err);
    } finally {
      setIsLoadingChats(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  // Fetch messages when activeChatId changes
  useEffect(() => {
    if (!activeChatId) return;

    // Only fetch if not already loaded or to refresh
    const loadSessionMessages = async () => {
      try {
        const res = await fetch(`/api/sessions/${activeChatId}`);
        if (res.ok) {
          const data = await res.json();
          const formatted = (data.messages || []).map((m) => {
            const msg = {
              id: m.id,
              role: m.role === "USER" ? "user" : "model",
              content: m.content,
            };

            // Map DB citations into the same shape as streaming sources
            if (m.Citations && m.Citations.length > 0) {
              msg.sources = m.Citations.map((c, idx) => {
                const chunkContent = c.chunk?.content || "";
                return {
                  citation_id: idx + 1,
                  chunk_id: c.chunk?.id,
                  chunk_index: c.chunk?.chunkIndex,
                  document_id: c.chunk?.document?.id,
                  document_filename: c.chunk?.document?.filename || "Unknown",
                  page_number: c.chunk?.pageNumber,
                  relevance_score: c.relevanceScore,
                  content_preview:
                    chunkContent.length > 150
                      ? chunkContent.slice(0, 150) + "…"
                      : chunkContent,
                };
              });
            }

            return msg;
          });
          setMessages((prev) => ({ ...prev, [activeChatId]: formatted }));
        }
      } catch (err) {
        console.error("Failed to load session messages:", err);
      }
    };

    loadSessionMessages();
  }, [activeChatId]);

  const activeMessages = activeChatId ? messages[activeChatId] || [] : [];

  const createNewChat = useCallback(async (title = "New conversation") => {
    try {
      const res = await fetch("/api/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });

      if (!res.ok) {
        throw new Error("Failed to create chat session");
      }

      const newChat = await res.json();
      setChats((prev) => [newChat, ...prev]);
      setMessages((prev) => ({ ...prev, [newChat.id]: [] }));
      setActiveChatId(newChat.id);
      return newChat.id;
    } catch (err) {
      console.error("Error creating chat:", err);
      return null;
    }
  }, []);

  const handleNewChat = useCallback(() => {
    createNewChat();
  }, [createNewChat]);

  const handleSelectChat = useCallback((id) => {
    setActiveChatId(id);
  }, []);

  const handleDeleteChat = useCallback(
    async (id) => {
      try {
        const res = await fetch(`/api/sessions/${id}`, {
          method: "DELETE",
        });

        if (res.ok) {
          setChats((prev) => {
            const updated = prev.filter((c) => c.id !== id);
            if (activeChatId === id) {
              setActiveChatId(updated.length > 0 ? updated[0].id : null);
            }
            return updated;
          });

          setMessages((prev) => {
            const next = { ...prev };
            delete next[id];
            return next;
          });
        }
      } catch (err) {
        console.error("Failed to delete chat:", err);
      }
    },
    [activeChatId],
  );

  const handleRenameChat = useCallback(async (id, newTitle) => {
    try {
      const res = await fetch(`/api/sessions/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: newTitle }),
      });

      if (res.ok) {
        setChats((prev) =>
          prev.map((c) => (c.id === id ? { ...c, title: newTitle } : c)),
        );
      }
    } catch (err) {
      console.error("Failed to rename chat:", err);
    }
  }, []);

  const handleSend = useCallback(
    async (text) => {
      if (isStreaming) return;

      let chatId = activeChatId;

      // If no active chat, create one with the message as title
      if (!chatId) {
        const generatedTitle =
          text.length > 35 ? text.slice(0, 35) + "…" : text;
        chatId = await createNewChat(generatedTitle);
        if (!chatId) return;
      } else {
        const currentChat = chats.find((c) => c.id === chatId);
        if (currentChat && currentChat.title === "New conversation") {
          const autoTitle = text.length > 35 ? text.slice(0, 35) + "…" : text;
          handleRenameChat(chatId, autoTitle);
        }
      }

      const userMsg = { role: "user", content: text };
      const streamingMsg = { role: "model", content: "", isStreaming: true };

      setMessages((prev) => ({
        ...prev,
        [chatId]: [...(prev[chatId] || []), userMsg, streamingMsg],
      }));

      setIsStreaming(true);

      try {
        const token = await getBackendToken();
        const headers = { "Content-Type": "application/json" };
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const res = await fetch(`${BACKEND_URL}/chat/`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            query: text,
            session_id: chatId,
            top_k: 6,
            candidate_k: 20,
          }),
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `Request failed (${res.status})`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith("data: ")) continue;

            const jsonStr = trimmed.slice(6);
            let event;
            try {
              event = JSON.parse(jsonStr);
            } catch {
              continue;
            }

            if (event.type === "token" || event.type === "answer") {
              setMessages((prev) => {
                const chatMsgs = [...(prev[chatId] || [])];
                const lastMsg = chatMsgs[chatMsgs.length - 1];
                if (
                  lastMsg &&
                  lastMsg.role === "model" &&
                  lastMsg.isStreaming
                ) {
                  chatMsgs[chatMsgs.length - 1] = {
                    ...lastMsg,
                    content: lastMsg.content + event.content,
                  };
                }
                return { ...prev, [chatId]: chatMsgs };
              });
            } else if (event.type === "error") {
              setMessages((prev) => {
                const chatMsgs = [...(prev[chatId] || [])];
                const lastMsg = chatMsgs[chatMsgs.length - 1];
                if (
                  lastMsg &&
                  lastMsg.role === "model" &&
                  lastMsg.isStreaming
                ) {
                  chatMsgs[chatMsgs.length - 1] = {
                    ...lastMsg,
                    content: event.message,
                    isStreaming: false,
                    isError: true,
                  };
                }
                return { ...prev, [chatId]: chatMsgs };
              });
            } else if (event.type === "sources") {
              setMessages((prev) => {
                const chatMsgs = [...(prev[chatId] || [])];
                const lastMsg = chatMsgs[chatMsgs.length - 1];
                if (
                  lastMsg &&
                  lastMsg.role === "model" &&
                  lastMsg.isStreaming
                ) {
                  chatMsgs[chatMsgs.length - 1] = {
                    ...lastMsg,
                    isStreaming: false,
                    sources: event.sources,
                  };
                }
                return { ...prev, [chatId]: chatMsgs };
              });
            }
          }
        }

        setMessages((prev) => {
          const chatMsgs = [...(prev[chatId] || [])];
          const lastMsg = chatMsgs[chatMsgs.length - 1];
          if (lastMsg && lastMsg.role === "model" && lastMsg.isStreaming) {
            chatMsgs[chatMsgs.length - 1] = {
              ...lastMsg,
              isStreaming: false,
            };
          }
          return { ...prev, [chatId]: chatMsgs };
        });
      } catch (err) {
        console.error("Streaming failed:", err);
        setMessages((prev) => {
          const chatMsgs = [...(prev[chatId] || [])];
          const lastMsg = chatMsgs[chatMsgs.length - 1];
          if (lastMsg && lastMsg.role === "model") {
            const hasContent = !!lastMsg.content;
            chatMsgs[chatMsgs.length - 1] = {
              ...lastMsg,
              content:
                lastMsg.content ||
                "Failed to connect to the server. Please try again.",
              isStreaming: false,
              isError: !hasContent,
            };
          }
          return { ...prev, [chatId]: chatMsgs };
        });
      } finally {
        setIsStreaming(false);
      }
    },
    [activeChatId, chats, createNewChat, handleRenameChat, isStreaming],
  );

  const handleFileUpload = useCallback(
    async (file) => {
      if (!file) return;
      if (file.size > 25 * 1024 * 1024) {
        SetLargeFiles(true);
        return;
      }

      setIsUploading(true);

      try {
        let chatId = activeChatId;
        if (!chatId) {
          chatId = await createNewChat(file.name);
          if (!chatId) return;
        }

        const formData = new FormData();
        formData.append("file", file);
        formData.append("user_id", session?.user?.id ?? "");
        formData.append("session_id", chatId);

        const token = await getBackendToken();
        const headers = {};
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const res = await fetch(`${BACKEND_URL}/upload/`, {
          method: "POST",
          headers,
          body: formData,
        });
        if (!res.ok) {
          const errBody = await res.json().catch(() => ({}));
          const detail = Array.isArray(errBody.detail)
            ? errBody.detail.map((e) => e.msg || JSON.stringify(e)).join("; ")
            : errBody.detail;
          const errorMsg = detail || `Upload failed (${res.status})`;

          if (
            res.status === 413 ||
            errorMsg.toLowerCase().includes("large") ||
            errorMsg.toLowerCase().includes("size")
          ) {
            SetLargeFiles(true);
            return;
          }

          throw new Error(errorMsg);
        }

        const data = await res.json();
        setUploadedFiles((prev) => [...prev, data.filename || file.name]);
      } catch (err) {
        console.error("Upload failed:", err);
        const errMsg = err?.message || "";
        if (
          errMsg.includes("413") ||
          errMsg.toLowerCase().includes("large") ||
          errMsg.toLowerCase().includes("size")
        ) {
          SetLargeFiles(true);
          return;
        }

        const chatId = activeChatId;
        if (chatId) {
          setMessages((prev) => ({
            ...prev,
            [chatId]: [
              ...(prev[chatId] || []),
              {
                role: "assistant",
                content: `Failed to upload file: ${err.message}`,
              },
            ],
          }));
        }
      } finally {
        setIsUploading(false);
      }
    },
    [activeChatId, createNewChat, session],
  );

  return (
    <div className="flex h-dvh overflow-hidden">
      <Sidebar
        chats={chats}
        activeChatId={activeChatId}
        onNewChat={handleNewChat}
        onSelectChat={handleSelectChat}
        onDeleteChat={handleDeleteChat}
        onRenameChat={handleRenameChat}
      />

      <div className="flex flex-1 flex-col overflow-hidden">
        {isLoadingChats ? (
          <div className="flex flex-1 items-center justify-center text-text-tertiary text-sm">
            Loading conversations...
          </div>
        ) : (
          <>
            <ChatArea
              messages={activeMessages}
              uploadedFiles={uploadedFiles}
              isStreaming={isStreaming}
            />
            <ChatInput
              onSend={handleSend}
              onFileUpload={handleFileUpload}
              isUploading={isUploading}
              isStreaming={isStreaming}
            />
          </>
        )}
      </div>

      {/* Large file Popup Modal */}
      {largeFiles && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-200"
          onClick={() => SetLargeFiles(false)}
        >
          <div
            className="w-full max-w-md rounded-2xl border border-border bg-surface p-6 shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-amber-500/15 text-amber-400">
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
              </div>
              <div>
                <h3 className="text-base font-semibold text-foreground">
                  File Too Large
                </h3>
                <p className="text-xs text-text-tertiary">
                  Maximum file size limit exceeded
                </p>
              </div>
            </div>

            <p className="text-sm text-text-secondary leading-relaxed">
              The selected file exceeds the maximum allowed size limit of{" "}
              <span className="font-medium text-foreground">25 MB</span>. Please
              upload a smaller document or split it into smaller files to
              continue.
            </p>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => SetLargeFiles(false)}
                className="rounded-lg bg-accent hover:bg-accent-dim px-4 py-2 text-sm font-medium text-background transition-colors cursor-pointer"
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
