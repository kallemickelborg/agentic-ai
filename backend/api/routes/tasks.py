from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models.domain import Task
from services import TaskService
from core.logging import logger
import json
import traceback

router = APIRouter()


@router.post("/solve-task/")
async def solve_task_endpoint(task: Task):
    """
    FastAPI endpoint that handles the task solving process.
    This endpoint maintains 100% compatibility with the frontend API.
    """
    logger.info(f"Received task: {task.dict()}")
    try:
        # Create task service instance
        task_service = TaskService()

        # Process the task using the service layer
        # This replaces all the if/elif logic while maintaining exact same behavior
        result = await task_service.process_task(task)

        return result

    except HTTPException as e:
        if e.status_code == 204:
            return {"message": "No research papers found", "restart": True}
        raise e
    except Exception as e:
        logger.error(f"Error in solve_task: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
