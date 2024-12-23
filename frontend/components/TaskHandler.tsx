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

interface Author {
	name: string;
}

interface Paper {
	title: string;
	link: string;
	authors: Author[];
	published_date: string;
	relevancy_score?: number;
	citation_score?: number;
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
		},
		{
			title: "Immune Function and Vitamin D3",
			link: "https://example.com/paper2",
			authors: [{ name: "Jane Smith" }],
			published_date: "2023-02-15",
		},
		{
			title: "Vitamin D3 Benefits Across Age Groups",
			link: "https://example.com/paper3",
			authors: [{ name: "Alice Johnson" }],
			published_date: "2023-03-30",
		},
	],
	analysisResponse:
		"Analysis of the selected papers shows strong evidence for the benefits of Vitamin D3 in bone health...",
	conclusionResponse:
		"In conclusion, Vitamin D3 offers significant benefits, particularly in bone health. However, more research is needed to...",
};

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

export default function TaskSolver() {
	const [taskState, setTaskState] = useState("Start");
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

	const handleTask = async () => {
		if (taskState === "Start" && taskDescription.trim() === "") {
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
			if (taskState === "Start") {
				nextState = "Clarify";
			} else if (taskState === "Clarify") {
				if (clarifyAnswers.every((ans) => ans.answer !== "")) {
					nextState = "Research";
				}
			} else if (taskState === "Research" && selectedPapers.length > 0) {
				nextState = "Analyze";
			} else if (taskState === "Analyze") {
				nextState = "Conclude";
			} else if (taskState === "Conclude") {
				nextState = "End";
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

			if (nextState === "Research" && taskState === "Clarify") {
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
								setTaskState("Research");
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

				setTaskState(nextState);
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
					setTaskState("Start");
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

	const handleRestart = () => {
		setTaskDescription("");
		setTaskState("Start");
		setNoResultsFound(false);
		setClarifyingQuestions([]);
		setClarifyAnswers([]);
		setResearchPapers([]);
		setSelectedPapers([]);
		setResponse("");
	};

	useEffect(() => {
		if (taskState === "Research" && researchPapers.length === 0) {
			console.log("Triggering research papers fetch...");
			handleTask();
		}
	}, [taskState]);

	useEffect(() => {
		console.log("Current state:", taskState);
		console.log("Research papers:", researchPapers);
		console.log("Selected papers:", selectedPapers);
	}, [taskState, researchPapers, selectedPapers]);

	const cycleState = (direction: "forward" | "backward") => {
		const states = [
			"Start",
			"Clarify",
			"Research",
			"Analyze",
			"Conclude",
			"End",
		];
		const currentIndex = states.indexOf(taskState);
		let newIndex;

		if (direction === "forward") {
			newIndex = (currentIndex + 1) % states.length;
		} else {
			newIndex = (currentIndex - 1 + states.length) % states.length;
		}

		setTaskState(states[newIndex]);

		switch (states[newIndex]) {
			case "Clarify":
				setClarifyingQuestions(placeholderData.clarifyingQuestions);
				break;
			case "Research":
				setResearchPapers(placeholderData.researchPapers);
				break;
			case "Analyze":
				setResponse(placeholderData.analysisResponse);
				break;
			case "Conclude":
				setResponse(placeholderData.conclusionResponse);
				break;
			default:
				setResponse("");
		}
	};

	const calculateProgress = () => {
		if (processingStatus.totalPapers === 0) return 0;
		return (
			(processingStatus.processedPapers / processingStatus.totalPapers) * 100
		);
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
					Agentic AI PubMed Research Assistant
				</Typography>
			</div>

			<motion.div
				initial={{ opacity: 0, y: 50 }}
				animate={{ opacity: 1, y: 0 }}
				transition={{ duration: 1 }}
				className="w-full mx-auto p-8 bg-white text-black"
			>
				<StepIndicator currentState={taskState} />

				{taskState === "Start" && (
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
				)}

				{taskState === "Clarify" && (
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

						{/* Paper Processing Status */}
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
													{Math.round(
														processingStatus.currentPaper.relevancy_score
													)}
													%
												</span>
												<span className="text-xs font-medium px-2 py-1 bg-blue-100 text-blue-800 rounded">
													Scientific Merit:{" "}
													{Math.round(
														processingStatus.currentPaper.citation_score
													)}
													%
												</span>
											</div>
										</div>
									)}
							</div>
						)}
					</div>
				)}

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

					{/* Show paper selection during Research state */}
					{taskState === "Research" && (
						<div className="mt-6 mb-4">
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
																	Relevancy: {Math.round(paper.relevancy_score)}
																	%
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

					{taskState !== "End" && (
						<Button
							onClick={handleTask}
							disabled={
								isLoading ||
								(taskState === "Research" && selectedPapers.length === 0)
							}
							variant="primary"
							className="w-1/2 text-center m"
						>
							{isLoading ? (
								<div className="flex items-center">
									<Spinner size="md" /> Thinking...
								</div>
							) : taskState === "Start" ? (
								"Start Research"
							) : taskState === "Clarify" &&
							  clarifyAnswers.some((ans) => ans.answer === "") ? (
								"Get Clarifying Questions"
							) : taskState === "Clarify" ? (
								"Submit Answers"
							) : taskState === "Research" ? (
								"Proceed with Selected Papers"
							) : (
								"Next Step"
							)}
						</Button>
					)}

					{/* Display selected papers in other states */}
					{taskState !== "Research" && selectedPapers.length > 0 && (
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
												Published:{" "}
												{paper.published_date || "Date not available"}
											</div>
										</ListItem>
									))}
							</List>
						</div>
					)}
				</motion.div>

				{toast && (
					<Toast
						message={toast.message}
						type={toast.type}
						onClose={() => setToast(null)}
					/>
				)}

				{taskState === "Research" && (
					<div>
						{noResultsFound && (
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
						)}
					</div>
				)}

				{/* Development mode toggle and navigation buttons */}
				{/* {process.env.NODE_ENV === "development" && (
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
									onClick={() => cycleState("backward")}
									className="px-4 py-2 bg-gray-300 rounded"
								>
									Previous State
								</button>
								<button
									onClick={() => cycleState("forward")}
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
