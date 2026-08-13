import { auth } from "@/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";

export async function GET(req, { params }) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id } = await params;

    const chatSession = await prisma.session.findUnique({
      where: { id },
      include: {
        messages: {
          orderBy: { createdAt: "asc" },
          select: {
            id: true,
            role: true,
            content: true,
            createdAt: true,
          },
        },
      },
    });

    if (!chatSession) {
      return NextResponse.json({ error: "Session not found" }, { status: 404 });
    }

    if (chatSession.userId !== session.user.id) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    return NextResponse.json(chatSession);
  } catch (error) {
    console.error("Error fetching session details:", error);
    return NextResponse.json(
      { error: "Failed to fetch session" },
      { status: 500 }
    );
  }
}

export async function PATCH(req, { params }) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id } = await params;
    const body = await req.json();
    const { title } = body;

    if (!title || typeof title !== "string") {
      return NextResponse.json(
        { error: "Title is required" },
        { status: 400 }
      );
    }

    const chatSession = await prisma.session.findUnique({
      where: { id },
    });

    if (!chatSession) {
      return NextResponse.json({ error: "Session not found" }, { status: 404 });
    }

    if (chatSession.userId !== session.user.id) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const updated = await prisma.session.update({
      where: { id },
      data: { title: title.trim() },
      select: {
        id: true,
        title: true,
        updatedAt: true,
      },
    });

    return NextResponse.json(updated);
  } catch (error) {
    console.error("Error updating session title:", error);
    return NextResponse.json(
      { error: "Failed to update session" },
      { status: 500 }
    );
  }
}

export async function DELETE(req, { params }) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id } = await params;

    const chatSession = await prisma.session.findUnique({
      where: { id },
    });

    if (!chatSession) {
      return NextResponse.json({ error: "Session not found" }, { status: 404 });
    }

    if (chatSession.userId !== session.user.id) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    await prisma.session.delete({
      where: { id },
    });

    return NextResponse.json({ success: true, id });
  } catch (error) {
    console.error("Error deleting session:", error);
    return NextResponse.json(
      { error: "Failed to delete session" },
      { status: 500 }
    );
  }
}
