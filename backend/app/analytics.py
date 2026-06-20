import csv
import math
from functools import lru_cache
from pathlib import Path
from statistics import mean
from typing import Any

from .config import PROJECT_DIR
from .database import connect
from .repositories import (
    feedback_summary,
    get_profile,
    latest_evaluation,
    learning_task_summary,
    list_learning_events,
    list_mastery,
)


DATASET_PATH = PROJECT_DIR / "datasets" / "uci_student_performance" / "raw" / "student-por.csv"


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mx, my = mean(xs), mean(ys)
    numerator = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denominator = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return round(numerator / denominator, 3) if denominator else 0.0


@lru_cache
def public_dataset_overview() -> dict[str, Any]:
    if not DATASET_PATH.exists():
        return {"available": False, "source": "UCI Student Performance"}
    with DATASET_PATH.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
    grades = [float(row["G3"]) for row in rows]
    study_time = [float(row["studytime"]) for row in rows]
    failures = [float(row["failures"]) for row in rows]
    absences = [float(row["absences"]) for row in rows]
    pass_count = sum(grade >= 10 for grade in grades)
    risk_count = sum(float(row["failures"]) > 0 or float(row["G3"]) < 10 for row in rows)
    return {
        "available": True,
        "name": "Student Performance",
        "source": "UCI Machine Learning Repository",
        "license": "CC BY 4.0",
        "records": len(rows),
        "features": 30,
        "subject": "Portuguese language course",
        "average_final_grade": round(mean(grades), 2),
        "pass_rate": round(pass_count / len(rows) * 100, 1),
        "risk_rate": round(risk_count / len(rows) * 100, 1),
        "average_absences": round(mean(absences), 1),
        "behavior_correlations": [
            {"factor": "学习时间", "field": "studytime", "correlation": pearson(study_time, grades)},
            {"factor": "历史挂科次数", "field": "failures", "correlation": pearson(failures, grades)},
            {"factor": "缺勤次数", "field": "absences", "correlation": pearson(absences, grades)},
        ],
        "limitations": [
            "数据来自葡萄牙两所中学，并非中国高校 Python 课程样本。",
            "相关性不代表因果关系，不用于直接训练或自动决定学生权益。",
            "本项目仅将其作为学习分析界面与风险解释方法的公开基准。",
        ],
    }


def local_learning_signals() -> dict[str, Any]:
    profile = get_profile()
    profile_id = profile.get("id") if profile else None
    with connect() as conn:
        resource_count = conn.execute(
            "SELECT COUNT(*) FROM resources WHERE profile_id=?", (profile_id,)
        ).fetchone()[0] if profile_id else 0
        tutor_count = conn.execute(
            "SELECT COUNT(*) FROM conversations WHERE role='user' AND profile_id=?",
            (profile_id,),
        ).fetchone()[0] if profile_id else 0
    evaluation = latest_evaluation(profile_id)
    mastery = list_mastery(profile_id)
    events = list_learning_events(profile_id, 8)
    feedback = feedback_summary(profile_id)
    active_plan = learning_task_summary(profile_id)
    latest_score = float(evaluation["score"]) if evaluation else None
    evaluated_weak = evaluation["weak_points"] if evaluation else []
    weak_points = list(dict.fromkeys((profile or {}).get("weak_points", []) + evaluated_weak))
    signals = []
    if latest_score is None:
        signals.append({"label": "测评证据", "value": "尚未测评", "status": "pending"})
    elif latest_score < 60:
        signals.append({"label": "最近测评", "value": f"{latest_score:.0f} 分", "status": "risk"})
    elif latest_score < 85:
        signals.append({"label": "最近测评", "value": f"{latest_score:.0f} 分", "status": "watch"})
    else:
        signals.append({"label": "最近测评", "value": f"{latest_score:.0f} 分", "status": "good"})
    signals.extend(
        [
            {"label": "资源生成", "value": f"{resource_count} 次", "status": "good" if resource_count else "pending"},
            {"label": "主动提问", "value": f"{tutor_count} 次", "status": "good" if tutor_count else "pending"},
        ]
    )
    low_mastery = [item for item in mastery if float(item["mastery"]) < 60]
    if low_mastery:
        recommendation = (
            f"知识点“{low_mastery[0]['knowledge_point']}”当前掌握度 "
            f"{low_mastery[0]['mastery']:.0f}%，建议先看对应讲义，再完成一次针对性复测。"
        )
    elif latest_score is None:
        recommendation = "先完成一次诊断测评，系统会用真实作答证据校准静态画像。"
    elif weak_points:
        recommendation = f"优先处理“{weak_points[0]}”：先使用启发式答疑，再完成一个最小代码练习和一次复测。"
    else:
        recommendation = "当前掌握情况良好，建议进入项目迁移任务，并用自己的数据替换示例数据。"
    if feedback["needs_adjustment"] > feedback["helpful"]:
        recommendation += " 最近“需要调整”的资源反馈较多，下一轮应更换讲解形式或缩小单次学习任务。"
    if active_plan and active_plan["next_task"]:
        recommendation = (
            f"下一步：{active_plan['next_task']['title']}（约 "
            f"{active_plan['next_task']['estimated_minutes']} 分钟）。{recommendation}"
        )
    return {
        "profile_id": profile_id,
        "profile_name": (profile or {}).get("display_name"),
        "latest_evaluation": evaluation,
        "signals": signals,
        "weak_points": weak_points[:5],
        "mastery": mastery,
        "mastery_average": round(mean([float(item["mastery"]) for item in mastery]), 1) if mastery else None,
        "recent_events": events,
        "resource_feedback": feedback,
        "active_plan": active_plan,
        "recommendation": recommendation,
        "principle": "近期学习行为 > 历史测评 > 静态画像",
    }
