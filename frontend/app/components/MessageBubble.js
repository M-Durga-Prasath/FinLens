"use client";

import { useState, useEffect } from "react";

export default function MessageBubble({
  role,
  content,
  isStreaming,
  isError,
  sources,
}) {
  const isUser = role === "user";
  const hasSources = !isUser && Array.isArray(sources) && sources.length > 0;

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
            <span className="ml-0.5 inline-block h-4 w-0.5 translate-y-0.75 animate-pulse bg-accent" />
          )}
        </p>

        {hasSources && (
          <div className="mt-3 flex flex-wrap gap-1.5 border-t border-border/50 pt-3">
            <span className="mr-1 text-[11px] text-text-tertiary self-center">
              Sources:
            </span>
            {sources.map((src) => (
              <CitationBadge key={src.citation_id} source={src} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function CitationBadge({ source }) {
  const [showTooltip, setShowTooltip] = useState(false);
  const [fetchedChunkIndex, setFetchedChunkIndex] = useState(null);

  const filename = source.document_filename || "Unknown file";
  const page = source.page_number;
  const preview = source.content_preview || "";
  const chunkIndex =
    source.chunk_index ??
    source.chunkIndex ??
    fetchedChunkIndex;

  useEffect(() => {
    if (chunkIndex == null && source.chunk_id && showTooltip) {
      let isMounted = true;
      fetch(`/api/chunks/${source.chunk_id}`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (isMounted && data?.chunkIndex != null) {
            setFetchedChunkIndex(data.chunkIndex);
          }
        })
        .catch(() => {});
      return () => {
        isMounted = false;
      };
    }
  }, [chunkIndex, source.chunk_id, showTooltip]);

  return (
    <div
      className="relative"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <span className="inline-flex h-6 min-w-6 cursor-pointer items-center justify-center rounded-md bg-accent/15 px-1.5 text-[11px] font-medium text-accent transition-colors hover:bg-accent/25">
        [{source.citation_id}]
      </span>

      {showTooltip && (
        <div className="absolute bottom-full left-1/2 z-50 mb-2 w-72 -translate-x-1/2 rounded-xl border border-border bg-surface-raised p-3 shadow-xl">
          <div className="absolute -bottom-1.5 left-1/2 h-3 w-3 -translate-x-1/2 rotate-45 border-b border-r border-border bg-surface-raised" />

          {/* Filename */}
          <div className="mb-2 flex items-center gap-1.5">
            <svg
              width="12"
              height="12"
              viewBox="0 0 16 16"
              fill="none"
              className="shrink-0 text-accent"
            >
              <path
                d="M3 1h7l4 4v10a1 1 0 01-1 1H3a1 1 0 01-1-1V2a1 1 0 011-1z"
                stroke="currentColor"
                strokeWidth="1.5"
              />
            </svg>
            <span className="truncate text-xs font-medium text-foreground">
              {filename}
            </span>
          </div>

          {/* Page number & Chunk Index */}
          {(page != null || chunkIndex != null) && (
            <div className="mb-2 flex flex-wrap items-center gap-2">
              {page != null && (
                <div className="flex items-center gap-1.5">
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 16 16"
                    fill="none"
                    className="shrink-0 text-text-tertiary"
                  >
                    <rect
                      x="2"
                      y="1"
                      width="12"
                      height="14"
                      rx="1.5"
                      stroke="currentColor"
                      strokeWidth="1.3"
                    />
                    <path
                      d="M5 5h6M5 8h4"
                      stroke="currentColor"
                      strokeWidth="1"
                      strokeLinecap="round"
                    />
                  </svg>
                  <span className="text-[11px] text-text-secondary">
                    Page {page}
                  </span>
                </div>
              )}

              {chunkIndex != null && (
                <span className="rounded bg-surface px-1.5 py-0.5 text-[10px] font-medium text-text-secondary border border-border/60">
                  Chunk #{chunkIndex}
                </span>
              )}
            </div>
          )}

          {/* Content preview */}
          {preview && (
            <p className="text-[11px] leading-relaxed text-text-secondary/80 line-clamp-3">
              "{preview}"
            </p>
          )}
        </div>
      )}
    </div>
  );
}
