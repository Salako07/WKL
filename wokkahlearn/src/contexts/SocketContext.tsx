// src/contexts/SocketContext.tsx
import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import io, { Socket } from 'socket.io-client';
import { useAppSelector } from '../store/store';
import { toast } from 'react-toastify';

interface SocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  joinRoom: (roomId: string) => void;
  leaveRoom: (roomId: string) => void;
  sendMessage: (roomId: string, message: any) => void;
  sendCodeChange: (roomId: string, change: any) => void;
  sendCursorPosition: (roomId: string, position: any) => void;
}

const SocketContext = createContext<SocketContextType | undefined>(undefined);

export const useSocket = () => {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
};

interface SocketProviderProps {
  children: React.ReactNode;
}

export const SocketProvider: React.FC<SocketProviderProps> = ({ children }) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const { isAuthenticated, accessToken } = useAppSelector(state => state.auth);
  const currentRooms = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (isAuthenticated && accessToken) {
      // Connect to WebSocket server
      const newSocket = io(process.env.REACT_APP_WS_URL || 'ws://localhost:8000', {
        auth: {
          token: accessToken,
        },
        transports: ['websocket'],
      });

      // Connection event handlers
      newSocket.on('connect', () => {
        setIsConnected(true);
        console.log('Connected to WebSocket server');
      });

      newSocket.on('disconnect', () => {
        setIsConnected(false);
        console.log('Disconnected from WebSocket server');
      });

      newSocket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
        toast.error('Connection error. Some features may not work properly.');
      });

      // Collaboration event handlers
      newSocket.on('user_joined', (data) => {
        toast.info(`${data.user.fullName} joined the room`);
      });

      newSocket.on('user_left', (data) => {
        toast.info(`${data.user.fullName} left the room`);
      });

      newSocket.on('chat_message', (data) => {
        // Handle incoming chat message
        // This would be handled by specific components
      });

      newSocket.on('code_change', (data) => {
        // Handle code changes from other users
        // This would be handled by the code editor component
      });

      newSocket.on('cursor_position', (data) => {
        // Handle cursor position updates from other users
        // This would be handled by the code editor component
      });

      newSocket.on('code_execution_result', (data) => {
        // Handle code execution results
        // This would be handled by the code execution component
      });

      newSocket.on('help_request', (data) => {
        toast.info(`Help request: ${data.request.title}`);
      });

      newSocket.on('error', (data) => {
        toast.error(data.message);
      });

      setSocket(newSocket);

      return () => {
        newSocket.close();
        setSocket(null);
        setIsConnected(false);
      };
    }
  }, [isAuthenticated, accessToken]);

  const joinRoom = (roomId: string) => {
    if (socket && isConnected) {
      socket.emit('join_room', { room_id: roomId });
      currentRooms.current.add(roomId);
    }
  };

  const leaveRoom = (roomId: string) => {
    if (socket && isConnected) {
      socket.emit('leave_room', { room_id: roomId });
      currentRooms.current.delete(roomId);
    }
  };

  const sendMessage = (roomId: string, message: any) => {
    if (socket && isConnected) {
      socket.emit('chat_message', {
        room_id: roomId,
        ...message,
      });
    }
  };

  const sendCodeChange = (roomId: string, change: any) => {
    if (socket && isConnected) {
      socket.emit('code_change', {
        room_id: roomId,
        ...change,
      });
    }
  };

  const sendCursorPosition = (roomId: string, position: any) => {
    if (socket && isConnected) {
      socket.emit('cursor_position', {
        room_id: roomId,
        ...position,
      });
    }
  };

  const value: SocketContextType = {
    socket,
    isConnected,
    joinRoom,
    leaveRoom,
    sendMessage,
    sendCodeChange,
    sendCursorPosition,
  };

  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  );
};