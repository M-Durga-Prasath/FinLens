import { auth } from "@/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";

export async function POST(req, { params }) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id: sessionId } = await params;
    const body = await req.json();
    const { role, content } = body;

    if (!role || !content) {
      return NextResponse.json(
        { error: "Role and content are required" },
        { status: 400 }
      );
    }

    const dbRole = role.toUpperCase();
    if (!["USER", "MODEL"].includes(dbRole)) {
      return NextResponse.json(
        { error: "Invalid role. Must be USER or MODEL" },
        { status: 400 }
      );
    }

    const chatSession = await prisma.session.findUnique({
      where: { id: sessionId },
    });

    if (!chatSession) {
      return NextResponse.json({ error: "Session not found" }, { status: 404 });
    }

    if (chatSession.userId !== session.user.id) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const message = await prisma.message.create({
      data: {
        sessionId,
        role: dbRole,
        content,
      },
    });

    // Touch session updatedAt
    await prisma.session.update({
      where: { id: sessionId },
      data: { updatedAt: new Date() },
    });

    return NextResponse.json(message, { status: 201 });
  } catch (error) {
    console.error("Error creating message:", error);
    return NextResponse.json(
      { error: "Failed to create message" },
      { status: 500 }
    );
  }
}
