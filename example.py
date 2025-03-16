from graph_manager import GraphManager
from base_classes import Element, Thought, Node
from state_nodes import NodeState


def main():
    """Demonstrate the productivity system with a simple example."""
    
    # Create a new graph manager
    graph_manager = GraphManager()
    
    # Example markdown for a small project
    markdown = """- [g] Build a transformer-based recommendation engine
	- [?] Which embedding technique should we use? ^q1
		- [a] Word2Vec ^alt1
			- [o] Fast to train, but fixed vocabulary
			- [o] Good for simple text recommendation
		- [a] BERT embeddings ^alt2
			- [o] Better semantic understanding
			- [o] Computationally more expensive
			- [P] Might exceed our memory budget
				- [ ] Investigate distilled models
				- [o] DistilBERT fits within memory constraints
				- [D] Use DistilBERT instead
		- [a] Custom embeddings ^alt3
			- [o] Can be optimized for our specific domain
			- [o] Requires more data to train effectively
		- [D] Selected ^alt2
	- [ ] Implement data preprocessing pipeline
		- [/] Design ETL workflow
		- [ ] Implement data cleaning
		- [ ] Set up feature extraction
	- [ ] Train recommendation model
		- [ ] Select hyperparameters
		- [ ] Implement training loop
		- [ ] Evaluate on test set
	- [I] We could add explainability features to help users understand recommendations
	- [m] This project structure works well for ML projects, should reuse it
"""

    # Load the markdown
    graph_manager.load_from_markdown(markdown)
    
    # Print the graph
    print("Nodes in the graph:")
    for node in graph_manager.graph.nodes:
        node_data = graph_manager.graph.nodes[node]
        print(f"- {node}: {node_data.get('type')} - {node_data.get('text')}")
    
    print("\nEdges in the graph:")
    for u, v, data in graph_manager.graph.edges(data=True):
        print(f"- {u} -> {v} ({data.get('type')})")
    
    # Find Question node
    question = graph_manager.get_node_by_ref("q1")
    if question:
        print(f"\nQuestion: {question.text}")
        print(f"Is resolved: {question.is_resolved()}")
        
        # Get alternatives
        alternatives = question.get_alternatives()
        print(f"Alternatives: {[alt.text for alt in alternatives]}")
        
        # Get decision
        for child in question.children:
            if child.node_type == "decision":
                print(f"Decision: {child.text}")
                alt = child.get_selected_alternative()
                if alt:
                    print(f"Selected alternative: {alt.text}")
                    print(f"Has problems: {alt.has_problems()}")
    
    # Get blocking nodes
    blocking_nodes = graph_manager.get_blocking_nodes()
    print(f"\nBlocking nodes: {[node.text for node in blocking_nodes]}")
    
    # Get actionable tasks
    actionable_tasks = graph_manager.get_actionable_tasks()
    print(f"\nActionable tasks: {[task.text for task in actionable_tasks]}")
    
    # Modify the graph
    print("\nModifying the graph...")
    
    # Add a new observation
    graph_manager.add_node(
        "observation", 
        "Model achieves 85% accuracy on test set", 
        question.id
    )
    
    # Mark a task as done
    task = None
    for node in graph_manager.graph.nodes:
        node_data = graph_manager.graph.nodes[node]
        if (node_data.get('type') == "task" and 
            node_data.get('text') == "Design ETL workflow"):
            task = graph_manager.get_node_by_id(node)
            break
    
    if task:
        graph_manager.update_task_state(task.id, "done")
        print(f"Marked task '{task.text}' as done")
    
    # Export to markdown
    modified_markdown = graph_manager.to_markdown()
    print("\nModified markdown:")
    print(modified_markdown)
    
    # Export to JSON
    graph_manager.export_to_json("productivity_graph.json")
    print("\nExported graph to productivity_graph.json")


if __name__ == "__main__":
    main()
