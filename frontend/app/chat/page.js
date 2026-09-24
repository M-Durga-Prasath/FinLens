"use client";

import { useState, useCallback, useEffect } from "react";
import { useSession } from "next-auth/react";
import Sidebar from "../components/Sidebar";
import ChatArea from "../components/ChatArea";
import ChatInput from "../components/ChatInput";

const BACKEND_URL = "http://localhost:8000";

export default function ChatPage() {
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
          const formatted = (data.messages || []).map((m) => ({
            id: m.id,
            role: m.role === "USER" ? "user" : "model",
            content: m.content,
          }));
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
    [activeChatId]
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
          prev.map((c) => (c.id === id ? { ...c, title: newTitle } : c))
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
        const res = await fetch(`${BACKEND_URL}/chat/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
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
                if (lastMsg && lastMsg.role === "model" && lastMsg.isStreaming) {
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
                if (lastMsg && lastMsg.role === "model" && lastMsg.isStreaming) {
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
                if (lastMsg && lastMsg.role === "model" && lastMsg.isStreaming) {
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
    [activeChatId, chats, createNewChat, handleRenameChat, isStreaming]
  );

  const handleFileUpload = useCallback(
    async (file) => {
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

        const res = await fetch(`${BACKEND_URL}/upload/`, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const errBody = await res.json().catch(() => ({}));
          const detail = Array.isArray(errBody.detail)
            ? errBody.detail.map((e) => e.msg || JSON.stringify(e)).join("; ")
            : errBody.detail;
          throw new Error(detail || `Upload failed (${res.status})`);
        }

        const data = await res.json();
        setUploadedFiles((prev) => [...prev, data.filename || file.name]);

      } catch (err) {
        console.error("Upload failed:", err);
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
    [activeChatId, createNewChat, session]
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
            <ChatArea messages={activeMessages} uploadedFiles={uploadedFiles} isStreaming={isStreaming} />
            <ChatInput
              onSend={handleSend}
              onFileUpload={handleFileUpload}
              isUploading={isUploading}
              isStreaming={isStreaming}
            />
          </>
        )}
      </div>
    </div>
  );
}
