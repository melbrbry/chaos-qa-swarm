"""LangGraph assembly for the chaos QA swarm."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from graph.nodes import (
  analyze_and_generate_attacks,
  generate_patch_node,
  run_judge_probe,
  run_judge_verify,
)
from graph.routing import route_after_probe, route_after_verify
from graph.state import SwarmState, initial_state


def build_graph():
  """Compile the exploration + remediation swarm graph."""
  graph = StateGraph(SwarmState)
  graph.add_node("chaos", analyze_and_generate_attacks)
  graph.add_node("judge_probe", run_judge_probe)
  graph.add_node("developer", generate_patch_node)
  graph.add_node("judge_verify", run_judge_verify)

  graph.set_entry_point("chaos")
  graph.add_edge("chaos", "judge_probe")
  graph.add_conditional_edges(
    "judge_probe",
    route_after_probe,
    {"developer": "developer", "end": END},
  )
  graph.add_edge("developer", "judge_verify")
  graph.add_conditional_edges(
    "judge_verify",
    route_after_verify,
    {"developer": "developer", "chaos": "chaos", "end": END},
  )
  return graph.compile()


def run_swarm(*, llm=None) -> SwarmState:
  """Run the swarm graph and return final state."""
  app = build_graph()
  if llm is not None:
    raise NotImplementedError("Custom llm injection is handled in tests via agent mocks")
  final_state = app.invoke(initial_state())
  return final_state
