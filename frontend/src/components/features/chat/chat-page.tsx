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
  type ReactNode,
} from "react";
import { Bot, Loader2, Send, Sparkles, User } from "lucide-react";
import { toast } from "sonner";

import { FamilyMemberFilter } from "@/components/documents";
import { PageHeader } from "@/components/shared";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useAskChat } from "@/hooks/use-chat";
import { ApiError } from "@/lib/api/errors";
import { formatDate, formatDocumentType } from "@/lib/format";
import { isRateLimitError } from "@/lib/processing";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/stores/ui-store";
import type { ChatAskResponse, ChatCitation } from "@/types/api";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: ChatAskResponse;
};

const SUGGESTIONS = [
  "What were the latest lab results?",
  "List medications from recent prescriptions.",
  "Summarize John Doe's blood work.",
  "Were any values outside the reference range?",
] as const;

function isBulletLine(line: string): boolean {
  return /^[-*•]\s+/.test(line.trim());
}

function AnswerBody({ content }: { content: string }) {
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

        return (
          <p
            key={`block-${blockIndex}`}
            className="whitespace-pre-wrap text-[0.9375rem] leading-7 text-pretty"
          >
            {block}
          </p>
        );
      })}
    </div>
  );
}

function CitationCard({ citation }: { citation: ChatCitation }) {
  return (
    <Link
      href={`/documents/${citation.document_id}`}
      className="group block rounded-xl border border-border/70 bg-background/80 p-3 transition-colors hover:border-brand-accent/40 hover:bg-accent/40"
    >
      <p className="truncate text-sm font-medium text-foreground group-hover:text-primary">
        {citation.original_filename}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">
        {formatDocumentType(citation.document_type)}
        {citation.document_date
          ? ` · ${formatDate(citation.document_date)}`
          : ""}
        {citation.page ? ` · p. ${citation.page}` : ""}
      </p>
      {citation.excerpt ? (
        <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-muted-foreground">
          {citation.excerpt}
        </p>
      ) : null}
    </Link>
  );
}

function SupportingDetailsPanel({
  details,
}: {
  details: NonNullable<ChatAskResponse["supporting_details"]>;
}) {
  const sections = [
    { label: "Patient", value: details.patient },
    { label: "Doctor", value: details.doctor },
    { label: "Hospital", value: details.hospital },
    { label: "Diagnosis", value: details.diagnosis },
    { label: "Follow-up", value: details.follow_up },
  ].filter((section) => section.value);

  const lists = [
    { label: "Medicines", items: details.medicines },
    { label: "Lab values", items: details.lab_values },
    { label: "Procedures", items: details.procedures },
  ].filter((section) => section.items.length > 0);

  if (sections.length === 0 && lists.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3 border-t border-border/50 pt-3">
      <p className="text-xs font-medium text-muted-foreground">
        Supporting details
      </p>
      {sections.length > 0 ? (
        <dl className="grid gap-2 sm:grid-cols-2">
          {sections.map((section) => (
            <div key={section.label} className="rounded-lg bg-muted/40 px-3 py-2">
              <dt className="text-[0.6875rem] font-medium text-muted-foreground">
                {section.label}
              </dt>
              <dd className="mt-0.5 text-sm text-foreground">{section.value}</dd>
            </div>
          ))}
        </dl>
      ) : null}
      {lists.map((section) => (
        <div key={section.label}>
          <p className="mb-1 text-xs font-medium text-muted-foreground">
            {section.label}
          </p>
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
            {section.items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

function TimelinePanel({
  timeline,
}: {
  timeline: ChatAskResponse["timeline"];
}) {
  if (!timeline.length) return null;

  return (
    <div className="space-y-2 border-t border-border/50 pt-3">
      <p className="text-xs font-medium text-muted-foreground">
        Related timeline
      </p>
      <ul className="space-y-2">
        {timeline.map((entry, index) => (
          <li
            key={`${entry.date ?? "unknown"}-${entry.label ?? "event"}-${index}`}
            className="rounded-lg border border-border/60 bg-background/60 px-3 py-2"
          >
            <p className="text-sm font-medium text-foreground">
              {entry.label ?? "Event"}
            </p>
            <p className="text-xs text-muted-foreground">
              {entry.date ? formatDate(entry.date) : "Date unknown"}
              {entry.detail ? ` · ${entry.detail}` : ""}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex gap-3",
        isUser ? "justify-end" : "justify-start",
      )}
    >
      {!isUser ? (
        <div className="mt-1 flex size-9 shrink-0 items-center justify-center rounded-xl bg-accent text-primary ring-1 ring-brand-accent/20">
          <Bot className="size-4" aria-hidden />
        </div>
      ) : null}

      <div
        className={cn(
          "max-w-[min(100%,42rem)] space-y-3 rounded-2xl px-4 py-3.5 shadow-tinted",
          isUser
            ? "rounded-br-md bg-primary text-primary-foreground"
            : "rounded-bl-md border border-border/60 bg-card text-card-foreground",
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap text-[0.9375rem] leading-7 text-pretty">
            {message.content}
          </p>
        ) : (
          <AnswerBody content={message.content} />
        )}

        {message.response?.insufficient_context ? (
          <p
            className={cn(
              "text-xs leading-relaxed",
              isUser ? "opacity-80" : "text-muted-foreground",
            )}
          >
            Limited matching documents were found for this question. Try a more
            specific ask, or upload related records.
          </p>
        ) : null}

        {message.response?.supporting_details ? (
          <SupportingDetailsPanel details={message.response.supporting_details} />
        ) : null}

        {message.response?.timeline?.length ? (
          <TimelinePanel timeline={message.response.timeline} />
        ) : null}

        {message.response?.citations.length ? (
          <div className="space-y-2 border-t border-border/50 pt-3">
            <p className="text-xs font-medium text-muted-foreground">
              Sources from your vault
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              {message.response.citations.map((citation) => (
                <CitationCard
                  key={`${citation.document_id}-${citation.score}`}
                  citation={citation}
                />
              ))}
            </div>
          </div>
        ) : null}
      </div>

      {isUser ? (
        <div className="mt-1 flex size-9 shrink-0 items-center justify-center rounded-xl bg-muted text-muted-foreground ring-1 ring-border/70">
          <User className="size-4" aria-hidden />
        </div>
      ) : null}
    </div>
  );
}

function ChatEmptyState({
  onSelect,
}: {
  onSelect: (prompt: string) => void;
}) {
  return (
    <div className="flex h-full min-h-[18rem] flex-col items-center justify-center px-4 py-10 text-center">
      <div className="mb-5 flex size-14 items-center justify-center rounded-2xl bg-accent text-primary ring-1 ring-brand-accent/25 shadow-tinted">
        <Sparkles className="size-6" aria-hidden />
      </div>
      <h2 className="font-heading text-xl font-semibold tracking-tight text-foreground">
        Ask about your family&apos;s records
      </h2>
      <p className="mt-2 max-w-md text-sm leading-relaxed text-muted-foreground text-pretty">
        Answers stay grounded in uploaded documents, with citations so you can
        open the source.
      </p>
      <div className="mt-8 grid w-full max-w-xl gap-2 sm:grid-cols-2">
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => onSelect(suggestion)}
            className="rounded-xl border border-border/70 bg-background/70 px-3.5 py-3 text-left text-sm leading-snug text-foreground shadow-tinted transition-colors hover:border-brand-accent/35 hover:bg-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}

function ThinkingIndicator() {
  return (
    <div className="flex items-center gap-3 text-sm text-muted-foreground">
      <div className="flex size-9 items-center justify-center rounded-xl bg-accent text-primary ring-1 ring-brand-accent/20">
        <Loader2 className="size-4 animate-spin" aria-hidden />
      </div>
      <div className="rounded-2xl rounded-bl-md border border-border/60 bg-card px-4 py-3 shadow-tinted">
        Reading your vault and drafting an answer...
      </div>
    </div>
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
    (state) => state.selectedFamilyMemberId,
  );
  const notifyLlmRateLimited = useUiStore((state) => state.notifyLlmRateLimited);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, askChat.isPending]);

  const sendQuestion = useCallback(
    async (raw: string) => {
      const trimmed = raw.trim();
      if (!trimmed || askChat.isPending) return;

      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
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

        setMessages((current) => [
          ...current,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: response.answer,
            response,
          },
        ]);
      } catch (error) {
        const message =
          error instanceof ApiError
            ? error.message
            : "Unable to get an answer right now.";

        if (isRateLimitError(message) || (error instanceof ApiError && error.status === 429)) {
          notifyLlmRateLimited({
            key: `chat:${Date.now()}`,
            source: "chat",
            detail: message,
          });
        } else {
          toast.error(message);
        }

        setMessages((current) =>
          current.filter((item) => item.id !== userMessage.id),
        );
        setQuestion(trimmed);
        textareaRef.current?.focus();
      }
    },
    [askChat, notifyLlmRateLimited, selectedFamilyMemberId],
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
        title="AI Chat"
        description="Ask about diagnoses, medications, and labs. Answers cite documents from your vault."
        actions={<FamilyMemberFilter className="w-full sm:w-56" />}
      />

      <section className="surface-panel flex min-h-[min(36rem,calc(100dvh-12rem))] flex-1 flex-col overflow-hidden rounded-2xl lg:min-h-0">
        <header className="flex shrink-0 items-start justify-between gap-4 border-b border-border/60 px-4 py-3.5 sm:px-5">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <div className="flex size-8 items-center justify-center rounded-xl bg-accent text-primary ring-1 ring-brand-accent/20">
                <Bot className="size-4" aria-hidden />
              </div>
              <h2 className="font-heading text-base font-semibold tracking-tight">
                Medical assistant
              </h2>
            </div>
            <p className="mt-1 text-xs text-muted-foreground sm:text-sm">
              Grounded in your uploaded records. Not a substitute for
              professional medical advice.
            </p>
          </div>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-5 sm:px-5">
          {messages.length === 0 && !askChat.isPending ? (
            <ChatEmptyState
              onSelect={(prompt) => {
                setQuestion(prompt);
                textareaRef.current?.focus();
              }}
            />
          ) : (
            <div className="mx-auto flex max-w-3xl flex-col gap-5">
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              {askChat.isPending ? <ThinkingIndicator /> : null}
              <div ref={scrollAnchorRef} />
            </div>
          )}
        </div>

        <form
          id={formId}
          onSubmit={handleSubmit}
          className="shrink-0 border-t border-border/60 bg-muted/30 px-4 py-4 sm:px-5"
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
                className="min-h-[4.5rem] resize-none border-0 bg-transparent p-1 shadow-none focus-visible:ring-0"
              />
              <div className="mt-2 flex items-center justify-between gap-3">
                <p className="text-[0.6875rem] text-muted-foreground">
                  Enter to send · Shift+Enter for a new line
                </p>
                <Button
                  type="submit"
                  size="sm"
                  className="rounded-xl"
                  disabled={!question.trim() || askChat.isPending}
                >
                  {askChat.isPending ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Send className="size-4" />
                  )}
                  {askChat.isPending ? "Thinking" : "Ask"}
                </Button>
              </div>
            </div>
          </div>
        </form>
      </section>
    </div>
  );
}
