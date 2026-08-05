"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  Send,
  User,
  AlertCircle,
  RotateCcw,
  Sparkles,
  ShieldCheck,
  FileText,
  Clock,
} from "lucide-react";
import { toast } from "sonner";

import { FamilyMemberFilter } from "@/components/documents";
import { PageHeader } from "@/components/shared";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useAskChat } from "@/hooks/use-chat";
import { ApiError } from "@/lib/api/errors";
import { formatDate } from "@/lib/format";
import { isRateLimitError } from "@/lib/processing";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/stores/ui-store";
import type { ChatAskResponse } from "@/types/api";

import { ChatEmptyStateHero } from "./empty-state";
import { ThinkingStateProgress } from "./thinking-indicator";
import { SourcesDrawer } from "./sources-drawer";
import { SupportingDetailsCards } from "./supporting-details-cards";
import { SuggestedQuestionsChips } from "./suggested-questions";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: ChatAskResponse;
  isStreaming?: boolean;
  error?: string;
};

function isBulletLine(line: string): boolean {
  return /^[-*•]\s+/.test(line.trim());
}

function AnswerBody({
  content,
  isStreaming,
}: {
  content: string;
  isStreaming?: boolean;
}) {
  const blocks = content
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean);

  if (blocks.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      {blocks.map((block, blockIndex) => {
        const lines = block.split("\n").map((line) => line.trimEnd());
        const bulletLines = lines.filter((line) => line.length > 0);

        if (
          bulletLines.length > 0 &&
          bulletLines.every((line) => isBulletLine(line))
        ) {
          return (
            <ul
              key={`block-${blockIndex}`}
              className="list-disc space-y-1.5 pl-5 text-[0.9375rem] leading-relaxed"
            >
              {bulletLines.map((line) => (
                <li key={line} className="text-pretty">
                  {line.replace(/^[-*•]\s+/, "")}
                </li>
              ))}
            </ul>
          );
        }

        const isLastBlock = blockIndex === blocks.length - 1;

        return (
          <p
            key={`block-${blockIndex}`}
            className="whitespace-pre-wrap text-[0.9375rem] leading-7 text-pretty"
          >
            {block}
            {isStreaming && isLastBlock ? (
              <span className="inline-block w-1.5 h-4 ml-1 bg-brand-accent animate-pulse vertical-middle" />
            ) : null}
          </p>
        );
      })}
    </div>
  );
}

function TimelinePanel({
  timeline,
}: {
  timeline: ChatAskResponse["timeline"];
}) {
  if (!timeline || !timeline.length) return null;

  return (
    <div className="space-y-2 border-t border-border/50 pt-3">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
        <Clock className="size-3.5 text-primary" />
        <span>Related Timeline Events</span>
      </div>
      <ul className="space-y-2">
        {timeline.map((entry, index) => (
          <li
            key={`${entry.date ?? "unknown"}-${entry.label ?? "event"}-${index}`}
            className="rounded-lg border border-border/60 bg-card/80 px-3 py-2 text-xs"
          >
            <p className="font-semibold text-foreground">
              {entry.label ?? "Event"}
            </p>
            <p className="mt-0.5 text-muted-foreground">
              {entry.date ? formatDate(entry.date) : "Date unknown"}
              {entry.detail ? ` · ${entry.detail}` : ""}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function MessageBubble({
  message,
  onSelectPrompt,
  onRetry,
}: {
  message: ChatMessage;
  onSelectPrompt: (prompt: string) => void;
  onRetry?: (query: string) => void;
}) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn(
        "flex gap-3",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser ? (
        <div className="mt-1 flex size-9 shrink-0 items-center justify-center rounded-xl bg-accent text-primary ring-1 ring-brand-accent/25 shadow-tinted">
          <Bot className="size-4" aria-hidden />
        </div>
      ) : null}

      <div
        className={cn(
          "max-w-[min(100%,44rem)] space-y-3.5 rounded-2xl px-4 py-3.5 shadow-tinted transition-all",
          isUser
            ? "rounded-br-md bg-primary text-primary-foreground"
            : "rounded-bl-md border border-border/70 bg-card text-card-foreground"
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap text-[0.9375rem] leading-7 text-pretty">
            {message.content}
          </p>
        ) : message.error ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold text-destructive">
              <AlertCircle className="size-4" />
              <span>Response Generation Failed</span>
            </div>
            <p className="text-xs leading-relaxed text-muted-foreground">
              {message.error}
            </p>
            {onRetry ? (
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => onRetry(message.content)}
                className="rounded-xl text-xs gap-1.5"
              >
                <RotateCcw className="size-3.5" />
                <span>Retry Question</span>
              </Button>
            ) : null}
          </div>
        ) : (
          <AnswerBody
            content={message.content}
            isStreaming={message.isStreaming}
          />
        )}

        {/* Insufficient Context Warning */}
        {message.response?.insufficient_context ? (
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs leading-relaxed text-amber-700 dark:text-amber-300">
            Limited matching documents were found in your vault for this query. Try a more specific question or upload additional medical records.
          </div>
        ) : null}

        {/* Extracted Clinical Details */}
        {message.response?.supporting_details && !message.isStreaming ? (
          <SupportingDetailsCards details={message.response.supporting_details} />
        ) : null}

        {/* Timeline Panel */}
        {message.response?.timeline?.length && !message.isStreaming ? (
          <TimelinePanel timeline={message.response.timeline} />
        ) : null}

        {/* Collapsible Sources Drawer */}
        {message.response?.citations?.length && !message.isStreaming ? (
          <SourcesDrawer citations={message.response.citations} />
        ) : null}

        {/* Contextual Follow-up Chips */}
        {!isUser && !message.isStreaming && message.response ? (
          <SuggestedQuestionsChips
            response={message.response}
            onSelect={onSelectPrompt}
          />
        ) : null}
      </div>

      {isUser ? (
        <div className="mt-1 flex size-9 shrink-0 items-center justify-center rounded-xl bg-muted text-muted-foreground ring-1 ring-border/70">
          <User className="size-4" aria-hidden />
        </div>
      ) : null}
    </motion.div>
  );
}

export function ChatPageContent() {
  const formId = useId();
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const askChat = useAskChat();
  const scrollAnchorRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const selectedFamilyMemberId = useUiStore(
    (state) => state.selectedFamilyMemberId
  );
  const notifyLlmRateLimited = useUiStore((state) => state.notifyLlmRateLimited);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, askChat.isPending]);

  // Token-by-token streaming effect simulation for fast, responsive text reveal
  const streamAssistantResponse = useCallback(
    (assistantId: string, fullResponse: ChatAskResponse) => {
      const fullText = fullResponse.answer;
      const chunks = fullText.split(/(?<=\s)/); // Split by word tokens
      let currentIdx = 0;

      const interval = setInterval(() => {
        currentIdx++;
        const currentText = chunks.slice(0, currentIdx).join("");

        setMessages((current) =>
          current.map((msg) =>
            msg.id === assistantId
              ? {
                  ...msg,
                  content: currentText,
                  isStreaming: currentIdx < chunks.length,
                }
              : msg
          )
        );

        if (currentIdx >= chunks.length) {
          clearInterval(interval);
        }
      }, 20); // 20ms per token chunk
    },
    []
  );

  const sendQuestion = useCallback(
    async (raw: string) => {
      const trimmed = raw.trim();
      if (!trimmed || askChat.isPending) return;

      const userMsgId = crypto.randomUUID();
      const assistantMsgId = crypto.randomUUID();

      const userMessage: ChatMessage = {
        id: userMsgId,
        role: "user",
        content: trimmed,
      };

      setMessages((current) => [...current, userMessage]);
      setQuestion("");

      try {
        const response = await askChat.mutateAsync({
          question: trimmed,
          family_member_id: selectedFamilyMemberId,
        });

        // Initialize placeholder assistant message for streaming
        setMessages((current) => [
          ...current,
          {
            id: assistantMsgId,
            role: "assistant",
            content: "",
            response,
            isStreaming: true,
          },
        ]);

        streamAssistantResponse(assistantMsgId, response);
      } catch (error) {
        const message =
          error instanceof ApiError
            ? error.message
            : "Unable to get an answer right now.";

        if (
          isRateLimitError(message) ||
          (error instanceof ApiError && error.status === 429)
        ) {
          notifyLlmRateLimited({
            key: `chat:${Date.now()}`,
            source: "chat",
            detail: message,
          });
        } else {
          toast.error(message);
        }

        // Keep error message inline for friendly UI recovery
        setMessages((current) => [
          ...current,
          {
            id: assistantMsgId,
            role: "assistant",
            content: trimmed,
            error: message,
            isStreaming: false,
          },
        ]);
        textareaRef.current?.focus();
      }
    },
    [askChat, notifyLlmRateLimited, selectedFamilyMemberId, streamAssistantResponse]
  );

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    void sendQuestion(question);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void sendQuestion(question);
    }
  };

  return (
    <div className="flex min-h-0 flex-col gap-4 lg:h-[calc(100dvh-6.5rem)] lg:gap-5">
      <PageHeader
        className="mb-0 shrink-0 border-b-0 pb-0"
        title="MedVault Copilot"
        description="Ask questions about diagnoses, medications, and labs. Answers are grounded in your uploaded records."
        actions={<FamilyMemberFilter className="w-full sm:w-56" />}
      />

      <section className="surface-panel flex min-h-[min(36rem,calc(100dvh-12rem))] flex-1 flex-col overflow-hidden rounded-2xl lg:min-h-0">
        {/* Header bar */}
        <header className="flex shrink-0 items-center justify-between gap-4 border-b border-border/60 px-4 py-3 sm:px-5">
          <div className="flex items-center gap-2.5">
            <div className="flex size-8 items-center justify-center rounded-xl bg-accent text-primary ring-1 ring-brand-accent/20">
              <Bot className="size-4" aria-hidden />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-heading text-sm font-semibold tracking-tight">
                  Medical Copilot
                </h2>
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[0.625rem] font-semibold text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                  <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  RAG Grounded
                </span>
              </div>
              <p className="text-[0.6875rem] text-muted-foreground">
                Grounded in your vault records · Not medical advice
              </p>
            </div>
          </div>
        </header>

        {/* Scrollable messages container */}
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-5 sm:px-5">
          {messages.length === 0 && !askChat.isPending ? (
            <ChatEmptyStateHero
              onSelectPrompt={(prompt) => {
                setQuestion(prompt);
                textareaRef.current?.focus();
              }}
            />
          ) : (
            <div className="mx-auto flex max-w-3xl flex-col gap-5">
              {messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  onSelectPrompt={(prompt) => void sendQuestion(prompt)}
                  onRetry={(query) => void sendQuestion(query)}
                />
              ))}

              {askChat.isPending ? <ThinkingStateProgress /> : null}
              <div ref={scrollAnchorRef} />
            </div>
          )}
        </div>

        {/* Chat input box */}
        <form
          id={formId}
          onSubmit={handleSubmit}
          className="shrink-0 border-t border-border/60 bg-muted/20 px-4 py-4 sm:px-5"
        >
          <div className="mx-auto max-w-3xl">
            <label htmlFor={`${formId}-question`} className="sr-only">
              Ask a question
            </label>
            <div className="rounded-2xl border border-border/80 bg-card p-3 shadow-tinted focus-within:border-brand-accent/40 focus-within:ring-2 focus-within:ring-ring/30">
              <Textarea
                id={`${formId}-question`}
                ref={textareaRef}
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about diagnoses, medications, lab values..."
                rows={2}
                className="min-h-[4.25rem] resize-none border-0 bg-transparent p-1 shadow-none focus-visible:ring-0 text-sm"
              />
              <div className="mt-2 flex items-center justify-between gap-3">
                <p className="text-[0.6875rem] text-muted-foreground">
                  Enter to send · Shift+Enter for a new line
                </p>
                <Button
                  type="submit"
                  size="sm"
                  className="rounded-xl font-medium gap-1.5"
                  disabled={!question.trim() || askChat.isPending}
                >
                  <Send className="size-3.5" />
                  <span>{askChat.isPending ? "Thinking..." : "Ask Copilot"}</span>
                </Button>
              </div>
            </div>
          </div>
        </form>
      </section>
    </div>
  );
}
