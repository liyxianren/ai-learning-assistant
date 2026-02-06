"""AI service layer that combines multimodal and ChatGLM models."""

from __future__ import annotations

from typing import Dict, Generator

import requests
from flask import current_app

from app.services.chatglm_service import chatglm_service
from app.utils.errors import APIError


class AIService:
    def recognize_image(self, image_base64: str) -> str:
        api_key = current_app.config.get("MULTIMODAL_API_KEY")
        api_url = current_app.config.get("MULTIMODAL_API_URL")
        model = current_app.config.get("MULTIMODAL_MODEL", "gpt-4-vision-preview")
        timeout = current_app.config.get("REQUEST_TIMEOUT", 120)

        if not api_key:
            raise APIError("图像识别服务未配置", 500)

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请仔细识别图片中的题目内容，提取所有文字、数字、公式。保持题目的原始格式，如果是数学题保留公式表达式。只输出识别到的文本内容，不要添加任何解释。",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_base64},
                        },
                    ],
                }
            ],
            "max_tokens": 2000,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.RequestException as exc:
            raise APIError(f"图像识别失败: {exc}", 500) from exc
        except (KeyError, IndexError, TypeError) as exc:
            raise APIError("图像识别返回格式异常", 500) from exc

    def parse_problem(self, text: str) -> Dict:
        return chatglm_service.parse_problem(text)

    def generate_solution(self, text: str, parse_result: Dict) -> Dict:
        return chatglm_service.generate_solution(text, parse_result)

    def generate_solution_stream(self, text: str, parse_result: Dict) -> Generator[str, None, None]:
        return chatglm_service.generate_solution_stream(text, parse_result)

    def parse_solution_content(self, content: str) -> Dict:
        return chatglm_service.parse_solution_content(content)

    def health_check(self) -> Dict[str, bool]:
        result = {"multimodal": False, "chatglm": False}

        api_key = current_app.config.get("MULTIMODAL_API_KEY")
        api_url = current_app.config.get("MULTIMODAL_API_URL")
        model = current_app.config.get("MULTIMODAL_MODEL", "gpt-4-vision-preview")

        if api_key:
            try:
                response = requests.post(
                    api_url,
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "Hi"}],
                        "max_tokens": 5,
                    },
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=10,
                )
                response.raise_for_status()
                result["multimodal"] = True
            except requests.RequestException:
                result["multimodal"] = False

        result["chatglm"] = chatglm_service.health_check()
        return result


ai_service = AIService()
