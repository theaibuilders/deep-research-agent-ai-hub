import { useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './App.css'

interface HistoryItem {
  query: string;
  answer: string;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');
  const [error, setError] = useState('');
  const [history, setHistory] = useState<HistoryItem[]>([]);

  const handleSubmit = async (e?: FormEvent) => {
    e?.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a question');
      return;
    }

    setError('');
    setResult('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query.trim() }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.error || 'Failed to get response');
      }

      setResult(data.answer);
      
      // Add to history
      setHistory(prev => {
        const newHistory = [{ query: query.trim(), answer: data.answer }, ...prev];
        return newHistory.slice(0, 5); // Keep only last 5
      });
    } catch (err) {
      console.error('Error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred while processing your request');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="app">
      <div className="container">
        <h1>🔬 Deep Research AI Agent</h1>
        <p className="subtitle">Ask anything and get comprehensive, research-backed answers</p>
        
        <div className="input-container">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything..."
            disabled={loading}
          />
          <button onClick={() => handleSubmit()} disabled={loading}>
            {loading ? 'Searching...' : 'Ask'}
          </button>
        </div>

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Searching the web and generating your answer...</p>
          </div>
        )}

        {error && <div className="error">{error}</div>}

        {result && (
          <div className="result-container">
            <h2>Answer:</h2>
            <div className="result markdown-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{result}</ReactMarkdown>
            </div>
          </div>
        )}

        {history.length > 0 && (
          <div className="history">
            <h2>Recent Queries</h2>
            {history.map((item, index) => (
              <div key={index} className="history-item">
                <div className="history-query">{item.query}</div>
                <div className="history-answer">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{item.answer}</ReactMarkdown>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App
