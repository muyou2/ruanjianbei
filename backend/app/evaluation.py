from typing import Any


def normalize_answer(value: str) -> str:
    return "".join(value.lower().split()).replace("。", "")


def score_question(question: dict[str, Any], answer: str) -> dict[str, Any]:
    actual = normalize_answer(answer)
    expected = normalize_answer(question["answer"])
    manual_review = False

    if question["type"] in {"single_choice", "true_false"}:
        correct = actual == expected
        points = 25.0 if correct else 0.0
        scoring_method = "精确匹配自动判分"
    elif question["type"] == "short_answer":
        keywords = ["样本", "偏差", "字段", "缺失", "填充"]
        matched = [word for word in keywords if word in actual]
        points = round(25 * len(matched) / len(keywords), 1)
        correct = points >= 15
        scoring_method = "MVP 关键词匹配评分"
    else:
        required_code = ["pd.read_csv", "isna().sum", "drop_duplicates", "fillna", "median"]
        matched = [
            statement
            for statement in required_code
            if normalize_answer(statement) in actual
        ]
        points = round(25 * len(matched) / len(required_code), 1)
        correct = points >= 20
        scoring_method = "MVP 关键语句检查（未执行代码）"
        manual_review = True

    return {
        "question_id": question["id"],
        "correct": correct,
        "points": points,
        "max_points": 25,
        "scoring_method": scoring_method,
        "manual_review": manual_review,
        "answer": answer,
        "expected": question["answer"],
        "explanation": question["explanation"],
    }
