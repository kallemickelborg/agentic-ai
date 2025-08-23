from typing import List

# State transition definitions
STATE_TRANSITIONS = {
    "Start": "Clarify",
    "Clarify": "Research",
    "Research": "Analyze",
    "Analyze": "Conclude",
    "Conclude": "Start",
}

STATE_SUBSTEPS = {
    "Start": ["Initializing the research assistant.", "Setting up the environment."],
    "Clarify": [
        "Analyzing the prompt for specificity.",
        "Generating clarifying questions.",
    ],
    "Research": [
        "Optimizing query for optimal findings.",
        "Querying medical publications.",
        "Finding relevant research papers for the prompt.",
    ],
    "Analyze": [
        "Analyzing the fetched research papers.",
        "Extracting key insights and data.",
    ],
    "Conclude": [
        "Formulating the final conclusion based on research.",
        "Ensuring all points are covered comprehensively.",
    ],
}

FORWARD_TRANSITIONS = {
    "Start": "Clarify",
    "Clarify": "Research",
    "Research": "Analyze",
    "Analyze": "Conclude",
    "Conclude": "Start",
}

BACKWARD_TRANSITIONS = {
    "Clarify": "Start",
    "Research": "Clarify",
    "Analyze": "Research",
    "Conclude": "Analyze",
    "Start": "Conclude",
}


class StateService:
    """Service for managing state transitions and substeps."""

    def get_next_state(self, current_state: str, direction: str = "forward") -> str:
        """Get the next state based on direction."""
        if direction == "forward":
            return FORWARD_TRANSITIONS.get(current_state, current_state)
        return BACKWARD_TRANSITIONS.get(current_state, current_state)

    def get_state_substeps(self, state: str) -> List[str]:
        """Get the substeps for a given state."""
        return STATE_SUBSTEPS.get(state, [])

    def get_state_transitions(self) -> dict:
        """Get all state transitions."""
        return STATE_TRANSITIONS.copy()

    def get_forward_transitions(self) -> dict:
        """Get forward state transitions."""
        return FORWARD_TRANSITIONS.copy()

    def get_backward_transitions(self) -> dict:
        """Get backward state transitions."""
        return BACKWARD_TRANSITIONS.copy()

    def is_valid_state(self, state: str) -> bool:
        """Check if a state is valid."""
        return state in STATE_TRANSITIONS

    def get_all_states(self) -> List[str]:
        """Get list of all valid states."""
        return list(STATE_TRANSITIONS.keys())
