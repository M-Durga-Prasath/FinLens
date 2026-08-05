/*
  Warnings:

  - You are about to drop the column `embeddings` on the `chunks` table. All the data in the column will be lost.
  - You are about to drop the `session` table. If the table is not empty, all the data it contains will be lost.
  - Added the required column `embedding` to the `chunks` table without a default value. This is not possible if the table is not empty.
  - Made the column `content` on table `chunks` required. This step will fail if there are existing NULL values in that column.
  - Made the column `chunkIndex` on table `chunks` required. This step will fail if there are existing NULL values in that column.
  - Made the column `tokenCount` on table `chunks` required. This step will fail if there are existing NULL values in that column.
  - Added the required column `filename` to the `documents` table without a default value. This is not possible if the table is not empty.

*/
-- CreateEnum
CREATE TYPE "DocStatus" AS ENUM ('PROCESSING', 'READY', 'FAILED');

-- DropForeignKey
ALTER TABLE "documents" DROP CONSTRAINT "documents_sessionId_fkey";

-- DropForeignKey
ALTER TABLE "messages" DROP CONSTRAINT "messages_sessionId_fkey";

-- DropForeignKey
ALTER TABLE "session" DROP CONSTRAINT "session_userId_fkey";

-- AlterTable
ALTER TABLE "chunks" DROP COLUMN "embeddings",
ADD COLUMN     "embedding" vector(384) NOT NULL,
ADD COLUMN     "pageNumber" INTEGER,
ALTER COLUMN "content" SET NOT NULL,
ALTER COLUMN "chunkIndex" SET NOT NULL,
ALTER COLUMN "tokenCount" SET NOT NULL;

-- AlterTable
ALTER TABLE "documents" ADD COLUMN     "filename" TEXT NOT NULL,
ADD COLUMN     "filetype" TEXT,
ADD COLUMN     "status" "DocStatus" NOT NULL DEFAULT 'PROCESSING';

-- DropTable
DROP TABLE "session";

-- CreateTable
CREATE TABLE "sessions" (
    "id" UUID NOT NULL,
    "title" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "userId" UUID NOT NULL,

    CONSTRAINT "sessions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "citations" (
    "id" UUID NOT NULL,
    "relevanceScore" DOUBLE PRECISION NOT NULL,
    "chunkId" UUID NOT NULL,
    "messageId" UUID NOT NULL,

    CONSTRAINT "citations_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "sessions_userId_created_at_idx" ON "sessions"("userId", "created_at" DESC);

-- CreateIndex
CREATE INDEX "citations_messageId_idx" ON "citations"("messageId");

-- CreateIndex
CREATE INDEX "citations_chunkId_idx" ON "citations"("chunkId");

-- CreateIndex
CREATE INDEX "chunks_documentId_idx" ON "chunks"("documentId");

-- CreateIndex
CREATE INDEX "documents_sessionId_idx" ON "documents"("sessionId");

-- CreateIndex
CREATE INDEX "documents_userId_idx" ON "documents"("userId");

-- CreateIndex
CREATE INDEX "messages_sessionId_created_at_idx" ON "messages"("sessionId", "created_at");

-- AddForeignKey
ALTER TABLE "sessions" ADD CONSTRAINT "sessions_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "documents" ADD CONSTRAINT "documents_sessionId_fkey" FOREIGN KEY ("sessionId") REFERENCES "sessions"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "messages" ADD CONSTRAINT "messages_sessionId_fkey" FOREIGN KEY ("sessionId") REFERENCES "sessions"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "citations" ADD CONSTRAINT "citations_chunkId_fkey" FOREIGN KEY ("chunkId") REFERENCES "chunks"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "citations" ADD CONSTRAINT "citations_messageId_fkey" FOREIGN KEY ("messageId") REFERENCES "messages"("id") ON DELETE CASCADE ON UPDATE CASCADE;

