"use client";

import { useState, useCallback } from "react";
import Sidebar from "../components/Sidebar";
import ChatArea from "../components/ChatArea";
import ChatInput from "../components/ChatInput";

export default function ChatPage() {
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState({});
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);

  const activeMessages = activeChatId ? messages[activeChatId] || [] : [];

  const createNewChat = useCallback(
    (title = "New conversation") => {
      const id = Date.now().toString();
      setChats((prev) => [{ id, title }, ...prev]);
      setMessages((prev) => ({ ...prev, [id]: [] }));
      setActiveChatId(id);
      return id;
    },
    []
  );

  const handleNewChat = useCallback(() => {
    createNewChat();
  }, [createNewChat]);

  const handleSelectChat = useCallback((id) => {
    setActiveChatId(id);
  }, []);

  const handleSend = useCallback(
    (text) => {
      let chatId = activeChatId;

      // If no active chat, create one with the message as the title
      if (!chatId) {
        chatId = createNewChat(
          text.length > 40 ? text.slice(0, 40) + "…" : text
        );
      }

      // Update title if it's still the default
      setChats((prev) =>
        prev.map((c) =>
          c.id === chatId && c.title === "New conversation"
            ? {
                ...c,
                title: text.length > 40 ? text.slice(0, 40) + "…" : text,
              }
            : c
        )
      );

      const userMsg = { role: "user", content: text };
      setMessages((prev) => ({
        ...prev,
        [chatId]: [...(prev[chatId] || []), userMsg],
      }));
    },
    [activeChatId, createNewChat]
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

        // Ensure there's an active chat
        if (!activeChatId) {
          createNewChat(file.name);
        }
      } catch (err) {
        console.error("Upload failed:", err);
        // Show error as a system message if there's an active chat
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
      />

      <div className="flex flex-1 flex-col overflow-hidden">
        <ChatArea messages={activeMessages} uploadedFiles={uploadedFiles} />
        <ChatInput
          onSend={handleSend}
          onFileUpload={handleFileUpload}
          isUploading={isUploading}
        />
      </div>
    </div>
  );
}
