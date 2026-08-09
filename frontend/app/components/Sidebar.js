"use client";

import Link from "next/link";

export default function Sidebar({
  chats,
  activeChatId,
  onNewChat,
  onSelectChat,
}) {
  return (
    <aside className="flex h-full w-[260px] shrink-0 flex-col border-r border-border bg-surface">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 pt-5 pb-4">
        <Link href="/chat" className="flex items-center gap-2.5 hover:opacity-80">
          <svg
            width="24"
            height="24"
            viewBox="0 0 32 32"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <rect
              x="2"
              y="4"
              width="20"
              height="26"
              rx="2"
              stroke="#3ecfb4"
              strokeWidth="2"
              fill="none"
            />
            <path
              d="M7 12h10M7 16h8M7 20h6"
              stroke="#3ecfb4"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
            <circle cx="24" cy="10" r="6" stroke="#3ecfb4" strokeWidth="2" fill="none" />
            <path
              d="M28.5 14.5L31 17"
              stroke="#3ecfb4"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
          <span className="text-base font-semibold tracking-tight text-foreground">
            FinLens
          </span>
        </Link>
      </div>

      {/* New Chat Button */}
      <div className="px-3 pb-3">
        <button
          onClick={onNewChat}
          className="flex w-full items-center gap-2 rounded-lg border border-border px-3 py-2.5 text-sm text-text-secondary hover:bg-surface-hover hover:text-foreground"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M8 3v10M3 8h10"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
          New chat
        </button>
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto px-3">
        {chats.length === 0 ? (
          <p className="px-3 py-6 text-center text-xs text-text-tertiary">
            No conversations yet
          </p>
        ) : (
          <div className="flex flex-col gap-0.5">
            {chats.map((chat) => (
              <button
                key={chat.id}
                onClick={() => onSelectChat(chat.id)}
                className={`w-full truncate rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                  activeChatId === chat.id
                    ? "bg-surface-hover text-foreground"
                    : "text-text-secondary hover:bg-surface-hover hover:text-foreground"
                }`}
              >
                {chat.title}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* User Section */}
      <div className="border-t border-border px-3 py-3">
        <div className="flex items-center gap-3 rounded-lg px-3 py-2 hover:bg-surface-hover cursor-pointer">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent/15 text-xs font-medium text-accent">
            U
          </div>
          <span className="truncate text-sm text-text-secondary">User</span>
        </div>
      </div>
    </aside>
  );
}
