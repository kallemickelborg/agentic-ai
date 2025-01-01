"use client";

import React, { useState, useEffect } from "react";
import axios from "axios";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Label from "@/components/ui/Label";
import Spinner from "@/components/ui/Spinner";
import Typography from "@/components/ui/Typography";
import List from "@/components/ui/List";
import ListItem from "@/components/ui/ListItem";
import { motion } from "framer-motion";
import Skeleton from "react-loading-skeleton";
import "react-loading-skeleton/dist/skeleton.css";
import StepIndicator from "./ui/StepIndicator";
import Toast from "./ui/ToastNotifications";
import { StateTooltip } from "./StateTooltip";

interface Author {
	name: string;
}

type TaskState = (typeof TASK_STATES)[keyof typeof TASK_STATES];

interface EvidencePoint {
	title: string;
	evidence: string;
}

interface Paper {
	title: string;
	link: string;
	authors: Author[];
	published_date: string;
	relevancy_score?: number;
	citation_score?: number;
	supporting_evidence?: EvidencePoint[];
	opposing_evidence?: EvidencePoint[];
	key_findings?: string;
	full_text_accessible: boolean;
	full_text_link?: string;
	source_type: "abstract_only" | "open_access" | "requires_access";
}

interface PaperAnalysis {
	title: string;
	link: string;
	supporting_evidence: string;
	opposing_evidence: string;
	key_findings: string;
}

interface Task {
	state: string;
	input_data: {
		selected_papers?: string[];
		clarify_answers?: { question: string; answer: string }[];
	};
	task_description: string;
	research_papers: Paper[];
	original_query?: string;
	enhanced_query?: string;
	paper_analyses?: PaperAnalysis[];
}

interface ClarifyAnswer {
	question: string;
	answer: string;
}

interface Question {
	question: string;
}

interface ProcessingStatus {
	totalPapers: number;
	processedPapers: number;
	currentPaper: {
		title: string;
		relevancy_score: number;
		citation_score: number;
	} | null;
}

const TASK_STATES = {
	START: "Start",
	CLARIFY: "Clarify",
	RESEARCH: "Research",
	ANALYZE: "Analyze",
	CONCLUDE: "Conclude",
} as const;

const placeholderData = {
	clarifyingQuestions: [
		"Are you interested in benefits related to bone health?",
		"Are you seeking information about the role of Vitamin D3 in immune function?",
		"Are you looking for benefits of Vitamin D3 for specific age groups or conditions?",
	],
	researchPapers: [
		{
			title: "Vitamin D3 and Bone Health",
			link: "https://example.com/paper1",
			authors: [{ name: "John Doe" }],
			published_date: "2023-01-01",
			full_text_accessible: true,
			source_type: "open_access" as const,
		},
		{
			title: "Immune Function and Vitamin D3",
			link: "https://example.com/paper2",
			authors: [{ name: "Jane Smith" }],
			published_date: "2023-02-15",
			full_text_accessible: true,
			source_type: "open_access" as const,
		},
		{
			title: "Vitamin D3 Benefits Across Age Groups",
			link: "https://example.com/paper3",
			authors: [{ name: "Alice Johnson" }],
			published_date: "2023-03-30",
			full_text_accessible: true,
			source_type: "open_access" as const,
		},
	],
	analysisResponse:
		"Analysis of the selected papers shows strong evidence for the benefits of Vitamin D3 in bone health...",
	conclusionResponse:
		"In conclusion, Vitamin D3 offers significant benefits, particularly in bone health. However, more research is needed to...",
};

function isValidPaper(
	paper: any
): paper is { title: string; relevancy_score: number; citation_score: number } {
	return (
		paper &&
		typeof paper.title === "string" &&
		typeof paper.relevancy_score === "number" &&
		typeof paper.citation_score === "number"
	);
}

const EvidenceToggle = ({ title, evidence }: EvidencePoint) => {
	const [isOpen, setIsOpen] = useState(false);

	return (
		<div className="border border-gray-200 rounded-lg mb-2">
			<button
				onClick={() => setIsOpen(!isOpen)}
				className="w-full px-4 py-2 text-left flex justify-between items-center hover:bg-gray-50 rounded-lg focus:outline-none"
			>
				<span className="font-medium">{title}</span>
				<span
					className={`transform transition-transform ${
						isOpen ? "rotate-180" : ""
					}`}
				>
					▼
				</span>
			</button>
			{isOpen && (
				<div className="px-4 py-2 border-t border-gray-200">
					<p className="text-sm text-gray-700 whitespace-pre-line">
						{evidence}
					</p>
				</div>
			)}
		</div>
	);
};

// Helper function to safely parse evidence
const parseEvidence = (evidence: any): EvidencePoint[] => {
	console.log("Parsing evidence:", evidence); // Debug log

	// If it's already an array of evidence points
	if (Array.isArray(evidence)) {
		console.log("Evidence is an array:", evidence); // Debug log
		return evidence.map((point) => {
			if (typeof point === "object" && point !== null) {
				return {
					title: point.title || "Untitled Evidence",
					evidence: point.evidence || "No details provided",
				};
			}
			return {
				title: "Untitled Evidence",
				evidence: String(point),
			};
		});
	}

	// If it's a string, try to parse it as JSON
	if (typeof evidence === "string") {
		try {
			const parsed = JSON.parse(evidence);
			console.log("Parsed JSON evidence:", parsed); // Debug log
			if (Array.isArray(parsed)) {
				return parsed.map((point) => ({
					title: point.title || "Untitled Evidence",
					evidence: point.evidence || "No details provided",
				}));
			}
			// If it's a single object
			if (typeof parsed === "object" && parsed !== null) {
				return [
					{
						title: parsed.title || "Untitled Evidence",
						evidence: parsed.evidence || "No details provided",
					},
				];
			}
		} catch (e) {
			console.error("Failed to parse evidence string:", e);
			// If it's a plain string, treat it as a single evidence point
			return [
				{
					title: "Evidence Point",
					evidence: evidence,
				},
			];
		}
	}

	console.log("Returning empty evidence array"); // Debug log
	return [];
};

export default function TaskSolver() {
	const [taskState, setTaskState] = useState<TaskState>(TASK_STATES.START);
	const [taskDescription, setTaskDescription] = useState("");
	const [response, setResponse] = useState("");
	const [researchPapers, setResearchPapers] = useState<Paper[]>([]);
	const [selectedPapers, setSelectedPapers] = useState<string[]>([]);
	const [isLoading, setIsLoading] = useState(false);
	const [currentSteps, setCurrentSteps] = useState<string[]>([]);
	const [toast, setToast] = useState<{
		message: string;
		type: "success" | "error";
	} | null>(null);
	const [clarifyingQuestions, setClarifyingQuestions] = useState<string[]>([]);
	const [clarifyAnswers, setClarifyAnswers] = useState<ClarifyAnswer[]>([]);
	const [isDevMode, setIsDevMode] = useState(false);
	const [noResultsFound, setNoResultsFound] = useState(false);
	const [processingStatus, setProcessingStatus] = useState<ProcessingStatus>({
		totalPapers: 0,
		processedPapers: 0,
		currentPaper: null,
	});
	const [originalQuery, setOriginalQuery] = useState<string>("");
	const [enhancedQuery, setEnhancedQuery] = useState<string>("");

	const handleSelectPaper = (link: string) => {
		setSelectedPapers((prev) =>
			prev.includes(link) ? prev.filter((l) => l !== link) : [...prev, link]
		);
	};

	const handleClarifyAnswer = (index: number, answer: string) => {
		setClarifyAnswers((prev) => {
			const newAnswers = [...prev];
			newAnswers[index] = { ...newAnswers[index], answer };
			return newAnswers;
		});
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
	};

	const calculateProgress = () => {
		if (processingStatus.totalPapers === 0) return 0;
		return (
			(processingStatus.processedPapers / processingStatus.totalPapers) * 100
		);
	};

	const cycleState = (direction: "forward" | "backward") => {
		const states = Object.values(TASK_STATES);
		const currentIndex = states.indexOf(taskState);
		let newIndex;

		if (direction === "forward") {
			newIndex = (currentIndex + 1) % states.length;
		} else {
			newIndex = (currentIndex - 1 + states.length) % states.length;
		}

		setTaskState(states[newIndex]);

		switch (states[newIndex]) {
			case TASK_STATES.CLARIFY:
				setClarifyingQuestions(placeholderData.clarifyingQuestions);
				break;
			case TASK_STATES.RESEARCH:
				setResearchPapers(placeholderData.researchPapers);
				break;
			case TASK_STATES.ANALYZE:
				setResponse(placeholderData.analysisResponse);
				break;
			case TASK_STATES.CONCLUDE:
				setResponse(placeholderData.conclusionResponse);
				break;
			default:
				setResponse("");
		}
	};

	const handleTask = async () => {
		if (taskState === TASK_STATES.START && taskDescription.trim() === "") {
			alert("Please enter a research topic.");
			return;
		}

		setIsLoading(true);
		setResponse("");
		setCurrentSteps([]);
		setNoResultsFound(false);
		setProcessingStatus({
			totalPapers: 0,
			processedPapers: 0,
			currentPaper: null,
		});

		try {
			let nextState = taskState;
			if (taskState === TASK_STATES.START) {
				nextState = TASK_STATES.CLARIFY;
			} else if (taskState === TASK_STATES.CLARIFY) {
				if (clarifyAnswers.every((ans) => ans.answer !== "")) {
					nextState = TASK_STATES.RESEARCH;
				}
			} else if (
				taskState === TASK_STATES.RESEARCH &&
				selectedPapers.length > 0
			) {
				nextState = TASK_STATES.ANALYZE;
			} else if (taskState === TASK_STATES.ANALYZE) {
				nextState = TASK_STATES.CONCLUDE;
			} else if (taskState === TASK_STATES.CONCLUDE) {
				nextState = TASK_STATES.START;
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

			console.log("Sending payload with state:", nextState);
			const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

			if (
				nextState === TASK_STATES.RESEARCH &&
				taskState === TASK_STATES.CLARIFY
			) {
				const response = await fetch(`${API_BASE_URL}/solve-task/`, {
					method: "POST",
					headers: {
						"Content-Type": "application/json",
					},
					body: JSON.stringify(payload),
				});

				const reader = response.body?.getReader();
				if (!reader) {
					throw new Error("No reader available");
				}

				while (true) {
					const { done, value } = await reader.read();
					if (done) break;

					const chunk = new TextDecoder().decode(value);
					const lines = chunk.split("\n");

					for (const line of lines) {
						if (line.startsWith("data: ")) {
							const data = JSON.parse(line.slice(6));
							console.log("Received update:", data);

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
								setTaskState(TASK_STATES.RESEARCH);
								if (data.original_query) setOriginalQuery(data.original_query);
								if (data.enhanced_query) setEnhancedQuery(data.enhanced_query);
							}
						}
					}
				}
			} else {
				const result = await axios.post(
					`${API_BASE_URL}/solve-task/`,
					payload,
					{
						headers: {
							"Content-Type": "application/json",
						},
						withCredentials: true,
					}
				);

				console.log("Server Response:", result.data);

				if (result.data.state === "Error") {
					setToast({ message: result.data.error_message, type: "error" });
					setIsLoading(false);
					return;
				}

				// Handle paper analyses
				if (result.data.paper_analyses) {
					// Update research papers with analysis results
					const updatedPapers = researchPapers.map((paper) => {
						const analysis = result.data.paper_analyses.find(
							(a: PaperAnalysis) => a.title === paper.title
						);
						if (analysis) {
							// Log the raw analysis data for debugging
							console.log(
								"Raw analysis data for paper:",
								paper.title,
								analysis
							);

							// Parse the evidence strings if they're JSON strings
							let supporting_evidence = [];
							let opposing_evidence = [];

							try {
								supporting_evidence =
									typeof analysis.supporting_evidence === "string"
										? JSON.parse(analysis.supporting_evidence)
										: analysis.supporting_evidence;
							} catch (e) {
								console.error("Error parsing supporting evidence:", e);
							}

							try {
								opposing_evidence =
									typeof analysis.opposing_evidence === "string"
										? JSON.parse(analysis.opposing_evidence)
										: analysis.opposing_evidence;
							} catch (e) {
								console.error("Error parsing opposing evidence:", e);
							}

							// Log the parsed evidence
							console.log("Parsed evidence for paper:", paper.title, {
								supporting_evidence,
								opposing_evidence,
							});

							return {
								...paper,
								supporting_evidence: supporting_evidence,
								opposing_evidence: opposing_evidence,
								key_findings:
									analysis.key_findings || "No key findings available.",
							};
						}
						return paper;
					});

					// Log the final updated papers
					console.log("Updated papers with analysis:", updatedPapers);

					setResearchPapers(updatedPapers);
				}

				setTaskState(result.data.state || nextState);
				setResponse(result.data.response || "");

				if (result.data.current_steps) {
					setCurrentSteps(result.data.current_steps);
				}

				if (result.data.questions) {
					setClarifyingQuestions(result.data.questions as string[]);
					setClarifyAnswers(
						(result.data.questions as string[]).map((q: string) => ({
							question: q,
							answer: "",
						}))
					);
				}

				if (result.data.restart) {
					setNoResultsFound(true);
					setTaskState(TASK_STATES.START);
					setClarifyingQuestions([]);
					setClarifyAnswers([]);
				}
			}

			setIsLoading(false);
		} catch (error: any) {
			console.error("Error during task processing:", error);
			setResponse("An error occurred while processing your request.");
			setToast({
				message: "An error occurred while processing your request.",
				type: "error",
			});
			setIsLoading(false);
		}
	};

	useEffect(() => {
		if (taskState === TASK_STATES.RESEARCH && researchPapers.length === 0) {
			console.log("Triggering research papers fetch...");
			handleTask();
		}
	}, [taskState]);

	useEffect(() => {
		console.log("Current state:", taskState);
		console.log("Research papers:", researchPapers);
		console.log("Selected papers:", selectedPapers);
	}, [taskState, researchPapers, selectedPapers]);

	const renderStartState = () => (
		<div className="mb-6">
			<Input
				type="text"
				id="taskDescription"
				value={taskDescription}
				onChange={(e) => setTaskDescription(e.target.value)}
				placeholder="e.g., Benefits of Omega-3 Fatty Acids"
				className="w-full p-3 bg-white border-2 border-black rounded-md"
			/>
		</div>
	);

	const renderClarifyState = () => (
		<div className="mb-6">
			<Typography variant="h2" className="mb-2 text-indigo-600">
				Clarifying Questions
			</Typography>
			{clarifyAnswers.map((qa, index) => (
				<div key={index} className="mb-4">
					<Label className="block mb-2">{qa.question}</Label>
					<div className="flex space-x-4">
						<Button
							onClick={() => handleClarifyAnswer(index, "Yes")}
							variant={qa.answer === "Yes" ? "primary" : "secondary"}
							className="w-1/2"
						>
							Yes
						</Button>
						<Button
							onClick={() => handleClarifyAnswer(index, "No")}
							variant={qa.answer === "No" ? "primary" : "secondary"}
							className="w-1/2"
						>
							No
						</Button>
					</div>
				</div>
			))}

			{processingStatus.totalPapers > 0 && (
				<div className="mt-6 bg-gray-50 p-4 rounded-lg">
					<div className="flex justify-between items-center mb-2">
						<Typography variant="h3" className="text-indigo-600">
							Processing Papers
						</Typography>
						<span className="text-sm text-gray-600">
							{processingStatus.processedPapers} of{" "}
							{processingStatus.totalPapers}
						</span>
					</div>

					<div className="w-full bg-gray-200 rounded-full h-2.5 my-4">
						<motion.div
							className="bg-indigo-600 h-2.5 rounded-full"
							initial={{ width: "0%" }}
							animate={{ width: `${calculateProgress()}%` }}
							transition={{ duration: 0.5 }}
						/>
					</div>

					{processingStatus.currentPaper &&
						isValidPaper(processingStatus.currentPaper) && (
							<div className="text-sm bg-white p-3 rounded-md shadow-sm">
								<div className="font-medium text-gray-800">
									{processingStatus.currentPaper.title}
								</div>
								<div className="flex space-x-4 mt-2">
									<span className="text-xs font-medium px-2 py-1 bg-green-100 text-green-800 rounded">
										Relevancy:{" "}
										{Math.round(processingStatus.currentPaper.relevancy_score)}%
									</span>
									<span className="text-xs font-medium px-2 py-1 bg-blue-100 text-blue-800 rounded">
										Scientific Merit:{" "}
										{Math.round(processingStatus.currentPaper.citation_score)}%
									</span>
								</div>
							</div>
						)}
				</div>
			)}
		</div>
	);

	const renderResearchState = () => (
		<>
			{noResultsFound ? (
				<div className="mt-4 text-center">
					<Typography variant="h3" className="mb-2 text-red-600">
						No research papers found...
					</Typography>
					<Typography variant="p" className="mb-4">
						Do you want to start over?
					</Typography>
					<Button onClick={handleRestart} variant="primary">
						Restart
					</Button>
				</div>
			) : (
				<div className="mt-6 mb-4">
					<div className="bg-gray-50 p-4 rounded-lg mb-4">
						<Typography variant="h3" className="text-indigo-600 mb-2">
							Research Query Information
						</Typography>
						<div className="space-y-2">
							<div>
								<span className="font-medium">Original Query: </span>
								<span className="text-gray-700">{originalQuery}</span>
							</div>
							<div>
								<span className="font-medium">Enhanced Query: </span>
								<span className="text-gray-700">{enhancedQuery}</span>
							</div>
						</div>
					</div>

					<List className="space-y-4">
						{Array.isArray(researchPapers) ? (
							researchPapers.map((paper, index) => (
								<ListItem
									key={index}
									className="p-4 border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow"
								>
									<label className="flex items-start space-x-4 cursor-pointer">
										<input
											type="checkbox"
											className="mt-1 h-4 w-4 text-indigo-600 rounded border-gray-300"
											checked={selectedPapers.includes(paper.link)}
											onChange={() => handleSelectPaper(paper.link)}
										/>
										<div className="flex-1">
											<div className="flex justify-between items-start">
												<a
													href={paper.link}
													target="_blank"
													rel="noopener noreferrer"
													className="text-sm text-indigo-600 font-semibold hover:text-indigo-800"
												>
													{paper.title}
												</a>
												<div className="flex space-x-2">
													{paper.relevancy_score !== undefined && (
														<span className="text-xs font-medium px-2 py-1 bg-green-100 text-green-800 rounded">
															Relevancy: {Math.round(paper.relevancy_score)}%
														</span>
													)}
													{paper.citation_score !== undefined && (
														<span className="text-xs font-medium px-2 py-1 bg-blue-100 text-blue-800 rounded">
															Scientific Merit:{" "}
															{Math.round(paper.citation_score)}%
														</span>
													)}
												</div>
											</div>
											<div className="mt-1 text-xs text-gray-600">
												{paper.authors && paper.authors.length > 0
													? `Authors: ${paper.authors
															.map((author) => author.name)
															.join(", ")}`
													: "Authors not available"}
											</div>
											<div className="text-xs text-gray-500">
												Published:{" "}
												{paper.published_date || "Date not available"}
											</div>
										</div>
									</label>
								</ListItem>
							))
						) : (
							<Typography variant="p" className="text-red-600">
								Error: Research papers data is not in the expected format
							</Typography>
						)}
					</List>
				</div>
			)}
		</>
	);

	const renderPaperAccessibility = (paper: Paper) => {
		switch (paper.source_type) {
			case "open_access":
				return (
					<span className="text-xs font-medium px-2 py-1 bg-green-100 text-green-800 rounded">
						Open Access
					</span>
				);
			case "requires_access":
				return (
					<span className="text-xs font-medium px-2 py-1 bg-yellow-100 text-yellow-800 rounded">
						Requires Institutional Access
					</span>
				);
			default:
				return (
					<span className="text-xs font-medium px-2 py-1 bg-gray-100 text-gray-800 rounded">
						Abstract Only
					</span>
				);
		}
	};

	const renderAnalyzeState = () => (
		<div className="mb-6">
			<div className="bg-gray-50 p-4 rounded-lg mb-4">
				<Typography variant="h3" className="text-indigo-600 mb-2">
					Research Query Information
				</Typography>
				<div className="space-y-2">
					<div>
						<span className="font-medium">Original Query: </span>
						<span className="text-gray-700">{originalQuery}</span>
					</div>
					<div>
						<span className="font-medium">Enhanced Query: </span>
						<span className="text-gray-700">{enhancedQuery}</span>
					</div>
				</div>
			</div>

			{/* Paper Analysis Section */}
			<div className="space-y-6">
				{researchPapers
					.filter((paper) => selectedPapers.includes(paper.link))
					.map((paper, index) => (
						<div
							key={index}
							className="bg-white p-6 rounded-lg shadow-sm border border-gray-200"
						>
							<div className="flex justify-between items-start mb-4">
								<div className="flex flex-col">
									<a
										href={paper.full_text_link || paper.link}
										target="_blank"
										rel="noopener noreferrer"
										className="text-lg text-indigo-600 font-semibold hover:text-indigo-800"
									>
										{paper.title}
									</a>
									<div className="mt-2 flex space-x-2">
										{renderPaperAccessibility(paper)}
									</div>
								</div>
								<div className="flex space-x-2">
									{paper.relevancy_score !== undefined && (
										<span className="text-sm font-medium px-2 py-1 bg-green-100 text-green-800 rounded">
											Relevancy: {Math.round(paper.relevancy_score)}%
										</span>
									)}
									{paper.citation_score !== undefined && (
										<span className="text-sm font-medium px-2 py-1 bg-blue-100 text-blue-800 rounded">
											Scientific Merit: {Math.round(paper.citation_score)}%
										</span>
									)}
								</div>
							</div>

							{paper.source_type === "requires_access" ? (
								<div className="bg-yellow-50 p-4 rounded-lg mb-4">
									<p className="text-yellow-800">
										This paper requires institutional access. Analysis is based
										on the abstract only.
									</p>
								</div>
							) : null}

							<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
								<div className="bg-green-50 p-4 rounded-lg">
									<h4 className="font-semibold text-green-800 mb-2">
										Supporting Evidence
									</h4>
									<div className="space-y-2">
										{paper.supporting_evidence &&
										parseEvidence(paper.supporting_evidence).length > 0 ? (
											parseEvidence(paper.supporting_evidence).map(
												(evidence, idx) => (
													<EvidenceToggle
														key={`${paper.title}-support-${idx}`}
														title={evidence.title}
														evidence={evidence.evidence}
													/>
												)
											)
										) : (
											<p className="text-sm text-gray-700">
												No supporting evidence found.
											</p>
										)}
									</div>
								</div>
								<div className="bg-red-50 p-4 rounded-lg">
									<h4 className="font-semibold text-red-800 mb-2">
										Opposing Evidence
									</h4>
									<div className="space-y-2">
										{paper.opposing_evidence &&
										parseEvidence(paper.opposing_evidence).length > 0 ? (
											parseEvidence(paper.opposing_evidence).map(
												(evidence, idx) => (
													<EvidenceToggle
														key={`${paper.title}-oppose-${idx}`}
														title={evidence.title}
														evidence={evidence.evidence}
													/>
												)
											)
										) : (
											<p className="text-sm text-gray-700">
												No opposing evidence found.
											</p>
										)}
									</div>
								</div>
							</div>

							<div className="mt-4 bg-gray-50 p-4 rounded-lg">
								<h4 className="font-semibold text-gray-800 mb-2">
									Key Findings
								</h4>
								<p className="text-sm text-gray-700 whitespace-pre-line">
									{paper.key_findings || "No key findings available."}
								</p>
							</div>
						</div>
					))}
			</div>
		</div>
	);

	const renderActionButton = () => {
		return (
			<Button
				onClick={handleTask}
				disabled={
					isLoading ||
					(taskState === TASK_STATES.RESEARCH && selectedPapers.length === 0)
				}
				variant="primary"
				className="w-1/2 text-center m"
			>
				{isLoading ? (
					<div className="flex items-center">
						<Spinner size="md" /> Thinking...
					</div>
				) : taskState === TASK_STATES.START ? (
					"Start Research"
				) : taskState === TASK_STATES.CLARIFY &&
				  clarifyAnswers.some((ans) => ans.answer === "") ? (
					"Get Clarifying Questions"
				) : taskState === TASK_STATES.CLARIFY ? (
					"Submit Answers"
				) : taskState === TASK_STATES.RESEARCH ? (
					"Proceed with Selected Papers"
				) : (
					"Next Step"
				)}
			</Button>
		);
	};

	const renderSelectedPapers = () => {
		if (taskState === TASK_STATES.RESEARCH || selectedPapers.length === 0)
			return null;

		return (
			<div className="mt-6">
				<Typography variant="h3" className="text-indigo-600 mb-2">
					Selected Papers ({selectedPapers.length})
				</Typography>
				<List className="space-y-4">
					{researchPapers
						.filter((paper) => selectedPapers.includes(paper.link))
						.map((paper, index) => (
							<ListItem
								key={index}
								className="p-4 border border-gray-200 rounded-lg shadow-sm"
							>
								<a
									href={paper.link}
									target="_blank"
									rel="noopener noreferrer"
									className="text-sm text-indigo-600 font-semibold hover:text-indigo-800"
								>
									{paper.title}
								</a>
								<div className="mt-1 text-xs text-gray-600">
									{paper.authors && paper.authors.length > 0
										? `Authors: ${paper.authors
												.map((author) => author.name)
												.join(", ")}`
										: "Authors not available"}
								</div>
								<div className="text-xs text-gray-500">
									Published: {paper.published_date || "Date not available"}
								</div>
							</ListItem>
						))}
				</List>
			</div>
		);
	};

	return (
		<motion.div
			initial={{ opacity: 0, y: 50 }}
			animate={{ opacity: 1, y: 0 }}
			transition={{ duration: 1 }}
			className="w-4/5 mx-auto flex flex-col items-center justify-center min-h-screen"
		>
			<div className="relative w-full">
				<StateTooltip currentState={taskState} />
				<Typography variant="h1" className="text-3xl mb-4 text-center">
					Stateful AI Agent for Knowledge Extraction in Medical Research
				</Typography>
			</div>

			<motion.div
				initial={{ opacity: 0, y: 50 }}
				animate={{ opacity: 1, y: 0 }}
				transition={{ duration: 1 }}
				className="w-full mx-auto p-8 bg-white text-black"
			>
				<StepIndicator currentState={taskState} />

				{taskState === TASK_STATES.START && renderStartState()}
				{taskState === TASK_STATES.CLARIFY && renderClarifyState()}

				<motion.div
					initial={{ opacity: 0 }}
					animate={{ opacity: 1 }}
					transition={{ delay: 1 }}
					className="mb-8"
				>
					{isLoading && (
						<div className="mt-6 mb-4">
							<Skeleton height={30} width={`80%`} />
							<Skeleton count={3} />
						</div>
					)}

					{taskState === TASK_STATES.RESEARCH && renderResearchState()}
					{taskState === TASK_STATES.ANALYZE && renderAnalyzeState()}

					{renderActionButton()}
					{renderSelectedPapers()}
				</motion.div>

				{toast && (
					<Toast
						message={toast.message}
						type={toast.type}
						onClose={() => setToast(null)}
					/>
				)}
			</motion.div>
		</motion.div>
	);
}
