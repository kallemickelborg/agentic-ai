import React from "react";
import Typography from "@/components/ui/Typography";
import { Paper } from "@/types/research";
import { PaperCard } from "@/components/ui/PaperCard";
import { QueryInfo } from "@/components/ui/QueryInfo";
import { Badge } from "@/components/ui/Badge";

interface AnalyzeStateProps {
	originalQuery: string;
	enhancedQuery: string;
	researchPapers: Paper[];
	selectedPapers: string[];
}

export const AnalyzeState: React.FC<AnalyzeStateProps> = ({
	originalQuery,
	enhancedQuery,
	researchPapers,
	selectedPapers,
}) => {
	const renderPaperAccessibility = (paper: Paper) => {
		switch (paper.source_type) {
			case "open_access":
				return (
					<Badge variant="success" size="sm">
						Open Access
					</Badge>
				);
			case "requires_access":
				return (
					<Badge variant="warning" size="sm">
						Requires Institutional Access
					</Badge>
				);
			default:
				return (
					<Badge variant="default" size="sm">
						Abstract Only
					</Badge>
				);
		}
	};

	const selectedPapersWithAnalysis = researchPapers.filter((paper) =>
		selectedPapers.includes(paper.link)
	);

	return (
		<div className="mb-6">
			<Typography variant="h1" className="text-indigo-600 mb-2">
				Evidence Found in Selected Research Papers
			</Typography>
			<QueryInfo originalQuery={originalQuery} enhancedQuery={enhancedQuery} />

			<div className="space-y-6">
				{selectedPapersWithAnalysis.length > 0 ? (
					selectedPapersWithAnalysis.map((paper, index) => (
						<PaperCard
							key={index}
							paper={paper}
							renderAccessibility={renderPaperAccessibility}
						/>
					))
				) : (
					<div className="text-center p-8 bg-gray-50 rounded-lg">
						<Typography variant="h3" className="text-gray-600 mb-2">
							No Papers Selected
						</Typography>
						<p className="text-gray-500">
							Please select papers in the Research step to view their analysis.
						</p>
					</div>
				)}
			</div>
		</div>
	);
};
