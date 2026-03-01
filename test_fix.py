#!/usr/bin/env python3
"""测试修复效果的脚本"""

import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.chatglm_service import chatglm_service

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
result = chatglm_service.parse_solution_content(test_content)
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
