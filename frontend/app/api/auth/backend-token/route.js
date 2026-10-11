import { auth } from "@/auth";
import { NextResponse } from "next/server";
import { SignJWT } from "jose";

export async function GET() {
  try {
    const secretKey = process.env.BACKEND_AUTH_SECRET;
    const session = await auth();

    if (!secretKey) {
      console.error("BACKEND_AUTH_SECRET is not set");
      return NextResponse.json(
        { error: "Server configuration error" },
        { status: 500 },
      );
    }

    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const secret = new TextEncoder().encode(secretKey);

    const token = await new SignJWT({
      userId: session.user.id,
      email: session.user.email,
    })
      .setProtectedHeader({ alg: "HS256" })
      .setIssuedAt()
      .setExpirationTime("1h")
      .sign(secret);

    return NextResponse.json({ token });
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to issue token", msg: error.message },
      { status: 500 },
    );
  }
}
