"""סוכן טיוטות מייל - LangGraph.

זרימה רגילה:
START -> fetch_email -> classify -> (תנאי) -> write_draft -> (תנאי) -> critic (לולאה, עד MAX_ROUNDS)
classify -> END אם אין צורך בתשובה
critic -> human_review (interrupt) -> save_draft -> END

מצב הערכה (for_eval=True): המייל מגיע כקלט, בלי Gmail, בלי עצירה לאישור ובלי שמירה.

מתגים להשוואת גרסאות (מועברים ב-config["configurable"]):
  use_critic - האם להפעיל את המבקר והלולאה
  few_shot   - האם להוסיף לסיווג הגדרות ודוגמאות
"""
from typing import Literal, TypedDict

from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from pydantic import BaseModel, Field

# מודל זול ואמין בתשלום (דורש ANTHROPIC_API_KEY בקובץ .env).
# להחלפת ספק: "openai:..." או "google_genai:..." (ולהתקין את החבילה המתאימה)
MODEL = "anthropic:claude-haiku-5-5"
MAX_ROUNDS = 2  # כמה פעמים המבקר יכול להחזיר לשכתוב


def get_llm():
    return init_chat_model(MODEL, max_retries=6)


# ---------------------------------------------------------------- State
class State(TypedDict, total=False):
    message_id: str          # קלט: איזה מייל לטפל
    email: dict              # המייל שנשלף
    category: str            # no_reply / simple / complex
    draft: str               # הטיוטה הנוכחית
    critic_ok: bool          # האם המבקר מרוצה
    critic_notes: str        # הערות המבקר
    rounds: int              # מונה סבבי כתיבה (עוצר את הלולאה)
    decision: str            # approve / edit / reject (מהאדם)
    final_text: str          # הנוסח הסופי אם האדם ערך
    draft_id: str            # מזהה הטיוטה שנשמרה ב-Gmail


class Classification(BaseModel):
    category: Literal["no_reply", "simple", "complex"]


class Verdict(BaseModel):
    ok: bool = Field(description="האם הטיוטה מוכנה")
    notes: str = Field(description="מה לתקן, אם לא מוכנה. ריק אם מוכנה")


# הגדרות ודוגמאות לגרסה המשופרת. הדוגמאות כאן שונות מאלה שבדאטהסט, כדי שלא יהיה "זליגה".
CLASSIFY_GUIDE = """הגדרות:
- no_reply: אין צורך בתשובה (ניוזלטר, הודעה אוטומטית, קבלה, פרסומת, מייל לידיעה בלבד).
- simple: תשובה קצרה וחד-משמעית (אישור, תיאום, תודה, בקשה בודדת).
- complex: כמה שאלות או בעיות, תלונה, משא ומתן, או נושא רגיש.

דוגמאות:
מייל: 'הצטרפו לניוזלטר החודשי שלנו עם טיפים חדשים' -> no_reply
מייל: 'ההזמנה שלך נאספה בהצלחה מנקודת האיסוף' -> no_reply
מייל: 'האם נוח לך להיפגש ביום שלישי בעשר?' -> simple
מייל: 'תודה רבה על המסמך, קיבלתי' -> simple
מייל: 'המוצר הגיע באיחור, חסר חלק, וגם החשבונית שגויה. מה תעשו בנידון?' -> complex
מייל: 'יש לי שלוש שאלות לגבי ההצעה: מחיר, לוחות זמנים והתחייבויות' -> complex
"""


def _to_text(content) -> str:
    """מודלים חדשים מחזירים לפעמים רשימת בלוקים (טקסט + מידע טכני). לוקחים רק את הטקסט."""
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts).strip()


def _email_text(email: dict) -> str:
    return f"From: {email['from']}\nSubject: {email['subject']}\n\n{email['body']}"


def _flags(config: RunnableConfig | None) -> tuple[bool, bool]:
    c = (config or {}).get("configurable", {})
    return c.get("use_critic", True), c.get("few_shot", True)


# ---------------------------------------------------------------- Nodes
def fetch_email(state: State) -> dict:
    import gmail_utils  # import מאוחר, כדי שהגרף ייבדק גם בלי חיבור ל-Gmail

    return {"email": gmail_utils.fetch_email(state["message_id"]), "rounds": 0}


def classify(state: State, config: RunnableConfig) -> dict:
    _, few_shot = _flags(config)
    prompt = "סווג את המייל לאחת מהקטגוריות: no_reply, simple, complex.\n\n"
    if few_shot:
        prompt += CLASSIFY_GUIDE + "\n"
    prompt += _email_text(state["email"])
    result = get_llm().with_structured_output(Classification).invoke(prompt)
    return {"category": result.category}


def write_draft(state: State) -> dict:
    style = (
        "קצרה ועניינית" if state["category"] == "simple"
        else "מפורטת, עונה על כל נקודה ושאלה, בטון מקצועי ומנומס"
    )
    prompt = (
        f"כתוב טיוטת תשובה למייל הבא. התשובה צריכה להיות {style}. "
        "כתוב באותה שפה של המייל. החזר רק את גוף התשובה.\n\n"
        + _email_text(state["email"])
    )
    if state.get("draft") and state.get("critic_notes"):
        prompt += (
            f"\n\nטיוטה קודמת:\n{state['draft']}\n\n"
            f"הערות לתיקון:\n{state['critic_notes']}\n\nשכתב בהתאם להערות."
        )
    draft = _to_text(get_llm().invoke(prompt).content)
    return {"draft": draft, "rounds": state.get("rounds", 0) + 1}


def critic(state: State) -> dict:
    llm = get_llm().with_structured_output(Verdict)
    verdict = llm.invoke(
        "בדוק את הטיוטה מול המייל המקורי: האם ענתה על כל השאלות והנקודות, "
        "האם הטון מתאים, והאם אין בה הבטחות שלא הוזכרו במייל.\n\n"
        f"המייל:\n{_email_text(state['email'])}\n\nהטיוטה:\n{state['draft']}"
    )
    return {"critic_ok": verdict.ok, "critic_notes": verdict.notes}


def human_review(state: State) -> dict:
    # העצירה: הגרף נעצר כאן ומחכה. הערך שחוזר הוא מה שהועבר ב-Command(resume=...)
    answer = interrupt(
        {
            "email": _email_text(state["email"]),
            "draft": state["draft"],
            "critic_notes": state.get("critic_notes", ""),
            "rounds": state["rounds"],
        }
    )
    return {"decision": answer["action"], "final_text": answer.get("text", "")}


def save_draft(state: State) -> dict:
    import gmail_utils

    text = state["final_text"] if state["decision"] == "edit" else state["draft"]
    return {"draft_id": gmail_utils.create_draft(state["email"], text)}


# ---------------------------------------------------------------- Graph
def build_graph(for_eval: bool = False):
    # אחרי הכתיבה/הבקרה: בריצה רגילה ממשיכים לאישור אנושי, בהערכה מסיימים
    final = END if for_eval else "human_review"

    def route_after_classify(state: State) -> str:
        return END if state["category"] == "no_reply" else "write_draft"

    def route_after_write(state: State, config: RunnableConfig) -> str:
        use_critic, _ = _flags(config)
        return "critic" if use_critic else final

    def route_after_critic(state: State) -> str:
        if state["critic_ok"] or state["rounds"] >= MAX_ROUNDS:
            return final
        return "write_draft"  # הלולאה

    def route_after_review(state: State) -> str:
        return END if state["decision"] == "reject" else "save_draft"

    g = StateGraph(State)
    g.add_node("classify", classify)
    g.add_node("write_draft", write_draft)
    g.add_node("critic", critic)

    if for_eval:
        g.add_edge(START, "classify")
    else:
        g.add_node("fetch_email", fetch_email)
        g.add_node("human_review", human_review)
        g.add_node("save_draft", save_draft)
        g.add_edge(START, "fetch_email")
        g.add_edge("fetch_email", "classify")
        g.add_conditional_edges("human_review", route_after_review, ["save_draft", END])
        g.add_edge("save_draft", END)

    g.add_conditional_edges("classify", route_after_classify, ["write_draft", END])
    g.add_conditional_edges("write_draft", route_after_write, ["critic", final])
    g.add_conditional_edges("critic", route_after_critic, ["write_draft", final])

    # ה-checkpointer שומר את המצב בזמן העצירה (בהערכה אין עצירה, ולכן אין צורך)
    return g.compile(checkpointer=None if for_eval else MemorySaver())
