"""ChatGLM API service."""

from __future__ import annotations

import json
import re
from typing import Dict, Generator, Iterable, Optional

import requests
from flask import current_app

from app.utils.errors import APIError


class ChatGLMService:
    def _request(self, data: dict, stream: bool = False) -> requests.Response:
        api_key = current_app.config.get("CHATGLM_API_KEY")
        api_url = current_app.config.get("CHATGLM_API_URL")
        timeout = current_app.config.get("REQUEST_TIMEOUT", 120)

        if not api_key:
            raise APIError("ChatGLM API Key 未配置", 500)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                api_url,
                json=data,
                headers=headers,
                timeout=timeout,
                stream=stream,
            )
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            message = str(exc)
            detail = ""
            if exc.response is not None:
                try:
                    detail = json.dumps(exc.response.json(), ensure_ascii=False)
                except Exception:  # noqa: BLE001
                    detail = exc.response.text
            if detail:
                message = f"{message}; {detail}"
            raise APIError(f"ChatGLM API 错误: {message}", 500) from exc

    def _build_parse_prompt(self, text: str) -> str:
        return f"""你是一位经验丰富的教师，请分析以下题目：

题目：{text}

请按以下 JSON 格式输出分析结果（只输出 JSON，不要添加 markdown 代码块标记或其他内容）：

{{
    \"type\": \"题目类型（选择/填空/解答/判断）\",
    \"subject\": \"所属学科\",
    \"knowledgePoints\": [\"知识点1\", \"知识点2\"],
    \"difficulty\": \"难度等级（简单/中等/困难）\",
    \"prerequisites\": [\"前置知识1\", \"前置知识2\"]
}}"""

    def parse_problem(self, text: str) -> Dict:
        request_data = {
            "model": current_app.config.get("CHATGLM_MODEL", "glm-4.7-flashx"),
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位专业的教育分析师，擅长分析各类学科题目。你必须只输出纯 JSON 格式，不要添加任何 markdown 标记或其他文字。",
                },
                {"role": "user", "content": self._build_parse_prompt(text)},
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
        }

        if current_app.config.get("CHATGLM_ENABLE_THINKING"):
            request_data["thinking"] = {"type": "enabled"}

        response = self._request(request_data)

        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise APIError("ChatGLM 响应结构异常", 500) from exc

        parsed = self._extract_json(content)
        return parsed

    def generate_solution(self, text: str, parse_result: Dict) -> Dict:
        knowledge_points = parse_result.get("knowledgePoints", [])
        if isinstance(knowledge_points, list):
            knowledge_text = "、".join(str(item) for item in knowledge_points)
        else:
            knowledge_text = str(knowledge_points)

        prompt = f"""你是一位耐心的 AI 教师，请为学生提供详细的解答。

题目：{text}

题目类型：{parse_result.get('type', '')}
所属学科：{parse_result.get('subject', '')}
知识点：{knowledge_text}
难度等级：{parse_result.get('difficulty', '')}

请按以下格式输出解答：

【解题思路】
分析题目的解题思路和方法

【详细步骤】
1. 步骤一
2. 步骤二
3. 步骤三
...

【最终答案】
给出简洁明确的答案

【知识总结】
总结本题涉及的知识点和解题技巧"""

        request_data = {
            "model": current_app.config.get("CHATGLM_MODEL", "glm-4.7-flashx"),
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位优秀的 AI 教师，擅长用清晰、易懂的方式讲解题目。你会引导学生思考，不仅给出答案，还会解释为什么这样做。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 1024,
        }

        if current_app.config.get("CHATGLM_ENABLE_THINKING"):
            request_data["thinking"] = {"type": "enabled"}

        response = self._request(request_data)

        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise APIError("ChatGLM 响应结构异常", 500) from exc

        return self.parse_solution_content(content)

    def generate_solution_stream(self, text: str, parse_result: Dict) -> Generator[str, None, None]:
        knowledge_points = parse_result.get("knowledgePoints", [])
        if isinstance(knowledge_points, list):
            knowledge_text = "、".join(str(item) for item in knowledge_points)
        else:
            knowledge_text = str(knowledge_points)

        prompt = f"""你是一位耐心的 AI 教师，请为学生提供详细的解答。

题目：{text}
题目类型：{parse_result.get('type', '')}
所属学科：{parse_result.get('subject', '')}
知识点：{knowledge_text}

请提供详细的解题思路、步骤、答案和知识总结。"""

        request_data = {
            "model": current_app.config.get("CHATGLM_MODEL", "glm-4.7-flashx"),
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位优秀的 AI 教师，擅长用清晰、易懂的方式讲解题目。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": True,
        }

        if current_app.config.get("CHATGLM_ENABLE_THINKING"):
            request_data["thinking"] = {"type": "enabled"}

        response = self._request(request_data, stream=True)

        for line in self._iter_sse_lines(response.iter_lines(decode_unicode=True)):
            if line == "[DONE]":
                break
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            delta = (
                parsed.get("choices", [{}])[0]
                .get("delta", {})
            )
            content = delta.get("content")
            if content:
                yield content

    @staticmethod
    def _iter_sse_lines(lines: Iterable[Optional[str]]) -> Generator[str, None, None]:
        for raw_line in lines:
            if not raw_line:
                continue
            line = raw_line.strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data:
                yield data

    @staticmethod
    def _extract_json(content: str) -> Dict:
        json_str = content.strip()

        code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", json_str)
        if code_block_match:
            json_str = code_block_match.group(1).strip()

        json_match = re.search(r"\{[\s\S]*\}", json_str)
        if json_match:
            json_str = json_match.group(0)

        json_str = json_str.replace("\ufeff", "").strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as exc:
            raise APIError(f"解析结果格式错误: {exc}", 500) from exc

    @staticmethod
    def parse_solution_content(content: str) -> Dict:
        result = {
            "thinking": "",
            "steps": [],
            "answer": "",
            "summary": "",
        }

        thinking_match = re.search(r"【解题思路】\s*\n?([\s\S]*?)(?=【|$)", content)
        if thinking_match:
            result["thinking"] = thinking_match.group(1).strip()

        steps_match = re.search(r"【详细步骤】\s*\n?([\s\S]*?)(?=【|$)", content)
        if steps_match:
            steps_text = steps_match.group(1).strip()
            result["steps"] = [
                re.sub(r"^\d+\.\s*", "", line).strip()
                for line in steps_text.splitlines()
                if line.strip()
            ]

        answer_match = re.search(r"【最终答案】\s*\n?([\s\S]*?)(?=【|$)", content)
        if answer_match:
            result["answer"] = answer_match.group(1).strip()

        summary_match = re.search(r"【知识总结】\s*\n?([\s\S]*?)(?=【|$)", content)
        if summary_match:
            result["summary"] = summary_match.group(1).strip()

        return result

    def health_check(self) -> bool:
        request_data = {
            "model": current_app.config.get("CHATGLM_MODEL", "glm-4.7-flashx"),
            "messages": [{"role": "user", "content": "你好"}],
            "max_tokens": 10,
        }
        try:
            self._request(request_data)
            return True
        except APIError:
            return False


chatglm_service = ChatGLMService()
