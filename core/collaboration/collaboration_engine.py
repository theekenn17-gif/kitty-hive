from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.cognitive.contracts import ContextQuery, ContextResponse, Evidence, Recommendation
from .confidence_engine import ConfidenceEngine
from .decision_bundle import DecisionBundle
from .evidence_merger import EvidenceMerger
from .provider_pipeline import ProviderPipeline
from .task_context import TaskContext
from .workflow_manager import WorkflowManager


class CollaborationEngine:
    def __init__(self, pipeline: ProviderPipeline | None = None, workflow_manager: WorkflowManager | None = None) -> None:
        self.pipeline = pipeline or ProviderPipeline()
        self.workflow_manager = workflow_manager or WorkflowManager()
        self.evidence_merger = EvidenceMerger()
        self.confidence_engine = ConfidenceEngine()

    def execute(self, query: ContextQuery) -> DecisionBundle:
        task_context = TaskContext.from_query(query)
        task_context.provider_names = self.workflow_manager.determine_provider_order(task_context, self.pipeline)
        task_context.execution_mode = self.workflow_manager.determine_mode(task_context)

        responses = self.pipeline.execute(
            query=query,
            provider_names=task_context.provider_names,
            execution_mode=task_context.execution_mode,
            timeout_seconds=task_context.timeout_seconds,
        )

        provider_responses: List[ContextResponse] = [response for _, response in responses]
        merged_evidence, merged_recommendations, freshness, impact, risk = self.evidence_merger.merge(provider_responses)
        confidence = self.confidence_engine.aggregate(provider_responses)
        confidence = self.confidence_engine.adjust_for_budget(
            confidence,
            token_budget=query.token_budget,
            used_tokens=self.confidence_engine.estimate_tokens(len(provider_responses), query.token_budget),
        )

        summary_parts = [response.summary for response in provider_responses if response.summary]
        executive_summary = " | ".join(summary_parts) if summary_parts else "Collaborative decision produced."
        risks = []
        if risk != "low":
            risks.append(f"Overall risk level: {risk}")
        for response in provider_responses:
            if response.metadata.get("failed"):
                risks.append(f"Provider failure: {response.summary}")

        return DecisionBundle(
            executive_summary=executive_summary,
            evidence=merged_evidence,
            recommendations=merged_recommendations,
            risks=risks,
            confidence_score=confidence,
            providers_consulted=[name for name, _ in responses],
            estimated_token_cost=self.confidence_engine.estimate_tokens(len(provider_responses), query.token_budget),
            estimated_execution_time=self.workflow_manager.estimate_time(len(provider_responses), task_context.timeout_seconds),
            metadata={
                "freshness": freshness,
                "impact": impact,
                "risk": risk,
                "execution_mode": task_context.execution_mode,
            },
        )
