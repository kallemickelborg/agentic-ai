import React from "react";
import Input from "@/components/ui/Input";
import { classes } from "@/styles/classes";

interface StartStateProps {
	taskDescription: string;
	setTaskDescription: (value: string) => void;
}

export const StartState: React.FC<StartStateProps> = ({
	taskDescription,
	setTaskDescription,
}) => {
	return (
		<div className={classes.body.content}>
			<Input
				type="text"
				id="taskDescription"
				value={taskDescription}
				onChange={(e) => setTaskDescription(e.target.value)}
				placeholder="e.g., Benefits of Omega-3 Fatty Acids"
				className={classes.item.input}
			/>
		</div>
	);
};
