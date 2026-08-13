"use client";

import { useState } from "react";
import { useSession, signOut } from "next-auth/react";
import Link from "next/link";

export default function Sidebar({
  chats,
  activeChatId,
  onNewChat,
  onSelectChat,
}) {
  const { data: session } = useSession();
  const user = session?.user;
  const [collapsed, setCollapsed] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const initials = user?.name
    ? user.name
        .split(" ")
        .map((w) => w[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : user?.email?.[0]?.toUpperCase() || "U";

  return (
    <aside
      className="flex h-full shrink-0 flex-col border-r border-border bg-surface transition-all duration-300 ease-in-out"
      style={{ width: collapsed ? 64 : 260 }}
    >
      {/* Header: Logo + Collapse toggle */}
      <div className="flex items-center justify-between px-3 pt-4 pb-3">
        {!collapsed && (
          <Link
            href="/chat"
            className="flex items-center gap-2.5 pl-2 hover:opacity-80"
          >
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
              <circle
                cx="24"
                cy="10"
                r="6"
                stroke="#3ecfb4"
                strokeWidth="2"
                fill="none"
              />
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
        )}

        {/* Collapse / Expand button */}
        <button
          onClick={() => setCollapsed((c) => !c)}
          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-text-secondary transition-colors hover:bg-surface-hover hover:text-foreground ${
            collapsed ? "mx-auto" : ""
          }`}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            className={`transition-transform duration-300 ${collapsed ? "rotate-180" : ""}`}
          >
            <path
              d="M10 3L5 8l5 5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>

      {/* New Chat Button */}
      <div className="px-3 pb-3">
        <button
          onClick={onNewChat}
          className={`flex w-full items-center rounded-lg border border-border text-sm text-text-secondary transition-colors hover:bg-surface-hover hover:text-foreground ${
            collapsed ? "justify-center px-0 py-2.5" : "gap-2 px-3 py-2.5"
          }`}
          title={collapsed ? "New chat" : undefined}
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            className="shrink-0"
          >
            <path
              d="M8 3v10M3 8h10"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
          {!collapsed && "New chat"}
        </button>
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto px-3">
        {chats.length === 0 ? (
          !collapsed && (
            <p className="px-3 py-6 text-center text-xs text-text-tertiary">
              No conversations yet
            </p>
          )
        ) : (
          <div className="flex flex-col gap-0.5">
            {chats.map((chat) => (
              <button
                key={chat.id}
                onClick={() => onSelectChat(chat.id)}
                className={`w-full rounded-lg text-left text-sm transition-colors ${
                  collapsed
                    ? "flex items-center justify-center px-0 py-2"
                    : "truncate px-3 py-2"
                } ${
                  activeChatId === chat.id
                    ? "bg-surface-hover text-foreground"
                    : "text-text-secondary hover:bg-surface-hover hover:text-foreground"
                }`}
                title={collapsed ? chat.title : undefined}
              >
                {collapsed ? (
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="none"
                    className="shrink-0"
                  >
                    <path
                      d="M2 3h12M2 8h8M2 13h10"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                    />
                  </svg>
                ) : (
                  chat.title
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* User Section */}
      <div className="relative border-t border-border px-3 py-3">
        <button
          onClick={() => setShowUserMenu((v) => !v)}
          className={`flex w-full items-center rounded-lg hover:bg-surface-hover cursor-pointer transition-colors ${
            collapsed ? "justify-center px-0 py-2" : "gap-3 px-3 py-2"
          }`}
          title={
            collapsed ? user?.name || user?.email || "User" : undefined
          }
        >
          {user?.image ? (
            <img
              src={user.image}
              alt=""
              className="h-8 w-8 shrink-0 rounded-full object-cover"
              referrerPolicy="no-referrer"
            />
          ) : (
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent/15 text-xs font-medium text-accent">
              {initials}
            </div>
          )}
          {!collapsed && (
            <div className="flex flex-1 flex-col overflow-hidden text-left">
              <span className="truncate text-sm text-foreground">
                {user?.name || "User"}
              </span>
              {user?.email && (
                <span className="truncate text-xs text-text-tertiary">
                  {user.email}
                </span>
              )}
            </div>
          )}
          {!collapsed && (
            <svg
              width="14"
              height="14"
              viewBox="0 0 16 16"
              fill="none"
              className={`shrink-0 text-text-tertiary transition-transform duration-200 ${
                showUserMenu ? "rotate-180" : ""
              }`}
            >
              <path
                d="M4 6l4 4 4-4"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}
        </button>

        {/* User dropdown menu */}
        {showUserMenu && (
          <div
            className={`absolute bottom-full mb-2 rounded-lg border border-border bg-surface-raised p-1 shadow-xl shadow-black/30 ${
              collapsed ? "left-1 w-44" : "left-3 right-3"
            }`}
          >
            {user?.email && collapsed && (
              <div className="border-b border-border px-3 py-2">
                <p className="truncate text-xs text-text-tertiary">
                  {user.email}
                </p>
              </div>
            )}
            <button
              onClick={() => signOut({ callbackUrl: "/" })}
              className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-text-secondary transition-colors hover:bg-surface-hover hover:text-red-400"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 16 16"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M6 2H3a1 1 0 00-1 1v10a1 1 0 001 1h3M11 11l3-3-3-3M14 8H6" />
              </svg>
              Sign out
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
