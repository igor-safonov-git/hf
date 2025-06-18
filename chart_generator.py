"""
Chart generator for creating bar charts and returning them as base64 data URIs.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
from typing import Dict, Union


def make_chart(
    data: Dict[str, Union[int, float]], 
    title: str, 
    xlabel: str = "", 
    ylabel: str = "Count"
) -> str:
    """
    Create a bar chart and return it as a base64 data URI.
    
    Args:
        data: Dictionary with labels as keys and values as numbers
        title: Chart title
        xlabel: X-axis label
        ylabel: Y-axis label
        
    Returns:
        Base64 encoded data URI string for the chart image
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Sort data by value (descending) and limit to top items if too many
    sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
    
    # Group small values into "Other" if more than 7 categories
    if len(sorted_items) > 7:
        top_items = sorted_items[:6]
        other_value = sum(value for _, value in sorted_items[6:])
        top_items.append(("Other", other_value))
        sorted_items = top_items
    
    # Extract labels and values
    labels = [str(label) for label, _ in sorted_items]
    values = [value for _, value in sorted_items]
    
    # Create bar chart
    bars = ax.bar(range(len(labels)), values)
    
    # Customize colors
    colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6', '#1abc9c', '#95a5a6']
    for i, bar in enumerate(bars):
        bar.set_color(colors[i % len(colors)])
    
    # Set labels and title
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Add value labels on bars
    for i, (bar, value) in enumerate(zip(bars, values)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + max(values) * 0.01,
                f'{int(value)}', ha='center', va='bottom')
    
    # Add grid for better readability
    ax.grid(axis='y', alpha=0.3)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Convert to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close(fig)
    
    return f"data:image/png;base64,{image_base64}"