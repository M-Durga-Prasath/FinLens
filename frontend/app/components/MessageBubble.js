"use client";

export default function MessageBubble({ role, content }) {
  const isUser = role === "user";

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? "bg-surface-raised text-foreground"
            : "border-l-2 border-accent bg-surface text-foreground"
        }`}
      >
        {!isUser && (
          <span className="mb-1 block text-xs font-medium text-accent">
            FinLens
          </span>
        )}
        <p className="whitespace-pre-wrap">{content}</p>
      </div>
    </div>
  );
}
