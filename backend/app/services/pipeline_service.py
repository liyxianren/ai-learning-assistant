"""Pipeline service coordinating recognition, parsing and solving."""

from __future__ import annotations

from typing import Dict, Generator

from app.extensions import db
from app.models.history import History
from app.services.ai_service import ai_service


class PipelineService:
    def solve_problem(self, input_data: Dict) -> Dict:
        result = {"success": True, "data": {}}

        try:
            if input_data.get("type") == "image":
                problem_text = ai_service.recognize_image(input_data.get("content", ""))
            else:
                problem_text = str(input_data.get("content", ""))

            result["data"]["recognizedText"] = problem_text

            parse_result = ai_service.parse_problem(problem_text)
            result["data"]["parseResult"] = parse_result

            solution = ai_service.generate_solution(problem_text, parse_result)
            result["data"]["solution"] = solution

            user_id = input_data.get("userId")
            if user_id:
                history_record = History(
                    user_id=user_id,
                    username=input_data.get("username"),
                    question=problem_text,
                    parse_result=parse_result,
                    solution=solution,
                )
                db.session.add(history_record)
                db.session.commit()
                result["data"]["historyId"] = history_record.id

            return result
        except Exception as exc:  # noqa: BLE001
            db.session.rollback()
            return {
                "success": False,
                "error": str(exc),
                "data": result["data"],
            }

    def recognize_only(self, image_base64: str) -> Dict:
        try:
            text = ai_service.recognize_image(image_base64)
            return {"success": True, "data": {"text": text}}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}

    def parse_only(self, text: str) -> Dict:
        try:
            parse_result = ai_service.parse_problem(text)
            return {"success": True, "data": parse_result}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}

    def solve_only(self, text: str, parse_result: Dict) -> Dict:
        try:
            solution = ai_service.generate_solution(text, parse_result)
            return {"success": True, "data": solution}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}

    def solve_stream(self, text: str, parse_result: Dict) -> Generator[str, None, None]:
        yield from ai_service.generate_solution_stream(text, parse_result)


pipeline_service = PipelineService()
