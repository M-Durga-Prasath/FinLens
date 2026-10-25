/**
 * Hybrid sliding-window rate limiter for Next.js API routes.
 *
 * - Primary: Upstash Redis (used in production / serverless when env vars are set)
 * - Backup / Dev: In-memory sliding-window store (used if env vars are missing or Redis fails)
 *
 * Optional env vars:
 *   UPSTASH_REDIS_REST_URL
 *   UPSTASH_REDIS_REST_TOKEN
 */

import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";
import { NextResponse } from "next/server";
import { auth } from "@/auth";

const hasUpstashCredentials = Boolean(
  process.env.UPSTASH_REDIS_REST_URL && process.env.UPSTASH_REDIS_REST_TOKEN
);

let redis = null;
if (hasUpstashCredentials) {
  try {
    redis = new Redis({
      url: process.env.UPSTASH_REDIS_REST_URL,
      token: process.env.UPSTASH_REDIS_REST_TOKEN,
    });
  } catch (err) {
    console.warn("[RateLimit] Failed to initialize Upstash Redis:", err?.message);
    redis = null;
  }
}

// ─── In-Memory Backup Store (Used in dev or as fallback) ─────────────────────

const memoryStore = new Map();
const CLEANUP_INTERVAL_MS = 5 * 60 * 1000;
let lastCleanup = Date.now();

function cleanupMemoryStore(windowMs) {
  const now = Date.now();
  if (now - lastCleanup < CLEANUP_INTERVAL_MS) return;
  lastCleanup = now;

  const cutoff = now - windowMs;
  for (const [key, timestamps] of memoryStore.entries()) {
    const valid = timestamps.filter((t) => t > cutoff);
    if (valid.length === 0) {
      memoryStore.delete(key);
    } else {
      memoryStore.set(key, valid);
    }
  }
}

function checkMemoryLimit(key, limit, windowMs) {
  const now = Date.now();
  const cutoff = now - windowMs;
  let timestamps = memoryStore.get(key) || [];
  timestamps = timestamps.filter((t) => t > cutoff);

  if (timestamps.length >= limit) {
    const oldest = timestamps[0];
    const retryAfterSec = Math.max(1, Math.ceil((oldest + windowMs - now) / 1000));
    const resetSec = Math.ceil((oldest + windowMs) / 1000);
    return { success: false, retryAfterSec, resetSec };
  }

  timestamps.push(now);
  memoryStore.set(key, timestamps);
  cleanupMemoryStore(windowMs);

  return { success: true };
}

// ─── Key extraction ──────────────────────────────────────────────────────────

async function getKey(req) {
  try {
    const session = await auth();
    if (session?.user?.id) {
      return `user:${session.user.id}`;
    }
  } catch {
    // Auth not available — fall through to IP
  }

  const forwarded = req.headers.get("x-forwarded-for");
  if (forwarded) {
    return `ip:${forwarded.split(",")[0].trim()}`;
  }

  const realIp = req.headers.get("x-real-ip");
  if (realIp) {
    return `ip:${realIp}`;
  }

  // Fallback for local development
  return "ip:127.0.0.1";
}

function createRateLimitResponse(limit, retryAfterSec, resetSec) {
  return NextResponse.json(
    {
      error: "Too many requests",
      message: `Rate limit exceeded. Try again in ${retryAfterSec} seconds.`,
      retryAfter: retryAfterSec,
    },
    {
      status: 429,
      headers: {
        "Retry-After": String(retryAfterSec),
        "X-RateLimit-Limit": String(limit),
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": String(resetSec),
      },
    },
  );
}

// ─── Rate limiter factory ────────────────────────────────────────────────────

/**
 * Create a rate limiter with the given configuration.
 *
 * @param {Object} options
 * @param {number} options.limit     - Max requests per window (default: 60)
 * @param {number} options.windowMs  - Window size in ms (default: 60000 = 1 min)
 * @param {string} options.prefix    - Key prefix (default: "rl")
 * @returns {{ check: (req: Request) => Promise<NextResponse|null> }}
 */
export function rateLimit({ limit = 60, windowMs = 60_000, prefix = "rl" } = {}) {
  const windowSec = Math.ceil(windowMs / 1000);

  let upstashLimiter = null;
  if (redis) {
    try {
      upstashLimiter = new Ratelimit({
        redis,
        limiter: Ratelimit.slidingWindow(limit, `${windowSec} s`),
        prefix,
      });
    } catch (err) {
      console.warn(`[RateLimit] Failed to create Upstash limiter for ${prefix}:`, err?.message);
    }
  }

  return {
    /**
     * Check if the request is rate-limited.
     * @param {Request} req - The incoming request
     * @returns {Promise<NextResponse|null>} A 429 response if limited, or null if allowed
     */
    async check(req) {
      const key = await getKey(req);

      // 1. Try Upstash Redis if available
      if (upstashLimiter) {
        try {
          const { success, limit: lim, reset } = await upstashLimiter.limit(key);

          if (!success) {
            const retryAfterSec = Math.max(1, Math.ceil((reset - Date.now()) / 1000));
            return createRateLimitResponse(lim, retryAfterSec, Math.ceil(reset / 1000));
          }

          return null; // Allowed by Upstash
        } catch (err) {
          // If Redis throws (network issue, downtime, quota), log and seamlessly fall back to memory
          console.warn(`[RateLimit] Upstash failed (${err?.message}), falling back to memory store.`);
        }
      }

      // 2. Backup / In-memory store (active in local dev or if Upstash fails)
      const memKey = `${prefix}:${key}`;
      const result = checkMemoryLimit(memKey, limit, windowMs);
      if (!result.success) {
        return createRateLimitResponse(limit, result.retryAfterSec, result.resetSec);
      }

      return null; // Allowed by in-memory limiter
    },
  };
}

// ─── Pre-configured limiters for common use cases ────────────────────────────

/** General API routes: 60 req/min */
export const generalLimiter = rateLimit({ limit: 60, windowMs: 60_000, prefix: "rl:gen" });

/** Read-heavy routes (fetching sessions, messages): 90 req/min */
export const readLimiter = rateLimit({ limit: 90, windowMs: 60_000, prefix: "rl:read" });

/** Write routes (creating sessions, messages): 30 req/min */
export const writeLimiter = rateLimit({ limit: 30, windowMs: 60_000, prefix: "rl:write" });

/** Auth-related routes (token generation): 20 req/min */
export const authLimiter = rateLimit({ limit: 20, windowMs: 60_000, prefix: "rl:auth" });
