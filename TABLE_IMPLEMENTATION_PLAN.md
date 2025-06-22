# Table Chart Type Implementation Plan

## Overview
This document outlines the comprehensive plan for implementing a table chart type in the Huntflow analytics system. Tables will provide a way to display detailed entity listings and breakdowns, complementing the existing bar, line, and scatter charts.

## Architecture Analysis

### Current System
- **Backend**: `chart_data_processor.py` → `universal_chart_processor.py` → real data processing
- **Frontend**: Chart.js rendering for bar/line/scatter visualizations
- **AI Prompt**: Rules for chart type selection (currently supports bar, line, scatter)

### Key Challenge
Chart.js does not support tables, requiring a parallel rendering system in the frontend.

## Implementation Plan

### Phase 1: Backend Data Processing

#### 1.1 Update chart_data_processor.py
**File**: `chart_data_processor.py`
**Changes**:
```python
# Line ~197 - Add to SUPPORTED_CHART_TYPES
SUPPORTED_CHART_TYPES = {'bar', 'line', 'scatter', 'table'}

# Modify validate_chart_config() to skip certain validations for tables
def validate_chart_config(chart_config: Dict) -> Tuple[bool, str]:
    if chart_config.get('type') == 'table':
        # Tables don't need x_axis/y_axis validation
        return True, ""
    # ... existing validation logic
```

#### 1.2 Create Table Data Structure
**File**: `universal_chart_processor.py`
**New Methods**:
```python
def _format_for_table(self, data_rows: List[Dict], group_by_field: str) -> Dict:
    """
    Format data for table display with columns and rows
    
    Returns:
        {
            "columns": [
                {"key": "name", "label": "Имя", "type": "text", "sortable": true},
                {"key": "count", "label": "Количество", "type": "number", "sortable": true},
                {"key": "percentage", "label": "Процент", "type": "percentage", "sortable": true}
            ],
            "rows": [
                {"name": "Анастасия Богач", "count": 45, "percentage": 23.5},
                {"name": "Михаил Танский", "count": 38, "percentage": 19.8}
            ],
            "metadata": {
                "total_rows": 15,
                "sorted_by": "count",
                "sort_order": "desc"
            }
        }
    """
```

### Phase 2: Frontend Table Rendering

#### 2.1 Add Table Rendering Function
**File**: `index.html`
**Location**: After Chart.js functions (~line 450)
```javascript
const renderTable = (tableData, container) => {
    // Clear container
    container.innerHTML = '';
    
    // Create wrapper div for responsive scrolling
    const wrapper = document.createElement('div');
    wrapper.className = 'table-wrapper';
    
    // Create table element
    const table = document.createElement('table');
    table.className = 'data-table';
    
    // Generate table header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    tableData.columns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col.label;
        th.className = col.sortable ? 'sortable' : '';
        th.dataset.key = col.key;
        
        if (col.sortable) {
            th.addEventListener('click', () => sortTable(col.key));
        }
        
        headerRow.appendChild(th);
    });
    
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Generate table body
    const tbody = document.createElement('tbody');
    
    tableData.rows.forEach(row => {
        const tr = document.createElement('tr');
        
        tableData.columns.forEach(col => {
            const td = document.createElement('td');
            const value = row[col.key];
            
            // Format based on column type
            switch(col.type) {
                case 'number':
                    td.textContent = value.toLocaleString('ru-RU');
                    td.className = 'numeric';
                    break;
                case 'percentage':
                    td.textContent = `${value.toFixed(1)}%`;
                    td.className = 'numeric';
                    break;
                default:
                    td.textContent = value;
            }
            
            tr.appendChild(td);
        });
        
        tbody.appendChild(tr);
    });
    
    table.appendChild(tbody);
    wrapper.appendChild(table);
    container.appendChild(wrapper);
};
```

#### 2.2 Modify Chart Rendering Logic
**Location**: In the useEffect that handles chart rendering (~line 430)
```javascript
// Check if it's a table type
if (report?.chart?.type === 'table') {
    // Get the chart container
    const container = chartRef.current.parentElement;
    
    // Render table instead of chart
    if (report.chart.real_data) {
        renderTable(report.chart.real_data, container);
    }
} else {
    // Existing Chart.js rendering logic
    const ctx = chartRef.current.getContext('2d');
    // ... rest of chart rendering
}
```

#### 2.3 Add Table CSS Styling
**Location**: In the <style> section (~line 100)
```css
.table-wrapper {
    width: 100%;
    overflow-x: auto;
    border-radius: 0.5rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
    background-color: white;
}

.data-table thead {
    background-color: #f9fafb;
}

.data-table th {
    padding: 0.75rem 1rem;
    text-align: left;
    font-weight: 600;
    color: #374151;
    border-bottom: 2px solid #e5e7eb;
    white-space: nowrap;
}

.data-table th.sortable {
    cursor: pointer;
    user-select: none;
    position: relative;
    padding-right: 2rem;
}

.data-table th.sortable:hover {
    background-color: #f3f4f6;
}

.data-table th.sortable::after {
    content: '↕';
    position: absolute;
    right: 0.75rem;
    opacity: 0.5;
}

.data-table th.sortable.asc::after {
    content: '↑';
    opacity: 1;
}

.data-table th.sortable.desc::after {
    content: '↓';
    opacity: 1;
}

.data-table td {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid #e5e7eb;
}

.data-table td.numeric {
    text-align: right;
    font-variant-numeric: tabular-nums;
}

.data-table tbody tr:hover {
    background-color: #f9fafb;
}

.data-table tbody tr:last-child td {
    border-bottom: none;
}

/* Mobile responsive */
@media (max-width: 640px) {
    .data-table {
        font-size: 0.75rem;
    }
    
    .data-table th,
    .data-table td {
        padding: 0.5rem;
    }
}
```

### Phase 3: AI Prompt Integration

#### 3.1 Update prompt.py
**Location**: Chart type rules section (~line 23)
```python
# Update supported chart types
"5. Choose chart type: bar, line, scatter, or table"

# Add table selection rules (after existing chart rules ~line 84)
"""
• TABLE: Use for entity listings, detailed breakdowns, "who/which/list" questions
  ✅ "Список всех рекрутеров" → table with recruiter names and metrics
  ✅ "Какие вакансии открыты?" → table with vacancy details
  ✅ "Покажи источники кандидатов" → table with source breakdown
  ✅ "Кто из рекрутеров нанял больше всех?" → table sorted by hires
  Example: {"type": "table", "label": "Список рекрутеров"}
"""

# Add table example in JSON examples section
"""
❌ WRONG - Using chart for entity listing:
Question: "Покажи всех рекрутеров"
{
  "chart": {"type": "bar"}  // ❌ Should be "table" for listings
}

✅ CORRECT - Using table for entity listing:
Question: "Покажи всех рекрутеров"
{
  "chart": {"type": "table"}  // ✅ Table for detailed entity lists
}
"""
```

### Phase 4: Entity-Specific Configurations

#### 4.1 Table Templates by Entity Type
**File**: `universal_chart_processor.py`
```python
TABLE_CONFIGURATIONS = {
    'recruiters': {
        'columns': [
            {'key': 'name', 'label': 'Рекрутер', 'type': 'text'},
            {'key': 'hires_count', 'label': 'Нанято', 'type': 'number'},
            {'key': 'applicants_count', 'label': 'Кандидатов', 'type': 'number'},
            {'key': 'conversion_rate', 'label': 'Конверсия', 'type': 'percentage'},
            {'key': 'avg_time_to_hire', 'label': 'Среднее время найма', 'type': 'number'}
        ],
        'default_sort': {'field': 'hires_count', 'order': 'desc'},
        'row_limit': 50
    },
    
    'vacancies': {
        'columns': [
            {'key': 'position', 'label': 'Позиция', 'type': 'text'},
            {'key': 'status', 'label': 'Статус', 'type': 'text'},
            {'key': 'created_date', 'label': 'Дата создания', 'type': 'date'},
            {'key': 'days_open', 'label': 'Дней открыта', 'type': 'number'},
            {'key': 'applicants_count', 'label': 'Кандидатов', 'type': 'number'}
        ],
        'default_sort': {'field': 'created_date', 'order': 'desc'},
        'row_limit': 100
    },
    
    'sources': {
        'columns': [
            {'key': 'name', 'label': 'Источник', 'type': 'text'},
            {'key': 'applicants_count', 'label': 'Кандидатов', 'type': 'number'},
            {'key': 'hires_count', 'label': 'Нанято', 'type': 'number'},
            {'key': 'conversion_rate', 'label': 'Конверсия', 'type': 'percentage'},
            {'key': 'avg_time_to_hire', 'label': 'Время найма', 'type': 'number'}
        ],
        'default_sort': {'field': 'applicants_count', 'order': 'desc'},
        'row_limit': 30
    },
    
    'stages': {
        'columns': [
            {'key': 'name', 'label': 'Этап', 'type': 'text'},
            {'key': 'applicants_count', 'label': 'Кандидатов', 'type': 'number'},
            {'key': 'percentage', 'label': 'От общего', 'type': 'percentage'},
            {'key': 'avg_days_in_stage', 'label': 'Дней на этапе', 'type': 'number'}
        ],
        'default_sort': {'field': 'order', 'order': 'asc'},
        'row_limit': 20
    }
}
```

### Phase 5: Testing Plan

#### 5.1 Test Scenarios
1. **Basic Table Queries**
   - "Покажи всех рекрутеров"
   - "Список открытых вакансий"
   - "Какие источники мы используем?"

2. **Filtered Table Queries**
   - "Рекрутеры за последние 3 месяца"
   - "Вакансии на Python разработчиков"
   - "Источники с конверсией больше 10%"

3. **Sorted Table Queries**
   - "Топ-5 рекрутеров по найму"
   - "Самые старые открытые вакансии"
   - "Источники по эффективности"

4. **Edge Cases**
   - Empty data sets
   - Very large data sets (100+ rows)
   - Mobile responsive behavior
   - Long text values

#### 5.2 Validation Checklist
- [ ] AI correctly chooses table type for listing queries
- [ ] Tables render with proper columns and formatting
- [ ] Data is accurate and matches filters
- [ ] Sorting works correctly
- [ ] Responsive design on mobile devices
- [ ] No regression in existing chart functionality
- [ ] Performance acceptable for large datasets

### Phase 6: Future Enhancements

1. **Interactive Features**
   - Client-side sorting
   - Column reordering
   - Inline search/filtering
   - Row selection

2. **Export Functionality**
   - Export to CSV
   - Copy to clipboard
   - Print-friendly view

3. **Advanced Display**
   - Pagination for large datasets
   - Expandable row details
   - Column grouping
   - Footer with totals/summaries

## Implementation Timeline

**Day 1**: Backend implementation (Phases 1.1-1.2)
**Day 2**: Frontend implementation (Phases 2.1-2.3)
**Day 3**: AI prompt integration and testing (Phases 3-5)
**Day 4**: Polish and bug fixes

## Success Metrics

1. **Functionality**: Tables display correctly for all entity types
2. **AI Accuracy**: >90% correct chart type selection for listing queries
3. **Performance**: Tables render in <500ms for up to 100 rows
4. **User Experience**: Clean, readable, responsive design
5. **Code Quality**: No regressions, clean implementation

## Risk Mitigation

1. **Performance Risk**: Large datasets
   - Mitigation: Implement row limits and pagination
   
2. **Mobile UX Risk**: Tables on small screens
   - Mitigation: Horizontal scroll, responsive font sizes
   
3. **AI Selection Risk**: Confusion between table and bar charts
   - Mitigation: Clear rules and examples in prompt

## Conclusion

This implementation adds tables as a first-class visualization option, enabling detailed entity listings and breakdowns that complement the existing aggregate visualizations. The approach maintains clean separation between chart and table rendering while reusing the existing data processing infrastructure.