import re
import json

def parse_receipt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()

    result = {}

    price_pattern = r'\n(\d[\d\s]*,\d{2})\nСтоимость'
    prices = re.findall(price_pattern, text)
    prices = [float(p.replace(" ", "").replace(",", ".")) for p in prices]

    result["prices"] = prices

    product_pattern = r'\d+\.\n(.+?)\n\d'
    products = re.findall(product_pattern, text, re.DOTALL)

    products = [p.strip().replace('\n', ' ') for p in products]
    result["products"] = products

    calculated_total = sum(prices)
    result["calculated_total"] = round(calculated_total, 2)

    total_pattern = r'ИТОГО:\n([\d\s]*,\d{2})'
    total_match = re.search(total_pattern, text)
    if total_match:
        official_total = float(total_match.group(1).replace(" ", "").replace(",", "."))
        result["official_total"] = official_total

    datetime_pattern = r'Время:\s*(\d{2}\.\d{2}\.\d{4}\s*\d{2}:\d{2}:\d{2})'
    datetime_match = re.search(datetime_pattern, text)
    if datetime_match:
        result["datetime"] = datetime_match.group(1)

    payment_pattern = r'(Банковская карта|Наличные)'
    payment_match = re.search(payment_pattern, text)
    if payment_match:
        result["payment_method"] = payment_match.group(1)

    return result


if __name__ == "__main__":
    parsed_data = parse_receipt(r"C:\Users\rayym\OneDrive\Рабочий стол\PP2_assignments\practice5\raw.txt")

    print("---- Parsed Receipt ----")
    print(json.dumps(parsed_data, indent=4, ensure_ascii=False))