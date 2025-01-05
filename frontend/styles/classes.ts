export const classes = {
	// Layout

	body: {
		wrapper:
			"h-screen w-full flex flex-col items-center justify-center gap-4 p-8",
		content: "w-full flex flex-col mx-auto bg-white text-black gap-4",
	},

	page: {
		container: "container flex flex-col gap-4",
		content: "w-full flex flex-col mx-auto bg-white text-black gap-4",
		states: "w-full flex flex-row mx-auto bg-white text-black gap-4",
	},

	item: {
		container: "w-full p-4 bg-gray-50 rounded-lg",
		label: "w-full text-lg",
		input: "w-full rounded-full border flex mx-auto p-2",
	},

	button: {
		container:
			"w-full flex mx-auto items-center justify-center text-center border border-transparent text-xs font-medium rounded-md focus:outline-none gap-4",
		primary: "w-full p-4 text-white bg-indigo-600 hover:bg-indigo-700",
		secondary: "w-full p-4 text-gray-700 bg-gray-200 hover:bg-gray-300",
	},

	// BELOW IS CODE THAT NEEDS REVISITING AND REFACTORING
	container: {
		base: "mb-6",
		withSpacing: "space-y-4",
		withPadding: "p-4",
	},

	// Cards
	card: {
		base: "rounded-lg",
		primary: "bg-white p-6 shadow-sm border border-gray-200",
		secondary: "bg-gray-50 p-4",
		withShadow: "shadow-sm hover:shadow-md transition-shadow",
	},

	// Typography
	text: {
		base: "text-gray-700",
		small: "text-sm",
		xsmall: "text-xs",
		heading: {
			base: "font-medium",
			primary: "text-indigo-600",
			secondary: "text-gray-800",
		},
	},

	// Progress
	progress: {
		container: "w-full bg-gray-200 rounded-full h-2.5 my-4",
		bar: "bg-indigo-600 h-2.5 rounded-full",
	},

	// Paper Processing
	paperProcessing: {
		container: "mt-6 bg-gray-50 p-4 rounded-lg",
		header: {
			container: "flex justify-between items-center mb-2",
			counter: "text-sm text-gray-600",
		},
		paper: {
			container: "text-sm bg-white p-3 rounded-md shadow-sm",
			title: "font-medium text-gray-800",
			badges: "flex space-x-4 mt-2",
		},
	},

	// Questions
	questions: {
		item: "p-4 bg-gray-50 rounded-lg w-1/2 mx-auto",
		label: "block mb-2 text-lg",
		loading: "text-gray-600 p-4 bg-gray-50 rounded-lg",
	},

	// Flex Layouts
	flex: {
		row: "flex",
		col: "flex flex-col",
		center: "items-center",
		between: "justify-between",
		gap2: "gap-2",
		gap4: "gap-4",
	},
};
