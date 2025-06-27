import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  TextField,
  IconButton,
  Button,
  Chip,
  Drawer,
  Divider,
  Badge,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  Send,
  Mic,
  MicOff,
  Videocam,
  VideocamOff,
  ScreenShare,
  StopScreenShare,
  People,
  Settings,
  ExitToApp,
  MoreVert,
  Code,
  Help,
  VolumeUp,
  VolumeOff,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useSocket } from '../../contexts/SocketContext';
import CodeEditor from '../CodeEditor/CodeEditor';

interface Participant {
  id: string;
  username: string;
  fullName: string;
  role: string;
  avatar?: string;
  isActive: boolean;
  lastActivity: string;
}

interface ChatMessage {
  id: string;
  sender: {
    username: string;
    fullName: string;
    avatar?: string;
  };
  messageType: string;
  content: string;
  createdAt: string;
  metadata?: any;
}

const CollaborationRoom: React.FC = () => {
  const { roomId } = useParams();
  const navigate = useNavigate();
  const { socket, isConnected, joinRoom, leaveRoom, sendMessage } = useSocket();
  
  const [room, setRoom] = useState<any>(null);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [showParticipants, setShowParticipants] = useState(true);
  const [sharedCode, setSharedCode] = useState('');
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOn, setIsVideoOn] = useState(false);
  const [showHelpRequest, setShowHelpRequest] = useState(false);
  const [helpRequest, setHelpRequest] = useState({
    title: '',
    description: '',
    type: 'general',
  });

  useEffect(() => {
    if (roomId && isConnected) {
      joinRoom(roomId);
    }

    return () => {
      if (roomId) {
        leaveRoom(roomId);
      }
    };
  }, [roomId, isConnected, joinRoom, leaveRoom]);

  useEffect(() => {
    if (!socket) return;

    const handleRoomState = (data: any) => {
      setRoom(data.room);
      setParticipants(data.participants);
    };

    const handleUserJoined = (data: any) => {
      setParticipants(prev => [...prev, data.user]);
    };

    const handleUserLeft = (data: any) => {
      setParticipants(prev => prev.filter(p => p.id !== data.user.id));
    };

    const handleChatMessage = (data: any) => {
      setMessages(prev => [...prev, data.message]);
    };

    const handleCodeChange = (data: any) => {
      setSharedCode(data.code);
    };

    socket.on('room_state', handleRoomState);
    socket.on('user_joined', handleUserJoined);
    socket.on('user_left', handleUserLeft);
    socket.on('chat_message', handleChatMessage);
    socket.on('code_change', handleCodeChange);

    return () => {
      socket.off('room_state', handleRoomState);
      socket.off('user_joined', handleUserJoined);
      socket.off('user_left', handleUserLeft);
      socket.off('chat_message', handleChatMessage);
      socket.off('code_change', handleCodeChange);
    };
  }, [socket]);

  const handleSendMessage = () => {
    if (!newMessage.trim() || !roomId) return;

    sendMessage(roomId, {
      message_type: 'text',
      content: newMessage,
    });

    setNewMessage('');
  };

  const handleCodeChange = (code: string) => {
    setSharedCode(code);
    if (roomId) {
      // Send code change to other participants
      socket?.emit('code_change', {
        room_id: roomId,
        code,
        change_type: 'replace',
      });
    }
  };

  const handleScreenShare = async () => {
    try {
      if (!isScreenSharing) {
        const stream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: true,
        });
        setIsScreenSharing(true);
        
        // Handle stream end
        stream.getVideoTracks()[0].addEventListener('ended', () => {
          setIsScreenSharing(false);
        });
      } else {
        setIsScreenSharing(false);
      }
    } catch (error) {
      console.error('Error sharing screen:', error);
    }
  };

  const handleSubmitHelpRequest = () => {
    if (!roomId) return;

    socket?.emit('help_request', {
      room_id: roomId,
      ...helpRequest,
      code_snippet: sharedCode,
    });

    setShowHelpRequest(false);
    setHelpRequest({ title: '', description: '', type: 'general' });
  };

  const handleLeaveRoom = () => {
    if (roomId) {
      leaveRoom(roomId);
    }
    navigate('/collaboration');
  };

  if (!room) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6">Joining room...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper elevation={1} sx={{ p: 2, borderRadius: 0 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h5">{room.title}</Typography>
            <Typography variant="body2" color="text.secondary">
              Room Code: {room.roomCode} • {participants.length} participants
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title={isMuted ? 'Unmute' : 'Mute'}>
              <IconButton onClick={() => setIsMuted(!isMuted)} color={isMuted ? 'error' : 'default'}>
                {isMuted ? <MicOff /> : <Mic />}
              </IconButton>
            </Tooltip>

            <Tooltip title={isVideoOn ? 'Turn off camera' : 'Turn on camera'}>
              <IconButton onClick={() => setIsVideoOn(!isVideoOn)} color={isVideoOn ? 'primary' : 'default'}>
                {isVideoOn ? <Videocam /> : <VideocamOff />}
              </IconButton>
            </Tooltip>

            <Tooltip title={isScreenSharing ? 'Stop sharing' : 'Share screen'}>
              <IconButton onClick={handleScreenShare} color={isScreenSharing ? 'primary' : 'default'}>
                {isScreenSharing ? <StopScreenShare /> : <ScreenShare />}
              </IconButton>
            </Tooltip>

            <Tooltip title="Request help">
              <IconButton onClick={() => setShowHelpRequest(true)}>
                <Help />
              </IconButton>
            </Tooltip>

            <Tooltip title="Leave room">
              <IconButton onClick={handleLeaveRoom} color="error">
                <ExitToApp />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Paper>

      {/* Main Content */}
      <Box sx={{ flexGrow: 1, display: 'flex' }}>
        {/* Code Editor */}
        <Box sx={{ flexGrow: 1 }}>
          <CodeEditor
            language="python"
            initialCode={sharedCode}
            onChange={handleCodeChange}
            height="100%"
            showExecuteButton={true}
          />
        </Box>

        {/* Sidebar */}
        <Box sx={{ width: '300px', borderLeft: 1, borderColor: 'divider', display: 'flex', flexDirection: 'column' }}>
          {/* Participants */}
          <Paper elevation={0} sx={{ borderRadius: 0, borderBottom: 1, borderColor: 'divider' }}>
            <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <People />
              <Typography variant="h6">Participants</Typography>
              <Chip label={participants.length} size="small" />
            </Box>
            <List dense>
              {participants.map((participant) => (
                <ListItem key={participant.id}>
                  <ListItemAvatar>
                    <Badge
                      variant="dot"
                      color={participant.isActive ? 'success' : 'default'}
                    >
                      <Avatar src={participant.avatar}>
                        {participant.fullName.charAt(0)}
                      </Avatar>
                    </Badge>
                  </ListItemAvatar>
                  <ListItemText
                    primary={participant.fullName}
                    secondary={participant.role}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>

          {/* Chat */}
          <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
              <Typography variant="h6">Chat</Typography>
            </Box>

            {/* Messages */}
            <Box sx={{ flexGrow: 1, overflow: 'auto', p: 1 }}>
              {messages.map((message) => (
                <Box key={message.id} sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <Avatar src={message.sender.avatar} sx={{ width: 24, height: 24 }}>
                      {message.sender.fullName.charAt(0)}
                    </Avatar>
                    <Typography variant="caption" fontWeight={600}>
                      {message.sender.fullName}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(message.createdAt).toLocaleTimeString()}
                    </Typography>
                  </Box>
                  <Typography variant="body2" sx={{ ml: 4 }}>
                    {message.content}
                  </Typography>
                </Box>
              ))}
            </Box>

            {/* Message Input */}
            <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Type a message..."
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                />
                <IconButton onClick={handleSendMessage} disabled={!newMessage.trim()}>
                  <Send />
                </IconButton>
              </Box>
            </Box>
          </Box>
        </Box>
      </Box>

      {/* Help Request Dialog */}
      <Dialog open={showHelpRequest} onClose={() => setShowHelpRequest(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Request Help</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Title"
            value={helpRequest.title}
            onChange={(e) => setHelpRequest({ ...helpRequest, title: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Description"
            value={helpRequest.description}
            onChange={(e) => setHelpRequest({ ...helpRequest, description: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            select
            label="Type"
            value={helpRequest.type}
            onChange={(e) => setHelpRequest({ ...helpRequest, type: e.target.value })}
          >
            <MenuItem value="general">General Question</MenuItem>
            <MenuItem value="debugging">Debugging Help</MenuItem>
            <MenuItem value="concept">Concept Explanation</MenuItem>
            <MenuItem value="code_review">Code Review</MenuItem>
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowHelpRequest(false)}>Cancel</Button>
          <Button onClick={handleSubmitHelpRequest} variant="contained">
            Send Request
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CollaborationRoom;