import asyncio
import json
import random


class ExerciseDB:
    def __init__(self):
        self.dataset = None
        self._loaded = False
        self._id_to_index: dict[str, int] = {}
        self._difficulty_indices: dict[str, list[int]] = {}
        self._all_indices: list[int] = []

    def _parse_problem(self, problem: dict, truncate_question: bool = False) -> dict:
        question = problem["question"]
        if truncate_question and len(question) > 200:
            question = question[:200] + "..."

        result = {
            "id": str(problem["id"]),
            "question": question,
            "starter_code": problem["starter_code"] or "",
            "difficulty": problem["difficulty"],
        }
        if not truncate_question:
            try:
                solutions = json.loads(problem["solutions"])
                result["solution"] = solutions[0] if solutions else ""
            except (json.JSONDecodeError, TypeError):
                result["solution"] = problem["solutions"] or ""
        return result

    def _build_indexes(self):
        self._id_to_index.clear()
        self._difficulty_indices.clear()
        self._all_indices.clear()
        for i in range(len(self.dataset)):
            row = self.dataset[i]
            str_id = str(row["id"])
            self._id_to_index[str_id] = i
            self._all_indices.append(i)
            diff = row["difficulty"]
            if diff not in self._difficulty_indices:
                self._difficulty_indices[diff] = []
            self._difficulty_indices[diff].append(i)

    def _load_sync(self):
        from datasets import load_dataset

        self.dataset = load_dataset(
            "json",
            data_files="hf://datasets/codeparrot/apps/train.jsonl",
            split="train",
        )
        self._build_indexes()
        self._loaded = True

    async def load(self):
        if not self._loaded:
            await asyncio.to_thread(self._load_sync)

    def _get_indices(self, difficulty: str) -> list[int]:
        if difficulty == "Any":
            return self._all_indices
        return self._difficulty_indices.get(difficulty, [])

    def _get_random_problem_sync(self, difficulty: str = "Any") -> dict | None:
        if not self._loaded or self.dataset is None:
            return None
        indices = self._get_indices(difficulty)
        if not indices:
            return None
        idx = random.choice(indices)
        return self._parse_problem(self.dataset[idx])

    async def get_random_problem(self, difficulty: str = "Any") -> dict | None:
        return await asyncio.to_thread(self._get_random_problem_sync, difficulty)

    def _list_problems_sync(
        self, difficulty: str = "Any", limit: int = 10, offset: int = 0, shuffle: bool = True
    ) -> list[dict]:
        if not self._loaded or self.dataset is None:
            return []
        indices = self._get_indices(difficulty)
        if shuffle:
            indices = random.sample(indices, len(indices))
        page = indices[offset : offset + limit]
        return [self._parse_problem(self.dataset[i], truncate_question=True) for i in page]

    def _count_problems_sync(self, difficulty: str = "Any") -> int:
        if not self._loaded or self.dataset is None:
            return 0
        return len(self._get_indices(difficulty))

    def _get_problem_by_id_sync(self, problem_id: str) -> dict | None:
        if not self._loaded or self.dataset is None:
            return None
        idx = self._id_to_index.get(problem_id)
        if idx is None:
            return None
        return self._parse_problem(self.dataset[idx])

    async def get_problem_by_id(self, problem_id: str) -> dict | None:
        return await asyncio.to_thread(self._get_problem_by_id_sync, problem_id)

    async def list_problems(
        self, difficulty: str = "Any", limit: int = 10, offset: int = 0, shuffle: bool = True
    ) -> list[dict]:
        return await asyncio.to_thread(
            self._list_problems_sync, difficulty, limit, offset, shuffle
        )

    async def count_problems(self, difficulty: str = "Any") -> int:
        return await asyncio.to_thread(self._count_problems_sync, difficulty)


exercise_db = ExerciseDB()
