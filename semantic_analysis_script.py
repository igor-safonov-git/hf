#!/usr/bin/env python3
"""
Analyze semantic relevance of 20 random queries from test results
"""
import json
import random

# Load test results
with open('comprehensive_test_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get all queries
queries = [result['query'] for result in data['results']]

# Sample 20 random queries
random.seed(42)  # For reproducible results
sample_queries = random.sample(queries, 20)

print("🔍 SEMANTIC RELEVANCE ANALYSIS")
print("=" * 60)
print("Analyzing 20 random queries for semantic relevance to recruitment systems:")
print()

# Categorize queries by semantic relevance
categories = {
    "🟢 RECRUITMENT CORE": [],      # Direct recruitment process
    "🟡 RECRUITMENT ADJACENT": [],  # Related to hiring but stretches boundaries  
    "🔴 EMPLOYEE LIFECYCLE": [],    # Post-hire employee data (impossible)
    "⚪ AMBIGUOUS": []              # Could be interpreted either way
}

for i, query in enumerate(sample_queries, 1):
    print(f"{i:2d}. {query}")
    
    # Analyze semantic relevance
    query_lower = query.lower()
    
    # Core recruitment terms
    recruitment_terms = ["кандидат", "вакансии", "найм", "рекрутер", "источник", "интервью", "оффер", "собеседование", "отбор", "воронка", "конверсия"]
    
    # Employee lifecycle terms (post-hire)
    employee_terms = ["уволилось", "увольнения", "текучесть", "стаж работы", "удовлетворенность сотрудников", "повышения", "бонусы", "обучение", "тренинги", "работает больше", "работает удаленно", "графику"]
    
    # Time/duration terms that could be ambiguous
    time_terms = ["дней", "месяц", "год", "время", "срок"]
    
    if any(term in query_lower for term in ["кандидат", "вакансии", "найм", "рекрутер", "источник", "интервью", "оффер", "собеседование", "отбор", "воронка", "конверсия"]):
        if any(term in query_lower for term in employee_terms):
            categories["⚪ AMBIGUOUS"].append((i, query))
            print("   ⚪ AMBIGUOUS - Contains both recruitment and employee terms")
        else:
            categories["🟢 RECRUITMENT CORE"].append((i, query))
            print("   🟢 RECRUITMENT CORE - Direct recruitment process")
    elif any(term in query_lower for term in employee_terms):
        categories["🔴 EMPLOYEE LIFECYCLE"].append((i, query))
        print("   🔴 EMPLOYEE LIFECYCLE - Post-hire employee data")
    else:
        categories["🟡 RECRUITMENT ADJACENT"].append((i, query))
        print("   🟡 RECRUITMENT ADJACENT - Related but stretches boundaries")
    
    print()

# Summary
print("📊 SEMANTIC RELEVANCE SUMMARY")
print("=" * 60)

for category, queries in categories.items():
    count = len(queries)
    percentage = (count / 20) * 100
    print(f"{category}: {count}/20 ({percentage:4.1f}%)")

print()
print("🔍 DETAILED ANALYSIS:")
print()

for category, query_list in categories.items():
    if query_list:
        print(f"{category}:")
        for num, query in query_list:
            print(f"  {num:2d}. {query}")
        print()

# Analysis conclusions
recruitment_core = len(categories["🟢 RECRUITMENT CORE"])
recruitment_adjacent = len(categories["🟡 RECRUITMENT ADJACENT"])
employee_lifecycle = len(categories["🔴 EMPLOYEE LIFECYCLE"])
ambiguous = len(categories["⚪ AMBIGUOUS"])

total_recruitment_relevant = recruitment_core + recruitment_adjacent + ambiguous

print("💡 CONCLUSIONS:")
print(f"• Pure recruitment queries: {recruitment_core}/20 ({recruitment_core/20*100:.1f}%)")
print(f"• Recruitment-adjacent: {recruitment_adjacent}/20 ({recruitment_adjacent/20*100:.1f}%)")
print(f"• Employee lifecycle (should be impossible): {employee_lifecycle}/20 ({employee_lifecycle/20*100:.1f}%)")
print(f"• Ambiguous (could go either way): {ambiguous}/20 ({ambiguous/20*100:.1f}%)")
print()
print(f"• Total recruitment-relevant: {total_recruitment_relevant}/20 ({total_recruitment_relevant/20*100:.1f}%)")
print(f"• Queries that should trigger impossible response: {employee_lifecycle}/20 ({employee_lifecycle/20*100:.1f}%)")