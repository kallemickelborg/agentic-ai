import React from "react";
import Typography from "@/components/ui/Typography";
import { Paper } from "@/types/research";
import { EvidenceToggle } from "@/components/ui/EvidenceToggle";

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

	console.log("AnalyzeState - Selected Papers:", selectedPapers);
	console.log("AnalyzeState - Research Papers:", researchPapers);

	const selectedPapersWithAnalysis = researchPapers.filter((paper) =>
		selectedPapers.includes(paper.link)
	);

	console.log(
		"AnalyzeState - Papers with Analysis:",
		selectedPapersWithAnalysis
	);

	return (
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

			<div className="space-y-6">
				{selectedPapersWithAnalysis.length > 0 ? (
					selectedPapersWithAnalysis.map((paper, index) => (
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

							{paper.source_type === "requires_access" && (
								<div className="bg-yellow-50 p-4 rounded-lg mb-4">
									<p className="text-yellow-800">
										This paper requires institutional access. Analysis is based
										on the abstract only.
									</p>
								</div>
							)}

							<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
								<div className="bg-green-50 p-4 rounded-lg">
									<h4 className="font-semibold text-green-800 mb-2">
										Supporting Evidence
									</h4>
									<div className="space-y-2">
										{paper.supporting_evidence &&
										paper.supporting_evidence.length > 0 ? (
											paper.supporting_evidence.map((evidence, idx) => (
												<EvidenceToggle
													key={`${paper.title}-support-${idx}`}
													title={evidence.title}
													evidence={evidence.evidence}
												/>
											))
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
										paper.opposing_evidence.length > 0 ? (
											paper.opposing_evidence.map((evidence, idx) => (
												<EvidenceToggle
													key={`${paper.title}-oppose-${idx}`}
													title={evidence.title}
													evidence={evidence.evidence}
												/>
											))
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
