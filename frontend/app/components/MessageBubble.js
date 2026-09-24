"use client";

export default function MessageBubble({ role, content, isStreaming, isError }) {
  const isUser = role === "user";

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? "bg-surface-raised text-foreground"
            : isError
              ? "border-l-2 border-red-400/60 bg-red-500/5 text-red-300"
              : "border-l-2 border-accent bg-surface text-foreground"
        }`}
      >
        {!isUser && (
          <span
            className={`mb-1 block text-xs font-medium ${
              isError ? "text-red-400" : "text-accent"
            }`}
          >
            FinLens
          </span>
        )}
        <p className="whitespace-pre-wrap">
          {content}
          {isStreaming && (
            <span className="ml-0.5 inline-block h-4 w-[2px] translate-y-[3px] animate-pulse bg-accent" />
          )}
        </p>
      </div>
    </div>
  );
}
