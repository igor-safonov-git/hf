"""
Chart Building Helpers for Huntflow Analytics
Centralized module containing all chart-building utilities for FE developers
"""
from typing import Dict, Any, List, Optional, Tuple
import asyncio
import logging
from collections import Counter

logger = logging.getLogger(__name__)

__all__ = [
    'build_chart_data_cpu',
    'build_chart_data_async', 
    'ChartDataBuilder'
]

def build_chart_data_cpu(items: List[Dict[str, Any]], field: str, 
                        mapping: Optional[Dict[str, Any]] = None, sort_by_count: bool = True, 
                        limit: Optional[int] = None) -> Dict[str, Any]:
    """
    CPU-bound: Convert item counts by field into chart format
    
    Args:
        items: List of data items to group
        field: Field name to group by
        mapping: Optional mapping for field values to display names
        sort_by_count: Whether to sort results by count (descending)
        limit: Maximum number of chart items to return
        
    Returns:
        Dict with 'labels' and 'values' arrays for chart rendering
    """
    # Count occurrences of each field value
    field_counts = Counter(item.get(field) for item in items if item.get(field) is not None)
    
    # Convert to chart format with mapping
    chart_items = []
    for field_value, count in field_counts.items():
        # Apply mapping if provided
        if mapping and field_value in mapping:
            field_name = mapping[field_value]
            if isinstance(field_name, dict):
                field_name = field_name.get('name', str(field_value))
            else:
                field_name = str(field_name)
        else:
            field_name = str(field_value)
        
        chart_items.append((field_name, count))
    
    # Sort by count if requested
    if sort_by_count:
        chart_items.sort(key=lambda x: x[1], reverse=True)
    
    # Apply limit if specified
    if limit and len(chart_items) > limit:
        chart_items = chart_items[:limit]
    
    labels = [item[0] for item in chart_items]
    values = [item[1] for item in chart_items]
    
    return {"labels": labels, "values": values}

async def build_chart_data_async(items: List[Dict[str, Any]], field: str, 
                                mapping: Optional[Dict[str, Any]] = None, sort_by_count: bool = True, 
                                limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Async wrapper for chart building - uses thread pool for large datasets
    
    Args:
        items: List of data items to group
        field: Field name to group by  
        mapping: Optional mapping for field values to display names
        sort_by_count: Whether to sort results by count (descending)
        limit: Maximum number of chart items to return
        
    Returns:
        Dict with 'labels' and 'values' arrays for chart rendering
    """
    # For small datasets, do it synchronously to avoid thread overhead
    if len(items) < 1000:
        return build_chart_data_cpu(items, field, mapping, sort_by_count, limit)
    
    # For large datasets, offload to thread pool to prevent blocking event loop
    logger.debug("Processing large dataset (%s items) in thread pool", len(items))
    return await asyncio.to_thread(
        build_chart_data_cpu, 
        items, field, mapping, sort_by_count, limit
    )

def build_status_chart_data_cpu(status_counts: Dict[int, int], status_mapping: Dict[int, Any]) -> Dict[str, Any]:
    """
    CPU-bound: Build chart data specifically for status distributions
    
    Args:
        status_counts: Dict mapping status_id -> count
        status_mapping: Dict mapping status_id -> status info
        
    Returns:
        Dict with 'labels' and 'values' arrays for chart rendering
    """
    chart_items = []
    
    for status_id, count in status_counts.items():
        status_info = status_mapping.get(status_id, {})
        if isinstance(status_info, dict):
            status_name = status_info.get('name', f'Status {status_id}')
        else:
            status_name = str(status_info)
        chart_items.append((status_name, count))
    
    # Sort by count descending
    chart_items.sort(key=lambda x: x[1], reverse=True)
    
    labels = [item[0] for item in chart_items]
    values = [item[1] for item in chart_items]
    
    return {"labels": labels, "values": values}

class ChartDataBuilder:
    """
    Utility class for building various chart data formats
    Provides a consistent interface for FE developers
    """
    
    @staticmethod
    def pie_chart(items: List[Dict[str, Any]], field: str, 
                  mapping: Optional[Dict[str, Any]] = None, limit: int = 10) -> Dict[str, Any]:
        """Build data for pie charts with automatic limiting"""
        return build_chart_data_cpu(items, field, mapping, sort_by_count=True, limit=limit)
    
    @staticmethod  
    def bar_chart(items: List[Dict[str, Any]], field: str,
                  mapping: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """Build data for bar charts"""
        return build_chart_data_cpu(items, field, mapping, sort_by_count=True, limit=limit)
    
    @staticmethod
    def time_series_prep(items: List[Dict[str, Any]], date_field: str, value_field: str) -> List[Tuple[str, Any]]:
        """Prepare data for time series charts"""
        # Extract date-value pairs and sort by date
        data_points = []
        for item in items:
            date_val = item.get(date_field)
            value_val = item.get(value_field)
            if date_val is not None and value_val is not None:
                data_points.append((str(date_val), value_val))
        
        # Sort by date string (assumes ISO format)
        data_points.sort(key=lambda x: x[0])
        return data_points
    
    @staticmethod
    def top_performers(items: List[Dict[str, Any]], performer_field: str, metric_field: str, 
                      limit: int = 5) -> Dict[str, Any]:
        """Build data for top performer charts (recruiters, sources, etc.)"""
        # Aggregate metrics by performer
        performer_totals = {}
        for item in items:
            performer = item.get(performer_field)
            metric = item.get(metric_field, 0)
            if performer:
                performer_totals[performer] = performer_totals.get(performer, 0) + metric
        
        # Sort by metric descending and limit
        sorted_performers = sorted(performer_totals.items(), key=lambda x: x[1], reverse=True)
        if limit:
            sorted_performers = sorted_performers[:limit]
        
        labels = [item[0] for item in sorted_performers]
        values = [item[1] for item in sorted_performers]
        
        return {"labels": labels, "values": values}