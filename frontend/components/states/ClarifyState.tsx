import React from "react";
import { motion } from "framer-motion";
import Button from "@/components/ui/Button";
import Label from "@/components/ui/Label";
import Typography from "@/components/ui/Typography";
import { ProcessingStatus } from "@/types/research";

interface ClarifyStateProps {
	clarifyAnswers: Array<{ question: string; answer: string }>;
	handleClarifyAnswer: (index: number, answer: string) => void;
	processingStatus: ProcessingStatus;
}

export const ClarifyState: React.FC<ClarifyStateProps> = ({
	clarifyAnswers,
	handleClarifyAnswer,
	processingStatus,
}) => {
	const calculateProgress = () => {
		if (processingStatus.totalPapers === 0) return 0;
		return (
			(processingStatus.processedPapers / processingStatus.totalPapers) * 100
		);
	};

	const isValidPaper = (
		paper: any
	): paper is {
		title: string;
		relevancy_score: number;
		citation_score: number;
	} => {
		return (
			paper &&
			typeof paper.title === "string" &&
			typeof paper.relevancy_score === "number" &&
			typeof paper.citation_score === "number"
		);
	};

	console.log("ClarifyState - clarifyAnswers:", clarifyAnswers);

	return (
		<div className="mb-6">
			{/* <Typography variant="h1" className="mb-2 text-indigo-600">
				Clarifying Questions
			</Typography> */}
			{clarifyAnswers && clarifyAnswers.length > 0 ? (
				<div className="space-y-4">
					{clarifyAnswers.map((qa, index) => (
						<div
							key={index}
							className="p-4 bg-gray-50 rounded-lg w-1/2 mx-auto"
						>
							<Label className="block mb-2 text-lg">{qa.question}</Label>
							<div className="flex gap-4">
								<Button
									onClick={() => handleClarifyAnswer(index, "Yes")}
									variant={qa.answer === "Yes" ? "primary" : "secondary"}
									className="w-full"
								>
									Yes
								</Button>
								<Button
									onClick={() => handleClarifyAnswer(index, "No")}
									variant={qa.answer === "No" ? "primary" : "secondary"}
									className="w-full"
								>
									No
								</Button>
							</div>
						</div>
					))}
				</div>
			) : (
				<div className="text-gray-600 p-4 bg-gray-50 rounded-lg">
					Loading questions...
				</div>
			)}

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
};
