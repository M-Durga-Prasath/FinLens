"use client";

import Link from "next/link";
import { useSession } from "next-auth/react";
import ShapeGrid from "./components/ShapeGrid";

export default function Home() {
  const { data: session } = useSession();

  return (
    <div className="relative flex flex-1 flex-col items-center justify-center overflow-hidden">
      {/* ShapeGrid Background */}
      <div className="absolute inset-0 z-0">
        <ShapeGrid
          speed={0.3}
          squareSize={44}
          direction="diagonal"
          borderColor="rgba(62, 207, 180, 0.08)"
          hoverFillColor="rgba(62, 207, 180, 0.15)"
          shape="square"
          hoverTrailAmount={6}
        />
      </div>

      {/* Radial fade overlay — keeps center content readable */}
      <div
        className="pointer-events-none absolute inset-0 z-1"
        style={{
          background:
            "radial-gradient(ellipse at center, rgba(10,10,10,0.85) 0%, rgba(10,10,10,0.4) 70%, rgba(10,10,10,0.2) 100%)",
        }}
      />

      {/* Content */}
      <main className="relative z-2 flex w-full max-w-2xl flex-col items-center px-6 py-20 text-center">
        {/* Logo */}
        <div className="mb-8 flex items-center gap-3">
          <svg
            width="36"
            height="36"
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
          <h1 className="text-4xl font-semibold tracking-tight text-foreground">
            Fin<span className="text-accent">Lens</span>
          </h1>
        </div>

        {/* Tagline */}
        <p className="mb-12 max-w-md text-lg leading-relaxed text-text-secondary">
          Upload your finance PDFs. Ask questions. Get answers grounded in your
          documents.
        </p>

        {/* Features */}
        <div className="mb-14 grid w-full max-w-lg gap-4 text-left sm:grid-cols-1">
          <Feature
            icon={
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path
                  d="M4 2h8l4 4v12a2 2 0 01-2 2H4a2 2 0 01-2-2V4a2 2 0 012-2z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                />
                <path d="M12 2v4h4" stroke="currentColor" strokeWidth="1.5" />
              </svg>
            }
            text="Upload and parse financial documents — PDFs, DOCX, and more"
          />
          <Feature
            icon={
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <rect
                  x="2"
                  y="2"
                  width="7"
                  height="9"
                  rx="1"
                  stroke="currentColor"
                  strokeWidth="1.5"
                />
                <rect
                  x="11"
                  y="2"
                  width="7"
                  height="9"
                  rx="1"
                  stroke="currentColor"
                  strokeWidth="1.5"
                />
                <path
                  d="M6 14v2a2 2 0 002 2h4a2 2 0 002-2v-2"
                  stroke="currentColor"
                  strokeWidth="1.5"
                />
                <circle cx="10" cy="14" r="1" fill="currentColor" />
              </svg>
            }
            text="Ask questions across multiple documents at once"
          />
          <Feature
            icon={
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path
                  d="M2 15l4-4 3 3 4-5 5 6"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <circle
                  cx="16"
                  cy="5"
                  r="2"
                  stroke="currentColor"
                  strokeWidth="1.5"
                />
              </svg>
            }
            text="Get context-aware answers grounded in your actual data"
          />
        </div>

        {/* CTA */}
        <Link
          href="/chat"
          className="group flex items-center gap-2 rounded-lg bg-accent px-7 py-3.5 text-sm font-semibold text-background hover:bg-accent-dim hover:shadow-lg hover:shadow-accent/20"
        >
          Start a conversation
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            className="transition-transform group-hover:translate-x-1"
          >
            <path
              d="M3 8h10M9 4l4 4-4 4"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </Link>
      </main>
    </div>
  );
}

function Feature({ icon, text }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-border/60 bg-background/60 p-4 backdrop-blur-sm transition-colors hover:border-accent/20 hover:bg-background/80">
      <span className="mt-0.5 shrink-0 text-accent">{icon}</span>
      <p className="text-sm leading-relaxed text-text-secondary">{text}</p>
    </div>
  );
}
