// src/components/Learning/LessonViewer.tsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  LinearProgress,
  Chip,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  IconButton,
  Divider,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Rating,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  SkipNext,
  SkipPrevious,
  MenuBook,
  Code,
  Quiz,
  PlayCircle,
  CheckCircle,
  BookmarkBorder,
  Bookmark,
  Share,
  Fullscreen,
  Notes,
  Help,
  Speed,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useParams, useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../store/store';
import { fetchLessonDetails, markLessonCompleted } from '../../store/slices/learningSlice';
import AITutorChat from '../AITutor/AITutorChat';

interface LessonViewerProps {
  lessonId?: string;
  courseId?: string;
}

const LessonViewer: React.FC<LessonViewerProps> = ({ lessonId, courseId }) => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { currentLesson, isLoading } = useAppSelector(state => state.learning);
  
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [videoProgress, setVideoProgress] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [bookmarked, setBookmarked] = useState(false);
  const [showNotes, setShowNotes] = useState(false);
  const [showAIHelp, setShowAIHelp] = useState(false);
  const [notes, setNotes] = useState('');
  const [showRating, setShowRating] = useState(false);
  const [rating, setRating] = useState(0);
  const [readingTime, setReadingTime] = useState(0);

  const videoRef = React.useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (lessonId) {
      dispatch(fetchLessonDetails(lessonId));
    }
  }, [lessonId, dispatch]);

  useEffect(() => {
    // Calculate estimated reading time
    if (currentLesson?.content) {
      const wordsPerMinute = 200;
      const wordCount = currentLesson.content.split(' ').length;
      setReadingTime(Math.ceil(wordCount / wordsPerMinute));
    }
  }, [currentLesson]);

  const handleVideoTimeUpdate = () => {
    if (videoRef.current) {
      const progress = (videoRef.current.currentTime / videoRef.current.duration) * 100;
      setVideoProgress(progress);
    }
  };

  const handleMarkCompleted = async () => {
    if (currentLesson) {
      await dispatch(markLessonCompleted(currentLesson.id));
      setShowRating(true);
    }
  };

  const handleSpeedChange = (speed: number) => {
    setPlaybackSpeed(speed);
    if (videoRef.current) {
      videoRef.current.playbackRate = speed;
    }
  };

  const handleBookmark = () => {
    setBookmarked(!bookmarked);
    // API call to bookmark/unbookmark lesson
  };

  const handleShare = () => {
    navigator.share?.({
      title: currentLesson?.title,
      url: window.location.href,
    });
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const renderCodeBlock = ({ language, children }: any) => (
    <SyntaxHighlighter
      style={tomorrow}
      language={language}
      customStyle={{
        margin: '1rem 0',
        borderRadius: '8px',
      }}
    >
      {children}
    </SyntaxHighlighter>
  );

  if (isLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Loading lesson...</Typography>
      </Box>
    );
  }

  if (!currentLesson) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6">Lesson not found</Typography>
        <Button onClick={() => navigate(-1)} sx={{ mt: 2 }}>
          Go Back
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      {/* Main Content */}
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Paper
          elevation={1}
          sx={{
            p: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderRadius: 0,
          }}
        >
          <Box>
            <Typography variant="h5" gutterBottom>
              {currentLesson.title}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Chip
                icon={currentLesson.lessonType === 'video' ? <PlayCircle /> : <MenuBook />}
                label={currentLesson.lessonType.toUpperCase()}
                size="small"
                color="primary"
              />
              <Typography variant="body2" color="text.secondary">
                {currentLesson.lessonType === 'video' 
                  ? `${currentLesson.videoDuration || '10:00'} minutes`
                  : `${readingTime} min read`
                }
              </Typography>
              {currentLesson.difficulty && (
                <Chip label={currentLesson.difficulty} size="small" variant="outlined" />
              )}
            </Box>
          </Box>

          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Take Notes">
              <IconButton onClick={() => setShowNotes(true)}>
                <Notes />
              </IconButton>
            </Tooltip>
            
            <Tooltip title={bookmarked ? "Remove Bookmark" : "Bookmark"}>
              <IconButton onClick={handleBookmark}>
                {bookmarked ? <Bookmark color="primary" /> : <BookmarkBorder />}
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Get AI Help">
              <IconButton onClick={() => setShowAIHelp(true)}>
                <Help />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Share">
              <IconButton onClick={handleShare}>
                <Share />
              </IconButton>
            </Tooltip>
          </Box>
        </Paper>

        {/* Video Player (if video lesson) */}
        {currentLesson.lessonType === 'video' && currentLesson.videoUrl && (
          <Box sx={{ position: 'relative', backgroundColor: 'black' }}>
            <video
              ref={videoRef}
              width="100%"
              height="400"
              controls
              onTimeUpdate={handleVideoTimeUpdate}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              style={{ display: 'block' }}
            >
              <source src={currentLesson.videoUrl} type="video/mp4" />
              Your browser does not support the video tag.
            </video>

            {/* Video Controls Overlay */}
            <Box
              sx={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                background: 'linear-gradient(transparent, rgba(0,0,0,0.7))',
                p: 2,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
              }}
            >
              <IconButton onClick={() => setIsPlaying(!isPlaying)} sx={{ color: 'white' }}>
                {isPlaying ? <Pause /> : <PlayArrow />}
              </IconButton>

              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Speed sx={{ color: 'white', fontSize: 20 }} />
                {[0.5, 0.75, 1, 1.25, 1.5, 2].map((speed) => (
                  <Button
                    key={speed}
                    size="small"
                    onClick={() => handleSpeedChange(speed)}
                    sx={{
                      color: playbackSpeed === speed ? 'primary.main' : 'white',
                      minWidth: 'auto',
                      px: 1,
                    }}
                  >
                    {speed}x
                  </Button>
                ))}
              </Box>

              <Box sx={{ flexGrow: 1 }} />

              <IconButton sx={{ color: 'white' }}>
                <Fullscreen />
              </IconButton>
            </Box>

            {/* Progress Bar */}
            <LinearProgress
              variant="determinate"
              value={videoProgress}
              sx={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                height: 4,
              }}
            />
          </Box>
        )}

        {/* Lesson Content */}
        <Box sx={{ flexGrow: 1, overflow: 'auto', p: 3 }}>
          {currentLesson.description && (
            <Paper elevation={1} sx={{ p: 3, mb: 3, bgcolor: 'grey.50' }}>
              <Typography variant="body1">{currentLesson.description}</Typography>
            </Paper>
          )}

          <Paper elevation={1} sx={{ p: 3 }}>
            <ReactMarkdown
              components={{
                code: renderCodeBlock,
                h1: ({ children }) => (
                  <Typography variant="h4" gutterBottom sx={{ mt: 3, mb: 2 }}>
                    {children}
                  </Typography>
                ),
                h2: ({ children }) => (
                  <Typography variant="h5" gutterBottom sx={{ mt: 3, mb: 2 }}>
                    {children}
                  </Typography>
                ),
                h3: ({ children }) => (
                  <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 1 }}>
                    {children}
                  </Typography>
                ),
                p: ({ children }) => (
                  <Typography variant="body1" paragraph>
                    {children}
                  </Typography>
                ),
                blockquote: ({ children }) => (
                  <Paper
                    elevation={0}
                    sx={{
                      borderLeft: 4,
                      borderColor: 'primary.main',
                      bgcolor: 'primary.50',
                      p: 2,
                      my: 2,
                      fontStyle: 'italic',
                    }}
                  >
                    {children}
                  </Paper>
                ),
              }}
            >
              {currentLesson.content}
            </ReactMarkdown>
          </Paper>

          {/* Additional Resources */}
          {currentLesson.additionalResources && currentLesson.additionalResources.length > 0 && (
            <Paper elevation={1} sx={{ p: 3, mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                Additional Resources
              </Typography>
              <List>
                {currentLesson.additionalResources.map((resource: any, index: number) => (
                  <ListItem key={index}>
                    <ListItemButton component="a" href={resource.url} target="_blank">
                      <ListItemText
                        primary={resource.title}
                        secondary={resource.description}
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            </Paper>
          )}
        </Box>

        {/* Navigation Footer */}
        <Paper
          elevation={3}
          sx={{
            p: 2,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Button
            startIcon={<SkipPrevious />}
            onClick={() => {/* Navigate to previous lesson */}}
          >
            Previous Lesson
          </Button>

          <Button
            variant="contained"
            startIcon={<CheckCircle />}
            onClick={handleMarkCompleted}
            disabled={currentLesson.userProgress?.status === 'completed'}
          >
            {currentLesson.userProgress?.status === 'completed' ? 'Completed' : 'Mark Complete'}
          </Button>

          <Button
            endIcon={<SkipNext />}
            onClick={() => {/* Navigate to next lesson */}}
          >
            Next Lesson
          </Button>
        </Paper>
      </Box>

      {/* AI Help Dialog */}
      <Dialog
        open={showAIHelp}
        onClose={() => setShowAIHelp(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>AI Tutor Help</DialogTitle>
        <DialogContent sx={{ height: 600, p: 0 }}>
          <AITutorChat
            sessionType="concept_explanation"
            initialQuery={`I need help understanding the lesson: ${currentLesson.title}`}
            context={{
              lesson_id: currentLesson.id,
              lesson_content: currentLesson.content.substring(0, 1000),
            }}
            height="600px"
          />
        </DialogContent>
      </Dialog>

      {/* Rating Dialog */}
      <Dialog open={showRating} onClose={() => setShowRating(false)}>
        <DialogTitle>Rate This Lesson</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            How would you rate this lesson?
          </Typography>
          <Rating
            value={rating}
            onChange={(_, value) => setRating(value || 0)}
            size="large"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowRating(false)}>Skip</Button>
          <Button onClick={() => setShowRating(false)} variant="contained">
            Submit
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LessonViewer;


// src/components/Learning/ExerciseInterface.tsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Button,
  LinearProgress,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Tooltip,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Help,
  Lightbulb,
  Check,
  Close,
  ExpandMore,
  Timer,
  Psychology,
  Bug,
  Star,
  TrendingUp,
} from '@mui/icons-material';
import CodeEditor from '../CodeEditor/CodeEditor';
import { useAppDispatch, useAppSelector } from '../../store/store';
import { submitExercise, requestHint } from '../../store/slices/learningSlice';
import { executeCode } from '../../store/slices/codeExecutionSlice';
import AITutorChat from '../AITutor/AITutorChat';

interface ExerciseInterfaceProps {
  exerciseId: string;
}

const ExerciseInterface: React.FC<ExerciseInterfaceProps> = ({ exerciseId }) => {
  const dispatch = useAppDispatch();
  const { currentExercise, isSubmitting } = useAppSelector(state => state.learning);
  const { isExecuting, currentExecution } = useAppSelector(state => state.codeExecution);
  
  const [code, setCode] = useState('');
  const [output, setOutput] = useState('');
  const [testResults, setTestResults] = useState<any[]>([]);
  const [showHints, setShowHints] = useState(false);
  const [hints, setHints] = useState<string[]>([]);
  const [usedHints, setUsedHints] = useState(0);
  const [showSolution, setShowSolution] = useState(false);
  const [timeSpent, setTimeSpent] = useState(0);
  const [showAIHelp, setShowAIHelp] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [currentStep, setCurrentStep] = useState(0);

  const startTime = React.useRef(Date.now());

  useEffect(() => {
    if (currentExercise) {
      setCode(currentExercise.starterCode || '');
    }
  }, [currentExercise]);

  useEffect(() => {
    // Timer for tracking time spent
    const timer = setInterval(() => {
      setTimeSpent(Math.floor((Date.now() - startTime.current) / 1000));
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    // Update test results when execution completes
    if (currentExecution?.testResults) {
      setTestResults(currentExecution.testResults);
      setOutput(currentExecution.stdout || currentExecution.stderr || '');
    }
  }, [currentExecution]);

  const handleRunCode = async () => {
    if (!code.trim()) return;

    await dispatch(executeCode({
      code,
      language: currentExercise?.programmingLanguage || 'python',
      exerciseId: currentExercise?.id,
    }));
  };

  const handleSubmit = async () => {
    if (!code.trim() || !currentExercise) return;

    const result = await dispatch(submitExercise({
      exerciseId: currentExercise.id,
      code,
      timeTaken: timeSpent,
      hintsUsed: usedHints,
    }));

    if (result.payload?.status === 'passed') {
      setCurrentStep(3); // Success step
    } else {
      setCurrentStep(2); // Review step
    }
  };

  const handleRequestHint = async () => {
    if (!currentExercise) return;

    const result = await dispatch(requestHint({
      exerciseId: currentExercise.id,
      currentCode: code,
    }));

    if (result.payload?.hint) {
      setHints([...hints, result.payload.hint]);
      setUsedHints(usedHints + 1);
      setShowHints(true);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getTestResultIcon = (status: string) => {
    switch (status) {
      case 'passed':
        return <Check color="success" />;
      case 'failed':
        return <Close color="error" />;
      default:
        return <Bug color="warning" />;
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy':
        return 'success';
      case 'medium':
        return 'warning';
      case 'hard':
        return 'error';
      default:
        return 'default';
    }
  };

  if (!currentExercise) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6">Exercise not found</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper elevation={1} sx={{ p: 2, borderRadius: 0 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h5" gutterBottom>
              {currentExercise.title}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <Chip
                label={currentExercise.difficulty}
                size="small"
                color={getDifficultyColor(currentExercise.difficulty) as any}
              />
              <Chip
                label={`${currentExercise.points} points`}
                size="small"
                variant="outlined"
              />
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Timer fontSize="small" />
                <Typography variant="body2">{formatTime(timeSpent)}</Typography>
              </Box>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Get Hint">
              <IconButton
                onClick={handleRequestHint}
                disabled={currentExercise.maxAttempts && usedHints >= 3}
              >
                <Lightbulb />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="AI Help">
              <IconButton onClick={() => setShowAIHelp(true)}>
                <Psychology />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Progress Stepper */}
        <Stepper activeStep={currentStep} sx={{ mt: 2 }}>
          <Step>
            <StepLabel>Code</StepLabel>
          </Step>
          <Step>
            <StepLabel>Test</StepLabel>
          </Step>
          <Step>
            <StepLabel>Review</StepLabel>
          </Step>
          <Step>
            <StepLabel>Complete</StepLabel>
          </Step>
        </Stepper>
      </Paper>

      {/* Main Content */}
      <Box sx={{ flexGrow: 1, display: 'flex' }}>
        {/* Left Panel - Instructions */}
        <Box sx={{ width: '40%', borderRight: 1, borderColor: 'divider', overflow: 'auto' }}>
          <Box sx={{ p: 3 }}>
            {/* Description */}
            <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Instructions
              </Typography>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {currentExercise.description}
              </Typography>
            </Paper>

            {/* Example/Test Cases Preview */}
            {testResults.length > 0 && (
              <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Test Results
                </Typography>
                <List dense>
                  {testResults.map((result, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        {getTestResultIcon(result.status)}
                      </ListItemIcon>
                      <ListItemText
                        primary={`Test Case ${index + 1}`}
                        secondary={result.status === 'failed' ? result.errorMessage : 'Passed'}
                      />
                    </ListItem>
                  ))}
                </List>
              </Paper>
            )}

            {/* Hints */}
            {hints.length > 0 && (
              <Accordion expanded={showHints} onChange={() => setShowHints(!showHints)}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6">
                    Hints ({hints.length} used)
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  {hints.map((hint, index) => (
                    <Alert key={index} severity="info" sx={{ mb: 1 }}>
                      <Typography variant="body2">{hint}</Typography>
                    </Alert>
                  ))}
                </AccordionDetails>
              </Accordion>
            )}

            {/* AI Feedback */}
            {feedback && (
              <Paper elevation={1} sx={{ p: 3, mb: 3, bgcolor: 'info.50' }}>
                <Typography variant="h6" gutterBottom color="info.main">
                  AI Feedback
                </Typography>
                <Typography variant="body2">{feedback}</Typography>
              </Paper>
            )}
          </Box>
        </Box>

        {/* Right Panel - Code Editor and Output */}
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Code Editor */}
          <Box sx={{ flexGrow: 1 }}>
            <CodeEditor
              language={currentExercise.programmingLanguage}
              initialCode={currentExercise.starterCode}
              onChange={setCode}
              height="100%"
              showExecuteButton={true}
              onExecute={handleRunCode}
            />
          </Box>

          {/* Output Panel */}
          <Paper
            elevation={1}
            sx={{
              height: '200px',
              borderRadius: 0,
              borderTop: 1,
              borderColor: 'divider',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <Box
              sx={{
                p: 1,
                borderBottom: 1,
                borderColor: 'divider',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <Typography variant="subtitle2">Output</Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<PlayArrow />}
                  onClick={handleRunCode}
                  disabled={isExecuting || !code.trim()}
                >
                  {isExecuting ? 'Running...' : 'Run'}
                </Button>
                <Button
                  size="small"
                  variant="contained"
                  onClick={handleSubmit}
                  disabled={isSubmitting || !code.trim()}
                >
                  {isSubmitting ? 'Submitting...' : 'Submit'}
                </Button>
              </Box>
            </Box>

            <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
              {isExecuting && <LinearProgress sx={{ mb: 2 }} />}
              
              <Typography
                component="pre"
                sx={{
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                  whiteSpace: 'pre-wrap',
                  color: output.includes('Error') ? 'error.main' : 'text.primary',
                }}
              >
                {output || 'Run your code to see output...'}
              </Typography>
            </Box>
          </Paper>
        </Box>
      </Box>

      {/* AI Help Dialog */}
      <Dialog
        open={showAIHelp}
        onClose={() => setShowAIHelp(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>AI Coding Assistant</DialogTitle>
        <DialogContent sx={{ height: 600, p: 0 }}>
          <AITutorChat
            sessionType="debugging"
            initialQuery={`I need help with this coding exercise: ${currentExercise.title}. Here's my current code: ${code}`}
            context={{
              exercise_id: currentExercise.id,
              exercise_description: currentExercise.description,
              current_code: code,
              programming_language: currentExercise.programmingLanguage,
            }}
            height="600px"
          />
        </DialogContent>
      </Dialog>

      {/* Solution Dialog */}
      <Dialog open={showSolution} onClose={() => setShowSolution(false)} maxWidth="md" fullWidth>
        <DialogTitle>Solution</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Viewing the solution will affect your score for this exercise.
          </Alert>
          <CodeEditor
            language={currentExercise.programmingLanguage}
            initialCode={currentExercise.solutionCode || '// Solution not available'}
            readOnly={true}
            height="400px"
            showToolbar={false}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSolution(false)}>Close</Button>
          <Button
            onClick={() => {
              setCode(currentExercise.solutionCode || '');
              setShowSolution(false);
            }}
            variant="contained"
          >
            Use This Solution
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ExerciseInterface;


// src/components/Collaboration/CollaborationRoom.tsx
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