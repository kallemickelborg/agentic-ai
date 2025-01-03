import React from "react";
import Typography from "@/components/ui/Typography";
import Button from "@/components/ui/Button";
import List from "@/components/ui/List";
import ListItem from "@/components/ui/ListItem";
import { Paper } from "@/types/research";

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
};
