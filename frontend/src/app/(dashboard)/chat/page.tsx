import type { Metadata } from "next";

import { ChatPageContent } from "@/components/features/chat/chat-page";

export const metadata: Metadata = {
  title: "AI Chat",
};

export default function ChatPage() {
  return <ChatPageContent />;
}
