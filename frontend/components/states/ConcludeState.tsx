import React from "react";
import Typography from "@/components/ui/Typography";

interface ConcludeStateProps {
	response: string;
}

export const ConcludeState: React.FC<ConcludeStateProps> = ({ response }) => {
	return (
		<div className="mb-6">
			<Typography variant="h2" className="mb-4 text-indigo-600">
				Research Conclusion
			</Typography>
			<div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
				<p className="text-gray-700 whitespace-pre-line">{response}</p>
			</div>
		</div>
	);
};
