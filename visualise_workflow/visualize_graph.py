#!/usr/bin/env python3
"""
Research Agent Graph Visualizer using Matplotlib and LangGraph

This script creates a visual representation of the research agent's LangGraph structure.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np
from typing import Dict, List, Tuple

def create_graph_visualization():
    """Create a matplotlib visualization of the research agent graph."""
    
    # Set up the figure and axis
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # Define node positions and properties
    nodes = {
        'start': {'pos': (5, 11), 'label': 'START', 'color': '#4CAF50', 'type': 'start'},
        'generate_queries': {'pos': (5, 9.5), 'label': 'generate_queries\n(LLM)', 'color': '#FF5722', 'type': 'llm'},
        'web_search': {'pos': (5, 8), 'label': 'web_search\n(Tool)', 'color': '#2196F3', 'type': 'tool'},
        'reflect': {'pos': (5, 6.5), 'label': 'reflect\n(LLM - Slot-Aware)', 'color': '#FF5722', 'type': 'llm'},
        'decision': {'pos': (5, 5), 'label': 'DECISION\nshould_continue', 'color': '#FFC107', 'type': 'decision'},
        'update_iteration': {'pos': (2, 3.5), 'label': 'update_iteration\n(Logic)', 'color': '#9C27B0', 'type': 'logic'},
        'synthesize': {'pos': (8, 3.5), 'label': 'synthesize\n(LLM)', 'color': '#FF5722', 'type': 'llm'},
        'end': {'pos': (5, 1.5), 'label': 'END', 'color': '#4CAF50', 'type': 'end'}
    }
    
    # Define edges with labels
    edges = [
        ('start', 'generate_queries', ''),
        ('generate_queries', 'web_search', ''),
        ('web_search', 'reflect', ''),
        ('reflect', 'decision', ''),
        ('decision', 'update_iteration', 'continue\n(missing slots)'),
        ('decision', 'synthesize', 'synthesize\n(all slots filled)'),
        ('update_iteration', 'web_search', 'loop back'),
        ('synthesize', 'end', '')
    ]
    
    # Draw nodes
    for node_name, node_data in nodes.items():
        x, y = node_data['pos']
        color = node_data['color']
        label = node_data['label']
        node_type = node_data['type']
        
        # Different shapes for different node types
        if node_type == 'start':
            # Start node (oval)
            node = FancyBboxPatch((x-1.2, y-0.4), 2.4, 0.8, 
                                boxstyle="round,pad=0.1", 
                                facecolor=color, edgecolor='black', linewidth=2)
        elif node_type == 'end':
            # End node (oval)
            node = FancyBboxPatch((x-1.2, y-0.4), 2.4, 0.8, 
                                boxstyle="round,pad=0.1", 
                                facecolor=color, edgecolor='black', linewidth=2)
        elif node_type == 'decision':
            # Decision node (diamond)
            diamond_points = np.array([[x, y+0.6], [x+0.8, y], [x, y-0.6], [x-0.8, y]])
            node = patches.Polygon(diamond_points, facecolor=color, edgecolor='black', linewidth=2)
        else:
            # Regular nodes (rectangle)
            node = FancyBboxPatch((x-1.2, y-0.4), 2.4, 0.8, 
                                boxstyle="round,pad=0.1", 
                                facecolor=color, edgecolor='black', linewidth=2)
        
        ax.add_patch(node)
        
        # Add text
        ax.text(x, y, label, ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Draw edges
    for start_node, end_node, label in edges:
        start_pos = nodes[start_node]['pos']
        end_pos = nodes[end_node]['pos']
        
        # Special handling for loop back edge
        if start_node == 'update_iteration' and end_node == 'web_search':
            # Create a curved loop back
            control_point = (1, 7.5)
            path = patches.FancyArrowPatch(
                start_pos, end_pos,
                connectionstyle=f"arc3,rad=-0.3",
                arrowstyle='->', mutation_scale=20, lw=2, color='red'
            )
            ax.add_patch(path)
            
            # Add label for loop
            ax.text(1.5, 7.8, 'loop back', fontsize=8, color='red', fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
        else:
            # Regular straight edges
            if label:
                # Add curved edge with label
                path = patches.FancyArrowPatch(
                    start_pos, end_pos,
                    connectionstyle=f"arc3,rad=0.2",
                    arrowstyle='->', mutation_scale=20, lw=2, color='black'
                )
                ax.add_patch(path)
                
                # Add edge label
                mid_x = (start_pos[0] + end_pos[0]) / 2
                mid_y = (start_pos[1] + end_pos[1]) / 2
                ax.text(mid_x + 0.3, mid_y, label, fontsize=7, 
                       bbox=dict(boxstyle="round,pad=0.2", facecolor='yellow', alpha=0.8))
            else:
                # Simple straight edge
                path = patches.FancyArrowPatch(
                    start_pos, end_pos,
                    arrowstyle='->', mutation_scale=20, lw=2, color='black'
                )
                ax.add_patch(path)
    
    # Add title and legend
    ax.text(5, 11.8, 'Research Agent LangGraph Structure', 
            ha='center', va='center', fontsize=16, fontweight='bold')
    
    # Add legend
    legend_elements = [
        patches.Patch(color='#4CAF50', label='Start/End'),
        patches.Patch(color='#FF5722', label='LLM Nodes'),
        patches.Patch(color='#2196F3', label='Tool Nodes'),
        patches.Patch(color='#9C27B0', label='Logic Nodes'),
        patches.Patch(color='#FFC107', label='Decision Node')
    ]
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98))
    
    # Add slot-aware information
    slot_info = """
    SLOT-AWARE FEATURES:
    • reflect identifies mandatory information slots
    • Matches evidence to specific slots (WHO, WHAT, WHEN, WHERE, HOW)
    • Only marks slots as "filled" with clear, consistent evidence
    • Generates targeted queries for missing slots
    • Continues until ALL slots are filled or max iterations reached
    """
    
    ax.text(0.5, 0.5, slot_info, fontsize=8, 
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue', alpha=0.8),
            verticalalignment='bottom')
    
    plt.tight_layout()
    return fig

def create_detailed_node_view():
    """Create a detailed view of node types and their functions."""
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Node details
    node_details = [
        {
            'name': 'generate_queries',
            'type': 'LLM Node',
            'pos': (2, 8.5),
            'color': '#FF5722',
            'description': [
                '• Breaks question into 3-5 specific queries',
                '• Returns JSON array of queries',
                '• Fallback to original question if parsing fails',
                '• Input: AgentState with question',
                '• Output: AgentState with queries array'
            ]
        },
        {
            'name': 'web_search',
            'type': 'Tool Node',
            'pos': (6, 8.5),
            'color': '#2196F3',
            'description': [
                '• Concurrent searches using Google Custom Search API',
                '• Merge and deduplicate results by URL',
                '• Fallback to mock search if API keys not set',
                '• Handle rate limits and timeouts gracefully',
                '• Input: AgentState with queries',
                '• Output: AgentState with docs array'
            ]
        },
        {
            'name': 'reflect',
            'type': 'LLM Node (Slot-Aware)',
            'pos': (10, 8.5),
            'color': '#FF5722',
            'description': [
                '• Identify mandatory information slots',
                '• Match evidence sentences to specific slots',
                '• Judge completeness and consistency',
                '• Generate targeted queries for missing slots',
                '• Return: {slots, filled, need_more, new_queries}',
                '• Slot types: WHO, WHAT, WHEN, WHERE, HOW'
            ]
        },
        {
            'name': 'should_continue',
            'type': 'Logic Node',
            'pos': (2, 5.5),
            'color': '#9C27B0',
            'description': [
                '• Determine if we should continue to another iteration',
                '• Input: AgentState',
                '• Output: "continue" or "synthesize"',
                '• Decision Logic:',
                '  - Missing slots AND have new_queries → continue',
                '  - All slots filled AND need_more=false → synthesize',
                '  - Max iterations reached → synthesize'
            ]
        },
        {
            'name': 'update_iteration',
            'type': 'Logic Node',
            'pos': (6, 5.5),
            'color': '#9C27B0',
            'description': [
                '• Update iteration count and prepare for next round',
                '• Increment iteration counter',
                '• Set new queries for next round if available',
                '• Clear previous results but keep slots',
                '• Reset filled_slots for next iteration',
                '• Logic: Prepares state for continued search'
            ]
        },
        {
            'name': 'synthesize',
            'type': 'LLM Node',
            'pos': (10, 5.5),
            'color': '#FF5722',
            'description': [
                '• Create final concise answer with structured citations',
                '• Generate direct, concise answer (≤80 words)',
                '• Create structured citations with id, title, url',
                '• Handle both old and new citation formats',
                '• Quality Constraints:',
                '  - Maximum 80 words',
                '  - Must include Markdown citations [1][2]...',
                '  - Direct answers without filler phrases'
            ]
        }
    ]
    
    # Draw node details
    for node in node_details:
        x, y = node['pos']
        color = node['color']
        
        # Draw node box
        node_box = FancyBboxPatch((x-1.5, y-1.8), 3, 3.6, 
                                boxstyle="round,pad=0.1", 
                                facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(node_box)
        
        # Add title
        ax.text(x, y+1.2, node['name'], ha='center', va='center', 
               fontsize=10, fontweight='bold')
        ax.text(x, y+0.8, node['type'], ha='center', va='center', 
               fontsize=8, style='italic')
        
        # Add description
        for i, desc in enumerate(node['description']):
            ax.text(x-1.3, y+0.4-i*0.25, desc, ha='left', va='top', 
                   fontsize=7, wrap=True)
    
    # Add title
    ax.text(6, 9.5, 'Detailed Node Functions', 
            ha='center', va='center', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    return fig

def create_data_flow_diagram():
    """Create a data flow diagram showing state transitions."""
    
    fig, ax = plt.subplots(1, 1, figsize=(16, 8))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # Define state flow
    states = [
        {'name': 'Initial State', 'pos': (1, 4), 'data': ['question']},
        {'name': 'After generate_queries', 'pos': (3, 4), 'data': ['question', 'queries']},
        {'name': 'After web_search', 'pos': (5, 4), 'data': ['question', 'queries', 'docs']},
        {'name': 'After reflect', 'pos': (7, 4), 'data': ['question', 'queries', 'docs', 'slots', 'filled_slots', 'need_more', 'new_queries']},
        {'name': 'Decision Point', 'pos': (9, 4), 'data': ['continue/synthesize']},
        {'name': 'After update_iteration', 'pos': (11, 4), 'data': ['question', 'new_queries', 'iteration', 'slots']},
        {'name': 'After synthesize', 'pos': (13, 4), 'data': ['question', 'docs', 'answer', 'citations', 'slots', 'filled_slots', 'iterations']},
        {'name': 'Final Output', 'pos': (15, 4), 'data': ['answer', 'citations', 'slots', 'filled_slots', 'iterations']}
    ]
    
    # Draw state boxes
    for state in states:
        x, y = state['pos']
        
        # Calculate box height based on data items
        data_height = len(state['data']) * 0.3 + 0.5
        
        # Draw state box
        state_box = FancyBboxPatch((x-1, y-data_height/2), 2, data_height, 
                                 boxstyle="round,pad=0.1", 
                                 facecolor='lightblue', edgecolor='blue', linewidth=2)
        ax.add_patch(state_box)
        
        # Add state name
        ax.text(x, y+data_height/2+0.2, state['name'], ha='center', va='bottom', 
               fontsize=9, fontweight='bold')
        
        # Add data items
        for i, data_item in enumerate(state['data']):
            ax.text(x-0.9, y+data_height/2-0.2-i*0.3, f"• {data_item}", 
                   ha='left', va='top', fontsize=7)
    
    # Draw arrows between states
    for i in range(len(states) - 1):
        start_pos = states[i]['pos']
        end_pos = states[i+1]['pos']
        
        arrow = patches.FancyArrowPatch(
            (start_pos[0] + 1, start_pos[1]), (end_pos[0] - 1, end_pos[1]),
            arrowstyle='->', mutation_scale=20, lw=2, color='red'
        )
        ax.add_patch(arrow)
    
    # Add title
    ax.text(8, 7.5, 'AgentState Data Flow Through Nodes', 
            ha='center', va='center', fontsize=14, fontweight='bold')
    
    # Add legend
    legend_elements = [
        patches.Patch(color='lightblue', label='State Data'),
        patches.Patch(color='red', label='Data Flow')
    ]
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98))
    
    plt.tight_layout()
    return fig

def main():
    """Create and display all visualizations."""
    
    print("Creating Research Agent Graph Visualizations...")
    
    # Create the main graph visualization
    fig1 = create_graph_visualization()
    fig1.savefig('research_agent_graph.png', dpi=300, bbox_inches='tight')
    print("✓ Main graph saved as 'research_agent_graph.png'")
    
    # Create detailed node view
    fig2 = create_detailed_node_view()
    fig2.savefig('node_details.png', dpi=300, bbox_inches='tight')
    print("✓ Node details saved as 'node_details.png'")
    
    # Create data flow diagram
    fig3 = create_data_flow_diagram()
    fig3.savefig('data_flow.png', dpi=300, bbox_inches='tight')
    print("✓ Data flow saved as 'data_flow.png'")
    
    # Display the main graph
    plt.figure(fig1.number)
    plt.show()
    
    print("\nVisualization complete! Check the generated PNG files for high-resolution versions.")

if __name__ == "__main__":
    main() 