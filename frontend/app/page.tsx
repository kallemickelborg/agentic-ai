import TaskHandler from "../components/TaskHandler";
import { classes } from "@/styles/classes";

export default function Home() {
	return (
		<main className={classes.body.content}>
			<TaskHandler />
		</main>
	);
}
