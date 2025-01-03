import { useState } from "react";
import { TASK_STATES, TaskState } from "@/constants/states";
import { ProcessingStatus, Paper, Task, PaperAnalysis } from "@/types/research";
import axios from "axios";

interface UseTaskStateProps {
	onError: (message: string) => void;
}

export const useTaskState = ({ onError }: UseTaskStateProps) => {
	const [taskState, setTaskState] = useState<TaskState>(TASK_STATES.START);
	const [taskDescription, setTaskDescription] = useState("");
	const [response, setResponse] = useState("");
	const [researchPapers, setResearchPapers] = useState<Paper[]>([]);
	const [selectedPapers, setSelectedPapers] = useState<string[]>([]);
	const [isLoading, setIsLoading] = useState(false);
	const [currentSteps, setCurrentSteps] = useState<string[]>([]);
	const [clarifyingQuestions, setClarifyingQuestions] = useState<string[]>([]);
	const [clarifyAnswers, setClarifyAnswers] = useState<
		Array<{ question: string; answer: string }>
	>([]);
	const [noResultsFound, setNoResultsFound] = useState(false);
	const [processingStatus, setProcessingStatus] = useState<ProcessingStatus>({
		totalPapers: 0,
		processedPapers: 0,
		currentPaper: null,
	});
	const [originalQuery, setOriginalQuery] = useState<string>("");
	const [enhancedQuery, setEnhancedQuery] = useState<string>("");
	const [stateHistory, setStateHistory] = useState<TaskState[]>([]);

	const handleClarifyAnswer = (index: number, answer: string) => {
		setClarifyAnswers((prev) => {
			const newAnswers = [...prev];
			newAnswers[index] = { ...newAnswers[index], answer };
			return newAnswers;
		});
	};

	const handleSelectPaper = (link: string) => {
		setSelectedPapers((prev) =>
			prev.includes(link) ? prev.filter((l) => l !== link) : [...prev, link]
		);
	};

	const handleRestart = () => {
		setTaskDescription("");
		setTaskState(TASK_STATES.START);
		setNoResultsFound(false);
		setClarifyingQuestions([]);
		setClarifyAnswers([]);
		setResearchPapers([]);
		setSelectedPapers([]);
		setResponse("");
		setStateHistory([]);
	};

	const determineNextState = (): TaskState => {
		switch (taskState) {
			case TASK_STATES.START:
				return TASK_STATES.CLARIFY;
			case TASK_STATES.CLARIFY:
				return clarifyAnswers.every((ans) => ans.answer !== "")
					? TASK_STATES.RESEARCH
					: TASK_STATES.CLARIFY;
			case TASK_STATES.RESEARCH:
				return selectedPapers.length > 0
					? TASK_STATES.ANALYZE
					: TASK_STATES.RESEARCH;
			case TASK_STATES.ANALYZE:
				return TASK_STATES.CONCLUDE;
			case TASK_STATES.CONCLUDE:
				return TASK_STATES.START;
			default:
				return TASK_STATES.START;
		}
	};

	const handleStateTransition = async (direction: "forward" | "backward") => {
		if (direction === "backward") {
			const previousState = stateHistory[stateHistory.length - 1];
			if (previousState) {
				setTaskState(previousState);
				setStateHistory((prev) => prev.slice(0, -1));
			}
			return;
		}

		await progressState();
	};

	const progressState = async () => {
		if (taskState === TASK_STATES.START && taskDescription.trim() === "") {
			onError("Please enter a research topic.");
			return;
		}

		setIsLoading(true);
		const nextState = determineNextState();

		try {
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

			if (
				nextState === TASK_STATES.RESEARCH &&
				taskState === TASK_STATES.CLARIFY
			) {
				await handleStreamingResponse(payload);
			} else {
				await handleRegularResponse(payload);
			}

			setStateHistory((prev) => [...prev, taskState]);
			setTaskState(nextState);
		} catch (error: any) {
			console.error("Error during task processing:", error);
			onError("An error occurred while processing your request.");
		} finally {
			setIsLoading(false);
		}
	};

	const handleStreamingResponse = async (payload: Task) => {
		const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;
		const response = await fetch(`${API_BASE_URL}/solve-task/`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(payload),
		});

		const reader = response.body?.getReader();
		if (!reader) throw new Error("No reader available");

		while (true) {
			const { done, value } = await reader.read();
			if (done) break;

			const chunk = new TextDecoder().decode(value);
			const lines = chunk.split("\n");

			for (const line of lines) {
				if (line.startsWith("data: ")) {
					const data = JSON.parse(line.slice(6));
					handleStreamingData(data);
				}
			}
		}
	};

	const handleStreamingData = (data: any) => {
		if (data.total_papers) {
			setProcessingStatus((prev) => ({
				...prev,
				totalPapers: data.total_papers,
				processedPapers: data.processed_papers,
				currentPaper: data.current_paper,
			}));
		}

		if (data.research_papers) {
			setResearchPapers(data.research_papers);
			if (data.original_query) setOriginalQuery(data.original_query);
			if (data.enhanced_query) setEnhancedQuery(data.enhanced_query);
		}
	};

	const handleRegularResponse = async (payload: Task) => {
		const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;
		const result = await axios.post(`${API_BASE_URL}/solve-task/`, payload, {
			headers: { "Content-Type": "application/json" },
			withCredentials: true,
		});

		console.log("Regular response:", result.data);

		if (result.data.state === "Error") {
			throw new Error(result.data.error_message);
		}

		// Handle clarifying questions
		if (result.data.questions) {
			const questions = result.data.questions;
			setClarifyingQuestions(questions);
			setClarifyAnswers(
				questions.map((q: string) => ({
					question: q,
					answer: "",
				}))
			);
		}

		// Handle paper analysis results
		if (result.data.paper_analyses) {
			console.log("Received paper analyses:", result.data.paper_analyses);
			const updatedPapers = researchPapers.map((paper) => {
				const analysis = result.data.paper_analyses.find(
					(a: PaperAnalysis) => a.title === paper.title
				);
				if (analysis) {
					return {
						...paper,
						supporting_evidence: analysis.supporting_evidence || [],
						opposing_evidence: analysis.opposing_evidence || [],
						key_findings: analysis.key_findings || "No key findings available.",
					};
				}
				return paper;
			});
			console.log("Updated papers with analysis:", updatedPapers);
			setResearchPapers(updatedPapers);
		}

		setResponse(result.data.response || "");

		if (result.data.current_steps) {
			setCurrentSteps(result.data.current_steps);
		}

		if (result.data.restart) {
			setNoResultsFound(true);
			handleRestart();
		}
	};

	return {
		taskState,
		taskDescription,
		setTaskDescription,
		response,
		researchPapers,
		selectedPapers,
		isLoading,
		currentSteps,
		clarifyingQuestions,
		clarifyAnswers,
		noResultsFound,
		processingStatus,
		originalQuery,
		enhancedQuery,
		stateHistory,
		handleClarifyAnswer,
		handleSelectPaper,
		handleRestart,
		handleStateTransition,
		progressState,
	};
};
