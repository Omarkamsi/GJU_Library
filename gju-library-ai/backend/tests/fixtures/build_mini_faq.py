import openpyxl

wb = openpyxl.Workbook()
ws = wb.active
ws.append(["Q (EN)", "Q (AR)", "A (EN)", "A (AR)", "Category"])
ws.append(
    [
        "What are the library hours?",
        "ما هي ساعات الدوام؟",
        "Open 8am–5pm.",
        "مفتوحة من 8 صباحًا إلى 5 مساءً.",
        "General",
    ]
)
ws.append([None, "أين تقع المكتبة؟", None, "داخل حرم الجامعة.", "General"])
wb.save("tests/fixtures/mini_faq.xlsx")
