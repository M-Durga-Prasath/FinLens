/*
  Warnings:

  - You are about to drop the column `SessionId` on the `documents` table. All the data in the column will be lost.
  - Added the required column `sessionId` to the `documents` table without a default value. This is not possible if the table is not empty.

*/
-- CreateExtension
CREATE EXTENSION IF NOT EXISTS "vector";

-- CreateEnum
CREATE TYPE "Role" AS ENUM ('USER', 'MODEL');

-- DropForeignKey
ALTER TABLE "documents" DROP CONSTRAINT "documents_SessionId_fkey";

-- AlterTable
ALTER TABLE "documents" DROP COLUMN "SessionId",
ADD COLUMN     "sessionId" UUID NOT NULL;

-- CreateTable
CREATE TABLE "messages" (
    "id" UUID NOT NULL,
    "role" "Role" NOT NULL,
    "content" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "sessionId" UUID NOT NULL,

    CONSTRAINT "messages_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "chunks" (
    "id" UUID NOT NULL,
    "embeddings" vector(384) NOT NULL,
    "content" TEXT,
    "chunkIndex" INTEGER,
    "tokenCount" INTEGER,
    "documentId" UUID NOT NULL,

    CONSTRAINT "chunks_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "documents" ADD CONSTRAINT "documents_sessionId_fkey" FOREIGN KEY ("sessionId") REFERENCES "session"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "messages" ADD CONSTRAINT "messages_sessionId_fkey" FOREIGN KEY ("sessionId") REFERENCES "session"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "chunks" ADD CONSTRAINT "chunks_documentId_fkey" FOREIGN KEY ("documentId") REFERENCES "documents"("id") ON DELETE CASCADE ON UPDATE CASCADE;
