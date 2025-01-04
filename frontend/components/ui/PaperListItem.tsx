import React from "react";
import { Paper } from "@/types/research";
import { Badge } from "./Badge";
import ListItem from "./ListItem";

interface PaperListItemProps {
	paper: Paper;
	isSelected: boolean;
	onSelect: (link: string) => void;
}

export const PaperListItem: React.FC<PaperListItemProps> = ({
	paper,
	isSelected,
	onSelect,
}) => {
	return (
		<ListItem className="p-4 border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
			<label className="flex items-start space-x-4 cursor-pointer">
				<input
					type="checkbox"
					className="mt-1 h-4 w-4 text-indigo-600 rounded border-gray-300"
					checked={isSelected}
					onChange={() => onSelect(paper.link)}
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
				</div>
			</label>
		</ListItem>
	);
};
