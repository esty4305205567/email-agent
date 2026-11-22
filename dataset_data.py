"""30 מיילים לדוגמה (מדומים, בלי מידע אישי) עם הסיווג הנכון לכל אחד."""

def _m(sender, subject, body, category):
    return {
        "email": {"from": sender, "subject": subject, "body": body},
        "category": category,
    }

EXAMPLES = [
    # ---------------- no_reply (8)
    _m("news@techdigest.example", "הסיכום השבועי: חדשות טכנולוגיה",
       "שלום, אלו הכתבות המובילות השבוע. לביטול המנוי לחצו כאן.", "no_reply"),
    _m("orders@shop.example", "ההזמנה שלך נשלחה",
       "ההזמנה מספר 4471 יצאה אליך. מספר מעקב: IL88123. אין צורך להשיב להודעה זו.", "no_reply"),
    _m("security@service.example", "הסיסמה שלך שונתה",
       "הסיסמה בחשבונך שונתה היום. אם זה היית אתה, אין צורך בפעולה.", "no_reply"),
    _m("dan@company.example", "תשובה אוטומטית: מחוץ למשרד",
       "אני לא זמין עד יום ראשון ואחזור להודעות עם שובי.", "no_reply"),
    _m("events@webinar.example", "תזכורת: הוובינר מחר בעשר",
       "זוהי תזכורת אוטומטית לוובינר שנרשמת אליו. קישור להצטרפות מצורף.", "no_reply"),
    _m("secretary@school.example", "פרוטוקול הישיבה לידיעה",
       "מצורף הפרוטוקול של הישיבה האחרונה, לידיעתכם בלבד. אין צורך בתגובה.", "no_reply"),
    _m("sales@store.example", "מבצע סוף עונה, עד 40% הנחה",
       "הצטרפו למבצע הגדול שלנו. ההטבה בתוקף עד סוף החודש.", "no_reply"),
    _m("billing@hosting.example", "קבלה על תשלום",
       "תודה על התשלום. קבלה מספר 9032 על סך 49 ש\"ח מצורפת להודעה.", "no_reply"),

    # ---------------- simple (11)
    _m("yossi@company.example", "פגישה ביום שלישי",
       "היי, נוח לך שניפגש ביום שלישי בארבע אחר הצהריים? תאשר לי בבקשה.", "simple"),
    _m("rachel@friend.example", "תודה על העזרה",
       "רציתי להגיד תודה על העזרה עם המצגת, ממש עזר לי.", "simple"),
    _m("avi@team.example", "אפשר לשלוח שוב את הקובץ?",
       "היי, לא מצליח לפתוח את הקובץ שנשלח אתמול. אפשר לשלוח שוב?", "simple"),
    _m("teacher@course.example", "קיבלת את המטלה?",
       "שלום, שלחתי אתמול את פרטי המטלה. אשמח שתאשרי שהגיעו אלייך.", "simple"),
    _m("moshe@client.example", "אפשר להזיז לחמישי?",
       "שלום, האם אפשר להעביר את השיחה שלנו מיום רביעי ליום חמישי באותה שעה?", "simple"),
    _m("sara@team.example", "פנוי לשיחה מחר?",
       "היי, יש לי שאלה קצרה לגבי המסמך. אתה פנוי לשיחה של חמש דקות מחר בבוקר?", "simple"),
    _m("office@company.example", "אישור הגעה לאירוע החברה",
       "האירוע השנתי יתקיים ביום חמישי הבא. אנא אשרו הגעה עד יום שני.", "simple"),
    _m("dana@partner.example", "מה הכתובת של המשרד?",
       "שלום, אני מגיעה אליכם מחר ולא מוצאת את הכתובת המדויקת. תוכל לשלוח?", "simple"),
    _m("accounts@supplier.example", "אישור קבלת חשבונית",
       "שלחנו חשבונית מספר 5520 בשבוע שעבר. אשמח לאישור קבלה.", "simple"),
    _m("nir@team.example", "האם יום ראשון מתאים להגשה?",
       "היי, אפשר להגיש את הטיוטה עד יום ראשון במקום חמישי? זה יעזור לי מאוד.", "simple"),
    _m("lea@colleague.example", "Quick check",
       "Hi, are you available for a call tomorrow at 11? Just need a quick yes or no.", "simple"),

    # ---------------- complex (11)
    _m("customer1@mail.example", "תלונה: הפרויקט מתעכב",
       "שלום, הפרויקט מתעכב כבר שלושה שבועות, לא קיבלתי עדכון ממישהו, והגרסה האחרונה שנשלחה כוללת טעויות שכבר ביקשתי לתקן. אני מבקש הסבר ולוח זמנים מחייב.", "complex"),
    _m("buyer@company.example", "שאלות לגבי ההצעה",
       "תודה על ההצעה. יש לי כמה שאלות: מה כולל המחיר, מתי אפשר להתחיל, האם יש אחריות, ומה קורה אם נרצה להרחיב בהמשך?", "complex"),
    _m("customer2@mail.example", "רוצה החזר כספי",
       "המוצר שקיבלתי לא עונה על מה שהובטח באתר. ניסיתי ליצור קשר פעמיים ולא ענו לי. אני דורש החזר מלא וגם הסבר מדוע לא חזרתם אליי.", "complex"),
    _m("customer3@mail.example", "פגום וגם רוצה לבטל מנוי",
       "הפריט שהזמנתי הגיע פגום, ובנוסף אני רוצה לבטל את המנוי החודשי שלי מיד. אשמח להנחיות לשני הנושאים.", "complex"),
    _m("lecturer@course.example", "הערות על העבודה",
       "קראתי את העבודה. יש שלושה דברים שצריך לתקן: המבנה, הבחירה במקורות וחלק הסיכום. בנוסף, האם תוכלי להסביר את ההחלטה בפרק השני?", "complex"),
    _m("manager@company.example", "סטטוס על שלוש המשימות",
       "אני צריך עדכון על שלוש המשימות הפתוחות. אני גם מודאג מהלו\"ז של הגרסה הבאה. אפשר לפגישה קצרה?", "complex"),
    _m("legal@vendor.example", "תנאי החוזה",
       "עברנו על הטיוטה. אנחנו לא מסכימים לסעיף התשלום ולסעיף הסיום, ומבקשים לדון בהארכת תקופת הניסיון. מה עמדתכם?", "complex"),
    _m("mentor@org.example", "משוב מפורט על ההצעה",
       "אשמח למשוב על ההצעה: מה החוזקות, מה החולשות, איך אפשר לצמצם עלויות, ומתי אפשר להציג אותה לוועדה?", "complex"),
    _m("student@course.example", "בקשה להארכה",
       "אני מבקשת הארכה להגשה כי היו לי נסיבות מורכבות בשבוע האחרון. אם לא ניתן, אשמח להבין אילו חלופות קיימות.", "complex"),
    _m("qa@team.example", "Bug report: login fails",
       "Login fails on mobile after the last update. Steps: open app, enter details, tap login. It also logs out other users. When can we expect a fix, and is there a workaround?", "complex"),
    _m("client@company.example", "Concerns about delivery",
       "We were promised delivery last week and nothing has arrived. The invoice also shows a charge we did not approve. Please explain and tell us how you plan to fix both.", "complex"),
]

assert len(EXAMPLES) == 30
