export interface Author {
	name: string;
}

export interface EvidencePoint {
	title: string;
	evidence: string;
}

export interface Paper {
	title: string;
	link: string;
	authors: Author[];
	published_date: string;
	relevancy_score?: number;
	citation_score?: number;
	supporting_evidence?: EvidencePoint[];
	opposing_evidence?: EvidencePoint[];
	key_findings?: string;
	full_text_accessible: boolean;
	full_text_link?: string;
	source_type: "abstract_only" | "open_access" | "requires_access";
}

export interface PaperAnalysis {
	title: string;
	link: string;
	supporting_evidence?: EvidencePoint[];
	opposing_evidence?: EvidencePoint[];
	key_findings?: string;
}

export interface ProcessingStatus {
	totalPapers: number;
	processedPapers: number;
	currentPaper: {
		title: string;
		relevancy_score: number;
		citation_score: number;
	} | null;
}

export interface Task {
	state: string;
	input_data: {
		selected_papers?: string[];
		clarify_answers?: { question: string; answer: string }[];
		direction?: "forward" | "backward";
		paper_analyses?: PaperAnalysis[];
	};
	task_description: string;
	research_papers: Paper[];
	state_history?: string[];
}

export interface ClarifyAnswer {
	question: string;
	answer: string;
}

export interface Question {
	question: string;
}
