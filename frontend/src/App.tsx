import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import { useState, useEffect, useRef, useCallback } from "react";
import { ProcessedEvent } from "@/components/ActivityTimeline";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ChatMessagesView } from "@/components/ChatMessagesView";
import { HumanReviewDialog } from "@/components/HumanReviewDialog";
import { Button } from "@/components/ui/button";

export default function App() {
  const [processedEventsTimeline, setProcessedEventsTimeline] = useState<
    ProcessedEvent[]
  >([]);
  const [historicalActivities, setHistoricalActivities] = useState<
    Record<string, ProcessedEvent[]>
  >({});
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const hasFinalizeEventOccurredRef = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const [forceRender, setForceRender] = useState(0);
  const messageHistoryRef = useRef<Message[]>([]);
  
  // 🔥 HITL状态管理已迁移到thread.interrupt (SDK管理)
  const thread = useStream<{
    messages: Message[];
    initial_search_query_count: number;
    max_research_loops: number;
    reasoning_model: string;
  }, {
    InterruptType: any; // 支持interrupt功能的泛型定义
  }>({
    apiUrl: import.meta.env.DEV
      ? "http://localhost:2024"
      : "http://localhost:8123",
    assistantId: "agent",
    messagesKey: "messages",
    onUpdateEvent: (event: any) => {
      let processedEvent: ProcessedEvent | null = null;
      console.log("onUpdateEvent-event", event);
      
      // 🔥 Interrupt 处理已迁移到thread.interrupt属性检测
      // 影响者营销图事件处理
      if (event.initialize_campaign_info) {
        console.log("onUpdateEvent-initialize_campaign_info", event.initialize_campaign_info);
        processedEvent = {
          title: "📋 初始化活动信息",
          data: `提取活动基本信息: ${event.initialize_campaign_info?.objective || "营销目标"}`,
        };
      } else if (event.auto_clarify_campaign_info) {
        console.log("onUpdateEvent-auto_clarify_campaign_info", event.auto_clarify_campaign_info);
        processedEvent = {
          title: "🤔 智能信息澄清",
          data: event.auto_clarify_campaign_info?.need_clarification 
            ? "需要更多信息补充" 
            : "信息完整，准备进行下一步",
        };
      } else if (event.request_human_review) {
        console.log("onUpdateEvent-request_human_review", event.request_human_review);
        processedEvent = {
          title: "👤 请求人工审核",
          data: "暂停执行，等待人工审核活动信息",
        };
      } else if (event.apply_human_review_result) {
        console.log("onUpdateEvent-apply_human_review_result", event.apply_human_review_result);
        processedEvent = {
          title: "✅ 应用审核结果",
          data: "处理用户审核反馈",
        };
      } else if (event.generate_campaign_plan) {
        console.log("onUpdateEvent-generate_campaign_plan", event.generate_campaign_plan);
        processedEvent = {
          title: "🚀 生成活动计划",
          data: "基于审核通过的信息生成完整活动计划",
        };
        hasFinalizeEventOccurredRef.current = true;
      }
      // 兼容原研究助手事件 (向后兼容)
      else if (event.initialize_campaign) {
        console.log("onUpdateEvent-initialize_campaign", event.initialize_campaign);
        processedEvent = {
          title: "Initializing Campaign",
          data: event.initialize_campaign?.objective || "",
        };
      } else if (event.web_research) {
        const sources = event.web_research.sources_gathered || [];
        const numSources = sources.length;
        const uniqueLabels = [
          ...new Set(sources.map((s: any) => s.label).filter(Boolean)),
        ];
        const exampleLabels = uniqueLabels.slice(0, 3).join(", ");
        processedEvent = {
          title: "Web Research",
          data: `Gathered ${numSources} sources. Related to: ${
            exampleLabels || "N/A"
          }.`,
        };
      } else if (event.reflection) {
        processedEvent = {
          title: "Reflection",
          data: "Analysing Web Research Results",
        };
      } else if (event.finalize_answer) {
        processedEvent = {
          title: "Finalizing Answer",
          data: "Composing and presenting the final answer.",
        };
        hasFinalizeEventOccurredRef.current = true;
      }
      
      if (processedEvent) {
        setProcessedEventsTimeline((prevEvents) => [
          ...prevEvents,
          processedEvent!,
        ]);
      }
    },
    onError: (error: any) => {
      setError(error.message);
    },
  });

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollViewport = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollViewport) {
        scrollViewport.scrollTop = scrollViewport.scrollHeight;
      }
    }
  }, [thread.messages]);

  // 消息状态监控和强制同步
  useEffect(() => {
    console.log("🔄 Messages updated, total count:", thread.messages.length);
    console.log("🔄 Loading state:", thread.isLoading);
    console.log("🔄 Thread state:", {
      error: thread.error,
      isLoading: thread.isLoading
    });
    
    // 更新消息历史记录
    const currentMessages = thread.messages;
    const previousMessages = messageHistoryRef.current;
    
    // 检查消息状态变化
    if (currentMessages.length !== previousMessages.length) {
      console.log(`📈 消息数量变化: ${previousMessages.length} → ${currentMessages.length}`);
      
      // 如果消息数量增加，检查新增消息
      if (currentMessages.length > previousMessages.length) {
        const newMessages = currentMessages.slice(previousMessages.length);
        console.log("📬 新增消息:", newMessages.map(msg => ({
          id: msg.id,
          type: msg.type,
          contentPreview: typeof msg.content === 'string' 
            ? msg.content.substring(0, 100) + '...'
            : msg.content
        })));
      }
    }
    
    // 更新历史记录
    messageHistoryRef.current = [...currentMessages];
    
    // 详细消息记录
    currentMessages.forEach((msg, index) => {
      console.log(`📨 Message ${index + 1}:`, {
        id: msg.id,
        type: msg.type,
        timestamp: new Date().toISOString(),
        contentLength: typeof msg.content === 'string' ? msg.content.length : 0,
        contentPreview: typeof msg.content === 'string' 
          ? msg.content.substring(0, 200) + (msg.content.length > 200 ? '...' : '')
          : msg.content
      });
    });

    // 检查连续AI消息
    if (currentMessages.length >= 2) {
      const lastTwo = currentMessages.slice(-2);
      if (lastTwo.length === 2 && lastTwo[0].type === 'ai' && lastTwo[1].type === 'ai') {
        console.log("🔍 发现连续AI消息，内容对比:");
        console.log("第一条AI ID:", lastTwo[0].id);
        console.log("第二条AI ID:", lastTwo[1].id);
        console.log("内容相同:", lastTwo[0].content === lastTwo[1].content);
        
        // 强制重新渲染以确保显示
        setForceRender(prev => prev + 1);
      }
    }
    
    // 定期状态检查（仅在非加载状态）
    if (!thread.isLoading && currentMessages.length > 0) {
      const checkTimer = setTimeout(() => {
        console.log("⏰ 定期状态检查 - 当前消息数:", thread.messages.length);
      }, 1000);
      
      return () => clearTimeout(checkTimer);
    }
  }, [thread.messages, thread.isLoading, thread.error]);

  useEffect(() => {
    if (
      hasFinalizeEventOccurredRef.current &&
      !thread.isLoading &&
      thread.messages.length > 0
    ) {
      const lastMessage = thread.messages[thread.messages.length - 1];
      if (lastMessage && lastMessage.type === "ai" && lastMessage.id) {
        setHistoricalActivities((prev) => ({
          ...prev,
          [lastMessage.id!]: [...processedEventsTimeline],
        }));
      }
      hasFinalizeEventOccurredRef.current = false;
    }
  }, [thread.messages, thread.isLoading, processedEventsTimeline]);

  const handleSubmit = useCallback(
    (submittedInputValue: string, effort: string, model: string) => {
      if (!submittedInputValue.trim()) return;
      setProcessedEventsTimeline([]);
      hasFinalizeEventOccurredRef.current = false;

      // convert effort to, initial_search_query_count and max_research_loops
      // low means max 1 loop and 1 query
      // medium means max 3 loops and 3 queries
      // high means max 10 loops and 5 queries
      let initial_search_query_count = 0;
      let max_research_loops = 0;
      switch (effort) {
        case "low":
          initial_search_query_count = 1;
          max_research_loops = 1;
          break;
        case "medium":
          initial_search_query_count = 3;
          max_research_loops = 3;
          break;
        case "high":
          initial_search_query_count = 5;
          max_research_loops = 10;
          break;
      }

      const newMessages: Message[] = [
        ...(thread.messages || []),
        {
          type: "human",
          content: submittedInputValue,
          id: Date.now().toString(),
        },
      ];
      console.log("handleSubmit-newMessages", newMessages);
      console.log("handleSubmit-initial_search_query_count", initial_search_query_count);
      console.log("handleSubmit-max_research_loops", max_research_loops);
      console.log("handleSubmit-reasoning_model", model);
      thread.submit({
        messages: newMessages,
        initial_search_query_count: initial_search_query_count,
        max_research_loops: max_research_loops,
        reasoning_model: model,
      });
    },
    [thread]
  );

  const handleCancel = useCallback(() => {
    thread.stop();
    window.location.reload();
  }, [thread]);

  // HITL Resume 处理函数 - 使用LangGraph React SDK
  const handleResume = useCallback(async (decision: boolean) => {
    if (!thread.interrupt) {
      console.error("❌ No interrupt to resume");
      return;
    }

    console.log(`🔄 Resuming execution with decision: ${decision}`);
    
    try {
      // 🔥 使用LangGraph React SDK的thread.submit方法
      thread.submit(undefined, { 
        command: { resume: decision }
      });
      
      console.log(`✅ Resume request sent with decision: ${decision}`);
      
    } catch (error) {
      console.error("❌ Resume error:", error);
      setError(`恢复执行失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  }, [thread]);

  const handleApprove = useCallback(async () => await handleResume(true), [handleResume]);
  const handleReject = useCallback(async () => await handleResume(false), [handleResume]);
  
  const handleInterruptCancel = useCallback(() => {
    // 🔥 SDK管理interrupt状态，取消操作只需要停止当前执行
    console.log("🚫 User cancelled interrupt dialog");
    // 注意：SDK的thread.interrupt由后端状态控制，前端无法直接清除
    // 如果需要真正取消，应该调用thread.stop()或类似方法
  }, []);

  return (
    <div className="flex h-screen bg-neutral-800 text-neutral-100 font-sans antialiased">
      {/* 实时调试信息 */}
      <div className="fixed top-0 right-0 bg-red-900 text-white p-2 text-xs z-50 opacity-75 max-w-xs">
        📊 消息数: {thread.messages.length} | 加载中: {thread.isLoading ? '是' : '否'}
        <br />
        错误: {thread.error ? '有' : '无'} | 强制渲染: {forceRender}
        <br />
        🚫 中断中: {thread.interrupt ? '是' : '否'} | SDK处理中: {thread.isLoading ? '是' : '否'}
        <br />
        历史记录: {messageHistoryRef.current.length}
        <br />
        <div className="text-xs opacity-75">
          {thread.messages.slice(-2).map((msg, idx) => (
            <div key={msg.id} className="truncate">
              {idx + 1}: {msg.type} - {msg.id?.substring(0, 8)}...
            </div>
          ))}
        </div>
      </div>
      <main className="h-full w-full max-w-4xl mx-auto">
          {thread.messages.length === 0 ? (
            <WelcomeScreen
              handleSubmit={handleSubmit}
              isLoading={thread.isLoading}
              onCancel={handleCancel}
            />
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="flex flex-col items-center justify-center gap-4">
                <h1 className="text-2xl text-red-400 font-bold">Error</h1>
                <p className="text-red-400">{JSON.stringify(error)}</p>

                <Button
                  variant="destructive"
                  onClick={() => window.location.reload()}
                >
                  Retry
                </Button>
              </div>
            </div>
          ) : (
            <ChatMessagesView
              messages={thread.messages}
              isLoading={thread.isLoading}
              scrollAreaRef={scrollAreaRef}
              onSubmit={handleSubmit}
              onCancel={handleCancel}
              liveActivityEvents={processedEventsTimeline}
              historicalActivities={historicalActivities}
              forceRender={forceRender}
            />
          )}
      </main>

      {/* 🔥 Human-in-the-Loop (HITL) 审核对话框 - 使用SDK的thread.interrupt */}
      <HumanReviewDialog
        open={!!thread.interrupt}
        payload={thread.interrupt?.value}
        onApprove={handleApprove}
        onReject={handleReject}
        onCancel={handleInterruptCancel}
        isLoading={thread.isLoading}
      />
    </div>
  );
}
