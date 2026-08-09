"use client";

import { useState, useRef } from "react";

export default function ChatInput({ onSend, onFileUpload, isUploading }) {
  const [input, setInput] = useState("");
  const fileRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setInput("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileUpload(file);
      // reset so the same file can be re-uploaded
      e.target.value = "";
    }
  };

  return (
    <div className="border-t border-border bg-background px-6 py-4">
      <form
        onSubmit={handleSubmit}
        className="mx-auto flex w-full max-w-3xl items-end gap-2"
      >
        {/* File attach */}
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.docx,.txt,.html"
          onChange={handleFileChange}
          className="hidden"
          id="file-upload-input"
        />
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={isUploading}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-text-tertiary hover:bg-surface-hover hover:text-text-secondary disabled:opacity-40"
          title="Attach a document"
          id="attach-file-btn"
        >
          {isUploading ? (
            <svg
              width="18"
              height="18"
              viewBox="0 0 18 18"
              fill="none"
              className="animate-spin"
            >
              <circle
                cx="9"
                cy="9"
                r="7"
                stroke="currentColor"
                strokeWidth="2"
                strokeDasharray="30"
                strokeDashoffset="10"
                strokeLinecap="round"
              />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path
                d="M15.5 8.5l-6.3 6.3a4 4 0 01-5.65-5.65l6.3-6.3a2.67 2.67 0 013.77 3.77l-6.3 6.28a1.33 1.33 0 01-1.88-1.88L11.7 4.7"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}
        </button>

        {/* Text input */}
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your documents..."
          rows={1}
          className="flex-1 resize-none rounded-xl border border-border bg-surface px-4 py-2.5 text-sm text-foreground placeholder:text-text-tertiary focus:border-accent/40 focus:outline-none"
          style={{ maxHeight: "120px" }}
          id="chat-message-input"
        />

        {/* Send */}
        <button
          type="submit"
          disabled={!input.trim()}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent text-background hover:bg-accent-dim disabled:opacity-30 disabled:hover:bg-accent"
          id="send-message-btn"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M14 2L7 9M14 2l-4 12-3-5.5L2 5.5 14 2z"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </form>
    </div>
  );
}
