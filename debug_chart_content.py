"""
Debug chart content validation logic
"""

# Sample chart data from the response
chart_real_data = {
    'labels': ['Отказ', 'Новые', 'Резюме у заказчика', 'Отправлено письмо', 'Интервью', 'Тестовое задание', 'Звонок кандидату', 'Оффер принят', 'Видеоинтервью пройдено', 'Обратная связь от заказчика', 'Выставлен оффер', 'Видеоинтервью', 'Тестирование SHL пройдено', 'Вышел на работу'], 
    'values': [22, 18, 7, 6, 5, 4, 4, 3, 3, 2, 2, 2, 1, 1], 
    'title': 'Distribution of Candidates by Recruitment Stage'
}

print("🔍 Debug Chart Content Validation")
print("=" * 40)

print(f"Chart data type: {type(chart_real_data)}")
print(f"Is list: {isinstance(chart_real_data, list)}")
print(f"Length: {len(chart_real_data) if isinstance(chart_real_data, list) else 'Not a list'}")

# The validation logic expects a list of data points, but we're getting a dict
print("\n❌ Issue Found:")
print("The validation logic expects: list of data points")
print("But chart_real_data is: dictionary with labels/values structure")

print("\n🔧 Fix needed:")
print("Update content validation to handle both:")
print("1. List format: [{'label': 'A', 'value': 10}, ...]")
print("2. Dict format: {'labels': [...], 'values': [...]}")

# Check if dict format has meaningful data
if isinstance(chart_real_data, dict):
    labels = chart_real_data.get('labels', [])
    values = chart_real_data.get('values', [])
    
    print(f"\n✅ Dict format analysis:")
    print(f"Labels count: {len(labels)}")
    print(f"Values count: {len(values)}")
    print(f"Non-zero values: {sum(1 for v in values if v != 0)}")
    print(f"Total data points: {sum(values)}")
    
    has_meaningful_data = len(labels) > 0 and len(values) > 0 and any(v != 0 for v in values)
    print(f"Has meaningful data: {'✅' if has_meaningful_data else '❌'}")