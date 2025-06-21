# Period Parameter Refactoring Plan

## Overview
Moving the 'period' parameter from individual metric filters to the report level to simplify the JSON schema and ensure consistent time filtering across all metrics in a report.

## Current State Analysis

### Current Schema Structure
- **Location**: `prompt.py` lines 421-492
- **Current Period Placement**: Inside each metric's `filters` object
- **Usage**: Each metric (main_metric, secondary_metrics, chart axes) can have different periods

### Current Period Implementation
- **Definition**: Lines 175-176 in prompt.py: `period: year | 6 month | 3 month | 1 month | 2 weeks | this week | today`
- **Processing**: `universal_filter.py` lines 56-90 with `PeriodFilter` class
- **Template**: Lines 494-564 showing period in each metric's filters

### Problems with Current Approach
1. **Redundancy**: Same period repeated across multiple metrics
2. **Inconsistency Risk**: Different metrics could have different periods
3. **JSON Bloat**: Unnecessary repetition in JSON structure
4. **User Confusion**: Unclear which period applies when multiple are specified

## Proposed New Schema Structure

### New Report-Level Period
```json
{
  "report_title": "Analytics Report",
  "period": "3 month",  // NEW: Single period for entire report
  "main_metric": {
    "label": "Main Metric",
    "value": {
      "operation": "count",
      "entity": "applicants",
      "filters": {
        // period removed from here
        "recruiters": "12345"
      }
    }
  },
  "secondary_metrics": [...], // period removed from all metrics
  "chart": {...} // period removed from x_axis and y_axis
}
```

### Benefits of New Approach
1. **Consistency**: Single period applies to all metrics
2. **Simplicity**: Reduced JSON complexity
3. **Clarity**: Clear time scope for entire report
4. **Maintainability**: Easier to modify and validate

## Implementation Plan

### Phase 1: Schema Updates
1. **Update JSON Schema** (`prompt.py` lines 421-492)
   - Add `period` as required property at report level
   - Remove period from query definition in filters
   - Update schema validation

2. **Update Response Template** (`prompt.py` lines 494-564)
   - Add period at report level
   - Remove period from all metric filters
   - Update example structures

### Phase 2: Processing Logic Updates
1. **Update Chart Data Processor** (`chart_data_processor.py`)
   - Extract period from report level
   - Pass period to all metric calculations
   - Ensure backward compatibility during transition

2. **Update Metrics Calculator** (`enhanced_metrics_calculator.py`)
   - Modify filter application to inherit report-level period
   - Update `_apply_universal_filters` method
   - Ensure period is applied consistently

### Phase 3: Filter Engine Updates
1. **Update Universal Filter Engine** (`universal_filter_engine.py`)
   - Modify parsing to accept report-level period
   - Ensure period inheritance for all queries
   - Update filter combination logic

2. **Update Filter Structures** (`universal_filter.py`)
   - Keep existing `PeriodFilter` class (no changes needed)
   - Update filter parsing to handle report-level period
   - Maintain backward compatibility

### Phase 4: Testing and Validation
1. **Update Test Files**
   - Modify all test files to use new schema
   - Test period inheritance functionality
   - Validate with real Huntflow data

2. **Integration Testing**
   - Test with various period values
   - Ensure consistent filtering across all metrics
   - Validate chart generation with new structure

## Technical Implementation Details

### Schema Changes Required
```json
// OLD schema in query definition
"filters": { "type": "object" }

// NEW schema at report level
"properties": {
  "period": { 
    "type": "string",
    "enum": ["year", "6 month", "3 month", "1 month", "2 weeks", "this week", "today"]
  },
  // ... existing properties
}
```

### Filter Processing Changes
```python
# OLD: Extract period from each metric's filters
period = metric['value']['filters'].get('period')

# NEW: Extract period from report level
period = report.get('period')
# Apply to all metrics in report
```

### Backward Compatibility Strategy
1. **Transition Period**: Support both old and new formats
2. **Graceful Fallback**: If report-level period missing, check metric-level
3. **Migration Helper**: Utility to convert old format to new format

## Risk Assessment

### Low Risk
- **Filter Logic**: Existing `PeriodFilter` class remains unchanged
- **Period Calculation**: Same time calculation logic
- **Entity Filtering**: No changes to entity-specific filtering

### Medium Risk
- **Template Updates**: Must update AI prompt templates carefully
- **Test Updates**: All existing tests need schema updates
- **Documentation**: Update examples and documentation

### High Risk
- **Breaking Changes**: Old JSON format will become invalid
- **Integration Points**: All systems consuming the API affected
- **Data Consistency**: Ensure period is consistently applied across all metrics

## Success Criteria
1. **Schema Validation**: New schema validates correctly
2. **Period Consistency**: All metrics in report use same period
3. **Performance**: No performance degradation
4. **Test Coverage**: All tests pass with new schema
5. **Real Data**: Validates with actual Huntflow data

## Rollback Plan
If issues arise:
1. Revert schema changes in `prompt.py`
2. Restore original template structure
3. Keep filter processing logic as fallback
4. Run regression tests to ensure stability

## Timeline
- **Phase 1**: Schema updates (1 change cycle)
- **Phase 2**: Processing logic (1 change cycle)
- **Phase 3**: Filter engine updates (1 change cycle)
- **Phase 4**: Testing and validation (1 change cycle)
- **Total**: 4 change cycles following one-change-at-a-time rule