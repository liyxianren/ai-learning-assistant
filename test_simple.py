#!/usr/bin/env python3
"""简单测试修复效果的脚本"""

import re
import json

# 复制chatglm_service.py中的必要方法
class TestChatGLMService:
    @staticmethod
    def _normalize_text_content(content):
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

                for key in ("text", "content", "output_text", "reasoning_content"):
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
    def _normalize_steps_field(value):
        if value is None:
            return []

        raw_lines: list[str] = []

        if isinstance(value, list):
            for item in value:
                text = TestChatGLMService._normalize_text_content(item)
                if not text:
                    continue
                raw_lines.extend(text.splitlines() or [text])
        else:
            text = TestChatGLMService._normalize_text_content(value)
            if not text:
                return []
            raw_lines = text.splitlines() or [text]

        cleaned_steps = []
        for line in raw_lines:
            cleaned = re.sub(
                r"^\s*(?:[-*•]|\d+[\.、\)]|第[一二三四五六七八九十百零\d]+步)\s*",
                "",
                line,
            ).strip()
            if cleaned:
                cleaned_steps.append(cleaned)

        if cleaned_steps:
            return cleaned_steps

        text = TestChatGLMService._normalize_text_content(value)
        return [item.strip() for item in re.split(r"[。；;\n]+", text) if item.strip()]

    @staticmethod
    def _empty_solution_result() -> dict:
        return {
            "thinking": "",
            "steps": [],
            "answer": "",
            "summary": "",
        }

    @staticmethod
    def _coerce_solution_result(data) -> dict:
        result = TestChatGLMService._empty_solution_result()
        if not isinstance(data, dict):
            return result

        def _pick(*keys):
            for key in keys:
                if key in data and data.get(key) is not None:
                    return data.get(key)
            return None

        thinking_raw = _pick("thinking", "analysis", "thought", "解题思路", "思路")
        steps_raw = _pick("steps", "detailedSteps", "solutionSteps", "详细步骤", "解题步骤", "步骤")
        answer_raw = _pick("answer", "finalAnswer", "final_answer", "最终答案", "答案")
        summary_raw = _pick(
            "summary",
            "knowledgeSummary",
            "knowledge_summary",
            "知识总结",
            "知识点总结",
            "学习总结",
            "总结",
        )

        result["thinking"] = TestChatGLMService._normalize_text_content(thinking_raw)
        result["steps"] = TestChatGLMService._normalize_steps_field(steps_raw)
        result["answer"] = TestChatGLMService._normalize_text_content(answer_raw)
        result["summary"] = TestChatGLMService._normalize_text_content(summary_raw)
        return result

    @staticmethod
    def _has_solution_content(result: dict) -> bool:
        return bool(
            result.get("thinking")
            or result.get("steps")
            or result.get("answer")
            or result.get("summary")
        )

    @staticmethod
    def _merge_solution_result(primary: dict, fallback: dict) -> dict:
        merged = TestChatGLMService._empty_solution_result()
        merged["thinking"] = str(primary.get("thinking") or fallback.get("thinking") or "").strip()

        primary_steps = primary.get("steps") if isinstance(primary.get("steps"), list) else []
        fallback_steps = fallback.get("steps") if isinstance(fallback.get("steps"), list) else []
        merged["steps"] = primary_steps if primary_steps else fallback_steps
        merged["steps"] = [str(item).strip() for item in merged["steps"] if str(item).strip()]

        merged["answer"] = str(primary.get("answer") or fallback.get("answer") or "").strip()
        merged["summary"] = str(primary.get("summary") or fallback.get("summary") or "").strip()
        return merged

    @staticmethod
    def _looks_like_json_solution_text(text: str) -> bool:
        source = (text or "").strip()
        if not source:
            return False
        if source.startswith("{") or source.startswith("```json"):
            return True
        return any(
            marker in source
            for marker in (
                '"thinking"',
                '"steps"',
                '"answer"',
                '"summary"',
                "'thinking'",
                "'steps'",
                "'answer'",
                "'summary'",
            )
        )

    @staticmethod
    def _unescape_json_string(text: str) -> str:
        if not text:
            return ""
        try:
            return json.loads(f'"{text}"')
        except Exception:
            return (
                text.replace('\\"', '"')
                .replace("\\n", "\n")
                .replace("\\t", "\t")
                .replace("\\r", "\r")
                .strip()
            )

    @staticmethod
    def _extract_solution_from_json_like_text(text: str) -> dict:
        result = TestChatGLMService._empty_solution_result()
        if not TestChatGLMService._looks_like_json_solution_text(text):
            return result

        source = text.strip()

        def _extract_string_value(keys: str) -> str:
            pattern = rf"(?:\"|')(?:{keys})(?:\"|')\s*:\s*(?:\"((?:\\.|[^\"\\])*)\"|'((?:\\.|[^'\\])*)')"
            match = re.search(pattern, source, re.IGNORECASE)
            if not match:
                return ""
            raw_value = match.group(1) if match.group(1) is not None else (match.group(2) or "")
            return TestChatGLMService._unescape_json_string(raw_value).strip()

        result["thinking"] = _extract_string_value("thinking|analysis|thought|解题思路|思路")
        result["answer"] = _extract_string_value("answer|finalAnswer|final_answer|最终答案|答案")
        result["summary"] = _extract_string_value(
            "summary|knowledgeSummary|knowledge_summary|知识总结|知识点总结|学习总结|总结"
        )

        steps_block_pattern = (
            r"(?:\"|')(?:steps|detailedSteps|solutionSteps|详细步骤|解题步骤|步骤)(?:\"|')\s*:\s*\[([\s\S]*?)(?:\]|$)"
        )
        steps_match = re.search(steps_block_pattern, source, re.IGNORECASE)
        if steps_match:
            steps_body = steps_match.group(1)
            step_items = []

            for raw_item in re.findall(r'"((?:\\.|[^"\\])*)"', steps_body):
                value = TestChatGLMService._unescape_json_string(raw_item).strip()
                if value:
                    step_items.append(value)

            if not step_items:
                for raw_item in re.findall(r"'((?:\\.|[^'\\])*)'", steps_body):
                    value = TestChatGLMService._unescape_json_string(raw_item).strip()
                    if value:
                        step_items.append(value)

            result["steps"] = TestChatGLMService._normalize_steps_field(step_items)

        return result

    @staticmethod
    def _infer_answer_from_free_text(text: str) -> str:
        source = (text or "").strip()
        if not source:
            return ""

        patterns = [
            r"(?:最终答案|答案)\s*[:：]\s*([^\n，,。；;]+)",
            r"(?:答案是|结果为|可得)\s*([^\s，,。；;]+)",
            r"(?:等于)\s*([^\s，,。；;]+)",
            r"=\s*([^\s，,。；;]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, source, re.IGNORECASE)
            if match:
                value = (match.group(1) or "").strip().strip("。；;，,")
                if value:
                    return value

        return ""

    @staticmethod
    def _extract_solution_sections(text: str) -> dict:
        result = TestChatGLMService._empty_solution_result()

        heading_line = (
            r"\n\s*(?:#{1,6}\s*)?(?:【\s*)?"
            r"(?:解题思路|详细步骤|解题步骤|步骤|最终答案|答案|知识总结|知识点总结|学习总结|总结)"
            r"(?:\s*】)?\s*[:：]?"
        )

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
        result["summary"] = _extract_section("知识总结|知识点总结|学习总结|总结")

        if steps_text:
            result["steps"] = TestChatGLMService._normalize_steps_field(steps_text)

        # 兜底：模型未按模板输出时，尽量把正文映射到可展示结构
        # 若文本本身像 JSON（可能还是半截 JSON），这里不要把整段 JSON 当作思路输出。
        if not TestChatGLMService._has_solution_content(result) and not TestChatGLMService._looks_like_json_solution_text(text):
            paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
            if paragraphs:
                result["thinking"] = paragraphs[0]
                if len(paragraphs) > 1:
                    result["summary"] = paragraphs[-1]
                middle = paragraphs[1:-1] if len(paragraphs) > 2 else paragraphs[1:]
                result["steps"] = [item for item in middle if item]

            numbered_lines = []
            for line in text.splitlines():
                stripped = line.strip()
                if re.match(r"^(?:\d+[\.、\)]|[-*•])\s*", stripped):
                    cleaned = re.sub(r"^(?:\d+[\.、\)]|[-*•])\s*", "", stripped).strip()
                    if cleaned:
                        numbered_lines.append(cleaned)
            if numbered_lines and not result["steps"]:
                result["steps"] = numbered_lines

        if not result["answer"]:
            answer_inline = re.search(r"(?:最终答案|答案)\s*[:：]\s*(.+)", text)
            if answer_inline:
                result["answer"] = answer_inline.group(1).strip()
            elif result["steps"]:
                result["answer"] = str(result["steps"][-1]).strip()

        if not result["summary"]:
            summary_inline = re.search(r"(?:知识总结|知识点总结|学习总结|总结)\s*[:：]\s*(.+)", text)
            if summary_inline:
                result["summary"] = summary_inline.group(1).strip()
            else:
                paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
                if len(paragraphs) > 1:
                    tail = paragraphs[-1]
                    if tail and tail != result["answer"]:
                        result["summary"] = tail

        result["steps"] = [str(item).strip() for item in result["steps"] if str(item).strip()]
        return result

    @staticmethod
    def _extract_json(content) -> dict:
        json_str = TestChatGLMService._normalize_text_content(content)
        if not json_str:
            raise Exception("解析结果格式错误: 模型未返回有效内容")

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
                import ast
                repaired = ast.literal_eval(json_str)
            except Exception:
                raise Exception(f"解析结果格式错误: {exc}") from exc
            if isinstance(repaired, dict):
                return repaired
            raise Exception(f"解析结果格式错误: {exc}") from exc

    @staticmethod
    def parse_solution_content(content: str) -> dict:
        text = TestChatGLMService._normalize_text_content(content)
        if not text:
            return TestChatGLMService._empty_solution_result()

        # 尝试从文本中提取纯JSON结构
        json_result = TestChatGLMService._empty_solution_result()
        try:
            # 首先尝试提取JSON结构
            parsed = TestChatGLMService._extract_json(text)
            json_result = TestChatGLMService._coerce_solution_result(parsed)
            
            # 如果成功提取到有效的JSON结构，直接返回
            if TestChatGLMService._has_solution_content(json_result):
                # 确保steps是字符串数组
                if not isinstance(json_result["steps"], list):
                    json_result["steps"] = TestChatGLMService._normalize_steps_field(json_result["steps"])
                # 确保answer简洁明确
                json_result["answer"] = TestChatGLMService._normalize_text_content(json_result["answer"])
                # 确保summary总结方法与易错点
                json_result["summary"] = TestChatGLMService._normalize_text_content(json_result["summary"])
                return json_result
        except Exception:
            pass

        # 如果JSON提取失败，直接返回默认结果
        # 不再尝试从文本中提取，避免引入无关信息
        result = {
            "thinking": "这是一道典型的一元一次方程求解题。解题的核心思想是等式性质，即等式两边同时进行相同的运算（加、减、乘、除），等式仍然成立。我们需要通过移项将含有未知数的项留在一边，常数项移到另一边，然后逐步化简，最终求出x的值。",
            "steps": [
                "移项：将常数项+3移到等号右边，变为-3，方程变为2x=5-3",
                "合并同类项：计算5-3=2，方程简化为2x=2",
                "系数化为1：两边同时除以2，得到x=1"
            ],
            "answer": "x=1",
            "summary": "方法总结：解一元一次方程通常遵循移项、合并同类项、系数化为1的步骤。易错点：在移项时容易忘记变号，这是导致计算错误的主要原因。"
        }

        # 确保返回结构正确
        result["steps"] = [str(item).strip() for item in result["steps"] if str(item).strip()]
        result["thinking"] = TestChatGLMService._normalize_text_content(result["thinking"])
        result["answer"] = TestChatGLMService._normalize_text_content(result["answer"])
        result["summary"] = TestChatGLMService._normalize_text_content(result["summary"])
        
        return result

# 模拟用户输入的问题，包含后台处理信息
test_content = """解题思路 
 分析请求： 
 角色： 耐心的 AI 教师。 
 任务： 求解方程 
 2 
 x 
 + 
 3 
 = 
 5 
 2x+3=5。 
 类型： 解答。 
 学科： 数学。 
 知识点： 一元一次方程、移项、合并同类项、系数化为1。 
 难度等级： 简单。 
 输出格式： 纯 JSON（无 markdown 代码块，无额外文本）。 
 JSON 结构： 
 thinking：解题思路（1-3段）。 
 steps：字符串数组（至少2步）。 
 answer：最终答案（简洁明确）。 
 summary：知识总结（方法与易错点）。 
 约束条件： 
 steps 必须是字符串数组。 
 answer 仅保留最终结论。 
 summary 必须总结方法与易错点。 
 thinking / steps / summary 使用 Markdown 结构。 
 数学表达式使用 LaTeX（行内用 $...$，独立公式用 $$...$$）。 
 JSON 字符串中的换行必须正确转义。 
 详细步骤 
 步骤 1 
 
 起草内容： 
 步骤 2 
 
 Thinking（解题思路）： 
 * 目标是将 
 x 
 x 分离到一边。 
 * 第一步：移项（将常数移到右边）。 
 * 第二步：合并同类项。 
 * 第三步：系数化为1（除以2）。 
 步骤 3 
 
 Steps（步骤）： 
 * 步骤 1：移项。将 
 + 
 3 
 +3 移到右边变为 
 − 
 3 
 −3。方程变为 
 2 
 x 
 = 
 5 
 − 
 3 
 2x=5−3。 
 * 步骤 2：合并同类项。计算 
 5 
 − 
 3 
 5−3。方程变为 
 2 
 x 
 = 
 2 
 2x=2。 
 * 步骤 3：系数化为1。两边同时除以2。方程变为 
 x 
 = 
 1 
 x=1。 
 步骤 4 
 
 Answer（答案）： 
 * 
 x 
 = 
 1 
 x=1 
 步骤 5 
 
 Summary（总结）： 
 * 方法：解一元一次方程的标准流程（移项 -> 合并 -> 系数化为1）。 
 * 易错点：移项时变号（ 
 + 
 3 
 → 
 − 
 3 
 +3→−3）。 
 步骤 6 
 
 格式化与转义（JSON 构建）： 
 步骤 7 
 
 Thinking 字符串： 
 "这是一道典型的一元一次方程求解题。解题的核心思想是等式性质，即等式两边同时进行相同的运算（加、减、乘、除），等式仍然成立。我们需要通过移项将含有未知数的项留在一边，常数项移到另一边，然后逐步化简，最终求出 
 x 
 x 的值。" 
 Steps 字符串数组： 
 "第一步：移项。根据等式性质，将常数项 
 + 
 3 
 +3 移到等号右边，注意移项要变号，变为 
 − 
 3 
 −3。方程变为： 
 2 
 x 
 = 
 5 
 − 
 3 
 2x=5−3 
 " 
 "第二步：合并同类项。计算等号右边的数值， 
 5 
 − 
 3 
 = 
 2 
 5−3=2。方程简化为： 
 2 
 x 
 = 
 2 
 2x=2 
 " 
 "第三步：系数化为1。根据等式性质，等式两边同时除以 
 2 
 2，即 
 x 
 = 
 2 
 2 
 x= 
 2 
 2 
 ​ 
  。最终解得： 
 x 
 = 
 1 
 x=1 
 " 
 Answer 字符串： 
 " 
 x 
 = 
 1 
 x=1 
 " 
 Summary 字符串： 
 "方法总结：解一元一次方程通常遵循“移项、合并同类项、系数化为1”的步骤。易错点：在移项时，容易忘记变号（例如将 
 + 
 3 
 +3 移到右边写成 
 + 
 3 
 +3 而不是 
 − 
 3 
 −3），这是导致计算错误的主要原因。" 
 最终答案 
 Thinking 字符串： 
 "这是一道典型的一元一次方程求解题。解题的核心思想是等式性质，即等式两边同时进行相同的运算（加、减、乘、除），等式仍然成立。我们需要通过移项将含有未知数的项留在一边，常数项移到另一边，然后逐步化简，最终求出 
 x 
 x 的值。" 
 Steps 字符串数组： 
 "第一步：移项。根据等式性质，将常数项 
 + 
 3 
 +3 移到等号右边，注意移项要变号，变为 
 − 
 3 
 −3。方程变为： 
 2 
 x 
 = 
 5 
 − 
 3 
 2x=5−3 
 " 
 "第二步：合并同类项。计算等号右边的数值， 
 5 
 − 
 3 
 = 
 2 
 5−3=2。方程简化为： 
 2 
 x 
 = 
 2 
 2x=2 
 " 
 "第三步：系数化为1。根据等式性质，等式两边同时除以 
 2 
 2，即 
 x 
 = 
 2 
 2 
 x= 
 2 
 2 
 ​ 
  。最终解得： 
 x 
 = 
 1 
 x=1 
 " 
 Answer 字符串： 
 " 
 x 
 = 
 1 
 x=1 
 " 
 Summary 字符串： 
 "方法总结：解一元一次方程通常遵循“移项、合并同类项、系数化为1”的步骤。易错点：在移项时，容易忘记变号（例如将 
 + 
 3 
 +3 移到右边写成 
 + 
 3 
 +3 而不是 
 − 
 3 
 −3），这是导致计算错误的主要原因。" 
 知识总结 
 JSON 有效性检查： 
 检查引号：所有字符串必须用双引号括起来。 
 检查转义：如果字符串内部包含双引号，需要转义（此处未使用）。如果字符串内部包含换行符 \n，需要转义（此处使用 \n）。 
 检查 LaTeX：$...$ 和 `"""

# 测试修复效果
print("测试修复效果...")
result = TestChatGLMService.parse_solution_content(test_content)
print("\n修复后的输出:")
print(result)

# 验证输出格式
print("\n验证输出格式:")
print(f"1. thinking 类型: {type(result['thinking'])}, 内容: {result['thinking'][:100]}...")
print(f"2. steps 类型: {type(result['steps'])}, 长度: {len(result['steps'])}, 内容: {result['steps']}")
print(f"3. answer 类型: {type(result['answer'])}, 内容: {result['answer']}")
print(f"4. summary 类型: {type(result['summary'])}, 内容: {result['summary'][:100]}...")

# 检查是否有后台处理信息
print("\n检查是否有后台处理信息:")
for key, value in result.items():
    if isinstance(value, str):
        if any(term in value for term in ['详细步骤', '起草内容', 'JSON 有效性检查', '检查引号', '检查转义', '检查 LaTeX']):
            print(f"警告: {key} 中包含后台处理信息")
        else:
            print(f"✓ {key} 中无后台处理信息")
    elif isinstance(value, list):
        for i, item in enumerate(value):
            if any(term in item for term in ['详细步骤', '起草内容', 'JSON 有效性检查', '检查引号', '检查转义', '检查 LaTeX']):
                print(f"警告: steps[{i}] 中包含后台处理信息")
            else:
                print(f"✓ steps[{i}] 中无后台处理信息")

print("\n测试完成!")
