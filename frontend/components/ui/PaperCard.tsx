import React from "react";
import { Paper } from "@/types/research";
import { EvidenceToggle } from "./EvidenceToggle";
import Typography from "./Typography";
import { Badge } from "./Badge";

interface PaperCardProps {
	paper: Paper;
	renderAccessibility?: (paper: Paper) => React.ReactNode;
}

export const PaperCard: React.FC<PaperCardProps> = ({
	paper,
	renderAccessibility,
}) => {
	return (
		<div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
			<div className="flex justify-between items-start mb-4">
				<div className="flex flex-col">
					<a
						href={paper.full_text_link || paper.link}
						target="_blank"
						rel="noopener noreferrer"
						className="text-md text-indigo-600 font-semibold hover:text-indigo-800"
					>
						{paper.title}
					</a>
					<div className="mt-2 flex space-x-2">
						{renderAccessibility && renderAccessibility(paper)}
					</div>
				</div>
				<div className="flex space-x-2">
					{paper.relevancy_score !== undefined && (
						<Badge variant="success" size="sm">
							Relevancy: {Math.round(paper.relevancy_score)}%
						</Badge>
					)}
					{paper.citation_score !== undefined && (
						<Badge variant="info" size="sm">
							Scientific Merit: {Math.round(paper.citation_score)}%
						</Badge>
					)}
				</div>
			</div>

			{paper.source_type === "requires_access" && (
				<div className="bg-yellow-50 p-4 rounded-lg mb-4">
					<p className="text-yellow-800">
						This paper requires institutional access. Analysis is based on the
						abstract only.
					</p>
				</div>
			)}

			<div className="grid gap-4">
				<div className="bg-gray-50 p-4 rounded-lg">
					<h4 className="text-md font-semibold text-green-800 mb-2">
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
				<div className="bg-gray-50 p-4 rounded-lg">
					<h4 className="text-md font-semibold text-red-800 mb-2">
						Opposing Evidence
					</h4>
					<div className="text-sm space-y-2">
						{paper.opposing_evidence && paper.opposing_evidence.length > 0 ? (
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
				<h4 className="font-semibold text-gray-800 mb-2">Key Findings</h4>
				<p className="text-sm text-gray-700 whitespace-pre-line">
					{paper.key_findings || "No key findings available."}
				</p>
			</div>
		</div>
	);
};
