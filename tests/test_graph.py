from openclaw_sdlc_agent.graph import build_sdlc_graph

def test_sdlc_graph_structure():
    app = build_sdlc_graph()
    assert app is not None

    # 获取图中所有节点名称
    nodes = [node for node in app.get_graph().nodes]
    print("Graph nodes:", nodes)

    # 验证新引入的 tester 和 reviewer 节点存在
    assert "tester" in nodes
    assert "reviewer" in nodes

    # 获取图中所有边
    edges = [(e.source, e.target) for e in app.get_graph().edges]
    print("Graph edges:", edges)

    # 验证并行触发与汇合逻辑
    assert ("frontend_dev", "tester") in edges
    assert ("frontend_dev", "reviewer") in edges
    assert ("tester", "devops") in edges
    assert ("reviewer", "devops") in edges

    # 验证原流程中的 code_reviewer 已经不在从 frontend_dev 连出的路径上
    assert ("frontend_dev", "code_reviewer") not in edges
