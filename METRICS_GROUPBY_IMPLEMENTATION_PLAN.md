# Unified Metrics group_by vs Independent Chart group_by Implementation Plan

## Overview

This plan implements a unified `group_by` parameter for primary and secondary metrics while keeping charts with independent grouping. This allows for more flexible analytical reports where metrics can be grouped differently from chart visualizations.

## Current Architecture Analysis

### Current System
- **Metrics Processing**: Main/secondary metrics use `group_by=None` and return single aggregated values
- **Chart Processing**: Charts use individual `group_by` from x_axis/y_axis and return grouped data  
- **JSON Schema**: Each query (main_metric.value, secondary_metrics[].value, chart.x_axis, chart.y_axis) has its own `group_by`
- **Processing Flow**: 
  ```
  report_json → process_main_metric() → calculate_main_metric_value() → Universal Chart Processor
  report_json → process_secondary_metrics() → calculate_secondary_metric_value() → Universal Chart Processor  
  report_json → process_chart_data() → get_entity_data() → Universal Chart Processor
  ```

### Current Limitations
- Metrics always return aggregated totals (no grouping)
- No way to get grouped metrics (e.g., "hires by each recruiter" as metrics)
- Chart grouping and metrics processing are completely separate
- Missing analytical flexibility for comparative reports

## Proposed Architecture

### New Structure
```json
{
  "report_title": "Report Title",
  "metrics_group_by": "recruiters",           // NEW: Unified grouping for all metrics
  "main_metric": {
    "label": "Primary Metric", 
    "value": {
      "operation": "count",
      "entity": "hires",
      "filters": {"period": "1 month"}        // No individual group_by
    }
  },
  "secondary_metrics": [
    {
      "label": "Secondary Metric 1",
      "value": {
        "operation": "count", 
        "entity": "applicants",
        "filters": {"period": "1 month"}      // No individual group_by
      }
    }
  ],
  "chart": {
    "type": "line",
    "x_axis": {
      "operation": "count",
      "entity": "hires", 
      "group_by": {"field": "month"},         // Independent chart grouping
      "filters": {"period": "6 month"}
    },
    "y_axis": {
      "operation": "count",
      "entity": "hires",
      "group_by": {"field": "month"},         // Independent chart grouping  
      "filters": {"period": "6 month"}
    }
  }
}
```

### Key Benefits
1. **Flexible Analysis**: Metrics grouped by recruiters, chart shows trends over time
2. **Comparative Reports**: See individual recruiter performance + overall trends
3. **Business Context**: Specific entity metrics + broader analytical context
4. **Backward Compatibility**: Existing reports continue to work

## Implementation Phases

### Phase 1: Schema and Data Structure Updates

#### 1.1 Update JSON Schema in prompt.py
```json
{
  "type": "object",
  "required": ["report_title", "main_metric", "secondary_metrics", "chart"],
  "properties": {
    "report_title": { "type": "string" },
    "metrics_group_by": { 
      "type": ["string", "null"],
      "description": "Optional grouping field for all metrics (main + secondary)"
    },
    "main_metric": {
      "type": "object",
      "required": ["label", "value"],
      "properties": {
        "label": { "type": "string" },
        "value": { "$ref": "#/definitions/metrics_query" }  // New definition without group_by
      }
    },
    "secondary_metrics": {
      "type": "array", 
      "items": {
        "properties": {
          "label": { "type": "string" },
          "value": { "$ref": "#/definitions/metrics_query" }  // New definition without group_by
        }
      }
    },
    "chart": {
      // Keep existing structure with individual group_by
      "x_axis": { "$ref": "#/definitions/chart_query" },
      "y_axis": { "$ref": "#/definitions/chart_query" }
    }
  },
  "definitions": {
    "metrics_query": {
      "type": "object",
      "required": ["operation", "entity", "filters"],
      "properties": {
        "operation": { "enum": ["count", "avg", "sum", "date_trunc"] },
        "entity": { "enum": ["applicants","vacancies","recruiters","hiring_managers","stages","sources","hires","rejections","actions","divisions"] },
        "value_field": { "type": ["string", "null"] },
        "filters": { "type": "object" }
        // NO group_by - uses report-level metrics_group_by
      }
    },
    "chart_query": {
      // Existing query definition with group_by
      "type": "object", 
      "required": ["operation", "entity", "filters"],
      "properties": {
        "operation": { "enum": ["count", "avg", "sum", "date_trunc"] },
        "entity": { "enum": ["applicants","vacancies","recruiters","hiring_managers","stages","sources","hires","rejections","actions","divisions"] },
        "value_field": { "type": ["string", "null"] },
        "group_by": {
          "oneOf": [
            { "type": "null" },
            { "type": "object", "required": ["field"], "properties": { "field": { "type": "string" } } }
          ]
        },
        "filters": { "type": "object" }
      }
    }
  }
}
```

#### 1.2 Add TypeScript Types in chart_data_processor.py
```python
class MetricsQuery(TypedDict):
    operation: str
    entity: str
    value_field: Optional[str]
    filters: Dict[str, Any]
    # No group_by field

class MainMetric(TypedDict):
    label: str
    value: MetricsQuery

class SecondaryMetric(TypedDict):
    label: str
    value: MetricsQuery

class ReportJson(TypedDict):
    report_title: str
    metrics_group_by: Optional[str]  # NEW
    main_metric: MainMetric
    secondary_metrics: List[SecondaryMetric]
    chart: ChartConfig
```

### Phase 2: Processing Logic Updates

#### 2.1 Update calculate_main_metric_value()
```python
async def calculate_main_metric_value(
    entity: str, 
    operation: str, 
    calc: EnhancedMetricsCalculator, 
    filters: Optional[Dict[str, Any]] = None,
    metrics_group_by: Optional[str] = None  # NEW parameter
) -> Union[int, float, Dict[str, Any]]:
    """Calculate main metric value - grouped or aggregated based on metrics_group_by."""
    
    try:
        result = await process_chart_via_universal_engine(
            entity=entity,
            operation=operation,
            group_by=metrics_group_by,  # Use report-level grouping
            filters=filters,
            calc=calc
        )
        
        if metrics_group_by:
            # Return grouped data: {"Nastya": 5, "Igor": 3, "Maria": 8}
            return dict(zip(result.get("labels", []), result.get("values", [])))
        else:
            # Return single aggregated value: 16
            if isinstance(result.get("values"), list) and result["values"]:
                return sum(result["values"]) if operation == "count" else result["values"][0]
            return 0
            
    except Exception as e:
        logger.error(f"Main metric calculation error: {e}")
        return 0 if not metrics_group_by else {}
```

#### 2.2 Update process_main_metric()
```python
async def process_main_metric(report_json: ReportJson, calc: EnhancedMetricsCalculator) -> None:
    """Process main metric with optional grouping."""
    
    try:
        main_metric = report_json.get("main_metric", {})
        value_config = main_metric.get("value", {})
        metrics_group_by = report_json.get("metrics_group_by")  # NEW
        
        entity = value_config.get(ENTITY_KEY, "")
        operation = value_config.get(OPERATION_KEY, COUNT_OPERATION)
        filters = value_config.get("filters", {})
        
        # Calculate with optional grouping
        real_value = await calculate_main_metric_value(
            entity, operation, calc, filters, metrics_group_by
        )
        
        # Store result
        report_json["main_metric"]["real_value"] = real_value
        
        # If grouped, also store breakdown for UI
        if metrics_group_by and isinstance(real_value, dict):
            report_json["main_metric"]["grouped_breakdown"] = real_value
            # Store total for compatibility
            report_json["main_metric"]["total_value"] = sum(real_value.values())
        
    except Exception as e:
        logger.error(f"Main metric processing error: {e}")
        report_json["main_metric"]["real_value"] = 0 if not metrics_group_by else {}
```

#### 2.3 Update process_secondary_metrics()
```python
async def process_secondary_metrics(report_json: ReportJson, calc: EnhancedMetricsCalculator) -> None:
    """Process secondary metrics with optional grouping."""
    
    metrics_group_by = report_json.get("metrics_group_by")  # NEW
    
    for i, metric in enumerate(report_json["secondary_metrics"]):
        try:
            value_config = metric.get("value", {})
            entity = value_config.get(ENTITY_KEY, "")
            operation = value_config.get(OPERATION_KEY, COUNT_OPERATION)
            filters = value_config.get("filters", {})
            
            # Calculate with same grouping as main metric
            real_value = await calculate_main_metric_value(
                entity, operation, calc, filters, metrics_group_by
            )
            
            # Store result
            report_json["secondary_metrics"][i]["real_value"] = real_value
            
            # If grouped, store breakdown
            if metrics_group_by and isinstance(real_value, dict):
                report_json["secondary_metrics"][i]["grouped_breakdown"] = real_value
                report_json["secondary_metrics"][i]["total_value"] = sum(real_value.values())
                
        except Exception as e:
            logger.error(f"Secondary metric {i} processing error: {e}")
            report_json["secondary_metrics"][i]["real_value"] = 0 if not metrics_group_by else {}
```

### Phase 3: Frontend Integration

#### 3.1 Update index.html to Display Grouped Metrics
```javascript
const renderMetrics = (reportData) => {
    const mainMetric = reportData.main_metric;
    const secondaryMetrics = reportData.secondary_metrics;
    const metricsGroupBy = reportData.metrics_group_by;
    
    if (metricsGroupBy) {
        // Display grouped metrics breakdown
        renderGroupedMetrics(mainMetric, secondaryMetrics, metricsGroupBy);
    } else {
        // Display single aggregated metrics (existing logic)
        renderSingleMetrics(mainMetric, secondaryMetrics);
    }
};

const renderGroupedMetrics = (mainMetric, secondaryMetrics, groupBy) => {
    const container = document.getElementById('metrics-container');
    
    // Create metrics breakdown table
    const breakdown = mainMetric.grouped_breakdown;
    const entityNames = Object.keys(breakdown);
    
    let html = `
        <div class="grouped-metrics">
            <h3>${mainMetric.label} (${groupBy})</h3>
            <table class="metrics-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>${mainMetric.label}</th>
                        ${secondaryMetrics.map(m => `<th>${m.label}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
    `;
    
    entityNames.forEach(name => {
        html += `
            <tr>
                <td>${name}</td>
                <td>${breakdown[name].toLocaleString('ru-RU')}</td>
                ${secondaryMetrics.map(m => 
                    `<td>${(m.grouped_breakdown[name] || 0).toLocaleString('ru-RU')}</td>`
                ).join('')}
            </tr>
        `;
    });
    
    html += `
                </tbody>
                <tfoot>
                    <tr class="totals">
                        <td><strong>Всего</strong></td>
                        <td><strong>${mainMetric.total_value.toLocaleString('ru-RU')}</strong></td>
                        ${secondaryMetrics.map(m => 
                            `<td><strong>${m.total_value.toLocaleString('ru-RU')}</strong></td>`
                        ).join('')}
                    </tr>
                </tfoot>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
};
```

### Phase 4: Prompt Updates and Examples

#### 4.1 Add New Prompt Rules
```text
METRICS GROUPING RULES:

1. Use `metrics_group_by` when user wants breakdown of metrics by specific dimension:
   ✅ "Сколько нанял каждый рекрутер?" → metrics_group_by: "recruiters"
   ✅ "Показатели по каждому источнику" → metrics_group_by: "sources"
   ✅ "Статистика по этапам" → metrics_group_by: "stages"

2. Leave `metrics_group_by: null` for total aggregated metrics:
   ✅ "Сколько всего нанято?" → metrics_group_by: null
   ✅ "Общая статистика по найму" → metrics_group_by: null

3. Chart grouping is INDEPENDENT of metrics grouping:
   ✅ metrics_group_by: "recruiters" + chart group_by: "month" 
   → Show each recruiter's totals + monthly trend chart

EXAMPLES:

❌ WRONG - Missing metrics grouping for breakdown question:
Question: "Покажи результаты каждого рекрутера за месяц"
{
  "metrics_group_by": null,  // ❌ Should group by recruiters
  "main_metric": {"label": "Нанято", "entity": "hires"}
}

✅ CORRECT - Proper metrics grouping:
Question: "Покажи результаты каждого рекрутера за месяц"
{
  "metrics_group_by": "recruiters",  // ✅ Groups all metrics by recruiters
  "main_metric": {"label": "Нанято", "entity": "hires"},
  "secondary_metrics": [
    {"label": "Кандидатов", "entity": "applicants"},
    {"label": "Среднее время", "entity": "hires", "value_field": "time_to_hire"}
  ],
  "chart": {
    "type": "line",
    "y_axis": {"entity": "hires", "group_by": {"field": "month"}}  // Chart shows monthly trend
  }
}

RESULT: User sees each recruiter's individual metrics + overall monthly hiring trend
```

#### 4.2 Update Response Template
```json
{
  "report_title": "Краткий заголовок отчета",
  "metrics_group_by": null,  // NEW: "recruiters"|"sources"|"stages"|null
  "main_metric": {
    "label": "Основная метрика",
    "value": {
      "operation": "count",
      "entity": "applicants", 
      "value_field": null,
      // NO group_by here - uses metrics_group_by
      "filters": {"period": "1 year"}
    }
  },
  "secondary_metrics": [
    {
      "label": "Дополнительная метрика 1",
      "value": {
        "operation": "count",
        "entity": "hires",
        "value_field": null,
        // NO group_by here - uses metrics_group_by
        "filters": {"period": "1 year"}
      }
    }
  ],
  "chart": {
    "label": "Название графика",
    "type": "bar", 
    "x_axis": {
      "operation": "count",
      "entity": "stages",
      "group_by": {"field": "stages"},  // Chart keeps independent grouping
      "filters": {"period": "1 year"}
    },
    "y_axis": {
      "operation": "count", 
      "entity": "applicants",
      "group_by": {"field": "stages"},  // Chart keeps independent grouping
      "filters": {"period": "1 year"}
    }
  }
}
```

## Use Cases and Examples

### Use Case 1: Recruiter Performance with Trend Analysis
**Question**: "Как работает каждый рекрутер в этом месяце и какая общая динамика?"

**Response**:
```json
{
  "report_title": "Эффективность рекрутеров и динамика найма",
  "metrics_group_by": "recruiters",
  "main_metric": {
    "label": "Нанято в этом месяце",
    "value": {"operation": "count", "entity": "hires", "filters": {"period": "1 month"}}
  },
  "secondary_metrics": [
    {
      "label": "Кандидатов добавлено", 
      "value": {"operation": "count", "entity": "applicants", "filters": {"period": "1 month"}}
    },
    {
      "label": "Среднее время найма",
      "value": {"operation": "avg", "entity": "hires", "value_field": "time_to_hire", "filters": {"period": "1 month"}}
    }
  ],
  "chart": {
    "type": "line",
    "label": "Динамика найма за 6 месяцев", 
    "y_axis": {"entity": "hires", "group_by": {"field": "month"}, "filters": {"period": "6 month"}}
  }
}
```

**Result**: 
- Metrics show each recruiter's individual performance for current month
- Chart shows overall company hiring trend over 6 months
- Perfect analytical context!

### Use Case 2: Source Effectiveness with Pipeline Analysis  
**Question**: "Эффективность каждого источника и общая воронка"

**Response**:
```json
{
  "report_title": "Источники кандидатов и воронка найма",
  "metrics_group_by": "sources",
  "main_metric": {
    "label": "Нанято по источникам",
    "value": {"operation": "count", "entity": "hires", "filters": {"period": "3 month"}}
  },
  "secondary_metrics": [
    {
      "label": "Кандидатов по источникам",
      "value": {"operation": "count", "entity": "applicants", "filters": {"period": "3 month"}}
    },
    {
      "label": "Конверсия по источникам", 
      "value": {"operation": "avg", "entity": "sources", "value_field": "conversion", "filters": {"period": "3 month"}}
    }
  ],
  "chart": {
    "type": "bar",
    "label": "Воронка по этапам",
    "y_axis": {"entity": "applicants", "group_by": {"field": "stages"}, "filters": {"period": "3 month"}}
  }
}
```

**Result**:
- Metrics show each source's individual effectiveness 
- Chart shows overall pipeline distribution by stages
- Complete recruitment analysis!

## Implementation Tasks

### Task 1: Schema Updates (chart_data_processor.py)
- [ ] Add `metrics_group_by` to ReportJson TypedDict
- [ ] Create MetricsQuery TypedDict without group_by
- [ ] Update validation logic for new structure

### Task 2: Processing Logic (chart_data_processor.py)  
- [ ] Update calculate_main_metric_value() to handle grouping
- [ ] Update process_main_metric() to use metrics_group_by
- [ ] Update process_secondary_metrics() to use metrics_group_by
- [ ] Add grouped result storage logic

### Task 3: Prompt Updates (prompt.py)
- [ ] Update JSON schema with metrics_group_by
- [ ] Add metrics grouping rules and examples
- [ ] Update response template
- [ ] Add use case examples

### Task 4: Frontend Updates (index.html)
- [ ] Add renderGroupedMetrics() function
- [ ] Add CSS for metrics breakdown table
- [ ] Update main render logic to handle both modes
- [ ] Add totals row for grouped metrics

### Task 5: Testing
- [ ] Test grouped metrics with different entities
- [ ] Test mixed scenarios (grouped metrics + different chart grouping)
- [ ] Test backward compatibility with existing reports
- [ ] Test frontend rendering for both modes

## Migration Strategy

### Backward Compatibility
- Existing reports without `metrics_group_by` continue to work exactly as before
- All current functionality remains unchanged
- New functionality is purely additive

### Rollout Plan
1. **Phase 1**: Implement backend logic with null `metrics_group_by` (no behavior change)
2. **Phase 2**: Add frontend support for grouped metrics display
3. **Phase 3**: Update prompt to start using grouped metrics for appropriate questions
4. **Phase 4**: Monitor and optimize based on usage patterns

## Success Metrics

### Technical Success
- [ ] All existing reports continue to work unchanged
- [ ] New grouped metrics reports render correctly  
- [ ] No performance degradation
- [ ] Clean separation between metrics and chart grouping

### Product Success  
- [ ] Users can analyze individual entity performance + broader trends
- [ ] More actionable and insightful reports
- [ ] Flexible analytical capabilities
- [ ] Improved user satisfaction with report depth

## Risk Mitigation

### Potential Risks
1. **Breaking Changes**: Ensure complete backward compatibility
2. **Performance**: Grouped metrics processing might be slower
3. **UI Complexity**: Grouped metrics display might be overwhelming
4. **User Confusion**: Two different grouping concepts

### Mitigation Strategies
1. **Extensive Testing**: Test all existing report patterns
2. **Performance Monitoring**: Monitor processing times and optimize if needed
3. **Progressive Enhancement**: Start with simple grouped displays
4. **Clear Documentation**: Update user documentation with examples

## Timeline

- **Week 1**: Schema and backend logic implementation  
- **Week 2**: Frontend updates and basic testing
- **Week 3**: Prompt updates and comprehensive testing
- **Week 4**: Refinement, optimization, and documentation

This plan provides a comprehensive approach to implementing unified metrics grouping while maintaining chart independence, enabling much more flexible and insightful analytical reports.