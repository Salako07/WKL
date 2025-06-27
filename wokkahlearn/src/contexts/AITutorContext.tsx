import React, { createContext, useContext, useReducer, useCallback } from 'react';
import { aiTutorAPI } from '../services/api';

interface AIMessage {
  id: string;
  messageType: 'user' | 'assistant' | 'system';
  content: string;
  codeLanguage?: string;
  suggestedImprovements?: string[];
  conceptsReferenced?: string[];
  confidenceScore?: number;
  createdAt: string;
}

interface AITutorSession {
  id: string;
  sessionType: string;
  status: string;
  title: string;
  initialQuery: string;
  totalMessages: number;
  startedAt: string;
  endedAt?: string;
  messages: AIMessage[];
}

interface AITutorState {
  currentSession: AITutorSession | null;
  sessions: AITutorSession[];
  isLoading: boolean;
  isGenerating: boolean;
  error: string | null;
}

type AITutorAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_GENERATING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_CURRENT_SESSION'; payload: AITutorSession | null }
  | { type: 'SET_SESSIONS'; payload: AITutorSession[] }
  | { type: 'ADD_MESSAGE'; payload: { sessionId: string; message: AIMessage } }
  | { type: 'ADD_MESSAGES'; payload: { sessionId: string; messages: AIMessage[] } }
  | { type: 'UPDATE_SESSION'; payload: AITutorSession };

const initialState: AITutorState = {
  currentSession: null,
  sessions: [],
  isLoading: false,
  isGenerating: false,
  error: null,
};

const aiTutorReducer = (state: AITutorState, action: AITutorAction): AITutorState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_GENERATING':
      return { ...state, isGenerating: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'SET_CURRENT_SESSION':
      return { ...state, currentSession: action.payload };
    case 'SET_SESSIONS':
      return { ...state, sessions: action.payload };
    case 'ADD_MESSAGE':
      if (state.currentSession?.id === action.payload.sessionId) {
        return {
          ...state,
          currentSession: {
            ...state.currentSession,
            messages: [...state.currentSession.messages, action.payload.message],
            totalMessages: state.currentSession.totalMessages + 1,
          },
        };
      }
      return state;
    case 'ADD_MESSAGES':
      if (state.currentSession?.id === action.payload.sessionId) {
        return {
          ...state,
          currentSession: {
            ...state.currentSession,
            messages: [...state.currentSession.messages, ...action.payload.messages],
            totalMessages: state.currentSession.totalMessages + action.payload.messages.length,
          },
        };
      }
      return state;
    case 'UPDATE_SESSION':
      return {
        ...state,
        currentSession: state.currentSession?.id === action.payload.id 
          ? action.payload 
          : state.currentSession,
        sessions: state.sessions.map(session =>
          session.id === action.payload.id ? action.payload : session
        ),
      };
    default:
      return state;
  }
};

interface AITutorContextType {
  state: AITutorState;
  startSession: (type: string, query: string, context?: any) => Promise<void>;
  sendMessage: (message: string, context?: any) => Promise<void>;
  loadSessions: () => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  endSession: (sessionId: string, feedback?: any) => Promise<void>;
  clearError: () => void;
}

const AITutorContext = createContext<AITutorContextType | undefined>(undefined);

export const useAITutor = () => {
  const context = useContext(AITutorContext);
  if (!context) {
    throw new Error('useAITutor must be used within an AITutorProvider');
  }
  return context;
};

interface AITutorProviderProps {
  children: React.ReactNode;
}

export const AITutorProvider: React.FC<AITutorProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(aiTutorReducer, initialState);

  const startSession = useCallback(async (type: string, query: string, context?: any) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    try {
      const response = await aiTutorAPI.createSession({
        session_type: type,
        initial_query: query,
        context_data: context || {},
      });

      const session: AITutorSession = {
        ...response.data,
        messages: [],
      };

      dispatch({ type: 'SET_CURRENT_SESSION', payload: session });

      // Send initial message and get AI response
      await sendMessage(query, context);
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: error.message || 'Failed to start AI session' });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, []);

  const sendMessage = useCallback(async (message: string, context?: any) => {
    if (!state.currentSession) return;

    dispatch({ type: 'SET_GENERATING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    try {
      // Add user message immediately
      const userMessage: AIMessage = {
        id: Date.now().toString(),
        messageType: 'user',
        content: message,
        createdAt: new Date().toISOString(),
      };

      dispatch({
        type: 'ADD_MESSAGE',
        payload: { sessionId: state.currentSession.id, message: userMessage },
      });

      // Send message to AI and get response
      const response = await aiTutorAPI.sendMessage(state.currentSession.id, {
        content: message,
        context: context || {},
      });

      // Add AI response
      const aiMessage: AIMessage = response.data.ai_response;
      dispatch({
        type: 'ADD_MESSAGE',
        payload: { sessionId: state.currentSession.id, message: aiMessage },
      });
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: error.message || 'Failed to send message' });
    } finally {
      dispatch({ type: 'SET_GENERATING', payload: false });
    }
  }, [state.currentSession]);

  const loadSessions = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      const response = await aiTutorAPI.getSessions();
      dispatch({ type: 'SET_SESSIONS', payload: response.data.results });
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: error.message || 'Failed to load sessions' });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, []);

  const loadSession = useCallback(async (sessionId: string) => {
    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      const [sessionResponse, messagesResponse] = await Promise.all([
        aiTutorAPI.getSession(sessionId),
        aiTutorAPI.getSessionMessages(sessionId),
      ]);

      const session: AITutorSession = {
        ...sessionResponse.data,
        messages: messagesResponse.data,
      };

      dispatch({ type: 'SET_CURRENT_SESSION', payload: session });
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: error.message || 'Failed to load session' });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, []);

  const endSession = useCallback(async (sessionId: string, feedback?: any) => {
    try {
      await aiTutorAPI.endSession(sessionId, feedback);
      
      // Update session status
      if (state.currentSession?.id === sessionId) {
        dispatch({
          type: 'UPDATE_SESSION',
          payload: { ...state.currentSession, status: 'completed' },
        });
      }
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: error.message || 'Failed to end session' });
    }
  }, [state.currentSession]);

  const clearError = useCallback(() => {
    dispatch({ type: 'SET_ERROR', payload: null });
  }, []);

  const value: AITutorContextType = {
    state,
    startSession,
    sendMessage,
    loadSessions,
    loadSession,
    endSession,
    clearError,
  };

  return (
    <AITutorContext.Provider value={value}>
      {children}
    </AITutorContext.Provider>
  );
};
