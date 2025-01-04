import React from "react";
import Typography from "@/components/ui/Typography";
import Button from "@/components/ui/Button";
import List from "@/components/ui/List";
import { Paper } from "@/types/research";
import { QueryInfo } from "@/components/ui/QueryInfo";
import { PaperListItem } from "@/components/ui/PaperListItem";

interface ResearchStateProps {
	noResultsFound: boolean;
	handleRestart: () => void;
	originalQuery: string;
	enhancedQuery: string;
	researchPapers: Paper[];
	selectedPapers: string[];
	handleSelectPaper: (link: string) => void;
}

export const ResearchState: React.FC<ResearchStateProps> = ({
	noResultsFound,
	handleRestart,
	originalQuery,
	enhancedQuery,
	researchPapers,
	selectedPapers,
	handleSelectPaper,
}) => {
	return (
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
					<QueryInfo
						originalQuery={originalQuery}
						enhancedQuery={enhancedQuery}
					/>

					<List className="space-y-4">
						{Array.isArray(researchPapers) ? (
							researchPapers.map((paper, index) => (
								<PaperListItem
									key={index}
									paper={paper}
									isSelected={selectedPapers.includes(paper.link)}
									onSelect={handleSelectPaper}
								/>
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
};
