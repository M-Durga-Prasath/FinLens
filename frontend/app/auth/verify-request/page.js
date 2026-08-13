import Link from "next/link";

export const metadata = {
  title: "Check your email — FinLens",
};

export default function VerifyRequestPage() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6">
      <div className="w-full max-w-sm rounded-2xl border border-border/60 bg-surface/80 p-8 text-center shadow-2xl shadow-black/40 backdrop-blur-xl">
        {/* Mail icon */}
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-accent/10">
          <svg
            width="32"
            height="32"
            viewBox="0 0 32 32"
            fill="none"
            stroke="#3ecfb4"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="3" y="6" width="26" height="20" rx="3" />
            <path d="M3 9l13 9 13-9" />
          </svg>
        </div>

        <h1 className="mb-2 text-lg font-semibold text-foreground">
          Check your email
        </h1>
        <p className="mb-6 text-sm leading-relaxed text-text-secondary">
          A sign-in link has been sent to your email address. Click the link in
          the email to sign in to FinLens.
        </p>

        <div className="rounded-lg border border-border/40 bg-background/60 p-4 text-left">
          <p className="text-xs leading-relaxed text-text-tertiary">
            <span className="font-medium text-text-secondary">Tip:</span>{" "}
            If you don&apos;t see the email, check your spam folder. The link
            expires in 24 hours.
          </p>
        </div>

        <Link
          href="/auth/signin"
          className="mt-6 inline-flex items-center gap-1.5 text-sm text-accent hover:text-accent-dim"
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
            <path d="M13 8H3M7 4L3 8l4 4" />
          </svg>
          Back to sign in
        </Link>
      </div>
    </div>
  );
}
