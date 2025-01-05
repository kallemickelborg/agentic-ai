import React from "react";
import { motion } from "framer-motion";
import Button from "@/components/ui/Button";
import Label from "@/components/ui/Label";
import Typography from "@/components/ui/Typography";
import { Badge } from "@/components/ui/Badge";
import { ProcessingStatus } from "@/types/research";
import { classes } from "@/styles/classes";
import { cn } from "@/utils/cn";

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

	return (
		<div className={classes.page.content}>
			{clarifyAnswers && clarifyAnswers.length > 0 ? (
				<div className={classes.page.content}>
					{clarifyAnswers.map((qa, index) => (
						<div key={index} className={classes.item.container}>
							<p className={classes.item.label}>{qa.question}</p>
							<div className={classes.button.container}>
								<Button
									onClick={() => handleClarifyAnswer(index, "Yes")}
									variant={qa.answer === "Yes" ? "primary" : "secondary"}
									className={
										qa.answer === "Yes"
											? classes.button.primary
											: classes.button.secondary
									}
								>
									Yes
								</Button>
								<Button
									onClick={() => handleClarifyAnswer(index, "No")}
									variant={qa.answer === "No" ? "primary" : "secondary"}
									className={
										qa.answer === "No"
											? classes.button.primary
											: classes.button.secondary
									}
								>
									No
								</Button>
							</div>
						</div>
					))}
				</div>
			) : (
				<div className={classes.questions.loading}>Loading questions...</div>
			)}

			{processingStatus.totalPapers > 0 && (
				<div className={classes.paperProcessing.container}>
					<div className={classes.paperProcessing.header.container}>
						<Typography variant="h3" className={classes.text.heading.primary}>
							Processing Papers
						</Typography>
						<span className={classes.paperProcessing.header.counter}>
							{processingStatus.processedPapers} of{" "}
							{processingStatus.totalPapers}
						</span>
					</div>

					<div className={classes.progress.container}>
						<motion.div
							className={classes.progress.bar}
							initial={{ width: "0%" }}
							animate={{ width: `${calculateProgress()}%` }}
							transition={{ duration: 0.5 }}
							style={{ width: `${calculateProgress()}%` }}
						/>
					</div>

					{processingStatus.currentPaper &&
						isValidPaper(processingStatus.currentPaper) && (
							<div className={classes.paperProcessing.paper.container}>
								<div className={classes.paperProcessing.paper.title}>
									{processingStatus.currentPaper.title}
								</div>
								<div className={classes.paperProcessing.paper.badges}>
									<Badge variant="success" size="sm">
										Relevancy:{" "}
										{Math.round(processingStatus.currentPaper.relevancy_score)}%
									</Badge>
									<Badge variant="info" size="sm">
										Scientific Merit:{" "}
										{Math.round(processingStatus.currentPaper.citation_score)}%
									</Badge>
								</div>
							</div>
						)}
				</div>
			)}
		</div>
	);
};
