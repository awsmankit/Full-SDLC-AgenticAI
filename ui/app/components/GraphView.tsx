"use client";

import React, { useMemo, useEffect } from "react";
import {
    ReactFlow,
    MiniMap,
    Controls,
    Background,
    useNodesState,
    useEdgesState,
    Node,
    Edge,
    Position,
    Handle,
    NodeProps,
    MarkerType
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Bot, Activity, Cpu, Terminal, CheckCircle, Zap, Sparkles } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// Reuse Icon Map
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
    "ProductManager": "text-purple-400 drop-shadow-[0_0_8px_rgba(192,132,252,0.8)]",
    "TestManager": "text-sky-400 drop-shadow-[0_0_8px_rgba(56,189,248,0.8)]",
    "TestLead": "text-amber-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.8)]",
    "AutomationQA": "text-emerald-400 drop-shadow-[0_0_8px_rgba(52,211,153,0.8)]",
    "ManualQA": "text-rose-400 drop-shadow-[0_0_8px_rgba(251,113,133,0.8)]",
    "Default": "text-gray-400 drop-shadow-[0_0_8px_rgba(156,163,175,0.8)]"
};

// --- Custom Node Component ---
interface AgentNodeData extends Record<string, unknown> {
    label: string;
    role: string;
    icon: string;
    active?: boolean;
    done?: boolean;
}

const AgentNode = ({ data, selected }: NodeProps<Node<AgentNodeData>>) => {
    const Icon = ICON_MAP[data.icon] || ICON_MAP.Default;
    const isActive = data.active;
    const isDone = data.done;
    const colorClass = AGENT_COLORS[data.id as string] || AGENT_COLORS.Default;

    return (
        <div
            className={cn(
                "flex flex-col items-center gap-3 p-4 rounded-xl border-2 bg-card w-48 relative transition-all duration-300",
                isActive ? "border-sky-400 shadow-[0_0_20px_rgba(56,189,248,0.3)] scale-110" : isDone ? "border-green-500" : "border-card-border",
                selected ? "ring-2 ring-sky-500" : ""
            )}
        >
            <Handle type="target" position={Position.Top} className="!bg-neutral-500 !w-3 !h-3" />

            <div className={cn(
                "w-12 h-12 rounded-full flex items-center justify-center transition-colors",
                isActive ? "bg-sky-900 text-sky-200" : isDone ? "bg-green-900 text-green-200" : "bg-muted-light text-muted"
            )}>
                <Icon className={cn("w-6 h-6 transition-all duration-300", isActive || isDone ? colorClass : "")} />
            </div>

            <div className="text-center">
                <div className="font-bold text-sm text-foreground">{data.label}</div>
                <div className="text-xs text-muted">{data.role}</div>
            </div>

            {isActive && (
                <div className="absolute -top-2 -right-2 w-4 h-4 bg-sky-500 rounded-full animate-ping" />
            )}

            <Handle type="source" position={Position.Bottom} className="!bg-neutral-500 !w-3 !h-3" />
        </div>
    );
};

const nodeTypes = {
    agent: AgentNode,
};

// --- Graph Definition ---
const INITIAL_NODES: Node[] = [
    {
        id: "ProductManager",
        type: "agent",
        position: { x: 250, y: 0 },
        data: { label: "ProductManager", role: "Product Manager", icon: "Bot", id: "ProductManager" },
    },
    {
        id: "TestManager",
        type: "agent",
        position: { x: 250, y: 150 },
        data: { label: "TestManager", role: "Test Manager", icon: "Activity", id: "TestManager" },
    },
    {
        id: "TestLead",
        type: "agent",
        position: { x: 250, y: 300 },
        data: { label: "TestLead", role: "Test Lead", icon: "Zap", id: "TestLead" },
    },
    {
        id: "AutomationQA",
        type: "agent",
        position: { x: 100, y: 450 },
        data: { label: "AutomationQA", role: "Automation QA", icon: "Cpu", id: "AutomationQA" },
    },
    {
        id: "ManualQA",
        type: "agent",
        position: { x: 400, y: 450 },
        data: { label: "ManualQA", role: "Manual QA", icon: "CheckCircle", id: "ManualQA" },
    },
];

const INITIAL_EDGES: Edge[] = [
    { id: "e1-2", source: "ProductManager", target: "TestManager", animated: true },
    { id: "e2-3", source: "TestManager", target: "TestLead", animated: true },
    { id: "e3-4", source: "TestLead", target: "AutomationQA", animated: true },
    { id: "e3-5", source: "TestLead", target: "ManualQA", animated: true },
];

interface GraphViewProps {
    activeAgent: string | null;
    workflowStatus: "idle" | "running" | "paused" | "complete" | "error";
    onAgentClick?: (agentId: string) => void;
}

export default function GraphView({ activeAgent, workflowStatus, onAgentClick }: GraphViewProps) {
    const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES);
    const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES);

    // Update node states based on activeAgent
    useEffect(() => {
        setNodes((nds) =>
            nds.map((node) => {
                const isBeforeActive = activeAgent
                    ? INITIAL_NODES.findIndex(n => n.id === activeAgent) > INITIAL_NODES.findIndex(n => n.id === node.id)
                    : false; // Simplistic logic, ideally we track 'completedAgents' set

                // Better logic: we need 'completedAgents' prop. 
                // For now, let's assume if activeAgent is X, previous ones are done?
                // But parallel branches make this tricky.
                // Let's rely on simple matching for active, and maybe 'done' based on general flow for now.

                let isDone = false;
                if (workflowStatus === "complete") isDone = true;
                else if (activeAgent) {
                    // Hardcoded flow order for visualization
                    const order = ["ProductManager", "TestManager", "TestLead", "AutomationQA", "ManualQA"];
                    const activeIdx = order.indexOf(activeAgent);
                    const nodeIdx = order.indexOf(node.id);
                    if (activeIdx > -1 && nodeIdx > -1 && nodeIdx < activeIdx) {
                        isDone = true;
                    }
                    // Handle parallel: if one of Automation/Manual is active, TestLead is done.
                    if ((activeAgent === "AutomationQA" || activeAgent === "ManualQA") && node.id === "TestLead") {
                        isDone = true;
                    }
                }

                return {
                    ...node,
                    data: {
                        ...node.data,
                        active: node.id === activeAgent,
                        done: isDone
                    },
                };
            })
        );

        // Animate edges based on active flow?
        // ReactFlow edges animate by default if 'animated: true'.

    }, [activeAgent, workflowStatus, setNodes]);

    return (
        <div className="w-full h-[500px] border border-card-border rounded-xl bg-card overflow-hidden">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={(_, node) => onAgentClick?.(node.id)}
                fitView
                attributionPosition="bottom-right"
                minZoom={0.5}
                maxZoom={1.5}
            >
                <Background color="#888" gap={16} size={1} className="opacity-10" />
                <Controls className="bg-white dark:bg-neutral-800 border-neutral-200 dark:border-neutral-700 text-neutral-600 dark:text-neutral-400" />
            </ReactFlow>
        </div>
    );
}
