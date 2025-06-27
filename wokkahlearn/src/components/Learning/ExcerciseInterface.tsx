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

