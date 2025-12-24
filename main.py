"""
Стандарт документации и оформления кода:

В решении используется единый стандарт оформления:
- документация функций оформлена в соответствии с PEP 257,
- аннотации типов соответствуют PEP 484.
"""


from dataclasses import dataclass
import urllib.request
from pathlib import Path
import json
import sys
import re

JSON_URL = 'raw-git-link'
JSON_FILE = Path("okved.json")

@dataclass(frozen=True)
class NormalizeResult:
    ok: bool
    value: str | None = None
    error: str | None = None

@dataclass(frozen=True)
class OkvedItem:
    code: str
    name: str
    code_digits: str

def download_okved_file(url: str, target: Path) -> None:
    """
    Скачиваем JSON файл
    :param url:
    :param target:
    :return:
    """
    with urllib.request.urlopen(url, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP error: {response.status}")
        target.write_bytes(response.read())

def normalise_phone_number(phone_number: str) -> NormalizeResult:
    """
    Метод нормализации мобильного телефона задаваемого пользователем
    :param phone_number: сырая строка с номером телефона, введенная пользователем
    :return:
    """
    digits = re.sub(r"\D", "", phone_number)

    # Извлекаем только цифры из введенной пользователем строки
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    # Возвращаем формат 11 цифр с кодом региона
    elif len(digits) == 11 and digits.startswith("7"):
        pass
    elif len(digits) == 10 and digits.startswith("9"):
        digits = "7" + digits
    else:
        return NormalizeResult(False, error="Неподдерживаемый формат мобильного номера телефона")
    # Проверка на стандартную длину номера телефона
    if len(digits) != 11:
        return NormalizeResult(False, error="Номер не может быть приведён к формату +79XXXXXXXXX")

    # Валидация по РФ номеру (79)
    if not digits.startswith("79"):
        return NormalizeResult(False, error="Не РФ мобильный номер телефона (+79XXXXXXXXX)")

    # Преобразуем в нормальный формат для номера телефона
    return NormalizeResult(True, value=f"+{digits}")

def parse_json(data: list[dict]) -> list[OkvedItem]:
    """
    Алгоритм парсинга JSON - файла
    :param data: JSON - файл
    :return result: Список записей в виде - OkvedItem(code = "01.11.13", name = "Садоводство", code_digits = "011113")
    """
    result: list[OkvedItem] = []

    def walk(node: dict) -> None:
        code = node.get("code")
        name = node.get("name")

        if code and name:
            code_digits = re.sub(r"\D", "", code)
            if code_digits:
                result.append(OkvedItem(code=code, name=name, code_digits=code_digits))

        for child in node.get("items", []):
            walk(child)
    for root in data:
        walk(root)

    return result

def find_match(phone: str, okved_items: list[OkvedItem]) -> tuple[OkvedItem | None, int]:
    """
    Метод поиска наилучшего совпадения хвоста мобильного номера телефона и кода ОКВЭД
    :param phone:
    :param okved_items:
    :return:
    """
    best_match = None
    best_length = 0

    for item in okved_items:
        if phone.endswith(item.code_digits):
            length = len(item.code_digits)
            if length > best_length:
                best_length = length
                best_match = item

    return best_match, best_length

def fallback_okved(okved_items: list[OkvedItem]) -> OkvedItem:
    """
    Дополнительная стратегия поиска best_match
    :param okved_items: список собранных из JSON - файла объектов
    :return:
    """
    return min(okved_items, key=lambda x: len(x.code_digits))

def main(argv: list[str]) -> int:
    """
    Проверка на ввод аргументов запуска скрипта: обязательно название скрипта и номера мобильного телефона:
    example.py 89XXXXXXXXX/example.py 79XXXXXXXXX/example.py +79XXXXXXXXX
    :param argv: Лист с аргументами: Название скрипта + номер мобильного телефона
    :return: 0
    """
    # ШАГ 1 - проверка введённых параметров и нормализация введённого мобильного номера телефона
    # Проверка на количество параметров запуска
    if len(argv) < 2:
        print(f"Вы использовали неверный формат запуска, попробуйте: python {Path(__file__).name} '<номер мобильного телефона>'")
        return 1

    # Проверка на проблемный формат ввода мобильного номера телефона
    elif len(argv) > 2:
        print("Номер телефона введен с разделителями/знаками, необходимо преобразование")
        raw_phone = " ".join(argv[1:])
        result = normalise_phone_number(raw_phone)

        if not result.ok:
            print("False")
            print(f"Error: {result.error}")
            return 1

        print("Нормализованная форма введённого номера телефона:", result.value)

    # Штатный случай, когда пользователь ввёл корректно 2 аргумента на запуск
    else:
        result = normalise_phone_number(argv[1])

        if not result.ok:
            print(f"False\nОшибка: {result.error}")
            return 1

        print(result.value)

    # ШАГ 2 - скачивание json - файла (если требуется)
    if not JSON_FILE.is_file():
        print("Файл okved.json отсутствует — скачиваем")
        try:
            download_okved_file(JSON_URL, JSON_FILE)
        except Exception as e:
            print("false")
            print(f"error: {e}")
            return 1
    else:
        print("Файл okved.json уже скачан")


    # ШАГ 3 - поиск кода ОКВЭД в файле по совпадению с хвостом введённого номера телефона

    data = json.loads(JSON_FILE.read_text(encoding="utf-8"))
    okved_items = parse_json(data)

    phone_digits = result.value.lstrip("+")
    best, match_len = find_match(phone_digits, okved_items)

    if best is None:
        best = fallback_okved(okved_items)
        match_len = 0

    print(f"ОКВЭД: {best.code} — {best.name}")
    print(f"Длина совпадения: {match_len}")

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
