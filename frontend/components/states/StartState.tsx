import React from "react";
import Input from "@/components/ui/Input";

interface StartStateProps {
	taskDescription: string;
	setTaskDescription: (value: string) => void;
}

export const StartState: React.FC<StartStateProps> = ({
	taskDescription,
	setTaskDescription,
}) => {
	return (
		<div className="mb-6">
			<Input
				type="text"
				id="taskDescription"
				value={taskDescription}
				onChange={(e) => setTaskDescription(e.target.value)}
				placeholder="e.g., Benefits of Omega-3 Fatty Acids"
				className="w-full p-3 bg-white border-2 border-black rounded-md"
			/>
		</div>
	);
};
