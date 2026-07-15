from __future__ import annotations

import os
import subprocess
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import chromadb
from chromadb.errors import InvalidArgumentError
from chromadb.utils import embedding_functions

from core.context_manager import load_repository_index, select_context

from ..contracts import BaseProvider, ContextQuery, ContextResponse, Evidence, ProviderStatus, Recommendation


class Librarian(BaseProvider):
    name = "librarian"

    def __init__(self, repo_root: str | None = None) -> None:
        self.repo_root = Path(repo_root or "/root/KITTY_HIVE").resolve()
        self.memory_path = self.repo_root / "memory" / "database"

    def query(self, query: ContextQuery) -> ContextResponse:
        """Return repository-aware context and relevant intelligence for a query."""
        try:
            index = load_repository_index(repo_root=self.repo_root)
            selection = select_context(
                task=query.task,
                agent=query.agent,
                repo_root=self.repo_root,
                max_items=5,
                include_adjacent=True,
            )

            dependency_graph, reverse_graph = self._build_dependency_graph(index)
            duplicate_symbols = self._find_duplicate_symbols(index)
            hotspots = self._find_hotspots(index)
            selected_files = [item["path"] for item in selection.get("selected_files", [])]
            adjacent_files = [item["path"] for item in selection.get("adjacent_files", [])]
            related_modules = self._find_related_modules(selected_files, dependency_graph, reverse_graph)
            impacted_files = self._find_impacted_files(selected_files, reverse_graph)
            architecture_notes = self._read_architecture_notes()
            memory_notes = self._query_memory(query.task)
            candidate_dead_code = self._find_dead_code(index, reverse_graph)
            violations = self._find_architecture_violations(selection, dependency_graph)

            summary = (
                f"Librarian found {len(selected_files)} relevant files, {len(related_modules)} related modules, "
                f"and {len(impacted_files)} potentially impacted files for '{query.task}'."
            )

            evidence = self._build_evidence(
                selected_files,
                impacted_files,
                memory_notes,
                architecture_notes,
            )

            recommendations = self._build_recommendations(
                selected_files,
                impacted_files,
                violations,
                candidate_dead_code,
            )

            return ContextResponse(
                summary=summary,
                evidence=evidence,
                recommendations=recommendations,
                confidence=0.82,
                freshness="fresh",
                impact="medium",
                risk="low" if not violations else "medium",
                sources=[self.name],
                metadata={
                    "repository_index_version": index.get("version"),
                    "selected_files": selected_files,
                    "adjacent_files": adjacent_files,
                    "related_modules": sorted(related_modules),
                    "impacted_files": sorted(impacted_files),
                    "hotspots": hotspots,
                    "duplicate_symbols": duplicate_symbols,
                    "architecture_notes": architecture_notes,
                    "memory_notes": memory_notes,
                    "candidate_dead_code": candidate_dead_code[:5],
                    "violations": violations,
                },
            )
        except Exception as exc:
            return ContextResponse(
                summary=f"Librarian failed to produce context: {exc}",
                evidence=[],
                recommendations=[],
                confidence=0.3,
                freshness="stale",
                impact="medium",
                risk="high",
                sources=[self.name],
                metadata={"error": str(exc)},
            )

    def status(self) -> ProviderStatus:
        """Return the provider health status."""
        return ProviderStatus(provider=self.name, available=True, metadata={"capability": "repository-intelligence"})

    def explain(self, subject: str) -> str:
        """Explain how Librarian derives its repository context."""
        return f"Librarian uses the repository index, symbol graph, git change history, and memory database to answer questions about {subject}."

    def _build_dependency_graph(self, index: Dict[str, Any]) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
        """Build dependency and reverse dependency graphs from the repository index."""
        module_to_path = {
            self._path_to_module(record["path"]): record["path"]
            for record in index.get("files", [])
        }
        dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        reverse_graph: Dict[str, Set[str]] = defaultdict(set)

        for record in index.get("files", []):
            source = record["path"]
            for imported in record.get("imports", []):
                target = self._resolve_import(imported, module_to_path)
                if target and target != source:
                    dependency_graph[source].add(target)
                    reverse_graph[target].add(source)

        return dependency_graph, reverse_graph

    def _path_to_module(self, path: str) -> str:
        """Convert a repository path to a dotted module name."""
        return path[:-3].replace("/", ".") if path.endswith(".py") else path.replace("/", ".")

    def _resolve_import(self, imported: str, module_map: Dict[str, str]) -> Optional[str]:
        """Resolve an import string to a repository path when possible."""
        if imported in module_map:
            return module_map[imported]

        for module_name, file_path in module_map.items():
            if module_name.startswith(imported + "."):
                return file_path

        imported_segment = imported.split(".")[0]
        for module_name, file_path in module_map.items():
            if module_name == imported_segment or module_name.startswith(imported_segment + "."):
                return file_path

        return None

    def _find_related_modules(self, selected_files: List[str], dependency_graph: Dict[str, Set[str]], reverse_graph: Dict[str, Set[str]]) -> Set[str]:
        """Identify modules related to the selected files through dependencies."""
        related: Set[str] = set()
        for path in selected_files:
            related.update(dependency_graph.get(path, set()))
            related.update(reverse_graph.get(path, set()))
        return related.difference(set(selected_files))

    def _find_impacted_files(self, selected_files: List[str], reverse_graph: Dict[str, Set[str]]) -> Set[str]:
        """Determine files that are impacted by changes to selected files."""
        impacted: Set[str] = set()
        queue = deque(selected_files)
        while queue:
            current = queue.popleft()
            for dependent in reverse_graph.get(current, set()):
                if dependent not in impacted and dependent not in selected_files:
                    impacted.add(dependent)
                    queue.append(dependent)
        return impacted

    def _find_duplicate_symbols(self, index: Dict[str, Any]) -> Dict[str, List[str]]:
        """Find duplicate function and class names across the repository."""
        duplicates: Dict[str, List[str]] = defaultdict(list)
        for record in index.get("files", []):
            path = record["path"]
            names = [symbol["name"] for symbol in record.get("functions", []) + record.get("classes", [])]
            for name in names:
                duplicates[name].append(path)
        return {name: paths for name, paths in duplicates.items() if len(paths) > 1}

    def _find_hotspots(self, index: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find recently changed files and hotspots from git metadata."""
        hotspots = []
        for record in index.get("files", []):
            timestamp = record.get("last_changed_unix")
            if timestamp is None:
                continue
            try:
                hotspots.append({"path": record["path"], "last_changed_unix": int(timestamp), "subject": record.get("last_commit_subject")})
            except ValueError:
                continue
        hotspots.sort(key=lambda item: item["last_changed_unix"], reverse=True)
        return hotspots[:5]

    def _query_memory(self, query_text: str) -> List[str]:
        """Query the existing ChromaDB memory store for related repository context."""
        if not self.memory_path.exists():
            return []

        try:
            client = chromadb.PersistentClient(path=str(self.memory_path))
            collection = client.get_collection(name="kitty_long_term_memory")
            embedding_function = embedding_functions.OllamaEmbeddingFunction(
                url="http://localhost:11434/api/embeddings",
                model_name="nomic-embed-text",
            )
            collection._embedding_function = embedding_function

            results = collection.query(query_texts=[query_text], n_results=3)
            documents = results.get("documents", [])
            if documents and isinstance(documents, list) and documents[0]:
                return [str(doc).strip() for doc in documents[0] if str(doc).strip()]
        except InvalidArgumentError:
            return []
        except Exception:
            return []
        return []

    def _read_architecture_notes(self) -> List[str]:
        """Extract architecture notes from existing Hive documentation."""
        candidates = [
            self.repo_root / "docs" / "structure_guide.md",
            self.repo_root / "strategic_breakdown.md",
            self.repo_root / "knowledge" / "kitty_core.txt",
        ]
        notes: List[str] = []
        for candidate in candidates:
            if candidate.exists():
                try:
                    content = candidate.read_text(encoding="utf-8", errors="ignore").strip()
                    if content:
                        lines = [line.strip() for line in content.splitlines() if line.strip()]
                        notes.extend(lines[:4])
                        break
                except Exception:
                    continue
        return notes

    def _find_dead_code(self, index: Dict[str, Any], reverse_graph: Dict[str, Set[str]]) -> List[str]:
        """Identify candidate dead code files from dependency data."""
        candidates: List[str] = []
        for record in index.get("files", []):
            path = record["path"]
            if path.endswith("/__init__.py"):
                continue
            inbound = reverse_graph.get(path, set())
            if not inbound and not record.get("entry_points"):
                candidates.append(path)
        return sorted(candidates)[:5]

    def _find_architecture_violations(self, selection: Dict[str, Any], dependency_graph: Dict[str, Set[str]]) -> List[str]:
        """Detect simple architecture boundary violations."""
        violations: List[str] = []
        selected_paths = {item["path"] for item in selection.get("selected_files", [])}
        for path in selected_paths:
            if path.startswith("core/"):
                for dependency in dependency_graph.get(path, set()):
                    if dependency.startswith("agents/"):
                        violations.append(f"core file {path} depends on agent module {dependency}")
                    if dependency.startswith("tools/"):
                        violations.append(f"core file {path} depends on tool module {dependency}")
        return violations

    def _build_evidence(
        self,
        selected_files: List[str],
        impacted_files: Set[str],
        memory_notes: List[str],
        architecture_notes: List[str],
    ) -> List[Evidence]:
        """Produce a compact evidence list for the query response."""
        evidence: List[Evidence] = []
        if selected_files:
            evidence.append(
                Evidence(
                    service=self.name,
                    domain="repository",
                    summary=f"Primary files: {', '.join(selected_files[:3])}",
                    confidence=0.8,
                    freshness="fresh",
                    impact="medium",
                    risk="low",
                    provenance="core/context_manager.py",
                )
            )
        if impacted_files:
            evidence.append(
                Evidence(
                    service=self.name,
                    domain="impact",
                    summary=f"Impacted files: {', '.join(sorted(list(impacted_files))[:3])}",
                    confidence=0.75,
                    freshness="fresh",
                    impact="medium",
                    risk="medium",
                    provenance="core/context_manager.py",
                )
            )
        if architecture_notes:
            evidence.append(
                Evidence(
                    service=self.name,
                    domain="architecture",
                    summary=architecture_notes[0],
                    confidence=0.7,
                    freshness="fresh",
                    impact="medium",
                    risk="low",
                    provenance="docs/structure_guide.md",
                )
            )
        if memory_notes:
            evidence.append(
                Evidence(
                    service=self.name,
                    domain="memory",
                    summary=f"Memory hint: {memory_notes[0][:120]}",
                    confidence=0.65,
                    freshness="fresh",
                    impact="medium",
                    risk="low",
                    provenance="memory/database",
                )
            )
        return evidence

    def _build_recommendations(
        self,
        selected_files: List[str],
        impacted_files: Set[str],
        violations: List[str],
        dead_code: List[str],
    ) -> List[Recommendation]:
        """Produce concise recommendations for the query response."""
        recommendations: List[Recommendation] = []
        if selected_files:
            recommendations.append(
                Recommendation(
                    service=self.name,
                    summary=f"Review primary files {', '.join(selected_files[:3])} and their direct dependencies.",
                    priority="high",
                    confidence=0.77,
                    impact="medium",
                    risk="low",
                    provenance="core/context_manager.py",
                )
            )
        if impacted_files:
            recommendations.append(
                Recommendation(
                    service=self.name,
                    summary=f"Assess the impact on {len(impacted_files)} dependent files before applying changes.",
                    priority="high",
                    confidence=0.74,
                    impact="medium",
                    risk="medium",
                    provenance="core/context_manager.py",
                )
            )
        if violations:
            recommendations.append(
                Recommendation(
                    service=self.name,
                    summary=f"Investigate architecture boundary issues: {violations[0]}",
                    priority="high",
                    confidence=0.7,
                    impact="high",
                    risk="medium",
                    provenance="core/context_manager.py",
                )
            )
        if dead_code:
            recommendations.append(
                Recommendation(
                    service=self.name,
                    summary=f"Review candidate dead code: {dead_code[:3]}",
                    priority="medium",
                    confidence=0.56,
                    impact="low",
                    risk="low",
                    provenance="core/context_manager.py",
                )
            )
        return recommendations
