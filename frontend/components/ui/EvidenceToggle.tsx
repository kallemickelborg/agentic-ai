import React, { useState } from "react";
import { EvidencePoint } from "@/types/research";

export const EvidenceToggle: React.FC<EvidencePoint> = ({
	title,
	evidence,
}) => {
	const [isOpen, setIsOpen] = useState(false);

	return (
		<div className="border border-gray-200 rounded-lg mb-2">
			<button
				onClick={() => setIsOpen(!isOpen)}
				className="w-full px-4 py-2 text-left flex justify-between items-center hover:bg-gray-50 rounded-lg focus:outline-none"
			>
				<span className="font-medium">{title}</span>
				<span
					className={`transform transition-transform ${
						isOpen ? "rotate-180" : ""
					}`}
				>
					▼
				</span>
			</button>
			{isOpen && (
				<div className="px-4 py-2 border-t border-gray-200">
					<p className="text-sm text-gray-700 whitespace-pre-line">
						{evidence}
					</p>
				</div>
			)}
		</div>
	);
};
