"use client";
import React, { useState } from "react";

export default function Home() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showRaw, setShowRaw] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setShowRaw(false);
    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!res.ok) throw new Error("API error");
      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center p-4">
      <h1 className="text-3xl font-bold mb-6">Research Agent</h1>
      <form onSubmit={handleSubmit} className="w-full max-w-xl flex flex-col gap-4 bg-white dark:bg-black/40 p-6 rounded-xl shadow">
        <textarea
          className="w-full p-3 rounded border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-base resize-vertical min-h-[80px]"
          placeholder="Enter your research question..."
          value={question}
          onChange={e => setQuestion(e.target.value)}
          required
        />
        <button
          type="submit"
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded disabled:opacity-50"
          disabled={loading || !question.trim()}
        >
          {loading ? "Searching..." : "Ask"}
        </button>
      </form>
      <div className="w-full max-w-xl mt-8">
        {error && <div className="text-red-600 mb-4">{error}</div>}
        {result && !error && (
          <div className="flex flex-col gap-4">
            {result.answer && (
              <div className="bg-blue-50 dark:bg-blue-900/40 border border-blue-200 dark:border-blue-700 text-blue-900 dark:text-blue-100 rounded p-4 mb-2 shadow-sm">
                <span className="font-semibold">Answer:</span>
                <div className="mt-2 whitespace-pre-line break-words">{result.answer}</div>
              </div>
            )}
            {result.citations && result.citations.length > 0 && (
              <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded p-4">
                <span className="font-semibold">Citations:</span>
                <ul className="list-disc list-inside mt-2">
                  {result.citations.map((c: any, i: number) => (
                    <li key={i} className="break-all">
                      {c.id && <span className="font-mono text-sm">[{c.id}]</span>} {c.title}
                      {c.url && (
                        <a href={c.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline ml-2">
                          (link)
                        </a>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <button
              className="text-xs text-blue-600 hover:underline self-end mt-2"
              type="button"
              onClick={() => setShowRaw(v => !v)}
            >
              {showRaw ? "Hide raw JSON" : "Show raw JSON"}
            </button>
            {showRaw && (
              <pre className="bg-gray-100 dark:bg-gray-800 p-4 rounded text-xs overflow-x-auto whitespace-pre-wrap mt-2">
                {JSON.stringify(result, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
