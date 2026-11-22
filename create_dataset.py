"""יוצר את הדאטהסט ב-LangSmith (מריצים פעם אחת).

דורש LANGSMITH_API_KEY בקובץ .env
"""
from dotenv import load_dotenv

load_dotenv()

import truststore

truststore.inject_into_ssl()  # שימוש באישורי Windows, פותר שגיאת SSL

from langsmith import Client

from dataset_data import EXAMPLES

DATASET_NAME = "email-agent-dataset"


def main():
    client = Client()
    if client.has_dataset(dataset_name=DATASET_NAME):
        print("הדאטהסט כבר קיים, לא יוצר מחדש.")
        return
    dataset = client.create_dataset(
        DATASET_NAME, description="מיילים מדומים עם הסיווג הנכון לכל אחד"
    )
    client.create_examples(
        inputs=[{"email": e["email"]} for e in EXAMPLES],
        outputs=[{"category": e["category"]} for e in EXAMPLES],
        dataset_id=dataset.id,
    )
    print(f"נוצר דאטהסט עם {len(EXAMPLES)} דוגמאות.")


if __name__ == "__main__":
    main()
