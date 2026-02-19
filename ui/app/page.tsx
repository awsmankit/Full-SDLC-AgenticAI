"use client";

import { useEffect, useState, useRef, Fragment } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  Terminal,
  FileText,
  CheckCircle,
  Play,
  Activity,
  Cpu,
  Zap,
  Sparkles,
  X,
  History,
  Sun,
  Moon,
  PauseCircle,
  PlayCircle,
  LayoutGrid,
  Network,
  Square
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import GraphView from "./components/GraphView";
import ArtifactViewer from "./components/ArtifactViewer";
import StreamingThought from "./components/StreamingThought";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Types
type WorkflowEventType =
  | "workflow_start"
  | "workflow_complete"
  | "workflow_paused"
  | "phase_start"
  | "phase_complete"
  | "agent_start"
  | "agent_complete"
  | "artifact_generated"
  | "thought_chunk"
  | "error";

interface WorkflowEvent {
  type: WorkflowEventType;
  data: any;
  timestamp: string;
  // ... other fields
}

// ... (rest of types remain same, just ensure we match context)

interface AgentState {
  name: string;
  role: string;
  status: "idle" | "working" | "done" | "error";
}

interface Artifact {
  filename: string;
  type: string;
  timestamp: string;
  agent?: string;
  path?: string;
}

interface AgentConfig {
  id: string;
  name: string;
  role: string;
  icon: string;
  IconComponent: any;
}

// Map icon strings from backend to Lucide components
const ICON_MAP: Record<string, any> = {
  Bot,
  Activity,
  Cpu,
  Terminal,
  CheckCircle,
  Zap,
  Sparkles,
  Default: Bot
};

const AGENT_COLORS: Record<string, string> = {
  "ProductManager": "group-hover:text-purple-400 group-hover:drop-shadow-[0_0_8px_rgba(192,132,252,0.8)]",
  "TestManager": "group-hover:text-sky-400 group-hover:drop-shadow-[0_0_8px_rgba(56,189,248,0.8)]",
  "TestLead": "group-hover:text-amber-400 group-hover:drop-shadow-[0_0_8px_rgba(251,191,36,0.8)]",
  "AutomationQA": "group-hover:text-emerald-400 group-hover:drop-shadow-[0_0_8px_rgba(52,211,153,0.8)]",
  "ManualQA": "group-hover:text-rose-400 group-hover:drop-shadow-[0_0_8px_rgba(251,113,133,0.8)]",
  "Default": "group-hover:text-gray-400 group-hover:drop-shadow-[0_0_8px_rgba(156,163,175,0.8)]"
};

const THOUGHT_COLORS: Record<string, string> = {
  "ProductManager": "text-purple-600 dark:text-purple-200",
  "TestManager": "text-sky-600 dark:text-sky-200",
  "TestLead": "text-amber-600 dark:text-amber-200",
  "AutomationQA": "text-emerald-600 dark:text-emerald-200",
  "ManualQA": "text-rose-600 dark:text-rose-200",
  "Default": "text-neutral-600 dark:text-neutral-200"
};

interface Run {
  id: string;
  timestamp: string;
  product_idea: string;
  status: string;
  total_tokens?: number;
}

export default function Dashboard() {
  // State
  const [logs, setLogs] = useState<string[]>([]);
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [workflowStatus, setWorkflowStatus] = useState<"idle" | "running" | "paused" | "complete" | "error">("idle");
  const [productIdea, setProductIdea] = useState("Update volume control for new RIC models");
  const [agentThoughts, setAgentThoughts] = useState<Record<string, string>>({});
  const [viewingAgent, setViewingAgent] = useState<string | null>(null);
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null);
  const [artifactContent, setArtifactContent] = useState<string>("");
  const [runs, setRuns] = useState<Run[]>([]);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [agents, setAgents] = useState<AgentConfig[]>([]);
  const [hitlEnabled, setHitlEnabled] = useState(false);
  const [viewMode, setViewMode] = useState<"graph" | "grid">("grid");

  // Refs
  const logsEndRef = useRef<HTMLDivElement>(null);
  const thoughtEndRef = useRef<HTMLDivElement>(null);

  // --- Helper Functions (Hoisted) ---

  const addLog = (msg: string) => {
    setLogs(prev => [...prev.slice(-99), `[${new Date().toLocaleTimeString()}] ${msg}`]);
  };

  const getLogColor = (msg: string) => {
    if (msg.includes("Error") || msg.includes("failed") || msg.includes("❌")) return "text-red-600 dark:text-red-400";
    if (msg.includes("Complete") || msg.includes("Success") || msg.includes("✅")) return "text-green-600 dark:text-green-400";
    if (msg.includes("Agent Active") || msg.includes("🤖")) return "text-sky-600 dark:text-sky-400 font-bold";
    if (msg.includes("Artifact") || msg.includes("📄")) return "text-amber-600 dark:text-yellow-400";
    if (msg.includes("Workflow Started") || msg.includes("🚀")) return "text-purple-600 dark:text-purple-400 font-bold";
    if (msg.includes("Paused") || msg.includes("Resuming")) return "text-yellow-500 font-bold";
    return "text-neutral-600 dark:text-neutral-300";
  };

  const fetchRuns = async () => {
    try {
      const res = await fetch("http://localhost:8000/runs");
      const data = await res.json();
      setRuns(data.runs || []);
    } catch (e) {
      console.error("Failed to fetch runs", e);
    }
  };

  const fetchAgents = async () => {
    try {
      const res = await fetch("http://localhost:8000/agents");
      const data = await res.json();
      // data is { "ProductManager": {...}, "TestManager": {...} }
      const agentList: AgentConfig[] = Object.entries(data).map(([key, agent]: [string, any]) => ({
        id: key, // "ProductManager"
        name: agent.name, // "Aishwarya"
        role: agent.role,
        icon: agent.icon,
        IconComponent: ICON_MAP[agent.icon] || ICON_MAP.Default
      }));
      setAgents(agentList);
    } catch (e) {
      addLog(`Error fetching agents: ${e}`);
    }
  };

  const handleEvent = (event: WorkflowEvent) => {
    const { type, data } = event;

    switch (type) {
      case "workflow_start":
        setWorkflowStatus("running");
        setArtifacts([]);
        setActiveAgent(null);
        setAgentThoughts({});
        setViewingAgent(null);
        if (data.run_id) {
          setCurrentRunId(data.run_id);
          fetchRuns();
        }
        addLog(`🚀 Workflow Started: ${data.product_idea}`);
        break;

      case "workflow_complete":
        setWorkflowStatus(data.status === "success" ? "complete" : "error");
        setActiveAgent(null);
        addLog(`✨ Workflow Complete: ${data.status} (Tokens: ${data.total_tokens || 0})`);
        fetchRuns(); // Refresh history to show tokens
        break;

      case "workflow_paused":
        setWorkflowStatus("paused");
        setActiveAgent(null);
        addLog(`⏸️ Workflow Paused: Waiting for approval to continue to ${data.next}`);
        break;

      case "agent_start":
        setActiveAgent(data.agent);
        setViewingAgent(data.agent); // Automatically switch to active agent
        // Don't clear history here, just ensure the key exists
        setAgentThoughts(prev => ({
          ...prev,
          [data.agent]: prev[data.agent] || ""
        }));
        addLog(`🤖 Agent Active: ${data.agent} (${data.role})`);
        break;

      case "agent_complete":
        addLog(`✅ Agent Complete: ${data.agent}`);
        break;

      case "thought_chunk":
        setAgentThoughts(prev => ({
          ...prev,
          [data.agent]: (prev[data.agent] || "") + data.chunk
        }));
        break;

      case "artifact_generated":
        setArtifacts(prev => [...prev, {
          filename: data.filename,
          type: data.type,
          timestamp: new Date().toLocaleTimeString(),
          agent: data.agent
        }]);
        addLog(`📄 Artifact Generated: ${data.filename}`);
        break;

      case "error":
        addLog(`❌ Error: ${data.message}`);
        break;
    }
  };

  const startWorkflow = async () => {
    if (!productIdea) return;
    try {
      const res = await fetch("http://localhost:8000/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_idea: productIdea,
          hitl_enabled: hitlEnabled
        }),
      });
      const data = await res.json();
      if (data.run_id) setCurrentRunId(data.run_id);
    } catch (e) {
      addLog(`Error starting workflow: ${e}`);
    }
  };

  const resumeWorkflow = async () => {
    if (!currentRunId) return;
    try {
      addLog("System: Resuming workflow...");
      const res = await fetch(`http://localhost:8000/resume/${currentRunId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hitl_enabled: hitlEnabled })
      });
      setWorkflowStatus("running");
    } catch (e) {
      addLog(`Error resuming workflow: ${e}`);
    }
  };

  const stopWorkflow = async () => {
    if (!currentRunId) return;
    try {
      addLog("System: Stopping workflow...");
      const res = await fetch(`http://localhost:8000/stop/${currentRunId}`, {
        method: "POST"
      });
      // Optionally the backend can emit a "workflow_complete" with status "stopped"
      // but we also set it here locally for immediate UI feedback if needed
      // or wait for the backend to emit via WS.
      setWorkflowStatus("idle");
    } catch (e) {
      addLog(`Error stopping workflow: ${e}`);
    }
  };

  const viewArtifact = async (filename: string) => {
    setSelectedArtifact(filename);
    setArtifactContent("Loading...");
    try {
      const url = currentRunId
        ? `http://localhost:8000/artifact?filename=${filename}&run_id=${currentRunId}`
        : `http://localhost:8000/artifact?filename=${filename}`;

      const res = await fetch(url);
      const data = await res.json();
      if (data.error) {
        setArtifactContent(`Error: ${data.error}`);
      } else {
        setArtifactContent(data.content);
      }
    } catch (e) {
      setArtifactContent(`Error fetching artifact: ${e}`);
    }
  };

  const loadRun = async (runId: string) => {
    setCurrentRunId(runId);
    setArtifacts([]); // Reset artifacts
    setLogs([`Switched to run: ${runId}`]);

    // Set status
    const run = runs.find(r => r.id === runId);
    if (run) {
      // If run status is 'paused', set it so UI shows Resume button
      setWorkflowStatus(run.status as any);
    }

    // Fetch artifacts
    try {
      addLog(`System: Fetching artifacts for run ${runId}...`);
      const res = await fetch(`http://localhost:8000/runs/${runId}/artifacts`);
      const data = await res.json();
      if (data.artifacts) {
        setArtifacts(data.artifacts);
        addLog(`System: Loaded ${data.artifacts.length} artifacts.`);
      }
    } catch (e) {
      addLog(`Error fetching artifacts for run ${runId}: ${e}`);
    }
  };

  // --- Effects ---

  // Dark Mode
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [isDarkMode]);

  // Init Data
  useEffect(() => {
    fetchRuns();
    fetchAgents();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // WebSocket
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    const connect = () => {
      ws = new WebSocket("ws://localhost:8000/ws");

      ws.onopen = () => {
        addLog("System: Connected to server");
      };

      ws.onmessage = (event) => {
        const msg: WorkflowEvent = JSON.parse(event.data);
        handleEvent(msg);
      };

      ws.onclose = () => {
        addLog("System: Disconnected. Retrying in 3s...");
        reconnectTimer = setTimeout(connect, 3000);
      };
    };

    connect();

    return () => {
      if (ws) {
        ws.onclose = null;
        ws.close();
      }
      clearTimeout(reconnectTimer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Scrolls
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  useEffect(() => {
    thoughtEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [agentThoughts, viewingAgent]);

  return (
    <div className={cn(
      "min-h-screen text-foreground p-8 font-mono flex flex-col gap-6 transition-colors duration-300 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-sky-200/30 via-neutral-50 to-neutral-50 dark:from-sky-900/20 dark:via-neutral-950 dark:to-black",
      isDarkMode ? "dark" : ""
    )}>

      {/* Header */}
      <header className="flex justify-between items-center border-b border-card-border pb-4 bg-background transition-colors">
        <div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-sky-400 to-purple-500 bg-clip-text text-transparent flex items-center gap-2">
            <Sparkles className="w-8 h-8 text-sky-400" />
            Multi-Agent QA Orchestrator
          </h1>

          <p className="text-muted text-sm">Hearing Aid Domain Adaptation</p>
        </div>
        <div className="flex items-center gap-4">

          {/* HITL Toggle */}
          <div
            onClick={() => setHitlEnabled(!hitlEnabled)}
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-full cursor-pointer transition-colors border",
              hitlEnabled ? "bg-amber-500/10 border-amber-500/50 text-amber-500" : "bg-neutral-100 dark:bg-neutral-800 border-transparent text-neutral-500"
            )}
            title="Human-in-the-Loop Mode"
          >
            <PauseCircle className="w-4 h-4" />
            <span className="text-xs font-bold">HITL: {hitlEnabled ? "ON" : "OFF"}</span>
          </div>

          {/* View Mode Toggle */}
          <div className="flex bg-neutral-100 dark:bg-neutral-800 rounded-lg p-1 border border-neutral-200 dark:border-neutral-700">
            <button
              onClick={() => setViewMode("graph")}
              className={cn(
                "p-1.5 rounded-md transition-all",
                viewMode === "graph" ? "bg-white dark:bg-neutral-700 shadow text-sky-500" : "text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300"
              )}
              title="Graph View"
            >
              <Network className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode("grid")}
              className={cn(
                "p-1.5 rounded-md transition-all",
                viewMode === "grid" ? "bg-white dark:bg-neutral-700 shadow text-sky-500" : "text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300"
              )}
              title="Grid View"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={() => setIsDarkMode(!isDarkMode)}
            className="p-2 rounded-full hover:bg-muted-light text-muted transition-colors"
          >
            {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
          <div className="flex gap-2">
            <input
              type="text"
              value={productIdea}
              onChange={(e) => setProductIdea(e.target.value)}
              className="bg-input border border-input-border text-foreground px-4 py-2 rounded w-80 focus:outline-none focus:border-sky-500 transition-colors placeholder:text-muted"
              placeholder="Enter product requirements..."
            />

            {workflowStatus === "paused" ? (
              <button
                onClick={resumeWorkflow}
                className="flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-white px-6 py-2 rounded font-bold transition-all shadow-[0_0_15px_rgba(245,158,11,0.5)] animate-pulse"
              >
                <PlayCircle className="w-4 h-4" />
                Approve & Continue
              </button>
            ) : workflowStatus === "running" ? (
              <div className="flex gap-2">
                <button
                  disabled
                  className="flex items-center gap-2 bg-sky-600/50 text-white px-6 py-2 rounded font-bold transition-all cursor-not-allowed"
                >
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                  >
                    <Activity className="w-4 h-4" />
                  </motion.div>
                  Running...
                </button>
                <button
                  onClick={stopWorkflow}
                  className="flex items-center gap-2 bg-rose-600 hover:bg-rose-500 text-white px-4 py-2 rounded font-bold transition-all shadow-[0_0_10px_rgba(225,29,72,0.3)] hover:shadow-[0_0_20px_rgba(225,29,72,0.5)]"
                  title="Stop Workflow"
                >
                  <Square className="w-4 h-4 fill-current" />
                  Stop
                </button>
              </div>
            ) : (
              <button
                onClick={startWorkflow}
                className="flex items-center gap-2 bg-sky-600 hover:bg-sky-500 text-white px-6 py-2 rounded font-bold transition-all"
              >
                <Play className="w-4 h-4" />
                Launch
              </button>
            )}


          </div>
        </div>


      </header >

      {/* Main Content */}
      < main className="grid grid-cols-12 gap-6 flex-1 relative" >

        {/* History Sidebar Toggle */}
        <button
          onClick={() => setShowHistory(!showHistory)}
          className="absolute -left-4 top-0 p-2 bg-white dark:bg-neutral-800 border-y border-r border-neutral-200 dark:border-neutral-700 rounded-r-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-600 dark:text-neutral-400 transition-colors z-20 shadow-md"
        >
          <History className="w-4 h-4" />
        </button>

        {/* History Sidebar */}
        <AnimatePresence>
          {
            showHistory && (
              <motion.div
                initial={{ x: -300, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -300, opacity: 0 }}

                className="absolute left-0 top-0 bottom-0 w-64 bg-card border border-card-border rounded-xl p-4 z-30 shadow-2xl"
              >
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-bold text-muted">Run History</h3>
                  <button onClick={() => setShowHistory(false)} className="text-muted hover:text-foreground"><X className="w-4 h-4" /></button>
                </div>
                <div className="space-y-2 overflow-y-auto max-h-full pb-4">
                  {runs.map(run => (
                    <button
                      key={run.id}
                      onClick={() => loadRun(run.id)}
                      className={cn(
                        "w-full text-left px-3 py-2 rounded text-xs font-mono transition-colors border block",
                        currentRunId === run.id
                          ? "bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/20"
                          : "bg-neutral-50 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 border-transparent hover:bg-neutral-100 dark:hover:bg-neutral-700"
                      )}
                    >
                      <div className="font-bold truncate">{run.id}</div>
                      <div className="opacity-70 truncate" title={run.product_idea || "No idea"}>{run.product_idea || "No idea"}</div>
                      <div className="flex justify-between items-center mt-1">
                        <div className={cn("text-[10px] uppercase", run.status === "paused" ? "text-amber-500 font-bold" : "opacity-50")}>
                          {run.status}
                        </div>
                        {run.total_tokens !== undefined && (
                          <div className="text-[10px] text-muted flex items-center gap-1">
                            <Cpu className="w-3 h-3" /> {run.total_tokens}
                          </div>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </motion.div>
            )
          }
        </AnimatePresence >

        {/* Left: Agents Pipeline */}
        <div className="col-span-8 space-y-6">
          {viewMode === "graph" ? (
            <GraphView activeAgent={activeAgent} workflowStatus={workflowStatus} onAgentClick={(id) => setViewingAgent(id)} />
          ) : (
            <div className="bg-card/50 border border-card-border rounded-xl p-6 min-h-[300px]">
              <h2 className="text-lg font-bold mb-6 text-muted">Agent Workflow</h2>
              <div className="flex items-stretch justify-between relative w-full">
                {agents.map((agent, index) => {
                  const isActive = activeAgent === agent.id;
                  const activeIndex = agents.findIndex(a => a.id === activeAgent);
                  const isDone = (activeIndex > -1 && index < activeIndex) || (workflowStatus === "complete" && true);
                  const glowClass = AGENT_COLORS[agent.id] || AGENT_COLORS.Default;

                  return (
                    <Fragment key={agent.id}>
                      <motion.div
                        animate={{
                          scale: isActive ? 1.1 : 1,
                          borderColor: isActive ? "#38bdf8" : isDone ? "#22c55e" : "var(--card-border)",
                          boxShadow: isActive ? "0 0 20px rgba(56, 189, 248, 0.3)" : "none"
                        }}
                        whileHover={{
                          scale: isActive ? 1.15 : 1.05,
                          boxShadow: isActive ? "0 0 30px rgba(56, 189, 248, 0.6)" : "0 0 15px rgba(56, 189, 248, 0.4)",
                          borderColor: isActive ? "#38bdf8" : "#38bdf8"
                        }}
                        className={cn(
                          "group flex flex-col items-center gap-3 p-4 rounded-xl border-2 bg-card w-40 relative z-10 transition-colors cursor-pointer",
                          isActive ? "border-sky-400" : isDone ? "border-green-500" : viewingAgent === agent.id ? "border-sky-400/50" : "border-card-border"
                        )}
                        onClick={() => setViewingAgent(agent.id)}
                      >
                        <div className={cn(
                          "w-12 h-12 rounded-full flex items-center justify-center transition-colors",
                          isActive ? "bg-sky-900 text-sky-200" : isDone ? "bg-green-900 text-green-200" : "bg-muted-light text-muted"
                        )}>
                          <agent.IconComponent className={cn("w-6 h-6 transition-all duration-300", glowClass)} />
                        </div>
                        <div className="text-center">
                          <div className="font-bold text-sm text-foreground">{agent.id}</div>
                          <div className="text-xs text-muted">{agent.role}</div>
                        </div>

                        {isActive && (
                          <motion.div
                            className="absolute -top-2 -right-2 w-4 h-4 bg-sky-500 rounded-full"
                            animate={{ scale: [1, 1.5, 1] }}
                            transition={{ repeat: Infinity, duration: 1.5 }}
                          />
                        )}
                      </motion.div>

                      {index < agents.length - 1 && (
                        <div className="flex-1 h-[2px] bg-neutral-800 relative mx-2 self-center rounded-full overflow-hidden">
                          <motion.div
                            className="absolute inset-0 bg-sky-500 origin-left"
                            initial={{ scaleX: 0 }}
                            animate={{ scaleX: isDone ? 1 : 0 }}
                            transition={{ duration: 0.5, ease: "easeInOut" }}
                          />
                        </div>
                      )}
                    </Fragment>
                  );
                })}
              </div>
            </div>
          )}

          {/* Live Thinking Stream */}
          <div className="bg-white dark:bg-black border border-neutral-200 dark:border-neutral-800 rounded-xl p-0 overflow-hidden flex flex-col h-[400px]">
            <div className="bg-neutral-100 dark:bg-neutral-900 px-4 py-2 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-500 dark:text-yellow-400" />
                <span className="font-bold text-neutral-600 dark:text-neutral-400">
                  {viewingAgent ? `${viewingAgent} Thoughts` : "Agent Thought Stream"}
                </span>
              </div>
              {activeAgent && (
                <span className="text-xs text-sky-600 dark:text-sky-400 animate-pulse">
                  {activeAgent} is thinking...
                </span>
              )}
            </div>
            <div className="flex-1 overflow-hidden bg-neutral-50 dark:bg-black relative flex flex-col">
              <StreamingThought
                content={agentThoughts[viewingAgent || ""] || ""}
                activeAgent={activeAgent === viewingAgent ? activeAgent : null}
                agentColorClass={viewingAgent ? (THOUGHT_COLORS[viewingAgent] || THOUGHT_COLORS.Default) : "text-neutral-500"}
              />
            </div>
          </div>

        </div >

        {/* Right: Logs & Artifacts */}
        < div className="col-span-4 flex flex-col gap-6" >

          {/* Artifacts */}
          <div className="bg-neutral-50 dark:bg-neutral-900/30 border border-neutral-200 dark:border-neutral-800 rounded-xl p-4 flex-1 max-h-[400px] overflow-hidden flex flex-col">
            <h3 className="text-md font-bold text-neutral-600 dark:text-neutral-400 mb-4 flex items-center gap-2">
              <FileText className="w-4 h-4" /> Generated Artifacts
            </h3>
            <div className="flex-1 overflow-y-auto space-y-2 pr-2">
              <AnimatePresence>
                {artifacts.map((art) => (
                  <motion.div
                    key={art.filename}
                    onClick={() => viewArtifact(art.filename)}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    whileHover={{ scale: 1.02 }}
                    className="bg-white dark:bg-neutral-800 p-3 rounded border border-neutral-200 dark:border-neutral-700 flex justify-between items-center cursor-pointer transition-colors hover:bg-neutral-100 dark:hover:bg-neutral-700"
                  >
                    <div className="flex items-center gap-3">
                      <div className="bg-neutral-700 p-2 rounded">
                        <FileText className="w-4 h-4 text-sky-400" />
                      </div>
                      <div className="overflow-hidden">
                        <div className="text-sm font-bold truncate w-40" title={art.filename}>{art.filename}</div>
                        <div className="text-xs text-neutral-500 uppercase">{art.type}</div>
                      </div>
                    </div>
                    <div className="text-xs text-neutral-500 font-mono">{art.timestamp}</div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>

          {/* System Logs */}
          <div className="flex flex-col bg-white dark:bg-black rounded-xl border border-neutral-200 dark:border-neutral-800 overflow-hidden font-mono text-sm h-[300px]">
            <div className="bg-neutral-100 dark:bg-neutral-900 px-4 py-2 border-b border-neutral-200 dark:border-neutral-800 flex items-center gap-2">
              <Terminal className="w-4 h-4 text-neutral-500 dark:text-neutral-400" />
              <span className="font-bold text-neutral-600 dark:text-neutral-400">System Logs</span>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-1 text-neutral-600 dark:text-neutral-300">
              {logs.map((log, i) => (
                <div key={i} className={cn("break-all text-xs border-b border-neutral-100 dark:border-white/5 pb-1 last:border-0", getLogColor(log))}>
                  <span className="opacity-50 mr-2 font-mono">&gt;</span>
                  {log}
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>

        </div >

      </main >

      {/* Artifact Viewer Modal */}
      {/* Artifact Viewer Modal */}
      <ArtifactViewer
        isOpen={!!selectedArtifact}
        onClose={() => setSelectedArtifact(null)}
        filename={selectedArtifact}
        content={artifactContent}
      />
    </div >
  );
}
