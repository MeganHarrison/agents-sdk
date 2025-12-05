"use client";

import { ChatKit, useChatKit } from "@openai/chatkit-react";

type RagChatKitPanelProps = {
  initialThreadId?: string | null;
  onThreadChange?: (threadId: string | null) => void;
  onResponseEnd?: () => void;
};

const CHATKIT_DOMAIN_KEY =
  process.env.NEXT_PUBLIC_CHATKIT_DOMAIN_KEY ?? "domain_pk_localhost_dev";

export function RagChatKitPanel({
  initialThreadId,
  onThreadChange,
  onResponseEnd,
}: RagChatKitPanelProps) {
  const chatkit = useChatKit({
    api: {
      url: "/rag-chatkit",  // Changed to RAG endpoint
      domainKey: CHATKIT_DOMAIN_KEY,
    },
    composer: {
      placeholder: "Ask about meetings, decisions, or projects...",
    },
    history: {
      enabled: false,
    },
    theme: {
      colorScheme: "light",
      radius: "round",
      density: "normal",
      color: {
        accent: {
          primary: "#2563eb",
          level: 1,
        },
      },
    },
    initialThread: initialThreadId ?? null,
    startScreen: {
      greeting: "Hi! I'm Alleato's AI Chief of Staff. I can help you understand patterns across meetings, track decisions and risks, and provide strategic insights. What would you like to know?",
      prompts: [
        {
          label: "Recent decisions",
          prompt: "What were the key decisions from last week's meetings?"
        },
        {
          label: "Project risks",
          prompt: "Show me risks identified in ASRS projects",
        },
        {
          label: "Pending tasks",
          prompt: "What tasks are pending for our current projects?"
        },
        {
          label: "Pattern analysis",
          prompt: "What patterns do you see in our project delays?"
        },
      ],
    },
    threadItemActions: {
      feedback: false,
    },
    onThreadChange: ({ threadId }) => onThreadChange?.(threadId ?? null),
    onResponseEnd: () => onResponseEnd?.(),
    onError: ({ error }) => {
      console.error("RAG ChatKit error", error);
    },
  });

  return (
    <div className="flex flex-col h-full flex-1 bg-white shadow-sm border border-gray-200 border-t-0 rounded-xl">
      <div className="bg-blue-600 text-white h-12 px-4 flex items-center rounded-t-xl">
        <h2 className="font-semibold text-sm sm:text-base lg:text-lg">
          Alleato Intelligence Chat
        </h2>
      </div>
      <div className="flex-1 overflow-hidden pb-1.5">
        <ChatKit
          control={chatkit.control}
          className="block h-full w-full"
          style={{ height: "100%", width: "100%" }}
        />
      </div>
    </div>
  );
}