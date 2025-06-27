// src/services/api.ts
import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { store } from '../store/store';
import { setTokens } from '../store/slices/authSlice';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = store.getState().auth.accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = store.getState().auth.refreshToken;
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          store.dispatch(setTokens({ access, refresh: refreshToken }));

          originalRequest.headers.Authorization = `Bearer ${access}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// API Service Classes
export class AuthAPI {
  async login(credentials: { email: string; password: string }) {
    return apiClient.post('/auth/login/', credentials);
  }

  async register(userData: {
    username: string;
    email: string;
    password: string;
    firstName: string;
    lastName: string;
  }) {
    return apiClient.post('/auth/register/', userData);
  }

  async logout() {
    const refreshToken = store.getState().auth.refreshToken;
    return apiClient.post('/auth/logout/', { refresh: refreshToken });
  }

  async getCurrentUser() {
    return apiClient.get('/auth/user/');
  }

  async updateProfile(data: any) {
    return apiClient.patch('/auth/user/', data);
  }

  async changePassword(data: { oldPassword: string; newPassword: string }) {
    return apiClient.post('/auth/change-password/', data);
  }

  async requestPasswordReset(email: string) {
    return apiClient.post('/auth/password-reset/', { email });
  }

  async confirmPasswordReset(data: { token: string; password: string }) {
    return apiClient.post('/auth/password-reset/confirm/', data);
  }
}

export class CoursesAPI {
  async getCourses(params: {
    page?: number;
    search?: string;
    category?: string;
    difficulty?: string;
    isFree?: boolean;
    ordering?: string;
  } = {}) {
    return apiClient.get('/courses/', { params });
  }

  async getCourseDetails(courseId: string) {
    return apiClient.get(`/courses/${courseId}/`);
  }

  async getCourseModules(courseId: string) {
    return apiClient.get(`/courses/${courseId}/modules/`);
  }

  async enrollInCourse(courseId: string) {
    return apiClient.post(`/courses/${courseId}/enroll/`);
  }

  async getCourseProgress(courseId: string) {
    return apiClient.get(`/courses/${courseId}/progress/`);
  }

  async getCategories() {
    return apiClient.get('/courses/categories/');
  }

  async rateCourse(courseId: string, rating: number, review?: string) {
    return apiClient.post(`/courses/${courseId}/rate/`, { rating, review });
  }
}

export class LearningAPI {
  async getLessons(params: { course?: string; module?: string } = {}) {
    return apiClient.get('/lessons/', { params });
  }

  async getLessonDetails(lessonId: string) {
    return apiClient.get(`/lessons/${lessonId}/`);
  }

  async markLessonCompleted(lessonId: string) {
    return apiClient.post(`/lessons/${lessonId}/mark_completed/`);
  }

  async getExercises(params: { lesson?: string; course?: string } = {}) {
    return apiClient.get('/exercises/', { params });
  }

  async getExerciseDetails(exerciseId: string) {
    return apiClient.get(`/exercises/${exerciseId}/`);
  }

  async submitExercise(exerciseId: string, data: {
    code: string;
    timeTaken?: number;
    hintsUsed?: number;
  }) {
    return apiClient.post(`/exercises/${exerciseId}/submit/`, data);
  }

  async getExerciseSubmissions(exerciseId: string) {
    return apiClient.get(`/exercises/${exerciseId}/submissions/`);
  }

  async requestHint(exerciseId: string, currentCode: string) {
    return apiClient.post(`/exercises/${exerciseId}/hint/`, { code: currentCode });
  }
}

export class AITutorAPI {
  async getSessions() {
    return apiClient.get('/ai-tutor/sessions/');
  }

  async createSession(data: {
    session_type: string;
    initial_query: string;
    context_data?: any;
  }) {
    return apiClient.post('/ai-tutor/sessions/', data);
  }

  async getSession(sessionId: string) {
    return apiClient.get(`/ai-tutor/sessions/${sessionId}/`);
  }

  async getSessionMessages(sessionId: string) {
    return apiClient.get(`/ai-tutor/sessions/${sessionId}/messages/`);
  }

  async sendMessage(sessionId: string, data: {
    content: string;
    context?: any;
  }) {
    return apiClient.post(`/ai-tutor/sessions/${sessionId}/send_message/`, data);
  }

  async endSession(sessionId: string, feedback?: any) {
    return apiClient.post(`/ai-tutor/sessions/${sessionId}/end/`, feedback);
  }

  async getRecommendations() {
    return apiClient.get('/ai-tutor/recommendations/');
  }

  async acceptRecommendation(recommendationId: string) {
    return apiClient.post(`/ai-tutor/recommendations/${recommendationId}/accept/`);
  }
}

export class CodeExecutionAPI {
  async getEnvironments() {
    return apiClient.get('/code-execution/environments/');
  }

  async executeCode(data: {
    code: string;
    environment_id: string;
    stdin_input?: string;
    exercise_id?: string;
  }) {
    return apiClient.post('/code-execution/execute/', data);
  }

  async getExecution(executionId: string) {
    return apiClient.get(`/code-execution/${executionId}/`);
  }

  async stopExecution(executionId: string) {
    return apiClient.post(`/code-execution/${executionId}/stop/`);
  }

  async getExecutionHistory() {
    return apiClient.get('/code-execution/');
  }
}

export class CollaborationAPI {
  async getRooms(params: { status?: string; room_type?: string } = {}) {
    return apiClient.get('/collaboration/rooms/', { params });
  }

  async createRoom(data: {
    title: string;
    description?: string;
    room_type: string;
    is_public?: boolean;
    max_participants?: number;
  }) {
    return apiClient.post('/collaboration/rooms/', data);
  }

  async joinRoom(roomId: string) {
    return apiClient.post(`/collaboration/rooms/${roomId}/join/`);
  }

  async leaveRoom(roomId: string) {
    return apiClient.post(`/collaboration/rooms/${roomId}/leave/`);
  }

  async getRoomMessages(roomId: string) {
    return apiClient.get(`/collaboration/rooms/${roomId}/messages/`);
  }

  async sendMessage(roomId: string, data: {
    message_type: string;
    content: string;
    metadata?: any;
  }) {
    return apiClient.post(`/collaboration/rooms/${roomId}/messages/`, data);
  }
}

export class AnalyticsAPI {
  async getDashboard() {
    return apiClient.get('/analytics/dashboard/');
  }

  async getPerformanceMetrics(params: {
    granularity?: string;
    start_date?: string;
    end_date?: string;
  } = {}) {
    return apiClient.get('/analytics/performance_metrics/', { params });
  }

  async getStudySessionss() {
    return apiClient.get('/analytics/study-sessions/');
  }

  async getInsights() {
    return apiClient.get('/analytics/insights/');
  }

  async getCourseAnalytics(courseId: string) {
    return apiClient.get(`/analytics/courses/${courseId}/`);
  }

  async getSkillProgress() {
    return apiClient.get('/analytics/skills/');
  }
}

// Export API instances
export const authAPI = new AuthAPI();
export const coursesAPI = new CoursesAPI();
export const learningAPI = new LearningAPI();
export const aiTutorAPI = new AITutorAPI();
export const codeExecutionAPI = new CodeExecutionAPI();
export const collaborationAPI = new CollaborationAPI();
export const analyticsAPI = new AnalyticsAPI();


// src/components/Dashboard/LearningStats.tsx
import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Box,
  LinearProgress,
  Chip,
  Avatar,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  TrendingUp,
  School,
  Code,
  Timer,
  Star,
  LocalFireDepartment,
  Psychology,
  EmojiEvents,
} from '@mui/icons-material';

interface LearningStatsProps {
  analytics: {
    totalStudyTime: number;
    coursesCompleted: number;
    currentStreak: number;
    averageScore: number;
    successRate: number;
    learningVelocity: number;
  };
  recentActivity: Array<{
    type: string;
    title: string;
    progress: number;
    timeSpent: number;
    date: string;
  }>;
}

const LearningStats: React.FC<LearningStatsProps> = ({ analytics, recentActivity }) => {
  const formatTime = (hours: number) => {
    if (hours < 1) {
      return `${Math.round(hours * 60)}m`;
    }
    return `${Math.round(hours)}h`;
  };

  const getStreakColor = (streak: number) => {
    if (streak >= 30) return 'error';
    if (streak >= 14) return 'warning';
    if (streak >= 7) return 'success';
    return 'primary';
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'success';
    if (score >= 75) return 'info';
    if (score >= 60) return 'warning';
    return 'error';
  };

  return (
    <Grid container spacing={3}>
      {/* Main Stats Cards */}
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                <Timer />
              </Avatar>
              <Box>
                <Typography color="text.secondary" variant="body2">
                  Total Study Time
                </Typography>
                <Typography variant="h5" component="div">
                  {formatTime(analytics.totalStudyTime)}
                </Typography>
              </Box>
            </Box>
            <Typography variant="body2" color="text.secondary">
              This month: {formatTime(analytics.totalStudyTime * 0.3)}
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                <School />
              </Avatar>
              <Box>
                <Typography color="text.secondary" variant="body2">
                  Courses Completed
                </Typography>
                <Typography variant="h5" component="div">
                  {analytics.coursesCompleted}
                </Typography>
              </Box>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Keep up the great work!
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <Avatar sx={{ bgcolor: getStreakColor(analytics.currentStreak) + '.main', mr: 2 }}>
                <LocalFireDepartment />
              </Avatar>
              <Box>
                <Typography color="text.secondary" variant="body2">
                  Current Streak
                </Typography>
                <Typography variant="h5" component="div">
                  {analytics.currentStreak} days
                </Typography>
              </Box>
            </Box>
            <Typography variant="body2" color="text.secondary">
              {analytics.currentStreak >= 7 ? '🔥 On fire!' : 'Keep going!'}
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <Avatar sx={{ bgcolor: getScoreColor(analytics.averageScore) + '.main', mr: 2 }}>
                <Star />
              </Avatar>
              <Box>
                <Typography color="text.secondary" variant="body2">
                  Average Score
                </Typography>
                <Typography variant="h5" component="div">
                  {Math.round(analytics.averageScore)}%
                </Typography>
              </Box>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Success rate: {Math.round(analytics.successRate)}%
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Performance Overview */}
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Learning Performance
            </Typography>
            
            <Box mb={3}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="body2">Exercise Success Rate</Typography>
                <Typography variant="body2" color="text.secondary">
                  {Math.round(analytics.successRate)}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={analytics.successRate}
                color={analytics.successRate >= 80 ? 'success' : 'primary'}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>

            <Box mb={3}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="body2">Learning Velocity</Typography>
                <Typography variant="body2" color="text.secondary">
                  {analytics.learningVelocity.toFixed(1)} lessons/week
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={Math.min(analytics.learningVelocity * 20, 100)}
                color="info"
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>

            <Box>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="body2">Average Score</Typography>
                <Typography variant="body2" color="text.secondary">
                  {Math.round(analytics.averageScore)}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={analytics.averageScore}
                color={getScoreColor(analytics.averageScore) as any}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Recent Activity */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            
            {recentActivity.slice(0, 5).map((activity, index) => (
              <Box key={index} mb={2}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="body2" noWrap sx={{ maxWidth: '70%' }}>
                    {activity.title}
                  </Typography>
                  <Chip
                    label={activity.type}
                    size="small"
                    variant="outlined"
                    color={activity.type === 'lesson' ? 'primary' : 'secondary'}
                  />
                </Box>
                
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="caption" color="text.secondary">
                    {formatTime(activity.timeSpent)} • {new Date(activity.date).toLocaleDateString()}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {Math.round(activity.progress)}%
                  </Typography>
                </Box>
                
                <LinearProgress
                  variant="determinate"
                  value={activity.progress}
                  size="small"
                  sx={{ height: 4, borderRadius: 2 }}
                />
              </Box>
            ))}
            
            {recentActivity.length === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                No recent activity
              </Typography>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Quick Actions */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            
            <Box display="flex" gap={2} flexWrap="wrap">
              <Tooltip title="Start a new coding session">
                <IconButton color="primary" sx={{ border: 1, borderColor: 'primary.main' }}>
                  <Code />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="Get AI help">
                <IconButton color="secondary" sx={{ border: 1, borderColor: 'secondary.main' }}>
                  <Psychology />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="View achievements">
                <IconButton color="warning" sx={{ border: 1, borderColor: 'warning.main' }}>
                  <EmojiEvents />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="Track progress">
                <IconButton color="info" sx={{ border: 1, borderColor: 'info.main' }}>
                  <TrendingUp />
                </IconButton>
              </Tooltip>
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default LearningStats;


// src/components/Dashboard/CourseProgress.tsx
import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Button,
  Grid,
  Avatar,
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  PlayArrow,
  MoreVert,
  Schedule,
  CheckCircle,
  BookmarkBorder,
  Share,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface CourseProgressProps {
  courses: Array<{
    id: string;
    title: string;
    instructor: {
      name: string;
      avatar?: string;
    };
    thumbnail?: string;
    progress: number;
    status: string;
    lastAccessed?: string;
    nextLesson?: {
      id: string;
      title: string;
    };
    estimatedTimeRemaining?: number;
    totalLessons: number;
    completedLessons: number;
  }>;
}

const CourseProgress: React.FC<CourseProgressProps> = ({ courses }) => {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [selectedCourse, setSelectedCourse] = React.useState<string | null>(null);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, courseId: string) => {
    setAnchorEl(event.currentTarget);
    setSelectedCourse(courseId);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedCourse(null);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'primary';
      case 'enrolled':
        return 'info';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Completed';
      case 'in_progress':
        return 'In Progress';
      case 'enrolled':
        return 'Not Started';
      default:
        return 'Unknown';
    }
  };

  const formatTimeRemaining = (hours: number) => {
    if (hours < 1) {
      return `${Math.round(hours * 60)}m remaining`;
    }
    return `${Math.round(hours)}h remaining`;
  };

  const handleContinue = (course: any) => {
    if (course.nextLesson) {
      navigate(`/courses/${course.id}/lessons/${course.nextLesson.id}`);
    } else {
      navigate(`/courses/${course.id}`);
    }
  };

  return (
    <Grid container spacing={3}>
      {courses.map((course) => (
        <Grid item xs={12} md={6} lg={4} key={course.id}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Course Header */}
            <Box
              sx={{
                height: 160,
                background: course.thumbnail
                  ? `url(${course.thumbnail})`
                  : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                position: 'relative',
                display: 'flex',
                alignItems: 'flex-end',
                p: 2,
              }}
            >
              <Box
                sx={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: 'linear-gradient(transparent, rgba(0,0,0,0.7))',
                }}
              />
              
              <Box sx={{ position: 'relative', zIndex: 1, width: '100%' }}>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                  <Typography
                    variant="h6"
                    color="white"
                    sx={{ fontWeight: 600, mb: 1, maxWidth: '80%' }}
                  >
                    {course.title}
                  </Typography>
                  
                  <IconButton
                    size="small"
                    sx={{ color: 'white' }}
                    onClick={(e) => handleMenuClick(e, course.id)}
                  >
                    <MoreVert />
                  </IconButton>
                </Box>
                
                <Box display="flex" alignItems="center" gap={1}>
                  <Avatar
                    src={course.instructor.avatar}
                    sx={{ width: 24, height: 24 }}
                  >
                    {course.instructor.name.charAt(0)}
                  </Avatar>
                  <Typography variant="body2" color="white" sx={{ opacity: 0.9 }}>
                    {course.instructor.name}
                  </Typography>
                </Box>
              </Box>
            </Box>

            <CardContent sx={{ flexGrow: 1, pb: 1 }}>
              {/* Progress Section */}
              <Box mb={2}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="body2" color="text.secondary">
                    Progress
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {Math.round(course.progress)}%
                  </Typography>
                </Box>
                
                <LinearProgress
                  variant="determinate"
                  value={course.progress}
                  sx={{ height: 8, borderRadius: 4, mb: 1 }}
                  color={course.progress === 100 ? 'success' : 'primary'}
                />
                
                <Typography variant="caption" color="text.secondary">
                  {course.completedLessons} of {course.totalLessons} lessons completed
                </Typography>
              </Box>

              {/* Status and Time */}
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Chip
                  label={getStatusLabel(course.status)}
                  size="small"
                  color={getStatusColor(course.status) as any}
                  variant={course.status === 'completed' ? 'filled' : 'outlined'}
                />
                
                {course.estimatedTimeRemaining && course.status !== 'completed' && (
                  <Box display="flex" alignItems="center" gap={0.5}>
                    <Schedule sx={{ fontSize: 16, color: 'text.secondary' }} />
                    <Typography variant="caption" color="text.secondary">
                      {formatTimeRemaining(course.estimatedTimeRemaining)}
                    </Typography>
                  </Box>
                )}
              </Box>

              {/* Next Lesson */}
              {course.nextLesson && course.status !== 'completed' && (
                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Up next:
                  </Typography>
                  <Typography variant="body2" fontWeight={500} noWrap>
                    {course.nextLesson.title}
                  </Typography>
                </Box>
              )}

              {/* Last Accessed */}
              {course.lastAccessed && (
                <Typography variant="caption" color="text.secondary" display="block" mb={2}>
                  Last accessed: {new Date(course.lastAccessed).toLocaleDateString()}
                </Typography>
              )}
            </CardContent>

            {/* Action Button */}
            <Box sx={{ p: 2, pt: 0 }}>
              <Button
                fullWidth
                variant={course.status === 'completed' ? 'outlined' : 'contained'}
                startIcon={course.status === 'completed' ? <CheckCircle /> : <PlayArrow />}
                onClick={() => handleContinue(course)}
              >
                {course.status === 'completed' ? 'Review' : 'Continue'}
              </Button>
            </Box>
          </Card>
        </Grid>
      ))}

      {/* Course Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleMenuClose}>
          <BookmarkBorder sx={{ mr: 1, fontSize: 20 }} />
          Bookmark Course
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <Share sx={{ mr: 1, fontSize: 20 }} />
          Share Course
        </MenuItem>
      </Menu>

      {/* Empty State */}
      {courses.length === 0 && (
        <Grid item xs={12}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 6 }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No courses in progress
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Explore our course catalog to start learning
              </Typography>
              <Button
                variant="contained"
                onClick={() => navigate('/courses')}
              >
                Browse Courses
              </Button>
            </CardContent>
          </Card>
        </Grid>
      )}
    </Grid>
  );
};

export default CourseProgress;