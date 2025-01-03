import React from "react";
import * as Tooltip from "@radix-ui/react-tooltip";
import { QuestionMarkCircledIcon } from "@radix-ui/react-icons";
import { motion, AnimatePresence } from "framer-motion";

interface StateTooltipProps {
	currentState: string;
}

const tooltipContent = {
	Start:
		"This tool will find relevant medical research papers from PubMed based on questions and statements. Begin by asking a question or making a statement that you would like to know more about.",
	Clarify:
		"To provide you with the most relevant research papers, we'll ask a few clarifying questions. This helps us understand your specific interests and requirements better.",
	Research:
		"We're now searching through PubMed's extensive database to find the most relevant papers. Each paper is evaluated based on its relevance to your query and scientific merit.",
	Analyze:
		"Review the selected papers in detail. Each paper's evidence is categorized as supporting or opposing your query, with key findings highlighted for easy reference.",
	Conclude:
		"Based on the analyzed papers, we'll provide a comprehensive conclusion that synthesizes the findings and addresses your original query.",
};

export const StateTooltip: React.FC<StateTooltipProps> = ({ currentState }) => {
	return (
		<Tooltip.Provider delayDuration={300}>
			<Tooltip.Root>
				<Tooltip.Trigger asChild>
					<motion.button
						className="fixed top-4 right-4 rounded-full p-2 bg-white hover:bg-gray-50 border border-gray-200 shadow-sm transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
						whileHover={{ scale: 1.05 }}
						whileTap={{ scale: 0.95 }}
						aria-label="Help"
					>
						<QuestionMarkCircledIcon className="w-6 h-6 text-indigo-600" />
					</motion.button>
				</Tooltip.Trigger>
				<AnimatePresence>
					<Tooltip.Portal>
						<Tooltip.Content
							className="z-50 max-w-md bg-white px-4 py-3 rounded-lg shadow-lg border border-gray-200 text-sm text-gray-700 leading-relaxed"
							sideOffset={5}
							asChild
						>
							<motion.div
								initial={{ opacity: 0, y: 5 }}
								animate={{ opacity: 1, y: 0 }}
								exit={{ opacity: 0, y: 5 }}
								transition={{ duration: 0.2 }}
							>
								{tooltipContent[currentState as keyof typeof tooltipContent] ||
									tooltipContent.Start}
								<Tooltip.Arrow className="fill-white" />
							</motion.div>
						</Tooltip.Content>
					</Tooltip.Portal>
				</AnimatePresence>
			</Tooltip.Root>
		</Tooltip.Provider>
	);
};
