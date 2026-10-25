import { auth } from "@/auth";
import { prisma } from "@/lib/prisma";
import { readLimiter } from "@/lib/rateLimit";
import { NextResponse } from "next/server";

export async function GET(req, { params }) {
  try {
    const blocked = await readLimiter.check(req);
    if (blocked) return blocked;

    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id } = await params;

    const chunk = await prisma.chunk.findUnique({
      where: { id },
      select: {
        chunkIndex: true,
        document: {
          select: {
            userId: true,
          },
        },
      },
    });

    if (!chunk) {
      return NextResponse.json({ error: "Chunk not found" }, { status: 404 });
    }

    if (chunk.document.userId !== session.user.id) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    return NextResponse.json({
      chunkIndex: chunk.chunkIndex,
    });
  } catch (error) {
    console.error("Failed to fetch chunk:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
