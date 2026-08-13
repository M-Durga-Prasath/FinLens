"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useSearchParams } from "next/navigation";
import ShapeGrid from "../../components/ShapeGrid";

export default function SignInPage() {
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") || "/chat";
  const error = searchParams.get("error");

  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [provider, setProvider] = useState(null); // track which button is loading

  const handleGoogleSignIn = async () => {
    setProvider("google");
    setIsLoading(true);
    await signIn("google", { callbackUrl });
  };

  const handleEmailSignIn = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    setProvider("resend");
    setIsLoading(true);
    await signIn("resend", { email, callbackUrl });
  };

  return (
    <div className="relative flex flex-1 flex-col items-center justify-center overflow-hidden">
      {/* Background grid */}
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

      {/* Radial fade */}
      <div
        className="pointer-events-none absolute inset-0 z-1"
        style={{
          background:
            "radial-gradient(ellipse at center, rgba(10,10,10,0.9) 0%, rgba(10,10,10,0.5) 70%, rgba(10,10,10,0.2) 100%)",
        }}
      />

      {/* Sign-in card */}
      <div className="relative z-2 w-full max-w-sm px-6">
        <div className="rounded-2xl border border-border/60 bg-surface/80 p-8 shadow-2xl shadow-black/40 backdrop-blur-xl">
          {/* Logo */}
          <div className="mb-6 flex items-center justify-center gap-2.5">
            <svg
              width="28"
              height="28"
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
            <span className="text-xl font-semibold tracking-tight text-foreground">
              Fin<span className="text-accent">Lens</span>
            </span>
          </div>

          <h1 className="mb-1 text-center text-lg font-semibold text-foreground">
            Welcome back
          </h1>
          <p className="mb-8 text-center text-sm text-text-secondary">
            Sign in to continue to FinLens
          </p>

          {/* Error message */}
          {error && (
            <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
              {error === "OAuthAccountNotLinked"
                ? "This email is already associated with another sign-in method."
                : error === "Verification"
                ? "The magic link has expired or has already been used."
                : "An error occurred during sign-in. Please try again."}
            </div>
          )}

          {/* Google button */}
          <button
            onClick={handleGoogleSignIn}
            disabled={isLoading}
            className="flex w-full items-center justify-center gap-3 rounded-lg border border-border bg-surface-raised px-4 py-3 text-sm font-medium text-foreground transition-all hover:border-accent/30 hover:bg-surface-hover disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading && provider === "google" ? (
              <Spinner />
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24">
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
              </svg>
            )}
            Continue with Google
          </button>

          {/* Divider */}
          <div className="my-6 flex items-center gap-3">
            <div className="h-px flex-1 bg-border" />
            <span className="text-xs text-text-tertiary">or</span>
            <div className="h-px flex-1 bg-border" />
          </div>

          {/* Magic link form */}
          <form onSubmit={handleEmailSignIn} className="flex flex-col gap-3">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
              required
              disabled={isLoading}
              className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground placeholder-text-tertiary outline-none transition-colors focus:border-accent/50 focus:ring-1 focus:ring-accent/20 disabled:cursor-not-allowed disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isLoading || !email.trim()}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-accent px-4 py-3 text-sm font-semibold text-background transition-all hover:bg-accent-dim hover:shadow-lg hover:shadow-accent/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading && provider === "resend" ? (
                <Spinner dark />
              ) : (
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <rect x="1" y="3" width="14" height="10" rx="1.5" />
                  <path d="M1 4.5L8 9l7-4.5" />
                </svg>
              )}
              Send magic link
            </button>
          </form>

          <p className="mt-6 text-center text-xs leading-relaxed text-text-tertiary">
            We&apos;ll email you a link to sign in — no password needed.
          </p>
        </div>
      </div>
    </div>
  );
}

function Spinner({ dark = false }) {
  return (
    <svg
      className="animate-spin"
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
    >
      <circle
        cx="8"
        cy="8"
        r="6"
        stroke={dark ? "rgba(10,10,10,0.3)" : "rgba(255,255,255,0.2)"}
        strokeWidth="2"
      />
      <path
        d="M14 8a6 6 0 00-6-6"
        stroke={dark ? "#0a0a0a" : "#ffffff"}
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}
