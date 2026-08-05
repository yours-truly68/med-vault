"use client";

import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  Send,
  User,
  AlertCircle,
  RotateCcw,
  Maximize2,
  Minimize2,
  X,
  Compass,
  ThumbsUp,
  ThumbsDown,
  Copy,
  Square,
  Paperclip,
  Mic,
  ArrowDown,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useCopilotContext } from "@/hooks/use-copilot-context";
import { ApiError } from "@/lib/api/errors";
import { isRateLimitError } from "@/lib/processing";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";
import {
  useCopilotStore,
  type CopilotMessage,
} from "@/stores/copilot-store";
import { useUiStore } from "@/stores/ui-store";

import { parseToolActionsFromResponse, executeCopilotToolAction } from "@/lib/copilot/action-dispatcher";
import { copilotTelemetry } from "@/lib/copilot/telemetry";

import { SourcesDrawer } from "@/components/features/chat/sources-drawer";
import { SupportingDetailsCards } from "@/components/features/chat/supporting-details-cards";
import { SuggestedQuestionsChips } from "@/components/features/chat/suggested-questions";
import { ThinkingStateProgress } from "@/components/features/chat/thinking-indicator";
import { SuggestedNavigationAction } from "./navigation-action";
import { ProactiveInsightsBanner } from "./proactive-insights";

const LIGHTWEIGHT_SUGGESTED_PROMPTS = [
  "Summarize my latest blood report",
  "Show abnormal lab values",
  "Compare my last two reports",
  "Explain my diabetes diagnosis",
  "What changed since last visit?",
];

function isBulletLine(line: string): boolean {
  return /^[-*•]\s+/.test(line.trim());
}

function CopilotAnswerBody({
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

  if (blocks.length === 0) return null;

  return (
    <div className="space-y-2.5">
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
              className="list-disc space-y-1 pl-4 text-xs sm:text-sm leading-relaxed"
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
            className="whitespace-pre-wrap text-xs sm:text-sm leading-relaxed text-pretty"
          >
            {block}
            {isStreaming && isLastBlock ? (
              <span className="inline-block w-1.5 h-3.5 ml-1 bg-brand-accent animate-pulse vertical-middle rounded-sm" />
            ) : null}
          </p>
        );
      })}
    </div>
  );
}

function CopilotBubble({
  message,
  onSelectPrompt,
  onRetry,
}: {
  message: CopilotMessage;
  onSelectPrompt: (prompt: string) => void;
  onRetry?: (query: string) => void;
}) {
  const isUser = message.role === "user";
  const router = useRouter();
  const [rated, setRated] = useState<"up" | "down" | null>(null);

  const toolActions = !isUser && message.content ? parseToolActionsFromResponse(message.content) : [];

  const handleRating = (rating: "up" | "down") => {
    setRated(rating);
    copilotTelemetry.track({
      type: "satisfaction_rating",
      messageId: message.id,
      rating,
    });
    toast.success("Thank you for your feedback!");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.15 }}
      className={cn("flex gap-2.5", isUser ? "justify-end" : "justify-start")}
    >
      {!isUser ? (
        <div className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-accent text-primary ring-1 ring-brand-accent/25 shadow-xs">
          <Bot className="size-3.5 text-brand-accent" aria-hidden />
        </div>
      ) : null}

      <div
        className={cn(
          "max-w-[min(100%,44rem)] space-y-2.5 rounded-2xl px-3.5 py-2.5 shadow-xs transition-all",
          isUser
            ? "rounded-br-xs bg-primary text-primary-foreground text-xs sm:text-sm leading-relaxed"
            : "rounded-bl-xs border border-border/70 bg-card text-card-foreground"
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : message.error ? (
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-destructive">
              <AlertCircle className="size-3.5" />
              <span>Response Stream Interrupted</span>
            </div>
            <p className="text-xs text-muted-foreground">{message.error}</p>
            {onRetry ? (
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => onRetry(message.content)}
                className="rounded-lg text-xs h-6 px-2 gap-1"
              >
                <RotateCcw className="size-3" />
                <span>Retry</span>
              </Button>
            ) : null}
          </div>
        ) : (
          <CopilotAnswerBody content={message.content} />
        )}

        {/* Proactive Grounded Insights */}
        {!isUser && message.response ? (
          <ProactiveInsightsBanner response={message.response} />
        ) : null}

        {/* Tool Actions Dispatcher Chips */}
        {!isUser && toolActions.length > 0 ? (
          <div className="flex flex-wrap gap-1 pt-0.5">
            {toolActions.map((act, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  copilotTelemetry.track({
                    type: "tool_action_executed",
                    actionType: act.type,
                  });
                  executeCopilotToolAction(act, router);
                }}
                className="inline-flex items-center gap-1 rounded-full border border-brand-accent/40 bg-accent/30 px-2.5 py-0.5 text-xs font-semibold text-primary hover:bg-accent transition-colors"
              >
                <span>⚡ {act.label}</span>
              </button>
            ))}
          </div>
        ) : null}

        {/* Suggested Navigation Action */}
        {!isUser && message.content ? (
          <SuggestedNavigationAction content={message.content} />
        ) : null}

        {/* Supporting Details */}
        {message.response?.supporting_details ? (
          <SupportingDetailsCards details={message.response.supporting_details} />
        ) : null}

        {/* Collapsible Sources Drawer */}
        {message.response?.citations?.length ? (
          <SourcesDrawer citations={message.response.citations} />
        ) : null}

        {/* Contextual Follow-up Chips & Feedback */}
        {!isUser && message.response ? (
          <div className="space-y-1.5 border-t border-border/40 pt-2">
            <SuggestedQuestionsChips
              response={message.response}
              onSelect={onSelectPrompt}
            />

            <div className="flex items-center justify-between text-[0.6875rem] text-muted-foreground pt-0.5">
              <span>Was this answer helpful?</span>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => {
                    if (message.content) {
                      navigator.clipboard.writeText(message.content);
                      toast.success("Answer copied to clipboard");
                    }
                  }}
                  className="p-1 rounded hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
                  title="Copy answer"
                >
                  <Copy className="size-3" />
                </button>
                <button
                  type="button"
                  onClick={() => handleRating("up")}
                  className={cn(
                    "p-1 rounded hover:bg-muted transition-colors",
                    rated === "up" && "text-emerald-500 font-bold"
                  )}
                  title="Helpful"
                >
                  <ThumbsUp className="size-3" />
                </button>
                <button
                  type="button"
                  onClick={() => handleRating("down")}
                  className={cn(
                    "p-1 rounded hover:bg-muted transition-colors",
                    rated === "down" && "text-destructive font-bold"
                  )}
                  title="Not helpful"
                >
                  <ThumbsDown className="size-3" />
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </div>

      {isUser ? (
        <div className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground ring-1 ring-border/70">
          <User className="size-3.5" aria-hidden />
        </div>
      ) : null}
    </motion.div>
  );
}

export function CopilotWindow() {
  const formId = useId();
  const [question, setQuestion] = useState("");
  const [isNearBottom, setIsNearBottom] = useState(true);

  const context = useCopilotContext();

  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const scrollAnchorRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const {
    messages,
    mode,
    chatState,
    setMode,
    setIsOpen,
    setChatState,
    setThinkingStage,
    addMessage,
    updateMessage,
    clearMessages,
  } = useCopilotStore();

  const notifyLlmRateLimited = useUiStore((state) => state.notifyLlmRateLimited);

  const handleScroll = useCallback(() => {
    if (!scrollContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    const distanceFromBottom = scrollHeight - (scrollTop + clientHeight);
    setIsNearBottom(distanceFromBottom < 60);
  }, []);

  const scrollToBottom = useCallback(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    if (isNearBottom) {
      scrollToBottom();
    }
  }, [messages, chatState, isNearBottom, scrollToBottom]);

  // Request Cancellation Handler
  const handleStopGenerating = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setChatState("CANCELLED");
    setThinkingStage(null);

    const lastMsg = messages[messages.length - 1];
    if (lastMsg && lastMsg.role === "assistant" && !lastMsg.content) {
      updateMessage(lastMsg.id, {
        content: "Generation stopped by user.",
        error: "Cancelled by user.",
      });
    }

    toast.info("Generation stopped");
    textareaRef.current?.focus();
  }, [messages, setChatState, setThinkingStage, updateMessage]);

  const sendQuestion = useCallback(
    async (raw: string) => {
      const trimmed = raw.trim();
      if (!trimmed || chatState === "CONNECTING" || chatState === "STREAMING") return;

      const userMsgId = crypto.randomUUID();
      const assistantMsgId = crypto.randomUUID();

      abortControllerRef.current = new AbortController();
      setChatState("CONNECTING");
      setThinkingStage("searching");

      addMessage({
        id: userMsgId,
        role: "user",
        content: trimmed,
        pageContext: context.pageTitle,
      });

      addMessage({
        id: assistantMsgId,
        role: "assistant",
        content: "",
      });

      setQuestion("");

      const token = useAuthStore.getState().accessToken;
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

      try {
        const response = await fetch(`${apiBaseUrl}/api/v1/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            question: trimmed,
            family_member_id: context.selectedFamilyMemberId,
          }),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok || !response.body) {
          throw new Error(`Streaming failed with status ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let accumulatedAnswer = "";
        let currentEvent = "";
        let lineBuffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          lineBuffer += decoder.decode(value, { stream: true });
          const lines = lineBuffer.split("\n");
          lineBuffer = lines.pop() ?? "";

          for (const line of lines) {
            const trimmedLine = line.trim();
            if (trimmedLine.startsWith("event: ")) {
              currentEvent = trimmedLine.replace("event: ", "").trim();
            } else if (trimmedLine.startsWith("data: ")) {
              const dataStr = trimmedLine.replace("data: ", "").trim();
              try {
                const data = JSON.parse(dataStr);
                if (currentEvent === "thinking") {
                  setChatState("CONNECTING");
                  if (data.stage) setThinkingStage(data.stage);
                } else if (currentEvent === "token") {
                  setChatState("STREAMING");
                  accumulatedAnswer += data.delta || "";
                  updateMessage(assistantMsgId, {
                    content: accumulatedAnswer,
                  });
                } else if (currentEvent === "metadata") {
                  if (data.citations) {
                    updateMessage(assistantMsgId, {
                      response: {
                        answer: accumulatedAnswer,
                        citations: data.citations,
                      } as any,
                    });
                  }
                } else if (currentEvent === "done") {
                  setChatState("FINISHED");
                  setThinkingStage(null);
                } else if (currentEvent === "error") {
                  setChatState("FAILED");
                  setThinkingStage(null);
                  updateMessage(assistantMsgId, {
                    error: data.detail || "Error streaming response",
                  });
                }
              } catch (e) {
                // Ignore chunk parse errors
              }
            }
          }
        }
      } catch (error: any) {
        if (error?.name === "AbortError") {
          return;
        }

        setChatState("FAILED");
        setThinkingStage(null);

        const message = error?.message || "Unable to connect to Copilot stream.";

        if (isRateLimitError(message)) {
          notifyLlmRateLimited({
            key: `chat:${Date.now()}`,
            source: "chat",
            detail: message,
          });
        } else {
          toast.error(message);
        }

        updateMessage(assistantMsgId, {
          error: message,
        });

        textareaRef.current?.focus();
      }
    },
    [addMessage, chatState, context.pageTitle, context.selectedFamilyMemberId, notifyLlmRateLimited, setChatState, setThinkingStage, updateMessage]
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
    <div className="flex flex-col h-full overflow-hidden bg-background text-foreground">
      {/* Simplified Clean Header Bar */}
      <header className="flex shrink-0 items-center justify-between gap-3 border-b border-border/60 bg-card/95 px-3.5 py-2.5 select-none">
        <div className="title-drag-handle flex items-center gap-2.5 min-w-0 cursor-grab active:cursor-grabbing">
          <div className="flex size-7 items-center justify-center rounded-lg bg-accent text-primary ring-1 ring-brand-accent/25">
            <Bot className="size-3.5 text-brand-accent" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <h3 className="font-heading text-xs font-bold tracking-tight truncate">
                MedVault Copilot
              </h3>
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-1.5 py-0.5 text-[0.625rem] font-bold text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                <span className="size-1 rounded-full bg-emerald-500 animate-pulse" />
                Active
              </span>
            </div>
            <div className="flex items-center gap-1 text-[0.6875rem] text-muted-foreground truncate">
              <Compass className="size-3 text-brand-accent shrink-0" />
              <span className="truncate">{context.pageTitle}</span>
            </div>
          </div>
        </div>

        {/* Minimal Header Controls (Fullscreen, Minimize, Close) */}
        <div className="flex items-center gap-1">
          <Button
            type="button"
            variant="ghost"
            size="icon-xs"
            title={mode === "fullscreen" ? "Exit Fullscreen" : "Fullscreen"}
            onClick={() => setMode(mode === "fullscreen" ? "expanded" : "fullscreen")}
            className="rounded-lg text-muted-foreground hover:text-foreground"
          >
            {mode === "fullscreen" ? (
              <Minimize2 className="size-3.5" />
            ) : (
              <Maximize2 className="size-3.5" />
            )}
          </Button>

          <Button
            type="button"
            variant="ghost"
            size="icon-xs"
            title="Minimize"
            onClick={() => setIsOpen(false)}
            className="rounded-lg text-muted-foreground hover:text-foreground"
          >
            <X className="size-3.5" />
          </Button>
        </div>
      </header>

      {/* Messages Scroll Area */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="relative min-h-0 flex-1 overflow-y-auto overscroll-contain px-3.5 py-4 space-y-3.5"
      >
        {messages.length === 0 ? (
          <div className="mx-auto flex max-w-lg flex-col items-center justify-center text-center py-8 px-2 space-y-4">
            <div className="flex size-10 items-center justify-center rounded-xl bg-accent text-primary ring-1 ring-brand-accent/25 shadow-xs">
              <Sparkles className="size-5 text-brand-accent animate-pulse" />
            </div>
            <div>
              <h3 className="font-heading text-sm font-bold tracking-tight text-foreground">
                How can I assist with your health records?
              </h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                Select a suggested query or ask your own question below.
              </p>
            </div>

            {/* Lightweight Suggested Prompt Chips */}
            <div className="flex flex-wrap items-center justify-center gap-1.5 pt-2 max-w-md">
              {LIGHTWEIGHT_SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => void sendQuestion(prompt)}
                  className="rounded-full border border-border/70 bg-card px-3 py-1.5 text-xs font-semibold text-foreground hover:border-brand-accent/40 hover:bg-accent/40 shadow-2xs transition-all cursor-pointer"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-3.5">
            {messages.map((message) => (
              <CopilotBubble
                key={message.id}
                message={message}
                onSelectPrompt={(prompt) => void sendQuestion(prompt)}
                onRetry={(query) => void sendQuestion(query)}
              />
            ))}

            {chatState === "CONNECTING" ? <ThinkingStateProgress /> : null}
            <div ref={scrollAnchorRef} />
          </div>
        )}

        {/* Floating Scroll to Bottom Button */}
        {!isNearBottom ? (
          <motion.button
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            onClick={scrollToBottom}
            className="sticky bottom-2 left-1/2 -translate-x-1/2 z-20 flex items-center gap-1 rounded-full border border-brand-accent/40 bg-card px-2.5 py-1 text-xs font-bold text-primary shadow-md hover:bg-accent transition-colors"
          >
            <span>Scroll down</span>
            <ArrowDown className="size-3" />
          </motion.button>
        ) : null}
      </div>

      {/* ChatGPT-style Compact Composer */}
      <form
        id={formId}
        onSubmit={handleSubmit}
        className="shrink-0 border-t border-border/60 bg-muted/20 px-3 py-3"
      >
        <div className="mx-auto max-w-3xl">
          <div className="rounded-xl border border-border/80 bg-card p-2.5 shadow-xs focus-within:border-brand-accent/40 focus-within:ring-1 focus-within:ring-ring/30">
            <textarea
              id={`${formId}-question`}
              ref={textareaRef}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`Ask Copilot about ${context.pageTitle}...`}
              rows={2}
              maxLength={4000}
              className="w-full min-h-[2.5rem] max-h-[140px] resize-none border-0 bg-transparent p-0.5 shadow-none focus:outline-none text-xs sm:text-sm leading-relaxed"
            />

            <div className="mt-1.5 flex items-center justify-between gap-2 pt-1 border-t border-border/30">
              <div className="flex items-center gap-1">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-xs"
                  title="Attach report"
                  className="size-6 rounded-md text-muted-foreground hover:text-foreground opacity-60"
                  disabled
                >
                  <Paperclip className="size-3.5" />
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-xs"
                  title="Voice input"
                  className="size-6 rounded-md text-muted-foreground hover:text-foreground opacity-60"
                  disabled
                >
                  <Mic className="size-3.5" />
                </Button>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-[0.625rem] font-medium text-muted-foreground">
                  {question.length} / 4000
                </span>

                {chatState === "CONNECTING" || chatState === "STREAMING" ? (
                  <Button
                    type="button"
                    size="sm"
                    variant="destructive"
                    onClick={handleStopGenerating}
                    className="rounded-lg h-7 text-xs font-semibold px-2.5 gap-1"
                  >
                    <Square className="size-3 fill-current" />
                    <span>Stop</span>
                  </Button>
                ) : (
                  <Button
                    type="submit"
                    size="sm"
                    className="rounded-lg h-7 text-xs font-semibold px-3 gap-1"
                    disabled={!question.trim()}
                  >
                    <Send className="size-3" />
                    <span>Ask</span>
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
