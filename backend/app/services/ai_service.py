"""AI service layer that combines multimodal and ChatGLM models."""

from __future__ import annotations

import json
from typing import Dict, Generator

import requests
from flask import current_app

from app.services.chatglm_service import chatglm_service
from app.utils.errors import APIError


class AIService:
    @staticmethod
    def _normalize_text_content(content) -> str:
        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            chunks = []
            for item in content:
                if isinstance(item, str):
                    if item.strip():
                        chunks.append(item.strip())
                    continue
                if not isinstance(item, dict):
                    continue

                text_value = item.get("text")
                if isinstance(text_value, str) and text_value.strip():
                    chunks.append(text_value.strip())
                    continue

                content_value = item.get("content")
                if isinstance(content_value, str) and content_value.strip():
                    chunks.append(content_value.strip())
            return "\n".join(chunks).strip()

        if isinstance(content, dict):
            for key in ("text", "content", "output_text"):
                value = content.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            return json.dumps(content, ensure_ascii=False).strip()

        if content is None:
            return ""

        return str(content).strip()

    def _resolve_multimodal_config(self) -> tuple[str, str, str]:
        # 图像识别固定走 ChatGLM 4.6V 通道，避免误用 OpenAI 配置
        api_key = current_app.config.get("CHATGLM_API_KEY")
        api_url = current_app.config.get("CHATGLM_API_URL")
        model = current_app.config.get("MULTIMODAL_MODEL", "glm-4.6v-flashx")
        return (api_key or "", api_url or "", model)

    def recognize_image(self, image_base64: str) -> str:
        api_key, api_url, model = self._resolve_multimodal_config()
        timeout = current_app.config.get("REQUEST_TIMEOUT", 120)

        if not api_key or not api_url:
            raise APIError("图像识别服务未配置", 500)

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_base64},
                        },
                        {
                            "type": "text",
                            "text": "请仔细识别图片中的题目内容，提取所有文字、数字、公式。保持题目的原始格式，如果是数学题保留公式表达式。只输出识别到的文本内容，不要添加任何解释。",
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
            raw_content = data["choices"][0]["message"]["content"]
            normalized_text = self._normalize_text_content(raw_content)
            if not normalized_text:
                raise APIError("图像识别结果为空", 500)
            return normalized_text
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

        api_key, api_url, model = self._resolve_multimodal_config()

        if api_key and api_url:
            try:
                response = requests.post(
                    api_url,
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "hi",
                                    }
                                ],
                            }
                        ],
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
