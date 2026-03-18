from app.schemas.thinking import ThinkingExpandRequest, ThinkingExpandResponse
from app.services.json_utils import extract_json_object
from app.services.llm_client import generate_text


def run_thinking_skill(request: ThinkingExpandRequest) -> ThinkingExpandResponse:
    idea = request.idea.strip() or "未提供想法。"
    style_note = request.rewrite_style or "默认"
    prompt = (
        "你是克制的写作与复盘助手。请只返回 JSON 对象，键包括："
        "title（字符串）、outline（数组）、content（字符串）、rewrite_options（数组）、"
        "key_points（数组）、tone_tags（数组）、export_title（字符串）、"
        "summary（字符串）、confidence_note（字符串）、reflection_prompt（字符串）、"
        "review_bridge（数组）、action_list（数组）。"
        "所有文本字段使用中文，不要输出其他内容。"
    )
    llm_text, llm_error = generate_text(
        prompt,
        (
            f"想法：{idea}\n模式：{request.mode}\n风格偏好：{style_note}\n"
            "要求：给用户整理思路、生成内容、收束成下一步行动。"
            "confidence_note 要给人信心，但不要鸡汤，不要喊口号。"
            "review_bridge 要把当前内容连接回复习或表达实践。"
        ),
    )
    parsed = extract_json_object(llm_text or "")

    content = parsed.get("content") if parsed else None
    content = content or llm_text or (
        f"思考技能占位输出：{idea}。"
        "下一步是接入风格控制与 LLM 草稿生成。"
    )
    if llm_error and llm_error != "demo_mode":
        content = f"{content}\n\n（LLM 调用状态：{llm_error}）"

    if not parsed:
        if request.mode == "outline":
            content = "大纲模式：优先输出条目式结构，不展开长段落。"
        elif request.mode == "review":
            content = "复盘模式：先总结今天学到了什么，再落成明天最小可执行任务。"
        elif request.mode == "script":
            content = "脚本模式：用镜头/对白的短句组织内容。"
        elif request.mode == "reflection":
            content = "反思模式：写清原因-感受-行动。"

    return ThinkingExpandResponse(
        mode=request.mode,
        title=parsed.get("title", "由一句话扩展出的草稿") if parsed else "由一句话扩展出的草稿",
        outline=parsed.get(
            "outline",
            [
                "清楚陈述原始想法。",
                "展开其中的矛盾或问题。",
                "以落地结论收束。",
            ],
        )
        if parsed
        else [
            "清楚陈述原始想法。",
            "展开其中的矛盾或问题。",
            "以落地结论收束。",
        ],
        content=content,
        rewrite_options=parsed.get("rewrite_options", ["更克制", "更直接", "短视频脚本"])
        if parsed
        else ["更克制", "更直接", "短视频脚本"],
        key_points=parsed.get("key_points", ["一句话总结观点", "补充一个例子", "落地一句行动"])
        if parsed
        else ["一句话总结观点", "补充一个例子", "落地一句行动"],
        tone_tags=parsed.get("tone_tags", ["克制", "清晰", "不煽动"])
        if parsed
        else ["克制", "清晰", "不煽动"],
        export_title=parsed.get("export_title", "examnova-thinking.txt") if parsed else "examnova-thinking.txt",
        summary=parsed.get("summary", "一句话总结：将想法转为可执行的行动。")
        if parsed
        else "一句话总结：将想法转为可执行的行动。",
        confidence_note=parsed.get(
            "confidence_note",
            "先把这一段写清楚，再把下一步缩到 15 分钟内，你就已经在推进了。",
        )
        if parsed
        else "先把这一段写清楚，再把下一步缩到 15 分钟内，你就已经在推进了。",
        reflection_prompt=parsed.get("reflection_prompt", "这段内容最值得你明天继续推进的部分是什么？")
        if parsed
        else "这段内容最值得你明天继续推进的部分是什么？",
        review_bridge=parsed.get(
            "review_bridge",
            ["把正文压缩成 3 个关键词", "写下明天要复习或续写的 1 个切口", "给自己留一个可验证的小目标"],
        )
        if parsed
        else ["把正文压缩成 3 个关键词", "写下明天要复习或续写的 1 个切口", "给自己留一个可验证的小目标"],
        action_list=parsed.get("action_list", ["写下 3 个关键点", "补充 1 个例子", "把结论落成一句话"])
        if parsed
        else ["写下 3 个关键点", "补充 1 个例子", "把结论落成一句话"],
    )
