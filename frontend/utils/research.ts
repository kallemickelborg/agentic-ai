import { EvidencePoint } from "@/types/research";

export const parseEvidence = (evidence: any): EvidencePoint[] => {
	console.log("Parsing evidence:", evidence);

	if (Array.isArray(evidence)) {
		console.log("Evidence is an array:", evidence);
		return evidence.map((point) => {
			if (typeof point === "object" && point !== null) {
				return {
					title: point.title || "Untitled Evidence",
					evidence: point.evidence || "No details provided",
				};
			}
			return {
				title: "Untitled Evidence",
				evidence: String(point),
			};
		});
	}

	if (typeof evidence === "string") {
		try {
			const parsed = JSON.parse(evidence);
			console.log("Parsed JSON evidence:", parsed);
			if (Array.isArray(parsed)) {
				return parsed.map((point) => ({
					title: point.title || "Untitled Evidence",
					evidence: point.evidence || "No details provided",
				}));
			}

			if (typeof parsed === "object" && parsed !== null) {
				return [
					{
						title: parsed.title || "Untitled Evidence",
						evidence: parsed.evidence || "No details provided",
					},
				];
			}
		} catch (e) {
			console.error("Failed to parse evidence string:", e);
			return [
				{
					title: "Evidence Point",
					evidence: evidence,
				},
			];
		}
	}

	console.log("Returning empty evidence array");
	return [];
};
