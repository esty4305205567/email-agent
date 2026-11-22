"""הרצת הסוכן על מייל אמיתי מ-Gmail, כולל שלב האישור האנושי.

שימוש:
    python run.py              # לוקח את המייל הלא-נקרא האחרון
    python run.py MESSAGE_ID   # מייל ספציפי
"""
import sys
import uuid

from dotenv import load_dotenv

load_dotenv()

import truststore

truststore.inject_into_ssl()  # שימוש באישורי Windows, פותר שגיאת SSL

from langgraph.types import Command

import gmail_utils
from graph import build_graph


def main():
    message_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not message_id:
        unread = gmail_utils.list_unread(max_results=1)
        if not unread:
            print("אין מיילים שלא נקראו.")
            return
        message_id = unread[0]

    graph = build_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    result = graph.invoke({"message_id": message_id}, config)

    # אם הגרף נעצר ב-interrupt, התוצאה מכילה __interrupt__
    if "__interrupt__" in result:
        info = result["__interrupt__"][0].value
        print("\n=== המייל ===\n" + info["email"])
        print("\n=== הטיוטה ===\n" + info["draft"])
        if info["critic_notes"]:
            print("\n=== הערות המבקר שנשארו ===\n" + info["critic_notes"])

        choice = input("\n[a]אשר / [e]ערוך / [r]דחה: ").strip().lower()
        if choice == "a":
            answer = {"action": "approve"}
        elif choice == "e":
            print("הדבק נוסח חדש (סיים בשורה ריקה):")
            lines = []
            while (line := input()) != "":
                lines.append(line)
            answer = {"action": "edit", "text": "\n".join(lines)}
        else:
            answer = {"action": "reject"}

        result = graph.invoke(Command(resume=answer), config)

    if result.get("draft_id"):
        print("הטיוטה נשמרה ב-Gmail:", result["draft_id"])
    else:
        print("לא נשמרה טיוטה (לא נדרשה תשובה, או שנדחתה).")


if __name__ == "__main__":
    main()
