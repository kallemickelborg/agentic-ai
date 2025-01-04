import React from "react";
import Typography from "./Typography";

interface QueryInfoProps {
	originalQuery: string;
	enhancedQuery: string;
}

export const QueryInfo: React.FC<QueryInfoProps> = ({
	originalQuery,
	enhancedQuery,
}) => {
	return (
		<div className="bg-gray-50 p-4 rounded-lg mb-4">
			<Typography variant="h2" className="text-lgtext-indigo-600 mb-2">
				Query Information
			</Typography>
			<div className="space-y-2">
				<div>
					<span className="text-sm">Original Query: </span>
					<span className="text-gray-700">{originalQuery}</span>
				</div>
				<div>
					<span className="text-sm">Enhanced Query: </span>
					<span className="text-gray-700">{enhancedQuery}</span>
				</div>
			</div>
		</div>
	);
};
