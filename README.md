# Phone → OKVED Matcher

Небольшая утилита для:
- нормализации российского мобильного номера к формату `+79XXXXXXXXX`,
- загрузки актуального `okved.json` по HTTPS,
- поиска кода ОКВЭД с максимальным совпадением по окончанию номера.

---

## Requirements

- Python 3.10+
- Внешние библиотеки не используются (только стандартная библиотека Python)

---

## Documentation & Code Style

The solution follows standard Python conventions:
- Docstrings are written according to **PEP 257**
- Type hints follow **PEP 484**
- Code style and naming follow **PEP 8**

---

## Run

```bash
python main.py "+7 (999) 123-45-67"
