"use client";

import { useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";

export default function ChatArea({ messages, uploadedFiles }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      {isEmpty ? (
        <div className="flex flex-1 flex-col items-center justify-center px-6">
          <svg
            width="48"
            height="48"
            viewBox="0 0 48 48"
            fill="none"
            className="mb-5 text-text-tertiary"
          >
            <rect
              x="6"
              y="8"
              width="28"
              height="34"
              rx="3"
              stroke="currentColor"
              strokeWidth="2"
            />
            <path
              d="M13 18h14M13 24h10M13 30h8"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
            <circle cx="38" cy="16" r="8" stroke="currentColor" strokeWidth="2" />
            <path d="M43.5 22L47 25.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <p className="mb-2 text-base font-medium text-text-secondary">
            Upload a PDF and start asking questions
          </p>
          <p className="max-w-xs text-center text-sm text-text-tertiary">
            Attach a financial document using the clip icon below, then ask
            anything about it.
          </p>
        </div>
      ) : (
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-6 py-6">
          {/* Show uploaded files indicator */}
          {uploadedFiles.length > 0 && (
            <div className="flex flex-wrap gap-2 pb-2">
              {uploadedFiles.map((file, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1.5 rounded-md bg-accent/10 px-2.5 py-1 text-xs text-accent"
                >
                  <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
                    <path
                      d="M3 1h7l4 4v10a1 1 0 01-1 1H3a1 1 0 01-1-1V2a1 1 0 011-1z"
                      stroke="currentColor"
                      strokeWidth="1.5"
                    />
                  </svg>
                  {file}
                </span>
              ))}
            </div>
          )}

          {messages.map((msg, i) => (
            <MessageBubble key={i} role={msg.role} content={msg.content} />
          ))}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}
