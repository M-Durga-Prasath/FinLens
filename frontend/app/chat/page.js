"use client";

import { useState, useCallback, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import ChatArea from "../components/ChatArea";
import ChatInput from "../components/ChatInput";

export default function ChatPage() {
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState({});
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoadingChats, setIsLoadingChats] = useState(true);

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
      let chatId = activeChatId;

      // If no active chat, create one with the message as title
      if (!chatId) {
        const generatedTitle =
          text.length > 35 ? text.slice(0, 35) + "…" : text;
        chatId = await createNewChat(generatedTitle);
        if (!chatId) return;
      } else {
        // Auto update title if current session title is "New conversation"
        const currentChat = chats.find((c) => c.id === chatId);
        if (currentChat && currentChat.title === "New conversation") {
          const autoTitle = text.length > 35 ? text.slice(0, 35) + "…" : text;
          handleRenameChat(chatId, autoTitle);
        }
      }

      // Optimistic user message addition
      const userMsg = { role: "user", content: text };
      setMessages((prev) => ({
        ...prev,
        [chatId]: [...(prev[chatId] || []), userMsg],
      }));

      try {
        // Persist user message in DB
        await fetch(`/api/sessions/${chatId}/messages`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ role: "USER", content: text }),
        });

        // Assistant reply placeholder (will integrate with AI model / backend RAG pipeline)
        const assistantText = `I have received your query: "${text}". Ask questions about uploaded documents or financial metrics anytime.`;

        // Persist assistant message in DB
        const assistantRes = await fetch(`/api/sessions/${chatId}/messages`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ role: "MODEL", content: assistantText }),
        });

        if (assistantRes.ok) {
          const modelMsgObj = { role: "model", content: assistantText };
          setMessages((prev) => ({
            ...prev,
            [chatId]: [...(prev[chatId] || []), modelMsgObj],
          }));
        }
      } catch (err) {
        console.error("Failed to send message:", err);
      }
    },
    [activeChatId, chats, createNewChat, handleRenameChat]
  );

  const handleFileUpload = useCallback(
    async (file) => {
      setIsUploading(true);

      try {
        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch("http://localhost:8000/upload/", {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Upload failed (${res.status})`);
        }

        const data = await res.json();
        setUploadedFiles((prev) => [...prev, data.filename || file.name]);

        let chatId = activeChatId;
        if (!chatId) {
          chatId = await createNewChat(file.name);
        }
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
    [activeChatId, createNewChat]
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
            <ChatArea messages={activeMessages} uploadedFiles={uploadedFiles} />
            <ChatInput
              onSend={handleSend}
              onFileUpload={handleFileUpload}
              isUploading={isUploading}
            />
          </>
        )}
      </div>
    </div>
  );
}
