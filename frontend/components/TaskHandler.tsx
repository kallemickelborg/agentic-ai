'use client';

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Label from '@/components/ui/Label';
import Spinner from '@/components/ui/Spinner';
import Typography from '@/components/ui/Typography';
import List from '@/components/ui/List';
import ListItem from '@/components/ui/ListItem';
import { motion } from 'framer-motion';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import StepIndicator from './ui/StepIndicator';
import Toast from './ui/ToastNotifications';

interface Author {
  name: string;
}

interface Paper {
  title: string;
  link: string;
  authors: Author[];
  published_date: string;
}

interface Task {
  state: string;
  input_data: {
    selected_papers?: string[];
    clarify_answers?: { question: string; answer: string }[];
  };
  task_description: string;
  research_papers: Paper[];
}

// Placeholder data
const placeholderData = {
  clarifyingQuestions: [
    "Are you interested in benefits related to bone health?",
    "Are you seeking information about the role of Vitamin D3 in immune function?",
    "Are you looking for benefits of Vitamin D3 for specific age groups or conditions?"
  ],
  researchPapers: [
    { title: "Vitamin D3 and Bone Health", link: "https://example.com/paper1", authors: [{ name: "John Doe" }], published_date: "2023-01-01" },
    { title: "Immune Function and Vitamin D3", link: "https://example.com/paper2", authors: [{ name: "Jane Smith" }], published_date: "2023-02-15" },
    { title: "Vitamin D3 Benefits Across Age Groups", link: "https://example.com/paper3", authors: [{ name: "Alice Johnson" }], published_date: "2023-03-30" },
  ],
  analysisResponse: "Analysis of the selected papers shows strong evidence for the benefits of Vitamin D3 in bone health...",
  synthesisResponse: "Synthesizing the information from the papers, we can conclude that Vitamin D3 plays a crucial role in...",
  conclusionResponse: "In conclusion, Vitamin D3 offers significant benefits, particularly in bone health. However, more research is needed to...",
};

export default function TaskSolver() {
  const [taskState, setTaskState] = useState('Start');
  const [taskDescription, setTaskDescription] = useState('');
  const [response, setResponse] = useState('');
  const [researchPapers, setResearchPapers] = useState<Paper[]>([]);
  const [selectedPapers, setSelectedPapers] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentSteps, setCurrentSteps] = useState<string[]>([]);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [clarifyingQuestions, setClarifyingQuestions] = useState<string[]>([]);
  const [clarifyAnswers, setClarifyAnswers] = useState<{ question: string; answer: string }[]>([]);
  const [isDevMode, setIsDevMode] = useState(false);

  const handleSelectPaper = (link: string) => {
    setSelectedPapers(prev =>
      prev.includes(link) ? prev.filter(l => l !== link) : [...prev, link]
    );
  };

  const handleClarifyAnswer = (index: number, answer: string) => {
    setClarifyAnswers(prev => {
      const newAnswers = [...prev];
      newAnswers[index] = { ...newAnswers[index], answer };
      return newAnswers;
    });
  };

  const handleTask = async () => {
    if (taskState === 'Start' && taskDescription.trim() === '') {
      alert('Please enter a research topic.');
      return;
    }

    setIsLoading(true);
    setResponse('');
    setCurrentSteps([]);

    try {
      let nextState = taskState;
      if (taskState === 'Start') {
        nextState = 'Clarify';
      } else if (taskState === 'Clarify' && clarifyAnswers.every(ans => ans.answer !== '')) {
        nextState = 'Research';
      } else if (taskState === 'Research' && selectedPapers.length > 0) {
        nextState = 'Analyze';
      }

      const payload: Task = {
        state: nextState,
        input_data: {
          selected_papers: selectedPapers,
          clarify_answers: clarifyAnswers,
        },
        task_description: taskDescription,
        research_papers: researchPapers,
      };

      const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;
      const result = await axios.post(`${API_BASE_URL}/solve-task/`, payload);

      console.log('Server Response:', result.data);

      setResponse(result.data.response);
      setTaskState(result.data.state);

      if (result.data.research_papers) {
        setResearchPapers(result.data.research_papers);
      }

      if (result.data.current_steps) {
        setCurrentSteps(result.data.current_steps);
      }

      if (result.data.questions) {
        setClarifyingQuestions(result.data.questions);
        setClarifyAnswers(result.data.questions.map((q: string) => ({ question: q, answer: '' })));
      }

      // Don't automatically trigger the next state
      setIsLoading(false);
    } catch (error) {
      console.error('Error during task processing:', error);
      setResponse('An error occurred while processing your request.');
      setToast({ message: 'An error occurred while processing your request.', type: 'error' });
    }
  };

  // New effect to handle automatic transitions
  useEffect(() => {
    if (taskState === 'Research' && researchPapers.length === 0) {
      handleTask();
    }
  }, [taskState]);

  // Function to cycle through states (for development purposes)
  const cycleState = (direction: 'forward' | 'backward') => {
    const states = ['Start', 'Clarify', 'Research', 'Analyze', 'Synthesize', 'Conclude', 'End'];
    const currentIndex = states.indexOf(taskState);
    let newIndex;

    if (direction === 'forward') {
      newIndex = (currentIndex + 1) % states.length;
    } else {
      newIndex = (currentIndex - 1 + states.length) % states.length;
    }

    setTaskState(states[newIndex]);

    // Set placeholder data based on the new state
    switch (states[newIndex]) {
      case 'Clarify':
        setClarifyingQuestions(placeholderData.clarifyingQuestions);
        break;
      case 'Research':
        setResearchPapers(placeholderData.researchPapers);
        break;
      case 'Analyze':
        setResponse(placeholderData.analysisResponse);
        break;
      case 'Synthesize':
        setResponse(placeholderData.synthesisResponse);
        break;
      case 'Conclude':
        setResponse(placeholderData.conclusionResponse);
        break;
      default:
        setResponse('');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 1 }}
      className="w-4/5 mx-auto flex flex-col items-center justify-center min-h-screen"
    >
      <div>
        <Typography variant="h1" className="text-3xl mb-4">
          Agentic AI Dietician
        </Typography>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
        className="w-full mx-auto p-8 bg-white text-black"
      >
        <StepIndicator currentState={taskState} />

        {taskState === 'Start' && (
          <div className="mb-6">
            <Input
              type="text"
              id="taskDescription"
              value={taskDescription}
              onChange={e => setTaskDescription(e.target.value)}
              placeholder="e.g., Benefits of Omega-3 Fatty Acids"
              className="w-full p-3 bg-white border-2 border-black rounded-md"
            />
          </div>
        )}

        {taskState === 'Clarify' && (
          <div className="mb-6">
            <Typography variant="h2">Clarifying Questions:</Typography>
            {clarifyingQuestions.map((question, index) => (
              <div key={index} className="mb-4">
                <Label className="block mb-2">{question}</Label>
                <input
                  type="text"
                  value={clarifyAnswers[index]?.answer || ''}
                  onChange={(e) => handleClarifyAnswer(index, e.target.value)}
                  className="border p-2 w-full"
                />
              </div>
            ))}
          </div>
        )}

        {taskState !== 'End' && (
          <Button
            onClick={handleTask}
            disabled={isLoading || (taskState === 'Research' && selectedPapers.length === 0)}
            variant="primary"
            className="w-1/2 text-center m"
          >
            {isLoading ? (
              <div className="flex items-center">
                <Spinner size="md" /> Thinking...
              </div>
            ) : taskState === 'Start' ? (
              'Start Research'
            ) : taskState === 'Clarify' && clarifyAnswers.some(ans => ans.answer === '') ? (
              'Get Clarifying Questions'
            ) : taskState === 'Clarify' ? (
              'Submit Answers'
            ) : taskState === 'Research' ? (
              'Proceed with Selected Papers'
            ) : (
              'Next Step'
            )}
          </Button>
        )}

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="mt-8"
        >
          <Typography variant="h2" className="text-indigo-600">Response</Typography>
          {/* Render the response as HTML to support bullet points and links */}
          <div
            className="prose text-xs"
            dangerouslySetInnerHTML={{ __html: response.replace(/\n/g, '<br>') }}
          />

          {isLoading && (
            <div className="mt-6">
              <Skeleton height={30} width={`80%`} />
              <Skeleton count={3} />
            </div>
          )}

          {currentSteps.length > 0 && (
            <div className="mt-6">
              <Typography variant="h3">Current Processing Steps:</Typography>
              <List>
                {currentSteps.map((step, index) => (
                  <ListItem key={index} className="p-4 pl-6 bg-gray-200 rounded">
                    {step}
                  </ListItem>
                ))}
              </List>
            </div>
          )}

          {/* Show paper selection only during Research state */}
          {taskState === 'Research' && researchPapers.length > 0 && (
            <div className="mt-6">
              <Typography variant="h3">Select Research Papers</Typography>
              <List className="paperList">
                {researchPapers.map((paper, index) => (
                  <ListItem key={index} className="paperItem">
                    <label className="flex items-start">
                      <input
                        type="checkbox"
                        className="paperCheckbox"
                        checked={selectedPapers.includes(paper.link)}
                        onChange={() => handleSelectPaper(paper.link)}
                      />
                      <div className="ml-2">
                        <a
                          href={paper.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-indigo-600 font-bold"
                        >
                          {paper.title}
                        </a>
                        <div className="text-xs">
                          {paper.authors && paper.authors.length > 0
                            ? `By ${paper.authors.map(author => author.name).join(', ')}`
                            : 'Authors not available'}
                          <br />
                          Published: {paper.published_date || 'Date not available'}
                        </div>
                      </div>
                    </label>
                  </ListItem>
                ))}
              </List>
            </div>
          )}

          {/* Display selected papers in other states */}
          {taskState !== 'Research' && selectedPapers.length > 0 && (
            <div className="mt-6">
              <Typography variant="h3">Selected Research Papers:</Typography>
              <List className="paperList">
                {researchPapers
                  .filter(paper => selectedPapers.includes(paper.link))
                  .map((paper, index) => (
                    <ListItem key={index} className="paperItem">
                      <a
                        href={paper.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-indigo-600 font-bold"
                      >
                        {paper.title}
                      </a>
                      <div className="text-xs">
                        {paper.authors && paper.authors.length > 0
                          ? `By ${paper.authors.map(author => author.name).join(', ')}`
                          : 'Authors not available'}
                        <br />
                        Published: {paper.published_date || 'Date not available'}
                      </div>
                    </ListItem>
                  ))}
              </List>
            </div>
          )}
        </motion.div>

        {toast && (
          <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
        )}

        {/* Development mode toggle and navigation buttons */}
        {/* {process.env.NODE_ENV === 'development' && (
          <div className="mt-4 p-4 bg-gray-100 rounded-lg">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={isDevMode}
                onChange={(e) => setIsDevMode(e.target.checked)}
                className="form-checkbox"
              />
              <span>Development Mode</span>
            </label>
            {isDevMode && (
              <div className="mt-2 flex justify-center space-x-4">
                <button
                  onClick={() => cycleState('backward')}
                  className="px-4 py-2 bg-gray-300 rounded"
                >
                  Previous State
                </button>
                <button
                  onClick={() => cycleState('forward')}
                  className="px-4 py-2 bg-gray-300 rounded"
                >
                  Next State
                </button>
              </div>
            )}
          </div>
        )} */}
      </motion.div>
    </motion.div>
  );
}