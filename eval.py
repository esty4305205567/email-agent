"""מריץ ניסוי הערכה ב-LangSmith.

    python eval.py baseline   # גרסה בסיסית: בלי מבקר, בלי הגדרות/דוגמאות בסיווג
    python eval.py improved   # גרסה משופרת: עם מבקר והגדרות ודוגמאות

מריצים את שתיהן על אותו דאטהסט, ומשווים בטבלת Experiments ב-LangSmith.
"""
import sys

from dotenv import load_dotenv

load_dotenv()

import truststore

truststore.inject_into_ssl()  # שימוש באישורי Windows, פותר שגיאת SSL

from langsmith import evaluate
from pydantic import BaseModel, Field

from create_dataset import DATASET_NAME
from graph import build_graph, get_llm

VERSIONS = {
    "baseline": {"use_critic": False, "few_shot": False},
    "improved": {"use_critic": True, "few_shot": True},
}


# ---------------------------------------------------------------- Target
def make_target(flags: dict):
    graph = build_graph(for_eval=True)

    def target(inputs: dict) -> dict:
        try:
            result = graph.invoke(
                {"email": inputs["email"], "rounds": 0},
                config={"configurable": flags},
            )
        except Exception as e:  # כשל במייל אחד לא עוצר את כל ההערכה
            print(f"שגיאה במייל '{inputs['email']['subject']}': {e}")
            return {"category": None, "draft": "", "rounds": 0, "error": str(e)}
        return {
            "category": result.get("category"),
            "draft": result.get("draft", ""),
            "rounds": result.get("rounds", 0),
        }

    return target


# ---------------------------------------------------------------- Evaluators
def category_correct(outputs: dict, reference_outputs: dict) -> dict:
    """בדיקת קוד פשוטה: האם הסיווג זהה לסיווג הנכון."""
    return {
        "key": "category_correct",
        "score": int(outputs.get("category") == reference_outputs["category"]),
    }


def rounds_used(outputs: dict) -> dict:
    """מדד יעילות: כמה סבבי כתיבה נדרשו."""
    if "error" in outputs:
        return {"key": "rounds_used", "score": None, "comment": "הריצה נכשלה"}
    return {"key": "rounds_used", "score": outputs.get("rounds", 0)}


class Judge(BaseModel):
    score: int = Field(description="1 אם הטיוטה טובה, 0 אם לא")
    reason: str = Field(description="הסבר קצר")


def draft_quality(inputs: dict, outputs: dict) -> dict:
    """מודל שופט: האם הטיוטה עונה על כל הנקודות בטון מתאים."""
    if not outputs.get("draft"):
        return {"key": "draft_quality", "score": None, "comment": "לא נכתבה טיוטה"}
    email = inputs["email"]
    verdict = get_llm().with_structured_output(Judge).invoke(
        "אתה בודק איכות של טיוטת תשובה למייל. תן 1 רק אם הטיוטה: "
        "(א) עונה על כל השאלות והנקודות במייל, (ב) בטון מנומס ומתאים, "
        "(ג) לא מבטיחה דברים שלא הוזכרו במייל. אחרת תן 0.\n\n"
        f"המייל:\nנושא: {email['subject']}\n{email['body']}\n\n"
        f"הטיוטה:\n{outputs['draft']}"
    )
    return {"key": "draft_quality", "score": verdict.score, "comment": verdict.reason}


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else ""
    if version not in VERSIONS:
        sys.exit("שימוש: python eval.py baseline | improved")
    flags = VERSIONS[version]
    evaluate(
        make_target(flags),
        data=DATASET_NAME,
        evaluators=[category_correct, rounds_used, draft_quality],
        experiment_prefix=version,
        metadata=flags,
        max_concurrency=4,  # כמה מיילים במקביל (מקצר את הזמן)
    )


if __name__ == "__main__":
    main()
