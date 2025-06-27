import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import CodeEditor from '../CodeEditor/CodeEditor';
import codeExecutionReducer from '../../store/slices/codeExecutionSlice';

// Mock Monaco Editor
jest.mock('@monaco-editor/react', () => ({
  Editor: ({ onChange, value }: any) => (
    <textarea
      data-testid="code-editor"
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
    />
  ),
}));

const mockStore = configureStore({
  reducer: {
    codeExecution: codeExecutionReducer,
  },
});

const renderCodeEditor = (props = {}) => {
  const defaultProps = {
    language: 'python',
    initialCode: '# Hello World',
    onChange: jest.fn(),
    onExecute: jest.fn(),
  };

  return render(
    <Provider store={mockStore}>
      <CodeEditor {...defaultProps} {...props} />
    </Provider>
  );
};

describe('CodeEditor', () => {
  test('renders code editor', () => {
    renderCodeEditor();
    expect(screen.getByTestId('code-editor')).toBeInTheDocument();
  });

  test('displays initial code', () => {
    renderCodeEditor({ initialCode: 'print("Hello")' });
    expect(screen.getByDisplayValue('print("Hello")')).toBeInTheDocument();
  });

  test('calls onChange when code changes', async () => {
    const mockOnChange = jest.fn();
    renderCodeEditor({ onChange: mockOnChange });
    
    const editor = screen.getByTestId('code-editor');
    fireEvent.change(editor, { target: { value: 'new code' } });
    
    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalledWith('new code');
    });
  });

  test('shows execute button when enabled', () => {
    renderCodeEditor({ showExecuteButton: true });
    expect(screen.getByRole('button', { name: /run/i })).toBeInTheDocument();
  });

  test('calls onExecute when execute button is clicked', () => {
    const mockOnExecute = jest.fn();
    renderCodeEditor({ 
      showExecuteButton: true, 
      onExecute: mockOnExecute,
      initialCode: 'print("test")'
    });
    
    fireEvent.click(screen.getByRole('button', { name: /run/i }));
    expect(mockOnExecute).toHaveBeenCalledWith('print("test")');
  });

  test('handles readonly mode', () => {
    renderCodeEditor({ readOnly: true });
    const editor = screen.getByTestId('code-editor');
    expect(editor).toHaveAttribute('readonly');
  });

  test('shows toolbar when enabled', () => {
    renderCodeEditor({ showToolbar: true });
    expect(screen.getByText(/environment/i)).toBeInTheDocument();
  });
});

