"use client";

import React, { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface StreamingThoughtProps {
    content: string;
    activeAgent: string | null;
    agentColorClass?: string;
}

export default function StreamingThought({ content, activeAgent, agentColorClass }: StreamingThoughtProps) {
    const endRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when content updates
    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [content]);

    if (!content && !activeAgent) {
        return (
            <div className="p-4 text-neutral-400 dark:text-neutral-700 italic">
                Waiting for agent activity...
            </div>
        );
    }

    return (
        <div className={cn(
            "p-4 flex-1 overflow-y-auto overflow-x-auto font-mono text-sm transition-colors duration-300 prose prose-sm max-w-none dark:prose-invert",
            "break-all whitespace-pre-wrap",
            "prose-p:my-0 prose-headings:my-1 prose-pre:my-1",
            agentColorClass ? agentColorClass : "text-neutral-500"
        )}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    // Override code blocks for syntax highlighting
                    code({ node, inline, className, children, ...props }: any) {
                        const match = /language-(\w+)/.exec(className || "");
                        return !inline && match ? (
                            <div className="rounded-lg overflow-hidden my-2 border border-neutral-800 shadow-sm">
                                <div className="bg-neutral-800/50 px-2 py-1 text-[10px] text-neutral-400 border-b border-neutral-800 flex justify-between uppercase font-sans tracking-wider">
                                    <span>{match[1]}</span>
                                </div>
                                <SyntaxHighlighter
                                    style={vscDarkPlus}
                                    language={match[1]}
                                    PreTag="div"
                                    customStyle={{ margin: 0, borderRadius: 0, background: '#0a0a0a', fontSize: '12px' }}
                                    wrapLines={true}
                                    wrapLongLines={true}
                                    {...props}
                                >
                                    {String(children).replace(/\n$/, "")}
                                </SyntaxHighlighter>
                            </div>
                        ) : (
                            <code className="bg-neutral-200 dark:bg-neutral-800 px-1 py-0.5 rounded text-xs font-bold text-sky-600 dark:text-sky-400" {...props}>
                                {children}
                            </code>
                        );
                    },
                    // Style paragraphs to respect colors if possible, but prose usually enforces its own
                    p: ({ node, ...props }) => <p className="m-0 break-words" {...props} />
                }}
            >
                {content || ""}
            </ReactMarkdown>

            {/* Blinking cursor if active */}
            {activeAgent && (
                <span className="inline-block w-2 h-4 bg-sky-500 ml-1 animate-pulse align-middle" />
            )}

            <div ref={endRef} />
        </div>
    );
}
