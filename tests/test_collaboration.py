from core.collaboration import CollaborationEngine, DecisionBundle, ProviderPipeline, TaskContext, WorkflowManager
from core.cognitive.contracts import ContextQuery


class StubProvider:
    def __init__(self, name: str, summary: str, confidence: float = 0.7):
        self.name = name
        self.summary = summary
        self.confidence = confidence

    def query(self, query: ContextQuery):
        from core.cognitive.contracts import ContextResponse

        return ContextResponse(
            summary=self.summary,
            evidence=[],
            recommendations=[],
            confidence=self.confidence,
            sources=[self.name],
        )

    def status(self):
        from core.cognitive.contracts import ProviderStatus

        return ProviderStatus(provider=self.name, available=True)

    def explain(self, subject: str) -> str:
        return subject


def test_provider_ordering_and_parallel_execution():
    pipeline = ProviderPipeline(
        providers={
            "librarian": StubProvider("librarian", "repo context"),
            "historian": StubProvider("historian", "past lessons"),
            "architect": StubProvider("architect", "design impact"),
        }
    )
    query = ContextQuery(task="build feature", required_services=["librarian", "historian", "architect"], token_budget=1000)
    task_context = TaskContext.from_query(query)
    task_context.provider_names = WorkflowManager().determine_provider_order(task_context, pipeline)
    task_context.execution_mode = WorkflowManager().determine_mode(task_context)

    responses = pipeline.execute(query, task_context.provider_names, execution_mode=task_context.execution_mode, timeout_seconds=5)
    assert [name for name, _ in responses] == ["librarian", "historian", "architect"]
    assert task_context.execution_mode == "parallel"


def test_confidence_merging_failure_isolation_and_decision_bundle():
    class FailingProvider(StubProvider):
        def query(self, query: ContextQuery):
            raise RuntimeError("boom")

    pipeline = ProviderPipeline(
        providers={
            "librarian": StubProvider("librarian", "repo context", confidence=0.8),
            "historian": FailingProvider("historian", "past lessons"),
            "architect": StubProvider("architect", "design impact", confidence=0.6),
        }
    )
    query = ContextQuery(task="implement change", required_services=["librarian", "historian", "architect"], token_budget=1000)
    engine = CollaborationEngine(pipeline=pipeline)
    bundle = engine.execute(query)

    assert isinstance(bundle, DecisionBundle)
    assert bundle.providers_consulted == ["librarian", "historian", "architect"]
    assert bundle.confidence_score < 1.0
    assert any("Provider failure" in risk for risk in bundle.risks)
    assert bundle.estimated_token_cost > 0
    assert bundle.estimated_execution_time > 0
