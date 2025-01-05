import type { Metadata } from "next";
import "../styles/globals.css";
import { classes } from "@/styles/classes";

export const metadata: Metadata = {
	title: "Stateful AI Agent for Knowledge Extraction in Medical Research",
	description:
		"A simple human-in-the-loop multi-state AI agent designed to answer medical research questions with research papers from PubMed. This project is based on the StateFlow research paper, using states with cascading function calling in a research pipeline. The benefit of using states is that it allows for a more structured and modular approach to the research process, making it easier to manage and scale. Using states is a different but highly effective approach for building AI agents, allowing for more deterministic and predictable behavior. The function calling is implemented using FastAPI, OpenAI API and DSPy to process Chain-of-Thought reasoning for prompting the LLM. The backend is interfaced using a frontend implemented in Next.js and Tailwind CSS.",
};

export default function RootLayout({
	children,
}: Readonly<{
	children: React.ReactNode;
}>) {
	return (
		<html lang="en" className={classes.body.wrapper}>
			<body className={classes.body.content}>{children}</body>
		</html>
	);
}
