"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

const ERROR_MESSAGES = {
  Configuration:
    "There is a problem with the server configuration. Please contact the administrator.",
  AccessDenied: "Access denied. You do not have permission to sign in.",
  Verification:
    "The magic link has expired or has already been used. Please request a new one.",
  OAuthSignin: "Could not start the Google sign-in flow. Please try again.",
  OAuthCallback:
    "Something went wrong during the Google sign-in callback. Please try again.",
  OAuthAccountNotLinked:
    "This email is already associated with a different sign-in method. Please use the original method you signed up with.",
  Default: "An unexpected error occurred. Please try again.",
};

export default function AuthErrorPage() {
  const searchParams = useSearchParams();
  const errorCode = searchParams.get("error") || "Default";
  const message = ERROR_MESSAGES[errorCode] || ERROR_MESSAGES.Default;

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6">
      <div className="w-full max-w-sm rounded-2xl border border-border/60 bg-surface/80 p-8 text-center shadow-2xl shadow-black/40 backdrop-blur-xl">
        {/* Error icon */}
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-red-500/10">
          <svg
            width="32"
            height="32"
            viewBox="0 0 32 32"
            fill="none"
            stroke="#ef4444"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="16" cy="16" r="12" />
            <path d="M16 10v8M16 22v.01" />
          </svg>
        </div>

        <h1 className="mb-2 text-lg font-semibold text-foreground">
          Authentication Error
        </h1>
        <p className="mb-6 text-sm leading-relaxed text-text-secondary">
          {message}
        </p>

        {errorCode && errorCode !== "Default" && (
          <div className="mb-6 rounded-lg border border-border/40 bg-background/60 px-4 py-3">
            <p className="font-mono text-xs text-text-tertiary">
              Error code:{" "}
              <span className="text-text-secondary">{errorCode}</span>
            </p>
          </div>
        )}

        <Link
          href="/auth/signin"
          className="inline-flex items-center gap-2 rounded-lg bg-accent px-6 py-2.5 text-sm font-semibold text-background transition-all hover:bg-accent-dim hover:shadow-lg hover:shadow-accent/20"
        >
          Try again
        </Link>
      </div>
    </div>
  );
}
