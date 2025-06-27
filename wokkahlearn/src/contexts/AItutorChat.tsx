import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  List,
  ListItem,
  Avatar,
  Chip,
  CircularProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Rating,
} from '@mui/material';
import {
  Send,
  SmartToy,
  Person,
  Code,
  Help,
  BugReport,
  School,
  Psychology,
  ThumbUp,
  ThumbDown,
} from '@mui/icons-material';
import { useAITutor } from '../../contexts/AITutorContext';
import CodeEditor from '../CodeEditor/CodeEditor';

interface AITutorChatProps {
  sessionType?: string;
  initialQuery?: string;
  context?: any;
  height?: string;
}

const AITutorChat: React.FC<AITutorChatProps> = ({
  sessionType = 'help_request',
  initialQuery = '',
  context,
  height = '600px',
}) => {
  const { state, startSession, sendMessage, endSession, clearError } = useAITutor();
  const [message, setMessage] = useState('');
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState({
    rating: 5,
    helpful: true,
    comments: '',
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (initialQuery && !state.currentSession) {
      startSession(sessionType, initialQuery, context);
    }
  }, [initialQuery, sessionType, context, startSession, state.currentSession]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [state.currentSession?.messages]);

  const handleSendMessage = async () => {
    if (!message.trim() || state.isGenerating) return;

    const messageToSend = message;
    setMessage('');
    await sendMessage(messageToSend, context);
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const handleEndSession = async () => {
    if (state.currentSession) {
      await endSession(state.currentSession.id, feedback);
      setShowFeedback(false);
    }
  };

  const getSessionTypeIcon = (type: string) => {
    switch (type) {
      case 'debugging':
        return <BugReport />;
      case 'concept':
        return <School />;
      case 'code_review':
        return <Code />;
      case 'learning_path':
        return <Psychology />;
      default:
        return <Help />;
    }
  };

  const renderMessage = (msg: any, index: number) => {
    const isUser = msg.messageType === 'user';
    const isAI = msg.messageType === 'assistant';

    return (
      <ListItem
        key={msg.id || index}
        sx={{
          flexDirection: 'column',
          alignItems: isUser ? 'flex-end' : 'flex-start',
          px: 2,
          py: 1,
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 1,
            maxWidth: '80%',
            flexDirection: isUser ? 'row-reverse' : 'row',
          }}
        >
          <Avatar
            sx={{
              width: 32,
              height: 32,
              bgcolor: isUser ? 'primary.main' : 'secondary.main',
            }}
          >
            {isUser ? <Person /> : <SmartToy />}
          </Avatar>

          <Paper
            elevation={1}
            sx={{
              p: 2,
              bgcolor: isUser ? 'primary.50' : 'grey.50',
              border: isUser ? '1px solid' : 'none',
              borderColor: 'primary.200',
            }}
          >
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
              {msg.content}
            </Typography>

            {/* Show code language if present */}
            {msg.codeLanguage && (
              <Chip
                label={msg.codeLanguage}
                size="small"
                sx={{ mt: 1, mr: 1 }}
              />
            )}

            {/* Show concepts referenced */}
            {msg.conceptsReferenced && msg.conceptsReferenced.length > 0 && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Concepts: {msg.conceptsReferenced.join(', ')}
                </Typography>
              </Box>
            )}

            {/* Show confidence score for AI messages */}
            {isAI && msg.confidenceScore && (
              <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Confidence: {Math.round(msg.confidenceScore * 100)}%
                </Typography>
              </Box>
            )}

            {/* Show suggested improvements */}
            {msg.suggestedImprovements && msg.suggestedImprovements.length > 0 && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                  Suggestions:
                </Typography>
                {msg.suggestedImprovements.map((suggestion: string, i: number) => (
                  <Typography key={i} variant="body2" sx={{ ml: 1, mt: 0.5 }}>
                    • {suggestion}
                  </Typography>
                ))}
              </Box>
            )}

            {/* Message timestamp */}
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
              {new Date(msg.createdAt).toLocaleTimeString()}
            </Typography>
          </Paper>
        </Box>
      </ListItem>
    );
  };

  if (!state.currentSession && state.isLoading) {
    return (
      <Box
        sx={{
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Starting AI tutor session...</Typography>
      </Box>
    );
  }

  return (
    <Paper elevation={3} sx={{ height, display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'center',
          gap: 2,
        }}
      >
        {getSessionTypeIcon(state.currentSession?.sessionType || sessionType)}
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h6">
            AI Tutor - {state.currentSession?.sessionType?.replace('_', ' ').toUpperCase() || 'Help'}
          </Typography>
          {state.currentSession && (
            <Typography variant="caption" color="text.secondary">
              Session started: {new Date(state.currentSession.startedAt).toLocaleString()}
            </Typography>
          )}
        </Box>
        <Button
          variant="outlined"
          size="small"
          onClick={() => setShowFeedback(true)}
          disabled={!state.currentSession}
        >
          End Session
        </Button>
      </Box>

      {/* Messages */}
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <List sx={{ py: 0 }}>
          {state.currentSession?.messages.map(renderMessage)}
          
          {/* Loading indicator */}
          {state.isGenerating && (
            <ListItem sx={{ justifyContent: 'flex-start', px: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}>
                  <SmartToy />
                </Avatar>
                <Paper elevation={1} sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CircularProgress size={16} />
                    <Typography variant="body2" color="text.secondary">
                      AI is thinking...
                    </Typography>
                  </Box>
                </Paper>
              </Box>
            </ListItem>
          )}
          
          <div ref={messagesEndRef} />
        </List>
      </Box>

      {/* Input */}
      <Box
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'divider',
          display: 'flex',
          gap: 1,
        }}
      >
        <TextField
          fullWidth
          multiline
          maxRows={4}
          placeholder="Ask the AI tutor for help..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={state.isGenerating}
        />
        <IconButton
          color="primary"
          onClick={handleSendMessage}
          disabled={!message.trim() || state.isGenerating}
        >
          <Send />
        </IconButton>
      </Box>

      {/* Feedback Dialog */}
      <Dialog open={showFeedback} onClose={() => setShowFeedback(false)}>
        <DialogTitle>Rate Your AI Tutor Experience</DialogTitle>
        <DialogContent>
          <Box sx={{ py: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Overall Rating
            </Typography>
            <Rating
              value={feedback.rating}
              onChange={(_, value) => setFeedback({ ...feedback, rating: value || 5 })}
              sx={{ mb: 2 }}
            />

            <Typography variant="subtitle2" gutterBottom>
              Was this session helpful?
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <Button
                variant={feedback.helpful ? 'contained' : 'outlined'}
                startIcon={<ThumbUp />}
                onClick={() => setFeedback({ ...feedback, helpful: true })}
              >
                Yes
              </Button>
              <Button
                variant={!feedback.helpful ? 'contained' : 'outlined'}
                startIcon={<ThumbDown />}
                onClick={() => setFeedback({ ...feedback, helpful: false })}
              >
                No
              </Button>
            </Box>

            <TextField
              fullWidth
              multiline
              rows={3}
              label="Additional Comments"
              value={feedback.comments}
              onChange={(e) => setFeedback({ ...feedback, comments: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowFeedback(false)}>Cancel</Button>
          <Button onClick={handleEndSession} variant="contained">
            Submit Feedback
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default AITutorChat;