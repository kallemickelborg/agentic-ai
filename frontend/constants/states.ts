export const TASK_STATES = {
	START: "Start",
	CLARIFY: "Clarify",
	RESEARCH: "Research",
	ANALYZE: "Analyze",
	CONCLUDE: "Conclude",
} as const;

export type TaskState = (typeof TASK_STATES)[keyof typeof TASK_STATES];

export const placeholderData = {
	clarifyingQuestions: [
		"Are you interested in benefits related to bone health?",
		"Are you seeking information about the role of Vitamin D3 in immune function?",
		"Are you looking for benefits of Vitamin D3 for specific age groups or conditions?",
	],
	researchPapers: [
		{
			title: "Vitamin D3 and Bone Health",
			link: "https://example.com/paper1",
			authors: [{ name: "John Doe" }],
			published_date: "2023-01-01",
			full_text_accessible: true,
			source_type: "open_access" as const,
		},
		{
			title: "Immune Function and Vitamin D3",
			link: "https://example.com/paper2",
			authors: [{ name: "Jane Smith" }],
			published_date: "2023-02-15",
			full_text_accessible: true,
			source_type: "open_access" as const,
		},
		{
			title: "Vitamin D3 Benefits Across Age Groups",
			link: "https://example.com/paper3",
			authors: [{ name: "Alice Johnson" }],
			published_date: "2023-03-30",
			full_text_accessible: true,
			source_type: "open_access" as const,
		},
	],
	analysisResponse:
		"Analysis of the selected papers shows strong evidence for the benefits of Vitamin D3 in bone health...",
	conclusionResponse:
		"In conclusion, Vitamin D3 offers significant benefits, particularly in bone health. However, more research is needed to...",
};
