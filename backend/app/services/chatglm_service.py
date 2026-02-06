"""ChatGLM API service."""

from __future__ import annotations

import ast
import json
import re
from typing import Dict, Generator, Iterable, Optional

import requests
from flask import current_app

from app.utils.errors import APIError


class ChatGLMService:
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

                for key in ("text", "content", "output_text"):
                    value = item.get(key)
                    if isinstance(value, str) and value.strip():
                        chunks.append(value.strip())
                        break
            return "\n".join(chunks).strip()

        if isinstance(content, dict):
            for key in ("text", "content", "output_text", "reasoning_content"):
                value = content.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            return json.dumps(content, ensure_ascii=False).strip()

        if content is None:
            return ""

        return str(content).strip()

    @staticmethod
    def _normalize_list_field(value) -> list[str]:
        if value is None:
            return []

        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]

        text = str(value).strip()
        if not text:
            return []

        if text.startswith("[") and text.endswith("]"):
            try:
                decoded = json.loads(text)
                if isinstance(decoded, list):
                    return [str(item).strip() for item in decoded if str(item).strip()]
            except Exception:  # noqa: BLE001
                pass

        parts = re.split(r"[，,、；;\n]+", text)
        return [part.strip(" -•*") for part in parts if part.strip(" -•*")]

    @staticmethod
    def _infer_type(text: str) -> str:
        normalized = text or ""
        if any(keyword in normalized for keyword in ("判断", "对错", "正确吗", "错误吗")):
            return "判断"
        if "填空" in normalized or "____" in normalized or "（  ）" in normalized:
            return "填空"
        if "选择" in normalized or re.search(r"\bA[\.、]\s*.+\bB[\.、]\s*.+", normalized):
            return "选择"
        return "解答"

    @staticmethod
    def _infer_subject(text: str) -> str:
        normalized = text or ""
        if re.search(r"[0-9xXyY+\-*/=^√π∫Σ≤≥<>]", normalized) or any(
            keyword in normalized for keyword in ("方程", "函数", "几何", "数学", "代数", "概率")
        ):
            return "数学"
        if any(keyword in normalized for keyword in ("英语", "English", "完形填空", "阅读理解")):
            return "英语"
        if any(keyword in normalized for keyword in ("物理", "电路", "力学", "速度", "加速度")):
            return "物理"
        if any(keyword in normalized for keyword in ("化学", "反应", "方程式", "元素")):
            return "化学"
        if any(keyword in normalized for keyword in ("生物", "细胞", "DNA", "遗传")):
            return "生物"
        return "综合"

    @staticmethod
    def _infer_difficulty(text: str) -> str:
        size = len((text or "").strip())
        if size <= 30:
            return "简单"
        if size <= 120:
            return "中等"
        return "困难"

    def _coerce_parse_result(self, data: Dict, source_text: str) -> Dict:
        raw_type = str(data.get("type", "")).strip()
        type_value = raw_type if raw_type in {"选择", "填空", "解答", "判断"} else self._infer_type(source_text)

        subject_value = str(data.get("subject", "")).strip() or self._infer_subject(source_text)

        difficulty_raw = str(data.get("difficulty", "")).strip()
        difficulty_value = (
            difficulty_raw
            if difficulty_raw in {"简单", "中等", "困难"}
            else self._infer_difficulty(source_text)
        )

        knowledge_points = self._normalize_list_field(data.get("knowledgePoints"))
        if not knowledge_points:
            knowledge_points = ["题型分析", "解题方法"]

        prerequisites = self._normalize_list_field(data.get("prerequisites"))
        if not prerequisites:
            prerequisites = ["相关基础概念"]

        return {
            "type": type_value,
            "subject": subject_value,
            "knowledgePoints": knowledge_points,
            "difficulty": difficulty_value,
            "prerequisites": prerequisites,
        }

    def _extract_fields_from_text(self, content: str, source_text: str) -> Dict:
        text = (content or "").strip()
        if not text:
            return self._coerce_parse_result({}, source_text)

        fields = {}

        type_match = re.search(r"(?:题目类型|类型)\s*[:：]\s*([^\n，,。；;]+)", text)
        subject_match = re.search(r"(?:所属学科|学科)\s*[:：]\s*([^\n，,。；;]+)", text)
        difficulty_match = re.search(r"(?:难度等级|难度)\s*[:：]\s*([^\n，,。；;]+)", text)
        kp_match = re.search(r"(?:知识点)\s*[:：]\s*([^\n]+)", text)
        pre_match = re.search(r"(?:前置知识|先修知识)\s*[:：]\s*([^\n]+)", text)

        if type_match:
            fields["type"] = type_match.group(1).strip()
        if subject_match:
            fields["subject"] = subject_match.group(1).strip()
        if difficulty_match:
            fields["difficulty"] = difficulty_match.group(1).strip()
        if kp_match:
            fields["knowledgePoints"] = self._normalize_list_field(kp_match.group(1).strip())
        if pre_match:
            fields["prerequisites"] = self._normalize_list_field(pre_match.group(1).strip())

        return self._coerce_parse_result(fields, source_text)

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

        normalized_content = self._normalize_text_content(content)

        try:
            parsed = self._extract_json(normalized_content)
            return self._coerce_parse_result(parsed, text)
        except APIError:
            current_app.logger.warning(
                "解析返回非标准 JSON，降级提取字段。content=%s",
                normalized_content[:600],
            )
            return self._extract_fields_from_text(normalized_content, text)

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
            message = response.json()["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise APIError("ChatGLM 响应结构异常", 500) from exc

        content = message.get("content") if isinstance(message, dict) else message
        normalized_content = self._normalize_text_content(content)

        # 某些配置下正文可能落在 reasoning_content；若 content 为空则兜底使用 reasoning_content
        if not normalized_content and isinstance(message, dict):
            normalized_content = self._normalize_text_content(message.get("reasoning_content"))

        if not normalized_content:
            raise APIError("解答生成失败: 模型未返回有效内容", 500)

        return self.parse_solution_content(normalized_content)

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
    def _extract_json(content) -> Dict:
        json_str = ChatGLMService._normalize_text_content(content)
        if not json_str:
            raise APIError("解析结果格式错误: 模型未返回有效内容", 500)

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
            try:
                repaired = ast.literal_eval(json_str)
            except Exception:  # noqa: BLE001
                raise APIError(f"解析结果格式错误: {exc}", 500) from exc
            if isinstance(repaired, dict):
                return repaired
            raise APIError(f"解析结果格式错误: {exc}", 500) from exc

    @staticmethod
    def parse_solution_content(content: str) -> Dict:
        result = {
            "thinking": "",
            "steps": [],
            "answer": "",
            "summary": "",
        }

        text = ChatGLMService._normalize_text_content(content)
        if not text:
            return result

        heading_line = r"\n\s*(?:#{1,6}\s*)?(?:【\s*)?(?:解题思路|详细步骤|解题步骤|步骤|最终答案|答案|知识总结|总结)(?:\s*】)?\s*[:：]?"

        def _extract_section(aliases: str) -> str:
            pattern = (
                r"(?:^|\n)\s*(?:#{1,6}\s*)?(?:【\s*)?(?:"
                + aliases
                + r")(?:\s*】)?\s*[:：]?\s*([\s\S]*?)(?="
                + heading_line
                + r"|\Z)"
            )
            match = re.search(pattern, text, re.IGNORECASE)
            return match.group(1).strip() if match else ""

        result["thinking"] = _extract_section("解题思路")
        steps_text = _extract_section("详细步骤|解题步骤|步骤")
        result["answer"] = _extract_section("最终答案|答案")
        result["summary"] = _extract_section("知识总结|总结")

        if steps_text:
            parsed_steps = []
            for line in steps_text.splitlines():
                cleaned = re.sub(r"^\s*(?:[-*•]|\d+[\.、\)]|第[一二三四五六七八九十百零\d]+步)\s*", "", line).strip()
                if cleaned:
                    parsed_steps.append(cleaned)
            if not parsed_steps:
                parsed_steps = [item.strip() for item in re.split(r"[。；;\n]+", steps_text) if item.strip()]
            result["steps"] = parsed_steps

        # 兜底：模型未按模板输出时，尽量把正文映射到可展示结构
        if not result["thinking"] and not result["steps"] and not result["answer"] and not result["summary"]:
            paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
            if paragraphs:
                result["thinking"] = paragraphs[0]
                if len(paragraphs) > 1:
                    result["summary"] = paragraphs[-1]
                middle = paragraphs[1:-1] if len(paragraphs) > 2 else paragraphs[1:]
                result["steps"] = middle

            numbered_lines = []
            for line in text.splitlines():
                stripped = line.strip()
                if re.match(r"^(?:\d+[\.、\)]|[-*•])\s*", stripped):
                    numbered_lines.append(re.sub(r"^(?:\d+[\.、\)]|[-*•])\s*", "", stripped).strip())
            if numbered_lines and not result["steps"]:
                result["steps"] = [line for line in numbered_lines if line]

        if not result["answer"]:
            answer_inline = re.search(r"(?:最终答案|答案)\s*[:：]\s*(.+)", text)
            if answer_inline:
                result["answer"] = answer_inline.group(1).strip()
            elif result["steps"]:
                result["answer"] = str(result["steps"][-1]).strip()

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
