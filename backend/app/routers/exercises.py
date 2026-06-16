from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_current_user
from app.models.db_models import User
from app.models.schemas import ExerciseResponse
from app.services.exercise_db import exercise_db

router = APIRouter()


@router.get("", response_model=list[ExerciseResponse])
async def list_exercises(
    difficulty: str = Query("Any", enum=["Any", "introductory", "interview", "competition"]),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    shuffle: bool = Query(True),
    current_user: User = Depends(get_current_user),
):
    problems = await exercise_db.list_problems(difficulty, limit, offset, shuffle)
    return [
        ExerciseResponse(
            id=p["id"],
            question=p["question"],
            starter_code=p["starter_code"],
            difficulty=p["difficulty"],
        )
        for p in problems
    ]


@router.get("/count")
async def count_exercises(
    difficulty: str = Query("Any", enum=["Any", "introductory", "interview", "competition"]),
    current_user: User = Depends(get_current_user),
):
    total = await exercise_db.count_problems(difficulty)
    return {"total": total}


@router.get("/random", response_model=ExerciseResponse)
async def get_random_exercise(
    difficulty: str = Query("Any", enum=["Any", "introductory", "interview", "competition"]),
    current_user: User = Depends(get_current_user),
):
    problem = await exercise_db.get_random_problem(difficulty)
    if problem is None:
        raise HTTPException(status_code=404, detail="No exercise found for this difficulty")
    return ExerciseResponse(
        id=problem["id"],
        question=problem["question"],
        starter_code=problem["starter_code"],
        difficulty=problem["difficulty"],
    )


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: str,
    current_user: User = Depends(get_current_user),
):
    problem = await exercise_db.get_problem_by_id(exercise_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return ExerciseResponse(
        id=problem["id"],
        question=problem["question"],
        starter_code=problem["starter_code"],
        difficulty=problem["difficulty"],
    )
