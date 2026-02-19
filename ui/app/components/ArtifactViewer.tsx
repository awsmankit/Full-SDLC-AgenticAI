"use client";

import { motion, AnimatePresence } from "framer-motion";
import { FileText, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

interface ArtifactViewerProps {
    isOpen: boolean;
    onClose: () => void;
    filename: string | null;
    content: string;
}

export default function ArtifactViewer({ isOpen, onClose, filename, content }: ArtifactViewerProps) {
    if (!isOpen) return null;

    // Determine if we should treat this as a code file
    const isCodeFile = filename?.endsWith(".py") || filename?.endsWith(".js") || filename?.endsWith(".json");
    const language = filename?.split('.').pop() || "text";

    // If it's a code file and not already wrapped in markdown, wrap it
    const displayContent = isCodeFile && !content.trim().startsWith("```")
        ? `\`\`\`${language}\n${content}\n\`\`\``
        : content;

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 bg-black/80 flex items-center justify-center p-8 z-50 backdrop-blur-sm"
                    onClick={onClose}
                >
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.9, opacity: 0 }}
                        onClick={(e) => e.stopPropagation()}
                        className="bg-neutral-900 border border-neutral-800 rounded-xl w-full max-w-4xl h-[85vh] flex flex-col shadow-2xl overflow-hidden"
                    >
                        {/* Header */}
                        <div className="flex justify-between items-center p-4 border-b border-neutral-800 bg-neutral-900">
                            <div className="flex items-center gap-3">
                                <div className="bg-neutral-800 p-2 rounded-lg">
                                    <FileText className="w-5 h-5 text-sky-400" />
                                </div>
                                <div className="flex flex-col">
                                    <h3 className="font-bold text-lg text-neutral-200">{filename}</h3>
                                    <span className="text-xs text-neutral-500 font-mono">Markdown & Code Viewer</span>
                                </div>
                            </div>
                            <button
                                onClick={onClose}
                                className="p-2 hover:bg-neutral-800 rounded-full transition-colors text-neutral-400 hover:text-white"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Content Area */}
                        <div className="flex-1 overflow-auto p-8 bg-neutral-950 prose prose-invert prose-sm max-w-none scrollbar-thin scrollbar-thumb-neutral-700 scrollbar-track-transparent">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                    code({ node, inline, className, children, ...props }: any) {
                                        const match = /language-(\w+)/.exec(className || "");
                                        return !inline && match ? (
                                            <div className="rounded-lg overflow-hidden my-4 border border-neutral-800 shadow-lg">
                                                <div className="bg-neutral-900 px-3 py-1 text-xs text-neutral-400 border-b border-neutral-800 flex justify-between">
                                                    <span>{match[1]}</span>
                                                </div>
                                                <SyntaxHighlighter
                                                    style={vscDarkPlus}
                                                    language={match[1]}
                                                    PreTag="div"
                                                    customStyle={{ margin: 0, borderRadius: 0, background: '#0a0a0a' }}
                                                    {...props}
                                                >
                                                    {String(children).replace(/\n$/, "")}
                                                </SyntaxHighlighter>
                                            </div>
                                        ) : (
                                            <code className="bg-neutral-800 text-sky-300 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                                                {children}
                                            </code>
                                        );
                                    }
                                }}
                            >
                                {displayContent}
                            </ReactMarkdown>
                        </div>

                        {/* Footer */}
                        <div className="p-3 bg-neutral-900 border-t border-neutral-800 text-right text-xs text-neutral-500">
                            Press ESC to close
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
