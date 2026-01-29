/**
 * ============================================================================
 * REACT FRONTEND - USER INTERFACE FOR THE AI AGENT
 * ============================================================================
 * 
 * This file implements the React frontend that allows users to interact
 * with our AI agent through a web browser.
 * 
 * KEY CONCEPTS FOR WORKSHOP:
 * 
 * 1. REACT FUNDAMENTALS:
 *    - Components: Reusable UI building blocks
 *    - JSX: HTML-like syntax in JavaScript
 *    - Hooks: Functions that let you use React features
 * 
 * 2. REACT HOOKS USED:
 *    - useState: Manage component state (query, loading, result, etc.)
 *    - State updates trigger re-renders
 * 
 * 3. FRONTEND-BACKEND COMMUNICATION:
 *    - fetch() API for HTTP requests
 *    - POST request with JSON body
 *    - Parse JSON response
 * 
 * 4. UI STATE MANAGEMENT:
 *    - Loading state: Show spinner while waiting
 *    - Error state: Display error messages
 *    - Result state: Show AI response
 *    - History: Remember recent queries
 * 
 * ============================================================================
 */

import { useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './App.css'

/**
 * TypeScript interface for query history items.
 * Interfaces help define the shape of data objects.
 */
interface HistoryItem {
  query: string;   // The user's question
  answer: string;  // The AI's response
}

/**
 * API URL CONFIGURATION
 * 
 * import.meta.env.VITE_API_URL:
 * - Vite's way of accessing environment variables
 * - Variables must be prefixed with VITE_ to be exposed to client
 * - Falls back to localhost:8000 for development
 * 
 * This allows deploying to different environments without code changes.
 */
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * App Component - Main application component
 * 
 * COMPONENT STRUCTURE:
 * - Input form for user queries
 * - Loading indicator
 * - Error display
 * - Result display (with Markdown rendering)
 * - Query history
 */
function App() {
  // ============================================================================
  // STATE MANAGEMENT with useState
  // ============================================================================
  // useState returns [currentValue, setterFunction]
  // When setter is called, component re-renders with new value
  
  // Input field value (controlled component pattern)
  const [query, setQuery] = useState('');
  
  // Loading state - true while waiting for API response
  const [loading, setLoading] = useState(false);
  
  // Current result from the API
  const [result, setResult] = useState('');
  
  // Error message (if any)
  const [error, setError] = useState('');
  
  // History of recent queries (limited to 5)
  const [history, setHistory] = useState<HistoryItem[]>([]);

  /**
   * handleSubmit - Process user query submission
   * 
   * ASYNC/AWAIT PATTERN:
   * - async function allows using await
   * - await pauses until Promise resolves
   * - Makes async code look synchronous
   * 
   * FETCH API:
   * - Modern browser API for HTTP requests
   * - Returns a Promise
   * - Must call response.json() to parse body
   * 
   * @param e - Optional form event (for form submission)
   */
  const handleSubmit = async (e?: FormEvent) => {
    // Prevent default form submission (page reload)
    e?.preventDefault();
    
    // INPUT VALIDATION
    // Check for empty query before making API call
    if (!query.trim()) {
      setError('Please enter a question');
      return;
    }

    // RESET STATE before new request
    // Clear previous errors and results
    setError('');
    setResult('');
    setLoading(true);  // Show loading indicator

    try {
      // FETCH API CALL
      // POST request to our backend API
      const response = await fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: {
          // Tell server we're sending JSON
          'Content-Type': 'application/json',
        },
        // Convert JavaScript object to JSON string
        body: JSON.stringify({ query: query.trim() }),
      });

      // Parse JSON response body
      const data = await response.json();

      // CHECK FOR HTTP ERRORS
      // response.ok is true for 200-299 status codes
      if (!response.ok) {
        throw new Error(data.detail || data.error || 'Failed to get response');
      }

      // SUCCESS: Update result state
      setResult(data.answer);
      
      // ADD TO HISTORY
      // Keep only last 5 queries (most recent first)
      setHistory(prev => {
        const newHistory = [{ query: query.trim(), answer: data.answer }, ...prev];
        return newHistory.slice(0, 5); // Limit to 5 items
      });
    } catch (err) {
      // ERROR HANDLING
      console.error('Error:', err);
      // Type narrowing: check if err is an Error instance
      setError(err instanceof Error ? err.message : 'An error occurred while processing your request');
    } finally {
      // CLEANUP: Always runs (success or error)
      setLoading(false);  // Hide loading indicator
    }
  };

  /**
   * handleKeyPress - Handle Enter key to submit
   * 
   * Allows users to submit by pressing Enter instead of clicking the button.
   * 
   * @param e - Keyboard event from the input
   */
  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  // ============================================================================
  // JSX RETURN - Component UI
  // ============================================================================
  // JSX is a syntax extension that looks like HTML but compiles to JavaScript
  // className is used instead of class (class is a reserved word in JS)
  
  return (
    <div className="app">
      <div className="container">
        {/* HEADER */}
        <h1>Web Search AI Agent</h1>
        <p className="subtitle">Ask anything and get comprehensive, research-backed answers</p>
        
        {/* INPUT FORM */}
        {/* 
          CONTROLLED COMPONENT PATTERN:
          - value={query} - Input value controlled by React state
          - onChange - Update state when user types
          This keeps React state as "single source of truth"
        */}
        <div className="input-container">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything..."
            disabled={loading}  // Disable while loading
          />
          <button onClick={() => handleSubmit()} disabled={loading}>
            {/* CONDITIONAL RENDERING: Different text based on state */}
            {loading ? 'Searching...' : 'Ask'}
          </button>
        </div>

        {/* LOADING INDICATOR */}
        {/* Conditional rendering: Only show when loading is true */}
        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Searching the web and generating your answer...</p>
          </div>
        )}

        {/* ERROR DISPLAY */}
        {/* Conditional rendering: Only show when error has a value */}
        {error && <div className="error">{error}</div>}

        {/* RESULT DISPLAY */}
        {/*
          REACT MARKDOWN:
          - Renders Markdown text as formatted HTML
          - remarkGfm adds GitHub Flavored Markdown support
          - Allows AI responses to include formatting, lists, code blocks, etc.
        */}
        {result && (
          <div className="result-container">
            <h2>Answer:</h2>
            <div className="result markdown-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{result}</ReactMarkdown>
            </div>
          </div>
        )}

        {/* QUERY HISTORY */}
        {/*
          ARRAY RENDERING:
          - .map() transforms array items into JSX elements
          - key prop helps React track which items changed
          - Using index as key is okay here since history order is stable
        */}
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
