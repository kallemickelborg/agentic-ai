"use client";

import React from "react";
import { motion } from "framer-motion";
import Skeleton from "react-loading-skeleton";
import "react-loading-skeleton/dist/skeleton.css";

// Components
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";
import Typography from "@/components/ui/Typography";
import StepIndicator from "@/components/ui/StepIndicator";
import Toast from "@/components/ui/ToastNotifications";
import { StateTooltip } from "@/components/ui/StateTooltip";

// State Components
import { StartState } from "./states/StartState";
import { ClarifyState } from "./states/ClarifyState";
import { ResearchState } from "./states/ResearchState";
import { AnalyzeState } from "./states/AnalyzeState";
import { ConcludeState } from "./states/ConcludeState";

// Hooks
import { useTaskState } from "@/hooks/useTaskState";

// Constants
import { TASK_STATES } from "@/constants/states";

export default function TaskHandler() {
	const [toast, setToast] = React.useState<{
		message: string;
		type: "success" | "error";
	} | null>(null);

	const {
		taskState,
		taskDescription,
		setTaskDescription,
		response,
		researchPapers,
		selectedPapers,
		isLoading,
		clarifyAnswers,
		noResultsFound,
		processingStatus,
		originalQuery,
		enhancedQuery,
		handleClarifyAnswer,
		handleSelectPaper,
		handleRestart,
		handleStateTransition,
		progressState,
	} = useTaskState({
		onError: (message) => setToast({ message, type: "error" }),
	});

	const renderActionButton = () => (
		<Button
			onClick={progressState}
			disabled={
				isLoading ||
				(taskState === TASK_STATES.RESEARCH && selectedPapers.length === 0)
			}
			variant="primary"
			className="w-1/3 flex mx-auto items-center justify-center text-center px-4 py-2 border border-transparent text-xs font-medium rounded-md focus:outline-none"
		>
			{isLoading ? (
				<div className="flex mx-auto items-center justify-center text-center px-4 py-2 border border-transparent text-xs font-medium rounded-md focus:outline-none">
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

	const renderBackButton = () => (
		<Button
			onClick={() => handleStateTransition("backward")}
			disabled={isLoading || taskState === TASK_STATES.START}
			variant="secondary"
			className="w-1/3 flex mx-auto items-center justify-center text-center px-4 py-2 border border-transparent text-xs font-medium rounded-md focus:outline-none"
		>
			Previous Step
		</Button>
	);

	const renderCurrentState = () => {
		switch (taskState) {
			case TASK_STATES.START:
				return (
					<StartState
						taskDescription={taskDescription}
						setTaskDescription={setTaskDescription}
					/>
				);
			case TASK_STATES.CLARIFY:
				return (
					<ClarifyState
						clarifyAnswers={clarifyAnswers}
						handleClarifyAnswer={handleClarifyAnswer}
						processingStatus={processingStatus}
					/>
				);
			case TASK_STATES.RESEARCH:
				return (
					<ResearchState
						noResultsFound={noResultsFound}
						handleRestart={handleRestart}
						originalQuery={originalQuery}
						enhancedQuery={enhancedQuery}
						researchPapers={researchPapers}
						selectedPapers={selectedPapers}
						handleSelectPaper={handleSelectPaper}
					/>
				);
			case TASK_STATES.ANALYZE:
				return (
					<AnalyzeState
						originalQuery={originalQuery}
						enhancedQuery={enhancedQuery}
						researchPapers={researchPapers}
						selectedPapers={selectedPapers}
					/>
				);
			case TASK_STATES.CONCLUDE:
				return <ConcludeState response={response} />;
			default:
				return null;
		}
	};

	return (
		<motion.div
			initial={{ opacity: 0, y: 50 }}
			animate={{ opacity: 1, y: 0 }}
			transition={{ duration: 1 }}
			className="w-full mx-auto flex flex-col items-center justify-center min-h-screen"
		>
			<motion.div
				initial={{ opacity: 0, y: 50 }}
				animate={{ opacity: 1, y: 0 }}
				transition={{ duration: 1 }}
				className="w-full mx-auto p-8 bg-white text-black"
			>
				<div className="relative w-full mb-10">
					<Typography variant="h1" className="text-3xl text-center">
						Stateful AI Agent for Knowledge Extraction in Medical Research
					</Typography>
				</div>

				<StateTooltip currentState={taskState} />
				<StepIndicator currentState={taskState} />

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

					{renderCurrentState()}

					<div className="flex justify-between items-center mt-4">
						{renderBackButton()}
						{renderActionButton()}
					</div>
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
