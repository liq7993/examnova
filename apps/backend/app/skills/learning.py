from __future__ import annotations

import math
import re

from app.schemas.study import StudyAnalyzeRequest, StudyAnalyzeResponse
from app.services.json_utils import extract_json_object
from app.services.llm_client import generate_text


def _shorten(text: str, limit: int = 18) -> str:
    cleaned = "".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1] + "..."


def _format_num(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def _ensure_text_list(value: object, fallback: list[str]) -> list[str]:
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return items or fallback
    if isinstance(value, dict):
        items = [f"{key}: {val}".strip() for key, val in value.items() if f"{key}{val}".strip()]
        return items or fallback
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return fallback
        parts = [part.strip(" -*\n\r\t") for part in re.split(r"[\n;；]+", text) if part.strip(" -*\n\r\t")]
        return parts or [text]
    return fallback


def _ensure_text(value: object, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _infer_topic(text: str, course: str) -> tuple[str, str]:
    combined = f"{course} {text}".lower()
    if any(
        keyword in combined
        for keyword in [
            "\u4e09\u76f8",
            "\u7535\u8def",
            "\u7535\u538b",
            "\u7535\u6d41",
            "\u76f8\u91cf",
            "\u529f\u7387\u56e0\u6570",
            "\u661f\u5f62",
            "\u4e09\u89d2\u5f62",
        ]
    ):
        return ("electrical", "\u4e09\u76f8\u7535\u8def")
    if any(
        keyword in combined
        for keyword in [
            "\u5706\u5468",
            "\u5411\u5fc3",
            "\u8f6c\u52a8\u60ef\u91cf",
            "\u89d2\u52a0\u901f\u5ea6",
            "\u5f39\u7c27",
            "\u632f\u5b50",
            "\u7b80\u8c10",
            "\u7406\u8bba\u529b\u5b66",
            "\u5927\u5b66\u7269\u7406",
        ]
    ):
        return ("physics", "\u5927\u5b66\u7269\u7406")
    if any(
        keyword in combined
        for keyword in [
            "\u659c\u9762",
            "\u6469\u64e6\u56e0\u6570",
            "\u521d\u901f\u5ea6",
            "\u53d7\u529b\u5206\u6790",
            "\u5c0f\u7403",
            "\u7269\u7406",
            "\u4f4d\u79fb",
            "\u52a0\u901f\u5ea6",
        ]
    ):
        return ("physics", "\u659c\u9762\u8fd0\u52a8")
    if any(
        keyword in combined
        for keyword in [
            "\u673a\u68b0",
            "\u8f74",
            "\u9f7f\u8f6e",
            "\u4f20\u52a8",
            "\u76ae\u5e26",
            "\u5e26\u4f20\u52a8",
            "\u7b80\u652f\u6881",
            "\u6881",
            "\u5f2f\u77e9",
            "\u626d\u77e9",
            "\u8f6c\u77e9",
            "\u529f\u7387",
            "\u8f6c\u901f",
            "\u652f\u5ea7\u53cd\u529b",
            "\u5f39\u7c27",
            "\u5706\u5468",
            "\u62c9\u6746",
            "\u5f39\u6027\u6a21\u91cf",
            "\u8f6c\u52a8\u60ef\u91cf",
            "\u89d2\u52a0\u901f\u5ea6",
            "\u7b80\u8c10",
            "\u5411\u5fc3",
            "\u526a\u5e94\u529b",
        ]
    ):
        return ("mechanical", "\u673a\u68b0\u57fa\u7840")
    if any(
        keyword in combined
        for keyword in [
            "\u6781\u9650",
            "\u5bfc\u6570",
            "\u79ef\u5206",
            "\u51fd\u6570",
            "\u9ad8\u6570",
            "\u5fae\u5206",
            "\u6cf0\u52d2",
            "\u6d1b\u5fc5\u8fbe",
        ]
    ):
        return ("calculus", "\u9ad8\u7b49\u6570\u5b66")
    if any(keyword in combined for keyword in ["\u5199\u4f5c", "\u968f\u7b14", "\u4f5c\u6587", "\u53cd\u601d", "\u8868\u8fbe"]):
        return ("writing", "\u5199\u4f5c\u8868\u8fbe")
    topic = _shorten(text, limit=10)
    return ("generic", topic or course or "\u5f53\u524d\u9898\u76ee")


def _base_review_blocks() -> dict[str, list[str]]:
    return {
        "review_schedule": [
            "10 \u5206\u949f\u540e\u56de\u770b\u4e00\u6b21",
            "30 \u5206\u949f\u540e\u62bd\u95ee\u4e00\u6b21",
            "12 \u5c0f\u65f6\u540e\u518d\u56de\u987e",
            "24 \u5c0f\u65f6\u540e\u518d\u5f3a\u5316",
        ],
        "time_plan": [
            "10 \u5206\u949f\u7406\u89e3\u9898\u76ee",
            "15 \u5206\u949f\u8ddf\u6b65\u9aa4\u505a\u4e00\u904d",
            "10 \u5206\u949f\u505a\u540c\u7c7b\u578b\u9898",
            "5 \u5206\u949f\u56de\u770b\u6613\u9519\u70b9",
        ],
    }


def _generic_fallback(topic_label: str) -> dict[str, object]:
    review = _base_review_blocks()
    return {
        "knowledge_points": [topic_label, "\u9898\u5e72\u5173\u952e\u4fe1\u606f", "\u89e3\u9898\u76ee\u6807"],
        "difficulty": "\u4e2d",
        "explanation": "\u5148\u628a\u9898\u76ee\u4e2d\u7684\u5df2\u77e5\u3001\u672a\u77e5\u548c\u76ee\u6807\u5199\u6e05\u695a\uff0c\u518d\u51b3\u5b9a\u7528\u54ea\u4e00\u79cd\u65b9\u6cd5\u3002",
        "solution_steps": [
            "\u5148\u63d0\u53d6\u9898\u76ee\u5df2\u77e5\u6761\u4ef6\u3001\u9650\u5236\u548c\u8981\u6c42\u8f93\u51fa\u7684\u7ed3\u679c\u3002",
            "\u5224\u65ad\u5c5e\u4e8e\u54ea\u4e00\u7c7b\u77e5\u8bc6\u70b9\uff0c\u518d\u9009\u5bf9\u5e94\u65b9\u6cd5\u3002",
            "\u6309\u9898\u5e72\u987a\u5e8f\u5199\u6e05\u6b65\u9aa4\uff0c\u907f\u514d\u8df3\u6b65\u3002",
            "\u6700\u540e\u68c0\u67e5\u7ed3\u8bba\u662f\u5426\u56de\u7b54\u4e86\u539f\u95ee\u9898\u3002",
        ],
        "formula_notes": [
            "\u5148\u5217\u5df2\u77e5\u4e0e\u672a\u77e5\uff0c\u518d\u5199\u5173\u7cfb\u5f0f\u3002",
            "\u5982\u679c\u9898\u76ee\u590d\u6742\uff0c\u5c31\u5148\u62c6\u6210\u4e24\u4e2a\u5c0f\u95ee\u9898\u5206\u522b\u5904\u7406\u3002",
        ],
        "novice_explain": "\u5148\u770b\u9898\u76ee\u5230\u5e95\u8981\u4f60\u6c42\u4ec0\u4e48\uff0c\u518d\u628a\u80fd\u7528\u7684\u4fe1\u606f\u4e00\u6761\u6761\u63a5\u8d77\u6765\u3002",
        "memory_tips": [
            "\u5df2\u77e5-\u76ee\u6807-\u65b9\u6cd5\u4e09\u680f\u7b14\u8bb0",
            "\u5148\u5217\u5173\u7cfb\u518d\u8ba1\u7b97",
            "\u5148\u7b54\u6838\u5fc3\u95ee\u9898\u518d\u8865\u7ec6\u8282",
        ],
        "exam_tricks": [
            "\u5148\u5708\u5173\u952e\u8bcd",
            "\u5148\u505a\u6700\u786e\u5b9a\u7684\u4e00\u6b65",
            "\u7b54\u6848\u6700\u540e\u56de\u5230\u9898\u76ee\u95ee\u6cd5",
        ],
        "diagram_hint": "\u5982\u679c\u9898\u76ee\u5173\u7cfb\u590d\u6742\uff0c\u53ef\u4ee5\u5148\u753b\u7ed3\u6784\u56fe\u3001\u6d41\u7a0b\u56fe\u6216\u5173\u7cfb\u56fe\u3002",
        "variant_questions": [
            "\u628a\u4e00\u4e2a\u5df2\u77e5\u91cf\u6362\u6210\u65b0\u7684\u6570\u503c\u540e\u91cd\u505a",
            "\u628a\u63d0\u95ee\u65b9\u5f0f\u6539\u6210\u89e3\u91ca\u578b\u540e\u91cd\u505a",
            "\u5220\u53bb\u4e00\u4e2a\u6761\u4ef6\u540e\u5224\u65ad\u8fd8\u80fd\u5426\u6c42\u89e3",
        ],
        "mini_quiz": [
            "\u8fd9\u9898\u771f\u6b63\u8981\u6c42\u7684\u7ed3\u679c\u662f\u4ec0\u4e48\uff1f",
            "\u6700\u5173\u952e\u7684\u5df2\u77e5\u6761\u4ef6\u662f\u4ec0\u4e48\uff1f",
            "\u54ea\u4e00\u6b65\u6700\u5bb9\u6613\u51fa\u9519\uff1f",
        ],
        "self_questions": [
            "\u6211\u5df2\u7ecf\u628a\u5df2\u77e5\u548c\u672a\u77e5\u5206\u5f00\u4e86\u5417\uff1f",
            "\u73b0\u5728\u54ea\u4e00\u6b65\u662f\u5728\u771f\u6b63\u63a8\u8fdb\u7ed3\u679c\uff1f",
            "\u5982\u679c\u6362\u4e00\u4e2a\u6761\u4ef6\uff0c\u539f\u65b9\u6cd5\u8fd8\u6210\u7acb\u5417\uff1f",
        ],
        "practice_set": [
            "\u5c0f\u5377\u9898 1\uff1a\u57fa\u7840\u540c\u578b\u9898",
            "\u5c0f\u5377\u9898 2\uff1a\u6761\u4ef6\u53d8\u5316\u9898",
            "\u5c0f\u5377\u9898 3\uff1a\u7efc\u5408\u5224\u65ad\u9898",
        ],
        "examples": [
            "\u4f8b\u9898 1\uff1a\u540c\u4e3b\u9898\u57fa\u7840\u9898",
            "\u4f8b\u9898 2\uff1a\u591a\u4e00\u6b65\u53d8\u5f62\u7684\u9898",
            "\u4f8b\u9898 3\uff1a\u8981\u6c42\u89e3\u91ca\u8fc7\u7a0b\u7684\u9898",
        ],
        "exam_focus_prediction": [
            "\u5df2\u77e5\u6761\u4ef6\u63d0\u53d6",
            "\u6b65\u9aa4\u5b8c\u6574\u6027",
            "\u7ed3\u679c\u56de\u5230\u539f\u95ee\u9898",
        ],
        "next_action": "\u5148\u628a\u9898\u76ee\u62c6\u6210\u5df2\u77e5\u3001\u672a\u77e5\u3001\u65b9\u6cd5\u4e09\u680f\uff0c\u518d\u8865\u505a\u4e00\u9053\u540c\u7c7b\u9898\u3002",
        "confidence_note": "\u5148\u628a\u95ee\u9898\u7ed3\u6784\u770b\u6e05\u695a\uff0c\u901a\u5e38\u5c31\u5df2\u7ecf\u8d70\u5b8c\u6700\u96be\u7684\u4e00\u534a\u4e86\u3002",
        "score_breakdown": [
            "\u6b65\u9aa4 1\uff1a\u8bc6\u522b\u9898\u76ee\u7ed3\u6784 2 \u5206",
            "\u6b65\u9aa4 2\uff1a\u5217\u51fa\u5173\u952e\u5173\u7cfb 3 \u5206",
            "\u6b65\u9aa4 3\uff1a\u63a8\u5bfc\u6216\u8ba1\u7b97 3 \u5206",
            "\u6b65\u9aa4 4\uff1a\u56de\u7b54\u539f\u95ee\u9898 2 \u5206",
        ],
        **review,
    }


def _template_payload(
    *,
    knowledge_points: list[str],
    explanation: str,
    solution_steps: list[str],
    formula_notes: list[str],
    novice_explain: str,
    memory_tips: list[str],
    exam_tricks: list[str],
    diagram_hint: str,
    variant_questions: list[str],
    mini_quiz: list[str],
    self_questions: list[str],
    practice_set: list[str],
    examples: list[str],
    exam_focus_prediction: list[str],
    next_action: str,
    confidence_note: str,
    score_breakdown: list[str],
    difficulty: str = "\u4e2d",
) -> dict[str, object]:
    review = _base_review_blocks()
    return {
        "knowledge_points": knowledge_points,
        "difficulty": difficulty,
        "explanation": explanation,
        "solution_steps": solution_steps,
        "formula_notes": formula_notes,
        "novice_explain": novice_explain,
        "memory_tips": memory_tips,
        "exam_tricks": exam_tricks,
        "diagram_hint": diagram_hint,
        "variant_questions": variant_questions,
        "mini_quiz": mini_quiz,
        "self_questions": self_questions,
        "practice_set": practice_set,
        "examples": examples,
        "exam_focus_prediction": exam_focus_prediction,
        "next_action": next_action,
        "confidence_note": confidence_note,
        "score_breakdown": score_breakdown,
        **review,
    }


def _solve_three_phase_star(text: str) -> dict[str, object] | None:
    line_voltage_match = re.search(r"\u7ebf\u7535\u538b(?:\u4e3a|=)?\s*([0-9]+(?:\.[0-9]+)?)\s*V", text, re.IGNORECASE)
    impedance_match = re.search(
        r"(?:\u6bcf\u76f8\u963b\u6297|\u76f8\u963b\u6297|Z)\s*(?:\u4e3a|=)?\s*([+-]?\d+(?:\.\d+)?)\s*([+-])\s*j\s*([0-9]+(?:\.\d+)?)",
        text,
        re.IGNORECASE,
    )
    if "\u661f\u5f62" not in text or not line_voltage_match or not impedance_match:
        return None

    line_voltage = float(line_voltage_match.group(1))
    r_value = float(impedance_match.group(1))
    sign = 1 if impedance_match.group(2) == "+" else -1
    x_value = sign * float(impedance_match.group(3))

    phase_voltage = line_voltage / math.sqrt(3)
    impedance_abs = math.sqrt(r_value**2 + x_value**2)
    current = phase_voltage / impedance_abs
    cos_phi = r_value / impedance_abs if impedance_abs else 0.0
    phi_deg = math.degrees(math.atan2(x_value, r_value)) if impedance_abs else 0.0
    total_active_power = math.sqrt(3) * line_voltage * current * cos_phi

    line_voltage_text = _format_num(line_voltage, 0)
    phase_voltage_text = _format_num(phase_voltage)
    impedance_abs_text = _format_num(impedance_abs)
    current_text = _format_num(current)
    cos_phi_text = _format_num(cos_phi)
    phi_text = _format_num(phi_deg)
    total_power_text = _format_num(total_active_power / 1000)

    review = _base_review_blocks()
    return {
        "knowledge_points": [
            "\u4e09\u76f8\u7535\u8def",
            "\u661f\u5f62\u8fde\u63a5",
            "\u7ebf\u7535\u538b\u4e0e\u76f8\u7535\u538b\u5173\u7cfb",
            "\u4e09\u76f8\u529f\u7387\u8ba1\u7b97",
        ],
        "difficulty": "\u4e2d",
        "explanation": "\u8fd9\u9898\u662f\u5bf9\u79f0\u4e09\u76f8\u661f\u5f62\u8d1f\u8f7d\u3002\u5148\u628a\u7ebf\u7535\u538b\u6362\u6210\u76f8\u7535\u538b $U_{ph}=U_L/\\sqrt{3}$\uff0c\u518d\u7531\u963b\u6297\u6a21 $|Z|=\\sqrt{R^2+X^2}$ \u6c42\u76f8\u7535\u6d41\uff0c\u6700\u540e\u7528\u4e09\u76f8\u6709\u529f\u529f\u7387\u516c\u5f0f $P=\\sqrt{3}U_LI_L\\cos\\varphi$ \u6c42\u603b\u6709\u529f\u529f\u7387\u3002",
        "solution_steps": [
            f"\u5df2\u77e5\u7ebf\u7535\u538b $U_L={line_voltage_text}\\,V$\uff0c\u661f\u5f62\u8fde\u63a5\u4e0b\u76f8\u7535\u538b $U_{{ph}}=U_L/\\sqrt{{3}}={phase_voltage_text}\\,V$\u3002",
            f"\u6bcf\u76f8\u963b\u6297 $Z={r_value:g}{'+' if x_value >= 0 else '-'}j{abs(x_value):g}\\,\\Omega$\uff0c\u963b\u6297\u6a21 $|Z|=\\sqrt{{{r_value:g}^2+{abs(x_value):g}^2}}={impedance_abs_text}\\,\\Omega$\u3002",
            f"\u76f8\u7535\u6d41 $I_{{ph}}=U_{{ph}}/|Z|={phase_voltage_text}/{impedance_abs_text}={current_text}\\,A$\u3002",
            f"\u661f\u5f62\u8fde\u63a5\u4e0b\u7ebf\u7535\u6d41 $I_L=I_{{ph}}={current_text}\\,A$\u3002",
            f"\u529f\u7387\u56e0\u6570 $\\cos\\varphi=R/|Z|={r_value:g}/{impedance_abs_text}={cos_phi_text}$\uff0c\u76f8\u89d2\u7ea6\u4e3a ${phi_text}^\\circ$\u3002",
            f"\u603b\u6709\u529f\u529f\u7387 $P=\\sqrt{{3}}U_LI_L\\cos\\varphi=\\sqrt{{3}}\\times{line_voltage_text}\\times{current_text}\\times{cos_phi_text}\\approx{total_power_text}\\,kW$\u3002",
        ],
        "formula_notes": [
            f"\u76f8\u7535\u538b\uff1a$U_{{ph}}=U_L/\\sqrt{{3}}={phase_voltage_text}\\,V$",
            f"\u963b\u6297\u6a21\uff1a$|Z|=\\sqrt{{R^2+X^2}}={impedance_abs_text}\\,\\Omega$",
            f"\u76f8\u7535\u6d41\uff1a$I_{{ph}}=U_{{ph}}/|Z|={current_text}\\,A$",
            f"\u7ebf\u7535\u6d41\uff1a$I_L=I_{{ph}}={current_text}\\,A$",
            f"\u529f\u7387\u56e0\u6570\uff1a$\\cos\\varphi=R/|Z|={cos_phi_text}$",
            f"\u603b\u6709\u529f\u529f\u7387\uff1a$P=\\sqrt{{3}}U_LI_L\\cos\\varphi\\approx{total_power_text}\\,kW$",
        ],
        "novice_explain": "\u770b\u5230\u661f\u5f62\u8fde\u63a5\u5148\u60f3\u5230 $U_{ph}=U_L/\\sqrt{3}$\uff0c\u518d\u7528 $I=U/|Z|$ \u6c42\u7535\u6d41\uff0c\u6700\u540e\u56de\u5230 $P=\\sqrt{3}UI\\cos\\varphi$\u3002",
        "memory_tips": ["\u5148\u5206\u6e05\u7ebf\u91cf\u548c\u76f8\u91cf", "\u770b\u5230\u590d\u963b\u6297\u5148\u6c42\u6a21", "\u529f\u7387\u9898\u6700\u540e\u56de\u5230 P=\u221a3UIcos\u03c6"],
        "exam_tricks": ["\u5148\u5199\u661f\u5f62\u8fde\u63a5\u5173\u7cfb", "\u5148\u6c42\u963b\u6297\u6a21\u518d\u7b97\u7535\u6d41", "\u529f\u7387\u56e0\u6570\u76f4\u63a5\u770b R/|Z|"],
        "diagram_hint": "\u56fe\u89e3\u5efa\u8bae\uff1a\u753b\u51fa\u5bf9\u79f0\u4e09\u76f8\u661f\u5f62\u8fde\u63a5\uff0c\u6807\u6ce8 U_L\u3001U_ph\u3001\u6bcf\u76f8\u963b\u6297 Z \u548c\u7535\u6d41\u65b9\u5411\u3002",
        "variant_questions": [
            "\u628a\u661f\u5f62\u8fde\u63a5\u6539\u6210\u4e09\u89d2\u5f62\u8fde\u63a5\u540e\u91cd\u505a",
            "\u628a\u963b\u6297\u6539\u6210 6+j8\u03a9 \u540e\u91cd\u65b0\u8ba1\u7b97",
            "\u5df2\u77e5\u603b\u6709\u529f\u529f\u7387\u548c\u529f\u7387\u56e0\u6570\u65f6\u53cd\u6c42\u7ebf\u7535\u6d41",
        ],
        "mini_quiz": [
            "\u4e3a\u4ec0\u4e48\u661f\u5f62\u8fde\u63a5\u4e0b\u7ebf\u7535\u6d41\u7b49\u4e8e\u76f8\u7535\u6d41\uff1f",
            "\u4e3a\u4ec0\u4e48\u529f\u7387\u56e0\u6570\u53ef\u4ee5\u5199\u6210 R/|Z|\uff1f",
            "\u5982\u679c\u6539\u6210\u4e09\u89d2\u5f62\u8fde\u63a5\uff0c\u76f8\u7535\u538b\u600e\u4e48\u53d8\uff1f",
        ],
        "self_questions": [
            "\u6211\u6709\u6ca1\u6709\u5148\u628a\u7ebf\u91cf\u548c\u76f8\u91cf\u5206\u6e05\uff1f",
            "\u963b\u6297\u6a21\u8fd9\u4e00\u6b65\u6709\u6ca1\u6709\u7b97\u9519\uff1f",
            "\u6700\u7ec8\u7ed3\u679c\u5355\u4f4d\u6709\u6ca1\u6709\u5199\u6210 kW\uff1f",
        ],
        "practice_set": [
            "\u5c0f\u5377\u9898 1\uff1a\u5df2\u77e5 U_L \u548c Z \u6c42 I_L",
            "\u5c0f\u5377\u9898 2\uff1a\u5df2\u77e5 I \u548c cos\u03c6 \u6c42 P",
            "\u5c0f\u5377\u9898 3\uff1a\u6bd4\u8f83\u661f\u5f62\u4e0e\u4e09\u89d2\u5f62\u8fde\u63a5",
        ],
        "examples": [
            "\u4f8b\u9898 1\uff1a\u5bf9\u79f0\u661f\u5f62\u8d1f\u8f7d\u6c42\u7ebf\u7535\u6d41",
            "\u4f8b\u9898 2\uff1a\u5df2\u77e5\u7535\u6d41\u548c\u529f\u7387\u56e0\u6570\u6c42\u4e09\u76f8\u6709\u529f\u529f\u7387",
            "\u4f8b\u9898 3\uff1a\u7531\u76f8\u7535\u538b\u53cd\u63a8\u7ebf\u7535\u538b",
        ],
        "exam_focus_prediction": ["\u661f\u5f62\u8fde\u63a5\u516c\u5f0f", "\u963b\u6297\u6a21\u8ba1\u7b97", "\u4e09\u76f8\u6709\u529f\u529f\u7387\u516c\u5f0f"],
        "next_action": "\u628a\u8fd9\u9898\u4e2d\u7684\u7ebf\u91cf\u3001\u76f8\u91cf\u3001\u529f\u7387\u91cf\u5206\u680f\u5199\u51fa\u6765\uff0c\u518d\u505a\u4e00\u9053\u540c\u7c7b\u578b\u4e09\u76f8\u9898\u3002",
        "confidence_note": "\u8fd9\u7c7b\u9898\u5173\u952e\u4e0d\u662f\u96be\uff0c\u800c\u662f\u5148\u628a\u7ebf\u91cf\u548c\u76f8\u91cf\u5206\u6e05\u3002",
        "score_breakdown": [
            "\u6b65\u9aa4 1\uff1a\u8bc6\u522b\u661f\u5f62\u8fde\u63a5 2 \u5206",
            "\u6b65\u9aa4 2\uff1a\u7ebf\u7535\u538b\u8f6c\u76f8\u7535\u538b 2 \u5206",
            "\u6b65\u9aa4 3\uff1a\u6c42\u7535\u6d41\u4e0e\u529f\u7387\u56e0\u6570 3 \u5206",
            "\u6b65\u9aa4 4\uff1a\u6c42\u603b\u6709\u529f\u529f\u7387\u5e76\u5199\u7ed3\u8bba 3 \u5206",
        ],
        **review,
    }


def _solve_incline_motion(text: str) -> dict[str, object] | None:
    combined = text.replace(" ", "")
    required = ["\u659c\u9762", "\u6469\u64e6\u56e0\u6570", "\u521d\u901f\u5ea6", "\u6700\u9ad8\u70b9"]
    if not all(keyword in combined for keyword in required):
        return None

    review = _base_review_blocks()
    return {
        "knowledge_points": [
            "\u659c\u9762\u53d7\u529b\u5206\u6790",
            "\u725b\u987f\u7b2c\u4e8c\u5b9a\u5f8b",
            "\u5300\u53d8\u901f\u76f4\u7ebf\u8fd0\u52a8",
            "\u52a8\u6469\u64e6\u529b\u65b9\u5411\u5224\u65ad",
        ],
        "difficulty": "\u4e2d",
        "explanation": "\u5c0f\u7403\u6cbf\u659c\u9762\u5411\u4e0a\u8fd0\u52a8\u65f6\uff0c\u6cbf\u659c\u9762\u5411\u4e0b\u7684\u529b\u6709\u4e24\u4e2a\uff1a\u91cd\u529b\u5206\u529b $mg\\sin\\theta$ \u548c\u52a8\u6469\u64e6\u529b $\\mu mg\\cos\\theta$\u3002\u56e0\u6b64\u5408\u52a0\u901f\u5ea6\u59cb\u7ec8\u6cbf\u659c\u9762\u5411\u4e0b\uff0c\u5927\u5c0f\u4e3a $g(\\sin\\theta+\\mu\\cos\\theta)$\u3002",
        "solution_steps": [
            "\u5148\u753b\u53d7\u529b\u56fe\uff1a\u91cd\u529b $mg$ \u7ad6\u76f4\u5411\u4e0b\uff0c\u652f\u6301\u529b $N$ \u5782\u76f4\u659c\u9762\u5411\u5916\uff0c\u52a8\u6469\u64e6\u529b $f$ \u6cbf\u659c\u9762\u5411\u4e0b\uff0c\u56e0\u4e3a\u5c0f\u7403\u5f53\u524d\u6cbf\u659c\u9762\u5411\u4e0a\u6ed1\u3002",
            "\u5782\u76f4\u659c\u9762\u65b9\u5411\u5e73\u8861\uff0c\u5f97 $N=mg\\cos\\theta$\uff0c\u6240\u4ee5 $f=\\mu N=\\mu mg\\cos\\theta$\u3002",
            "\u6cbf\u659c\u9762\u5411\u4e0a\u53d6\u6b63\u65b9\u5411\uff0c\u5219 $ma=-mg\\sin\\theta-\\mu mg\\cos\\theta$\u3002",
            "\u5316\u7b80\u5f97 $a=-g(\\sin\\theta+\\mu\\cos\\theta)$\uff0c\u8fd9\u662f\u4e00\u4e2a\u5300\u51cf\u901f\u8fc7\u7a0b\u3002",
            "\u5230\u6700\u9ad8\u70b9\u65f6 $v=0$\uff0c\u7531 $v=v_0+at$ \u5f97 $t=\\dfrac{v_0}{g(\\sin\\theta+\\mu\\cos\\theta)}$\u3002",
            "\u518d\u7531 $v^2-v_0^2=2as$\uff0c\u4ee3\u5165 $v=0$ \u4e0e $a=-g(\\sin\\theta+\\mu\\cos\\theta)$\uff0c\u5f97 $s=\\dfrac{v_0^2}{2g(\\sin\\theta+\\mu\\cos\\theta)}$\u3002",
        ],
        "formula_notes": [
            "$N=mg\\cos\\theta$",
            "$f=\\mu N=\\mu mg\\cos\\theta$",
            "$ma=-mg\\sin\\theta-\\mu mg\\cos\\theta$",
            "$a=-g(\\sin\\theta+\\mu\\cos\\theta)$",
            "$t=\\dfrac{v_0}{g(\\sin\\theta+\\mu\\cos\\theta)}$",
            "$s=\\dfrac{v_0^2}{2g(\\sin\\theta+\\mu\\cos\\theta)}$",
        ],
        "novice_explain": "\u5173\u952e\u5148\u522b\u5957\u516c\u5f0f\uff0c\u5148\u5224\u65ad\u6469\u64e6\u529b\u65b9\u5411\u3002\u5c0f\u7403\u5411\u4e0a\u6ed1\uff0c\u6240\u4ee5\u6469\u64e6\u529b\u4e00\u5b9a\u5411\u4e0b\u3002\u53d7\u529b\u4e00\u6e05\u695a\uff0c\u518d\u5199 $a=-g(\\sin\\theta+\\mu\\cos\\theta)$\uff0c\u540e\u9762\u5c31\u662f\u6807\u51c6\u5300\u51cf\u901f\u3002",
        "memory_tips": [
            "\u6469\u64e6\u529b\u603b\u662f\u53cd\u7740\u8fd0\u52a8\u65b9\u5411",
            "\u5148\u5199 N=mgcos\u03b8 \u518d\u5199 f=\u03bcN",
            "\u6700\u9ad8\u70b9\u7edf\u4e00\u4f7f\u7528 v=0",
        ],
        "exam_tricks": [
            "\u5148\u753b\u53d7\u529b\u56fe\u518d\u5217\u65b9\u7a0b",
            "\u6cbf\u659c\u9762\u53d6\u8f74\u6700\u7701\u4e8b",
            "\u65f6\u95f4\u9898\u5148\u7528 v=v0+at",
        ],
        "diagram_hint": "\u56fe\u89e3\u5efa\u8bae\uff1a\u753b\u4e00\u5757\u503e\u89d2\u4e3a \u03b8 \u7684\u659c\u9762\uff0c\u5c0f\u7403\u5728\u659c\u9762\u4e0a\uff0c\u6807\u51fa mg \u7ad6\u76f4\u5411\u4e0b\u3001N \u5782\u76f4\u659c\u9762\u5411\u5916\u3001f \u6cbf\u659c\u9762\u5411\u4e0b\uff0c\u5e76\u628a\u91cd\u529b\u5206\u89e3\u6210 mgsin\u03b8 \u4e0e mgcos\u03b8\u3002",
        "variant_questions": [
            "\u82e5\u5c0f\u7403\u6539\u4e3a\u6cbf\u659c\u9762\u4e0b\u6ed1\uff0c\u6469\u64e6\u529b\u65b9\u5411\u548c\u52a0\u901f\u5ea6\u600e\u4e48\u53d8\uff1f",
            "\u82e5\u5df2\u77e5\u6700\u5927\u4f4d\u79fb\uff0c\u53cd\u6c42\u521d\u901f\u5ea6 v0",
            "\u82e5\u659c\u9762\u5149\u6ed1\u5373 \u03bc=0\uff0c\u7ed3\u679c\u5982\u4f55\u7b80\u5316\uff1f",
        ],
        "mini_quiz": [
            "\u4e3a\u4ec0\u4e48\u6469\u64e6\u529b\u662f\u6cbf\u659c\u9762\u5411\u4e0b\uff1f",
            "\u4e3a\u4ec0\u4e48\u652f\u6301\u529b\u53ef\u4ee5\u5199\u6210 N=mgcos\u03b8\uff1f",
            "\u6700\u9ad8\u70b9\u65f6\u54ea\u4e2a\u7269\u7406\u91cf\u7b49\u4e8e 0\uff1f",
        ],
        "self_questions": [
            "\u6211\u6709\u6ca1\u6709\u5148\u5224\u65ad\u8fd0\u52a8\u65b9\u5411\uff1f",
            "\u6cbf\u659c\u9762\u65b9\u5411\u7684\u6b63\u8d1f\u53f7\u6709\u6ca1\u6709\u5199\u5bf9\uff1f",
            "\u6700\u540e\u7684\u65f6\u95f4\u548c\u4f4d\u79fb\u516c\u5f0f\u662f\u4e0d\u662f\u7b26\u5408\u7269\u7406\u610f\u4e49\uff1f",
        ],
        "practice_set": [
            "\u5c0f\u5377\u9898 1\uff1a\u5149\u6ed1\u659c\u9762\u4e0a\u62db\u9898",
            "\u5c0f\u5377\u9898 2\uff1a\u5e26\u6469\u64e6\u659c\u9762\u4f4d\u79fb\u9898",
            "\u5c0f\u5377\u9898 3\uff1a\u53d7\u529b\u56fe\u4e0e\u8fd0\u52a8\u65b9\u7a0b\u7ed3\u5408\u9898",
        ],
        "examples": [
            "\u4f8b\u9898 1\uff1a\u6cbf\u659c\u9762\u4e0a\u6ed1\u6c42\u505c\u4e0b\u6240\u9700\u65f6\u95f4",
            "\u4f8b\u9898 2\uff1a\u659c\u9762\u4e0a\u6ed1\u6c42\u6700\u5927\u4f4d\u79fb",
            "\u4f8b\u9898 3\uff1a\u753b\u53d7\u529b\u5206\u6790\u56fe\u5e76\u89e3\u91ca\u5404\u529b\u65b9\u5411",
        ],
        "exam_focus_prediction": [
            "\u6469\u64e6\u529b\u65b9\u5411\u5224\u65ad",
            "\u6cbf\u659c\u9762\u5217\u725b\u987f\u7b2c\u4e8c\u5b9a\u5f8b",
            "\u5300\u51cf\u901f\u516c\u5f0f\u4ee3\u5165 v=0",
        ],
        "next_action": "\u5148\u81ea\u5df1\u4e0d\u770b\u7b54\u6848\u91cd\u753b\u4e00\u904d\u53d7\u529b\u56fe\uff0c\u518d\u628a\u65f6\u95f4\u516c\u5f0f\u548c\u4f4d\u79fb\u516c\u5f0f\u72ec\u7acb\u63a8\u4e00\u904d\u3002",
        "confidence_note": "\u8fd9\u9898\u771f\u6b63\u7684\u6293\u624b\u662f\u5148\u628a\u53d7\u529b\u65b9\u5411\u5199\u5bf9\uff0c\u540e\u9762\u5c31\u662f\u6807\u51c6\u5300\u51cf\u901f\u3002",
        "score_breakdown": [
            "\u6b65\u9aa4 1\uff1a\u753b\u5bf9\u53d7\u529b\u56fe 3 \u5206",
            "\u6b65\u9aa4 2\uff1a\u5217\u51fa\u6cbf\u659c\u9762\u65b9\u5411\u65b9\u7a0b 3 \u5206",
            "\u6b65\u9aa4 3\uff1a\u6c42\u65f6\u95f4 2 \u5206",
            "\u6b65\u9aa4 4\uff1a\u6c42\u6700\u5927\u4f4d\u79fb 2 \u5206",
        ],
        **review,
    }


def _solve_power_torque_speed(text: str) -> dict[str, object] | None:
    if not all(keyword in text for keyword in ["功率", "转矩", "转速"]):
        return None
    return _template_payload(
        knowledge_points=["功率-转矩-转速关系", "角速度换算", "机械功率"],
        explanation="这类题的核心就是 $P=T\\omega$ 和 $\\omega=2\\pi n/60$，工程里常直接写成 $P(\\mathrm{kW})=Tn/9550$。",
        solution_steps=[
            "先判断题目要求的是功率 $P$、转矩 $T$ 还是转速 $n$。",
            "写出基本关系 $P=T\\omega$，再写 $\\omega=2\\pi n/60$。",
            "联立得到工程常用公式 $P=Tn/9550$。",
            "把已知量代入，求出未知量。",
            "最后检查单位：$P$ 用 kW，$T$ 用 N·m，$n$ 用 r/min。",
        ],
        formula_notes=[
            "$P=T\\omega$",
            "$\\omega=2\\pi n/60$",
            "$P=\\dfrac{2\\pi nT}{60}$",
            "$P(\\mathrm{kW})=\\dfrac{T(\\mathrm{N\\cdot m})n(\\mathrm{r/min})}{9550}$",
            "$T=\\dfrac{9550P}{n}$",
            "$n=\\dfrac{9550P}{T}$",
        ],
        novice_explain="记一句话：功率 = 转矩 × 转得有多快。工程题里通常直接用 $P=Tn/9550$。",
        memory_tips=["先写 $P=T\\omega$", "工程题优先想 $9550$ 公式", "单位统一后再算"],
        exam_tricks=["先判断求谁", "先列公式再代入", "最后写清单位"],
        diagram_hint="图解建议：画一根旋转轴，标出转矩 $T$、转速 $n$ 和输出功率 $P$。",
        variant_questions=["已知功率和转速求转矩", "已知转矩和转速求功率", "已知功率和转矩求转速"],
        mini_quiz=["为什么有 $P=T\\omega$？", "$9550$ 常数从哪里来？", "转速加倍时功率怎么变？"],
        self_questions=["单位统一了吗？", "转速是不是 r/min？", "最后写清所求量了吗？"],
        practice_set=["小卷题 1：电机 $P,n$ 求 $T$", "小卷题 2：主轴 $T,n$ 求 $P$", "小卷题 3：反求转速"],
        examples=["例题 1：电机输出转矩", "例题 2：机床主轴功率", "例题 3：减速器输入输出换算"],
        exam_focus_prediction=["公式换算", "单位统一", "结果判断"],
        next_action="再自己把 $P=T\\omega$ 推到 $P=Tn/9550$ 写一遍。",
        confidence_note="这类题不难，关键是单位别混。",
        score_breakdown=["步骤 1：写出关系式 2 分", "步骤 2：完成换算 2 分", "步骤 3：正确代入 4 分", "步骤 4：单位与结论 2 分"],
    )


def _solve_gear_ratio(text: str) -> dict[str, object] | None:
    if "\u9f7f\u8f6e" not in text or "\u9f7f\u6570" not in text:
        return None
    return _template_payload(
        knowledge_points=["齿轮传动比", "齿数关系", "转速换算"],
        explanation="齿轮题的核心是节圆线速度相等，所以有 $n_1z_1=n_2z_2$，进而得到 $i=n_1/n_2=z_2/z_1$。",
        solution_steps=[
            "先分清主动轮和从动轮，记好齿数 $z_1,z_2$。",
            "写出基本关系 $n_1z_1=n_2z_2$。",
            "再写传动比 $i=n_1/n_2=z_2/z_1$。",
            "根据所求量变形公式并代入。",
            "检查结果是否符合直觉：齿数多的一侧通常转得更慢。",
        ],
        formula_notes=["$n_1z_1=n_2z_2$", "$i=\\dfrac{n_1}{n_2}=\\dfrac{z_2}{z_1}$", "$n_2=\\dfrac{n_1z_1}{z_2}$", "$T_2\\approx iT_1$（忽略损失）"],
        novice_explain="小齿轮带大齿轮时，大齿轮通常转得慢，所以 $n$ 和 $z$ 是反着变的。",
        memory_tips=["先写 $n_1z_1=n_2z_2$", "主动从动下标别混", "先算传动比再算转速"],
        exam_tricks=["先定下标", "再写传动比", "最后用直觉反查"],
        diagram_hint="图解建议：画两个啮合齿轮，标出 $z_1,z_2,n_1,n_2$ 和转动方向。",
        variant_questions=["已知传动比求转速", "已知转速反求齿数", "加效率后求输出转矩"],
        mini_quiz=["为什么 $n$ 与 $z$ 成反比？", "传动比是不是永远大于 1？", "外啮合方向如何变化？"],
        self_questions=["主动和从动写对了吗？", "传动比定义用反了吗？", "结果合理吗？"],
        practice_set=["小卷题 1：齿数求传动比", "小卷题 2：齿数求转速", "小卷题 3：转矩换算"],
        examples=["例题 1：单级齿轮传动", "例题 2：减速器输出转速", "例题 3：反求齿数"],
        exam_focus_prediction=["传动比定义", "齿数转速关系", "下标对应"],
        next_action="再自己画一组主动轮和从动轮，把 $i=n_1/n_2=z_2/z_1$ 口述一遍。",
        confidence_note="齿轮题最容易错的不是算数，而是下标关系。",
        score_breakdown=["步骤 1：写出关系式 3 分", "步骤 2：正确代入 3 分", "步骤 3：求得结果 2 分", "步骤 4：结论 2 分"],
    )


def _solve_belt_drive(text: str) -> dict[str, object] | None:
    if "\u5e26\u4f20\u52a8" not in text and "\u76ae\u5e26" not in text:
        return None
    return _template_payload(
        knowledge_points=["带传动速度关系", "轮径与转速", "打滑修正"],
        explanation="带传动的关键是两轮接触带的线速度相同，因此 $\\pi D_1n_1=\\pi D_2n_2$，化简就是 $n_1D_1=n_2D_2$。",
        solution_steps=[
            "先写带速相等：主动轮与从动轮的带速相同。",
            "由 $v=\\pi Dn/60$ 得到 $n_1D_1=n_2D_2$。",
            "根据所求量变形成 $n_2=n_1D_1/D_2$ 或其他形式。",
            "若题目提到打滑，再乘以打滑修正系数。",
            "最后检查大小轮快慢是否符合直觉。",
        ],
        formula_notes=["$v=\\pi Dn/60$", "$n_1D_1=n_2D_2$", "$n_2=\\dfrac{n_1D_1}{D_2}$", "$i=\\dfrac{n_1}{n_2}=\\dfrac{D_2}{D_1}$（忽略打滑）"],
        novice_explain="同一根皮带跑得一样快，所以大轮就转得慢，小轮就转得快。",
        memory_tips=["先写带速相等", "轮径与转速反比", "看清有没有打滑"],
        exam_tricks=["直接写 $n_1D_1=n_2D_2$", "所求量对应变形", "最后靠直觉检查"],
        diagram_hint="图解建议：画两个皮带轮和皮带，标出 $D_1,D_2,n_1,n_2$ 以及带速 $v$。",
        variant_questions=["已知轮径求转速", "已知转速求轮径", "带打滑修正的转速题"],
        mini_quiz=["为什么大轮转得慢？", "$nD$ 关系从哪里来？", "打滑会怎么影响结果？"],
        self_questions=["有没有漏掉打滑条件？", "轮径单位统一了吗？", "结果是否合理？"],
        practice_set=["小卷题 1：轮径求转速", "小卷题 2：转速求轮径", "小卷题 3：含打滑系数"],
        examples=["例题 1：风机带传动", "例题 2：机床皮带轮", "例题 3：反求轮径比"],
        exam_focus_prediction=["带速相等", "轮径转速反比", "打滑修正"],
        next_action="再自己从 $v=\\pi Dn/60$ 出发推到 $n_1D_1=n_2D_2$ 一遍。",
        confidence_note="带传动题最稳的检查方法是先判断大小轮快慢。",
        score_breakdown=["步骤 1：写出带速关系 3 分", "步骤 2：化简 2 分", "步骤 3：代入计算 3 分", "步骤 4：结论 2 分"],
    )


def _solve_axial_deformation(text: str) -> dict[str, object] | None:
    if not any(keyword in text for keyword in ["\u62c9\u6746", "\u538b\u6746", "\u8f74\u5411\u529b", "\u5f39\u6027\u6a21\u91cf", "\u4f38\u957f"]):
        return None
    return _template_payload(
        knowledge_points=["轴向拉压", "正应力", "轴向变形", "胡克定律"],
        explanation="拉压杆题的主线很稳定：先用 $\\sigma=F/A$ 求应力，再用 $\\Delta L=FL/(EA)$ 或 $\\varepsilon=\\sigma/E$ 求变形。",
        solution_steps=[
            "先列出轴向力 $F$、截面积 $A$、长度 $L$ 和弹性模量 $E$。",
            "先求正应力 $\\sigma=F/A$。",
            "若求应变，则用 $\\varepsilon=\\sigma/E$。",
            "若求伸长或压缩量，则用 $\\Delta L=FL/(EA)$。",
            "最后检查单位是否统一，尤其是 $E$ 和 $A$。",
        ],
        formula_notes=["$\\sigma=F/A$", "$\\varepsilon=\\Delta L/L$", "$E=\\sigma/\\varepsilon$", "$\\Delta L=FL/(EA)$"],
        novice_explain="力越大、杆越长、材料越软，就越容易变形；面积越大，就越不容易变形。",
        memory_tips=["先写 $\\sigma=F/A$", "变形题最后回到 $\\Delta L=FL/(EA)$", "单位最容易错"],
        exam_tricks=["先看求应力还是求变形", "分段杆件要分段算", "先统一单位再代入"],
        diagram_hint="图解建议：画一根受拉或受压的直杆，标出轴向力 $F$、长度 $L$ 和截面积 $A$。",
        variant_questions=["分段拉杆总变形", "温度与机械变形叠加", "已知许用应力反求截面积"],
        mini_quiz=["为什么面积越大变形越小？", "$E$ 代表什么？", "拉杆和压杆公式形式为什么相似？"],
        self_questions=["单位统一了吗？", "题目求的是应力还是变形？", "是不是分段杆件？"],
        practice_set=["小卷题 1：求应力", "小卷题 2：求变形", "小卷题 3：分段杆件"],
        examples=["例题 1：圆杆拉伸", "例题 2：方杆压缩", "例题 3：组合杆变形"],
        exam_focus_prediction=["应力公式", "变形公式", "单位换算"],
        next_action="把 $\\sigma=F/A$ 和 $\\Delta L=FL/(EA)$ 的物理意义自己口述一遍。",
        confidence_note="拉压题更像单位管理题，单位对了就成功一大半。",
        score_breakdown=["步骤 1：识别模型 2 分", "步骤 2：写出应力公式 2 分", "步骤 3：写出变形公式 4 分", "步骤 4：结论 2 分"],
    )


def _solve_shaft_torsion(text: str) -> dict[str, object] | None:
    if not any(keyword in text for keyword in ["\u626d\u8f6c", "\u626d\u77e9", "\u526a\u5e94\u529b", "\u626d\u8f6c\u89d2"]):
        return None
    return _template_payload(
        knowledge_points=["轴扭转", "极惯性矩", "剪应力", "扭转角"],
        explanation="圆轴扭转题通常有两条主线：强度看 $\\tau_{max}=T/W_t$，刚度看 $\\varphi=TL/(GJ)$。实心圆轴常用 $J=\\pi d^4/32$、$W_t=\\pi d^3/16$。",
        solution_steps=[
            "先标出扭矩 $T$、直径 $d$、轴长 $L$ 和剪切模量 $G$。",
            "若求剪应力，先写 $W_t=\\pi d^3/16$，再用 $\\tau_{max}=T/W_t$。",
            "若求扭转角，先写 $J=\\pi d^4/32$，再用 $\\varphi=TL/(GJ)$。",
            "根据题目要求代入并求解。",
            "最后检查单位体系是否统一。",
        ],
        formula_notes=["$J=\\pi d^4/32$", "$W_t=\\pi d^3/16$", "$\\tau_{max}=T/W_t=16T/(\\pi d^3)$", "$\\varphi=TL/(GJ)$"],
        novice_explain="强度问题看应力 $\\tau$，刚度问题看转角 $\\varphi$。先分清题目问什么，再选公式。",
        memory_tips=["强度看 $\\tau$，刚度看 $\\varphi$", "先写 $J$ 和 $W_t$", "扭矩单位别混"],
        exam_tricks=["先判断求应力还是求转角", "圆轴题先写标准公式", "最后写清最大值位置"],
        diagram_hint="图解建议：画一根圆轴，在两端标出扭矩 $T$，在截面处标出直径 $d$。",
        variant_questions=["空心轴扭转", "分段圆轴转角叠加", "已知许用剪应力反求直径"],
        mini_quiz=["为什么转角用 $J$ 而不是 $W_t$？", "最大剪应力出现在轴心还是表面？", "空心轴和实心轴区别是什么？"],
        self_questions=["分清强度和刚度了吗？", "题目是不是空心轴？", "单位统一了吗？"],
        practice_set=["小卷题 1：求剪应力", "小卷题 2：求转角", "小卷题 3：反求直径"],
        examples=["例题 1：主轴扭矩求应力", "例题 2：传动轴求转角", "例题 3：许用应力设计"],
        exam_focus_prediction=["$J$ 与 $W_t$ 区分", "扭转应力公式", "扭转角公式"],
        next_action="再自己写一遍“强度看 $\\tau$，刚度看 $\\varphi$”。",
        confidence_note="扭转题不难，最怕的是把 $J$ 和 $W_t$ 用反。",
        score_breakdown=["步骤 1：识别模型 2 分", "步骤 2：写出截面量 2 分", "步骤 3：列式计算 4 分", "步骤 4：结论 2 分"],
    )


def _solve_support_reaction(text: str) -> dict[str, object] | None:
    if not any(keyword in text for keyword in ["\u7b80\u652f\u6881", "\u652f\u5ea7\u53cd\u529b", "\u8de8\u4e2d", "\u96c6\u4e2d\u529b"]):
        return None
    return _template_payload(
        knowledge_points=["简支梁支反力", "平衡方程", "跨中集中载荷"],
        explanation="简支梁支反力题本质上就是静力平衡：先列 $\\sum F_y=0$，再列 $\\sum M=0$。若集中力作用在跨中，常直接有 $R_A=R_B=P/2$。",
        solution_steps=[
            "先画受力图，标出支反力 $R_A$、$R_B$ 和外载荷。",
            "列竖直方向平衡：$\\sum F_y=0$。",
            "再对 A 点或 B 点取矩，列 $\\sum M=0$。",
            "若载荷在跨中，可直接利用对称性写 $R_A=R_B=P/2$。",
            "若还要求最大弯矩，则跨中集中力时 $M_{max}=PL/4$。",
        ],
        formula_notes=["$\\sum F_y=0$", "$\\sum M_A=0$", "$R_A+R_B=P$", "$R_A=R_B=P/2$（跨中集中力）", "$M_{max}=PL/4$"],
        novice_explain="先别急着想弯矩图，先把梁支起来。梁没飞起来，就说明上下力平衡，再用取矩把两端反力分开。",
        memory_tips=["先画受力图", "先列 $\\sum F_y=0$", "取矩点尽量避开未知力"],
        exam_tricks=["跨中载荷先想对称", "取矩优先选支座点", "先求支反力再谈弯矩"],
        diagram_hint="图解建议：画一根简支梁，两端标出支座反力 $R_A,R_B$，跨中画向下集中力 $P$。",
        variant_questions=["偏心集中力支反力", "均布载荷支反力", "求支反力后继续求弯矩"],
        mini_quiz=["为什么取矩常选支座点？", "跨中载荷为什么两端反力相等？", "偏心载荷时哪一步改变？"],
        self_questions=["受力图有漏力吗？", "力臂写对了吗？", "结果是否合理？"],
        practice_set=["小卷题 1：跨中集中力", "小卷题 2：偏心载荷", "小卷题 3：均布载荷"],
        examples=["例题 1：简支梁跨中载荷", "例题 2：偏心载荷反力", "例题 3：支反力+最大弯矩"],
        exam_focus_prediction=["受力图", "平衡方程", "力臂判断"],
        next_action="再自己用一题跨中集中力梁练习口算 $R_A=R_B=P/2$。",
        confidence_note="梁支反力题的抓手就是受力图，图对了，式子就顺。",
        score_breakdown=["步骤 1：画图 3 分", "步骤 2：列力平衡 2 分", "步骤 3：列矩平衡 3 分", "步骤 4：结论 2 分"],
    )


def _solve_beam_bending(text: str) -> dict[str, object] | None:
    if not any(keyword in text for keyword in ["\u5f2f\u77e9", "\u5f2f\u66f2\u5e94\u529b", "\u6297\u5f2f", "\u622a\u9762\u7cfb\u6570"]):
        return None
    return _template_payload(
        knowledge_points=["弯曲正应力", "截面系数", "危险截面"],
        explanation="弯曲强度题的核心公式是 $\\sigma=M/W$。先找到最大弯矩所在的危险截面，再找截面系数 $W$，最后求应力。",
        solution_steps=[
            "先确定危险截面，也就是弯矩最大的地方。",
            "写出弯曲正应力公式 $\\sigma=M/W$。",
            "根据截面形状写出 $W$，如矩形 $W=bh^2/6$、圆形 $W=\\pi d^3/32$。",
            "代入弯矩和截面系数，求出最大应力。",
            "若题目给了许用应力，再做强度校核。",
        ],
        formula_notes=["$\\sigma=M/W$", "$W=I/y_{max}$", "$W_{矩形}=bh^2/6$", "$W_{圆}=\\pi d^3/32$"],
        novice_explain="可以记成：弯矩越大、截面越弱，应力就越大，所以最后就是看 $M/W$ 这个比值。",
        memory_tips=["先找最大弯矩", "再找截面系数", "最后回到 $\\sigma=M/W$"],
        exam_tricks=["危险截面先行", "矩形截面常考", "单位统一到 N·mm 更稳"],
        diagram_hint="图解建议：画出梁的危险截面，在上下缘标出拉应力和压应力，并标出弯矩 $M$。",
        variant_questions=["已知许用应力反求尺寸", "矩形改圆形", "联立弯矩图与强度条件"],
        mini_quiz=["为什么危险截面在最大弯矩处？", "为什么截面高度更敏感？", "$W$ 和 $I$ 的关系是什么？"],
        self_questions=["危险截面判断对了吗？", "截面系数公式用对了吗？", "题目求应力还是尺寸？"],
        practice_set=["小卷题 1：矩形截面弯曲应力", "小卷题 2：圆截面弯曲应力", "小卷题 3：反求尺寸"],
        examples=["例题 1：简支梁最大应力", "例题 2：悬臂梁危险截面", "例题 3：抗弯设计"],
        exam_focus_prediction=["危险截面", "截面系数", "强度校核"],
        next_action="把“危险截面 → 最大弯矩 → 截面系数 → 应力”这条链自己顺一遍。",
        confidence_note="这类题主要不是难在算，而是难在先找对危险截面。",
        score_breakdown=["步骤 1：判断危险截面 2 分", "步骤 2：写公式 2 分", "步骤 3：求 $W$ 并代入 4 分", "步骤 4：校核结论 2 分"],
    )


def _solve_uniform_circular_motion(text: str) -> dict[str, object] | None:
    if not any(keyword in text for keyword in ["\u5706\u5468", "\u5411\u5fc3", "\u534a\u5f84", "\u89d2\u901f\u5ea6", "\u7ebf\u901f\u5ea6"]):
        return None
    return _template_payload(
        knowledge_points=["匀速圆周运动", "向心加速度", "向心力"],
        explanation="圆周运动题的核心是虽然速率可不变，但速度方向在变，所以仍有指向圆心的加速度 $a_n=v^2/r=\\omega^2r$，向心力为 $F_n=ma_n$。",
        solution_steps=[
            "先看题目已知的是 $v$、$\\omega$ 还是 $n$。",
            "如有需要，先做换算：$v=\\omega r$。",
            "写出向心加速度 $a_n=v^2/r=\\omega^2r$。",
            "若求向心力，则 $F_n=mv^2/r=m\\omega^2r$。",
            "最后说明该向心力由哪个真实力提供。",
        ],
        formula_notes=["$v=\\omega r$", "$a_n=v^2/r=\\omega^2r$", "$F_n=mv^2/r=m\\omega^2r$", "$T=2\\pi/\\omega$"],
        novice_explain="圆周运动只要在转，就必须有个力把它不断拉向圆心。",
        memory_tips=["先统一到 $v$ 或 $\\omega$", "向心量都指向圆心", "最后回到真实受力"],
        exam_tricks=["先写 $a_n$", "向心力不是新力", "方向要写清"],
        diagram_hint="图解建议：画圆轨迹，在某点画切向速度 $v$ 和指向圆心的 $a_n$ 或 $F_n$。",
        variant_questions=["已知周期求向心加速度", "已知角速度求向心力", "判断由哪个力提供向心力"],
        mini_quiz=["为什么匀速圆周仍有加速度？", "向心力是不是一种新力？", "速度方向和向心力方向关系是什么？"],
        self_questions=["区分速率和速度了吗？", "方向写对了吗？", "是否回到了真实受力？"],
        practice_set=["小卷题 1：绳球圆周运动", "小卷题 2：汽车转弯", "小卷题 3：圆锥摆"],
        examples=["例题 1：已知半径和速度求向心力", "例题 2：已知角速度求加速度", "例题 3：摩擦力提供向心力"],
        exam_focus_prediction=["向心加速度公式", "真实受力分析", "方向判断"],
        next_action="再自己说一遍：向心力不是新力，而是合力的效果。",
        confidence_note="这类题最容易错的地方是只背公式，却没回到受力来源。",
        score_breakdown=["步骤 1：统一已知量 2 分", "步骤 2：写出 $a_n$ 2 分", "步骤 3：写出 $F_n$ 3 分", "步骤 4：说明受力来源 3 分"],
    )


def _solve_rotational_dynamics(text: str) -> dict[str, object] | None:
    if not any(keyword in text for keyword in ["\u8f6c\u52a8\u60ef\u91cf", "\u89d2\u52a0\u901f\u5ea6", "\u529b\u77e9", "\u8f6c\u52a8\u5b9a\u5f8b"]):
        return None
    return _template_payload(
        knowledge_points=["转动定律", "力矩平衡", "角加速度"],
        explanation="转动题对应平动里的 $F=ma$，核心就是 $\\sum M=J\\alpha$。力矩负责让物体转起来，转动惯量 $J$ 决定它有多难转。",
        solution_steps=[
            "先选定转轴并规定正方向。",
            "列出各力对转轴的力矩。",
            "写出转动方程 $\\sum M=J\\alpha$。",
            "若要求角速度或转角，再接 $\\omega=\\omega_0+\\alpha t$ 或 $\\theta=\\omega_0t+\\tfrac12\\alpha t^2$。",
            "最后检查力矩正负号。",
        ],
        formula_notes=["$\\sum M=J\\alpha$", "$\\alpha=\\sum M/J$", "$\\omega=\\omega_0+\\alpha t$", "$\\theta=\\omega_0t+\\tfrac12\\alpha t^2$"],
        novice_explain="可以把它看成 $F=ma$ 的转动版：力变成力矩，质量变成转动惯量，加速度变成角加速度。",
        memory_tips=["先定转轴和正方向", "先求合力矩", "再接角运动学"],
        exam_tricks=["转动题先写 $\\sum M=J\\alpha$", "最后检查符号", "看清是否还要接时间关系"],
        diagram_hint="图解建议：画出转轴，在各力作用点标出力和力臂，再标出角加速度 $\\alpha$ 的方向。",
        variant_questions=["已知力矩求角加速度", "已知角加速度反求力矩", "平动转动联立的绳轮系统"],
        mini_quiz=["为什么是 $\\sum M=J\\alpha$？", "力矩正负号怎么判断？", "转动惯量大意味着什么？"],
        self_questions=["转轴选对了吗？", "正方向写清了吗？", "要不要再接运动学？"],
        practice_set=["小卷题 1：圆盘转动", "小卷题 2：飞轮角加速度", "小卷题 3：绳轮系统"],
        examples=["例题 1：圆盘受力矩", "例题 2：飞轮速度变化", "例题 3：复合力矩题"],
        exam_focus_prediction=["转轴选择", "力矩符号", "转动与运动学衔接"],
        next_action="把 $F=ma$ 和 $\\sum M=J\\alpha$ 做一张对照表，自己比较一遍。",
        confidence_note="转动题不怕公式多，怕的是轴没定好、方向没约定好。",
        score_breakdown=["步骤 1：选轴定向 2 分", "步骤 2：列力矩 3 分", "步骤 3：写方程 3 分", "步骤 4：收尾 2 分"],
    )


def _solve_spring_oscillation(text: str) -> dict[str, object] | None:
    if not any(keyword in text for keyword in ["\u5f39\u7c27", "\u632f\u5b50", "\u5468\u671f", "\u9891\u7387", "\u7b80\u8c10"]):
        return None
    return _template_payload(
        knowledge_points=["弹簧振子", "简谐振动", "周期与频率"],
        explanation="质点-弹簧振子的标准结果是 $\\omega_n=\\sqrt{k/m}$，所以周期 $T=2\\pi\\sqrt{m/k}$，频率 $f=1/T$。",
        solution_steps=[
            "先识别为质点-弹簧简谐振动模型。",
            "写出恢复力 $F=-kx$ 和方程 $m\\ddot{x}+kx=0$。",
            "由标准结果得到 $\\omega_n=\\sqrt{k/m}$。",
            "再写周期 $T=2\\pi/\\omega_n=2\\pi\\sqrt{m/k}$。",
            "若要求频率，则 $f=1/T$；若要求位移表达式，可写 $x=A\\cos(\\omega_nt+\\varphi)$。",
        ],
        formula_notes=["$F=-kx$", "$m\\ddot{x}+kx=0$", "$\\omega_n=\\sqrt{k/m}$", "$T=2\\pi\\sqrt{m/k}$", "$f=1/T$", "$x=A\\cos(\\omega_nt+\\varphi)$"],
        novice_explain="弹簧越硬，振得越快；质量越大，振得越慢。",
        memory_tips=["先写 $F=-kx$", "再写 $\\omega_n=\\sqrt{k/m}$", "周期频率互为倒数"],
        exam_tricks=["看到弹簧振子就先写周期公式", "注意区分角频率和频率", "相位题单独看初始条件"],
        diagram_hint="图解建议：画一端固定的弹簧和质块，标出平衡位置、位移 $x$ 和恢复力 $-kx$。",
        variant_questions=["已知周期求刚度", "已知频率求质量", "写出位移表达式"],
        mini_quiz=["为什么 $k$ 大周期反而小？", "恢复力为什么总与位移方向相反？", "频率和角频率是什么关系？"],
        self_questions=["我有没有写出标准方程？", "题目求的是周期还是频率？", "最后是否回到了物理意义？"],
        practice_set=["小卷题 1：已知 $m,k$ 求 $T$", "小卷题 2：已知 $T$ 求 $k$", "小卷题 3：写位移方程"],
        examples=["例题 1：标准弹簧振子", "例题 2：频率反求参数", "例题 3：相位初值题"],
        exam_focus_prediction=["周期公式", "频率换算", "标准方程识别"],
        next_action="自己从 $F=-kx$ 推到 $\\omega_n=\\sqrt{k/m}$ 再写一遍。",
        confidence_note="弹簧振子题很适合模板化，稳住几条公式就能拿分。",
        score_breakdown=["步骤 1：写方程 3 分", "步骤 2：写角频率 2 分", "步骤 3：写周期/频率 3 分", "步骤 4：结论 2 分"],
    )


def _deterministic_solution(topic_kind: str, text: str) -> dict[str, object] | None:
    topic_solvers = {
        "electrical": [
            _solve_three_phase_star,
        ],
        "physics": [
            _solve_incline_motion,
            _solve_uniform_circular_motion,
            _solve_rotational_dynamics,
            _solve_spring_oscillation,
        ],
        "mechanical": [
            _solve_power_torque_speed,
            _solve_gear_ratio,
            _solve_belt_drive,
            _solve_axial_deformation,
            _solve_shaft_torsion,
            _solve_support_reaction,
            _solve_beam_bending,
            _solve_uniform_circular_motion,
            _solve_rotational_dynamics,
            _solve_spring_oscillation,
        ],
    }
    generic_solvers = [
        _solve_three_phase_star,
        _solve_incline_motion,
        _solve_power_torque_speed,
        _solve_gear_ratio,
        _solve_belt_drive,
        _solve_axial_deformation,
        _solve_shaft_torsion,
        _solve_support_reaction,
        _solve_beam_bending,
        _solve_uniform_circular_motion,
        _solve_rotational_dynamics,
        _solve_spring_oscillation,
    ]
    solvers = topic_solvers.get(topic_kind, []) + generic_solvers
    for solver in solvers:
        solved = solver(text)
        if solved is not None:
            return solved
    return None


def _build_core_prompt(text: str, course: str, explanation_mode: str) -> tuple[str, str]:
    system_prompt = (
        "\u4f60\u662f\u9762\u5411\u4e2d\u56fd\u5927\u5b66\u751f\u7684 AI \u590d\u4e60\u8001\u5e08\u3002"
        "\u8bf7\u53ea\u8fd4\u56de\u4e00\u4e2a JSON \u5bf9\u8c61\uff0c\u4e0d\u8981\u8f93\u51fa\u989d\u5916\u8bf4\u660e\u3002"
        "JSON \u5fc5\u987b\u5305\u542b\uff1aknowledge_points,difficulty,explanation,solution_steps,formula_notes,novice_explain,diagram_hint,next_action\u3002"
        "\u5982\u679c\u9898\u76ee\u91cc\u7ed9\u4e86\u5177\u4f53\u6570\u503c\u3001\u7b26\u53f7\u6761\u4ef6\u6216\u516c\u5f0f\u53c2\u6570\uff0c\u5fc5\u987b\u771f\u6b63\u4ee3\u5165\u5e76\u7ed9\u51fa\u8ba1\u7b97\u6216\u63a8\u5bfc\uff0c\u4e0d\u8981\u53ea\u5199\u5957\u8def\u3002"
        "\u6240\u6709\u516c\u5f0f\u8bf7\u7528 $...$ \u5305\u88f9\u5185\u8054\u516c\u5f0f\uff0c\u7528 $$...$$ \u5305\u88f9\u72ec\u7acb\u516c\u5f0f\u3002"
        "solution_steps \u6700\u591a 6 \u6761\uff0cformula_notes \u6700\u591a 6 \u6761\u3002"
    )
    user_prompt = f"\u9898\u76ee\uff1a{text}\n\u8bfe\u7a0b\uff1a{course}\n\u6a21\u5f0f\uff1a{explanation_mode}\n\u8bf7\u5148\u7ed9\u4e3b\u89e3\u3002"
    return (system_prompt, user_prompt)


def _build_full_prompt(text: str, course: str, explanation_mode: str) -> tuple[str, str]:
    system_prompt = (
        "\u4f60\u662f\u9762\u5411\u4e2d\u56fd\u5927\u5b66\u751f\u7684 AI \u590d\u4e60\u8001\u5e08\u3002"
        "\u8bf7\u53ea\u8fd4\u56de\u4e00\u4e2a JSON \u5bf9\u8c61\uff0c\u4e0d\u8981\u8f93\u51fa\u989d\u5916\u8bf4\u660e\u3002"
        "JSON \u5fc5\u987b\u5305\u542b\uff1aknowledge_points,difficulty,explanation,solution_steps,formula_notes,novice_explain,"
        "review_schedule,time_plan,memory_tips,exam_tricks,diagram_hint,variant_questions,mini_quiz,self_questions,"
        "practice_set,examples,exam_focus_prediction,next_action,confidence_note,score_breakdown\u3002"
        "\u5982\u679c\u9898\u76ee\u91cc\u7ed9\u4e86\u5177\u4f53\u6570\u503c\u3001\u7b26\u53f7\u6761\u4ef6\u6216\u516c\u5f0f\u53c2\u6570\uff0c\u5fc5\u987b\u771f\u6b63\u4ee3\u5165\u5e76\u7ed9\u51fa\u8ba1\u7b97\u6216\u63a8\u5bfc\uff0c\u4e0d\u8981\u53ea\u5199\u5957\u8def\u3002"
        "confidence_note \u8981\u514b\u5236\u3001\u5177\u4f53\uff0c\u4e0d\u8981\u9e21\u6c64\u3002"
        "\u6240\u6709\u516c\u5f0f\u8bf7\u7528 $...$ \u5305\u88f9\u5185\u8054\u516c\u5f0f\uff0c\u7528 $$...$$ \u5305\u88f9\u72ec\u7acb\u516c\u5f0f\u3002"
    )
    user_prompt = f"\u9898\u76ee\uff1a{text}\n\u8bfe\u7a0b\uff1a{course}\n\u6a21\u5f0f\uff1a{explanation_mode}\n\u8bf7\u5728\u4e3b\u89e3\u4e4b\u5916\uff0c\u8865\u8db3\u590d\u4e60\u5b89\u6392\u3001\u6613\u9519\u63d0\u9192\u3001\u5c0f\u6d4b\u9898\u548c\u53d8\u5f0f\u9898\u3002"
    return (system_prompt, user_prompt)


def _build_risk_notice(llm_error: str | None, detail_level: str) -> str:
    notice = "AI \u53ef\u80fd\u4ea7\u751f\u5e7b\u89c9\uff0c\u8bf7\u5728\u5173\u952e\u6b65\u9aa4\u4e0a\u81ea\u884c\u6838\u9a8c\u3002"
    if detail_level == "core":
        notice += " \u5f53\u524d\u5148\u8fd4\u56de\u4e3b\u89e3\uff0c\u4fa7\u680f\u8865\u5145\u4f1a\u7a0d\u540e\u5b8c\u6210\u3002"
    if llm_error and llm_error != "demo_mode":
        notice += f"\uff08\u672c\u6b21\u5df2\u5207\u6362\u5230\u672c\u5730\u515c\u5e95\uff1a{llm_error}\uff09"
    return notice


def _response_from_payload(
    request: StudyAnalyzeRequest,
    payload: dict[str, object],
    fallback: dict[str, object],
    *,
    llm_error: str | None = None,
) -> StudyAnalyzeResponse:
    detail_level = (request.detail_level or "full").lower()
    return StudyAnalyzeResponse(
        knowledge_points=_ensure_text_list(payload.get("knowledge_points"), fallback["knowledge_points"]),
        difficulty=_ensure_text(payload.get("difficulty"), str(fallback["difficulty"])),
        explanation_mode=request.explanation_mode,
        explanation=_ensure_text(payload.get("explanation"), str(fallback["explanation"])),
        solution_steps=_ensure_text_list(payload.get("solution_steps"), fallback["solution_steps"]),
        formula_notes=_ensure_text_list(payload.get("formula_notes"), fallback["formula_notes"]),
        novice_explain=_ensure_text(payload.get("novice_explain"), str(fallback["novice_explain"])),
        review_schedule=_ensure_text_list(payload.get("review_schedule"), fallback["review_schedule"]),
        time_plan=_ensure_text_list(payload.get("time_plan"), fallback["time_plan"]),
        memory_tips=_ensure_text_list(payload.get("memory_tips"), fallback["memory_tips"]),
        exam_tricks=_ensure_text_list(payload.get("exam_tricks"), fallback["exam_tricks"]),
        diagram_hint=_ensure_text(payload.get("diagram_hint"), str(fallback["diagram_hint"])),
        variant_questions=_ensure_text_list(payload.get("variant_questions"), fallback["variant_questions"]),
        mini_quiz=_ensure_text_list(payload.get("mini_quiz"), fallback["mini_quiz"]),
        self_questions=_ensure_text_list(payload.get("self_questions"), fallback["self_questions"]),
        practice_set=_ensure_text_list(payload.get("practice_set"), fallback["practice_set"]),
        examples=_ensure_text_list(payload.get("examples"), fallback["examples"]),
        exam_focus_prediction=_ensure_text_list(payload.get("exam_focus_prediction"), fallback["exam_focus_prediction"]),
        next_action=_ensure_text(payload.get("next_action"), str(fallback["next_action"])),
        confidence_note=_ensure_text(payload.get("confidence_note"), str(fallback["confidence_note"])),
        risk_notice=_build_risk_notice(llm_error, detail_level),
        score_breakdown=_ensure_text_list(payload.get("score_breakdown"), fallback["score_breakdown"]),
    )


def run_learning_skill(request: StudyAnalyzeRequest) -> StudyAnalyzeResponse:
    text = request.input_text.strip() or "\u672a\u63d0\u4f9b\u9898\u76ee\u6587\u672c\u3002"
    detail_level = (request.detail_level or "full").lower()
    topic_kind, topic_label = _infer_topic(text, request.course)
    generic_fallback = _generic_fallback(topic_label)
    deterministic = _deterministic_solution(topic_kind, text)
    fallback = deterministic or generic_fallback

    if deterministic is not None:
        return _response_from_payload(request, deterministic, fallback)

    if detail_level == "core":
        prompt, user_prompt = _build_core_prompt(text, request.course, request.explanation_mode)
    else:
        prompt, user_prompt = _build_full_prompt(text, request.course, request.explanation_mode)

    llm_text, llm_error = generate_text(prompt, user_prompt)
    parsed = extract_json_object(llm_text or "") or {}
    payload = fallback | parsed
    return _response_from_payload(request, payload, fallback, llm_error=llm_error)
