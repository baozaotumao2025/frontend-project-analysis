# ruff: noqa: E501
from __future__ import annotations

import json
from pathlib import Path

import pytest

from frontend_project_analysis.core.domain import ArtifactStatus, ArtifactType, DependencyType
from frontend_project_analysis.infrastructure.storage import session_scope
from frontend_project_analysis.repositories.dependencies import add_dependency
from frontend_project_analysis.repositories.projects import ensure_project
from frontend_project_analysis.repositories.versions import upsert_artifact
from frontend_project_analysis.workflow.io.graph_export import (
    build_graph_projection,
    render_graph_html,
)
from frontend_project_analysis.workflow.io.relations import render_relations_markdown
from frontend_project_analysis.workflow.state.definitions import WorkflowStateError
from tests.cli_support import bootstrap_project, invoke_with_root, prepare_database


def _write_markdown_artifact(path: Path, artifact_type: str, slug: str, round_number: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        f"artifact_type: {artifact_type}\n"
        f"slug: {slug}\n"
        f"round: {round_number}\n"
        "status: draft\n"
        "project: crm-web\n"
        f"title: {slug.replace('-', ' ').title()}\n"
        "---\n"
        f"# {slug.replace('-', ' ').title()}\n",
        encoding="utf-8",
    )


def _write_gwt_artifact(path: Path, slug: str, feature_slug: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "artifact_type: gwt\n"
        f"slug: {slug}\n"
        "round: 5\n"
        "status: draft\n"
        "project: crm-web\n"
        f"feature: {feature_slug}\n"
        f"title: {slug.replace('-', ' ').title()}\n"
        "---\n"
        "\n"
        f"Feature: {slug}\n\n"
        "  Scenario: Happy Path\n"
        "    Given the actor is signed in\n"
        "    When they complete the happy path\n"
        "    Then the result succeeds\n\n"
        "  Scenario: Permission Case\n"
        "    Given the actor lacks permission\n"
        "    When they try the action\n"
        "    Then access is denied\n\n"
        "  Scenario: Error Case\n"
        "    Given the service fails\n"
        "    When they retry the action\n"
        "    Then an error is shown\n\n"
        "  Scenario: Edge Case\n"
        "    Given duplicate input exists\n"
        "    When they retry the action\n"
        "    Then the state remains consistent\n\n"
        "  Scenario: Accessibility Case\n"
        "    Given keyboard-only navigation is active\n"
        "    When they complete the action\n"
        "    Then the result stays usable\n",
        encoding="utf-8",
    )


def _register_artifact(
    session,
    project,
    artifact_type: ArtifactType,
    slug: str,
    relative_path: str,
):
    return upsert_artifact(
        session=session,
        project=project,
        artifact_type=artifact_type,
        slug=slug,
        title=slug.replace("-", " ").title(),
        source_path=relative_path,
        status=ArtifactStatus.DRAFT,
        metadata={},
        created_by="test",
    )


def test_relations_export_projects_the_same_row_set_into_all_three_matrices(
    tmp_path: Path,
) -> None:
    paths = prepare_database(tmp_path)

    files = {
        "alpha_persona": tmp_path / "docs" / "personas" / "alpha-persona.md",
        "beta_persona": tmp_path / "docs" / "personas" / "beta-persona.md",
        "alpha_story": tmp_path / "docs" / "story-maps" / "alpha-journey.md",
        "alpha_page": tmp_path / "docs" / "pages" / "alpha-page.md",
        "alpha_feature": tmp_path / "docs" / "features" / "alpha-feature.md",
        "alpha_gwt": tmp_path / "docs" / "gwt" / "alpha-feature.feature",
    }
    _write_markdown_artifact(files["alpha_persona"], "persona", "alpha-persona", 1)
    _write_markdown_artifact(files["beta_persona"], "persona", "beta-persona", 1)
    _write_markdown_artifact(files["alpha_story"], "story_map", "alpha-journey", 2)
    _write_markdown_artifact(files["alpha_page"], "page", "alpha-page", 3)
    _write_markdown_artifact(files["alpha_feature"], "feature", "alpha-feature", 4)
    _write_gwt_artifact(files["alpha_gwt"], "alpha-feature", "alpha-feature")

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        _register_artifact(
            session,
            project,
            ArtifactType.PERSONA,
            "alpha-persona",
            "docs/personas/alpha-persona.md",
        )
        _register_artifact(
            session,
            project,
            ArtifactType.PERSONA,
            "beta-persona",
            "docs/personas/beta-persona.md",
        )
        _register_artifact(
            session,
            project,
            ArtifactType.STORY_MAP,
            "alpha-journey",
            "docs/story-maps/alpha-journey.md",
        )
        _register_artifact(
            session,
            project,
            ArtifactType.PAGE,
            "alpha-page",
            "docs/pages/alpha-page.md",
        )
        _register_artifact(
            session,
            project,
            ArtifactType.FEATURE,
            "alpha-feature",
            "docs/features/alpha-feature.md",
        )
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.GWT,
            slug="alpha-feature",
            title="Alpha Feature",
            source_path="docs/gwt/alpha-feature.feature",
            status=ArtifactStatus.DRAFT,
            metadata={"feature": "alpha-feature"},
            created_by="test",
        )

        add_dependency(
            session,
            project,
            "story_map:alpha-journey",
            "persona:alpha-persona",
            DependencyType.REQUIRES,
            True,
        )
        add_dependency(
            session,
            project,
            "page:alpha-page",
            "story_map:alpha-journey",
            DependencyType.REQUIRES,
            True,
        )
        add_dependency(
            session,
            project,
            "feature:alpha-feature",
            "page:alpha-page",
            DependencyType.REQUIRES,
            True,
        )
        add_dependency(
            session,
            project,
            "gwt:alpha-feature",
            "feature:alpha-feature",
            DependencyType.REQUIRES,
            True,
        )

        written = render_relations_markdown(session, project, tmp_path)

    assert len(written) == 3
    psp_text = (tmp_path / "analysis" / "relations" / "persona-story-page-matrix.md").read_text(
        encoding="utf-8"
    )
    feature_text = (
        tmp_path / "analysis" / "relations" / "feature-coverage-matrix.md"
    ).read_text(encoding="utf-8")
    gwt_text = (tmp_path / "analysis" / "relations" / "gwt-feature-matrix.md").read_text(
        encoding="utf-8"
    )

    assert "| Persona | Story Map | Page | Feature | GWT |" in psp_text
    assert "| Feature | Persona | Page | Story Map | GWT |" in feature_text
    assert "| GWT | Feature | Page | Persona | Story Map |" in gwt_text

    alpha_persona_link = "[persona:alpha-persona](../../docs/personas/alpha-persona.md)"
    beta_persona_link = "[persona:beta-persona](../../docs/personas/beta-persona.md)"
    alpha_story_link = "[story_map:alpha-journey](../../docs/story-maps/alpha-journey.md)"
    alpha_page_link = "[page:alpha-page](../../docs/pages/alpha-page.md)"
    alpha_feature_link = "[feature:alpha-feature](../../docs/features/alpha-feature.md)"
    alpha_gwt_link = "[gwt:alpha-feature](../../docs/gwt/alpha-feature.feature)"
    alpha_persona_graph_link = "[↗](./graph.html?persona=persona%3Aalpha-persona&focus_ref=persona%3Aalpha-persona&path_scope=downstream)"
    alpha_feature_graph_link = "[↗](./graph.html?feature=feature%3Aalpha-feature&focus_ref=feature%3Aalpha-feature&path_scope=both)"
    alpha_page_graph_link = "[↗](./graph.html?focus_ref=page%3Aalpha-page&path_scope=both)"
    alpha_gwt_graph_link = "[↗](./graph.html?focus_ref=gwt%3Aalpha-feature&path_scope=upstream)"

    for matrix_text in (psp_text, feature_text, gwt_text):
        assert alpha_persona_link in matrix_text
        assert beta_persona_link in matrix_text
        assert alpha_feature_link in matrix_text
        assert alpha_gwt_link in matrix_text
        assert alpha_persona_graph_link in matrix_text
        assert alpha_feature_graph_link in matrix_text
        assert alpha_page_graph_link in matrix_text
        assert alpha_gwt_graph_link in matrix_text

    assert alpha_story_link in psp_text
    assert alpha_page_link in psp_text
    assert alpha_story_link in feature_text
    assert alpha_page_link in feature_text
    assert alpha_story_link in gwt_text
    assert alpha_page_link in gwt_text


def test_graph_projection_contains_nodes_edges_rows_and_coverage_summary(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)

    files = {
        "persona": tmp_path / "docs" / "personas" / "alpha-persona.md",
        "story_map": tmp_path / "docs" / "story-maps" / "alpha-journey.md",
        "page": tmp_path / "docs" / "pages" / "alpha-page.md",
        "feature": tmp_path / "docs" / "features" / "alpha-feature.md",
        "gwt": tmp_path / "docs" / "gwt" / "alpha-feature.feature",
    }
    _write_markdown_artifact(files["persona"], "persona", "alpha-persona", 1)
    _write_markdown_artifact(files["story_map"], "story_map", "alpha-journey", 2)
    _write_markdown_artifact(files["page"], "page", "alpha-page", 3)
    _write_markdown_artifact(files["feature"], "feature", "alpha-feature", 4)
    _write_gwt_artifact(files["gwt"], "alpha-feature", "alpha-feature")

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        _register_artifact(
            session, project, ArtifactType.PERSONA, "alpha-persona", "docs/personas/alpha-persona.md"
        )
        _register_artifact(
            session, project, ArtifactType.STORY_MAP, "alpha-journey", "docs/story-maps/alpha-journey.md"
        )
        _register_artifact(
            session, project, ArtifactType.PAGE, "alpha-page", "docs/pages/alpha-page.md"
        )
        _register_artifact(
            session, project, ArtifactType.FEATURE, "alpha-feature", "docs/features/alpha-feature.md"
        )
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.GWT,
            slug="alpha-feature",
            title="Alpha Feature",
            source_path="docs/gwt/alpha-feature.feature",
            status=ArtifactStatus.DRAFT,
            metadata={"feature": "alpha-feature"},
            created_by="test",
        )

        add_dependency(
            session,
            project,
            "story_map:alpha-journey",
            "persona:alpha-persona",
            DependencyType.REQUIRES,
            True,
        )
        add_dependency(
            session,
            project,
            "page:alpha-page",
            "story_map:alpha-journey",
            DependencyType.REQUIRES,
            True,
        )
        add_dependency(
            session,
            project,
            "feature:alpha-feature",
            "page:alpha-page",
            DependencyType.REQUIRES,
            True,
        )
        add_dependency(
            session,
            project,
            "gwt:alpha-feature",
            "feature:alpha-feature",
            DependencyType.REQUIRES,
            True,
        )

        payload = build_graph_projection(session, project, tmp_path)

    assert payload["summary"]["node_count"] == 5
    assert payload["summary"]["edge_count"] == 4
    assert payload["summary"]["row_count"] == 1
    assert payload["summary"]["coverage"]["feature"]["artifact_count"] == 1
    assert payload["summary"]["coverage"]["gwt"]["row_count"] == 1
    assert payload["rows"] == [
        {
            "persona": "persona:alpha-persona",
            "story_map": "story_map:alpha-journey",
            "page": "page:alpha-page",
            "feature": "feature:alpha-feature",
            "gwt": "gwt:alpha-feature",
        }
    ]
    feature_node = next(node for node in payload["nodes"] if node["ref"] == "feature:alpha-feature")
    assert feature_node["analysis_link"] == "../../docs/features/alpha-feature.md"
    assert feature_node["group"] == {
        "lane": "feature",
        "lane_label": "Feature",
        "column": 3,
    }
    assert feature_node["adjacent_refs"] == ["gwt:alpha-feature", "page:alpha-page"]
    assert feature_node["direct_upstream_refs"] == ["page:alpha-page"]
    assert feature_node["direct_downstream_refs"] == ["gwt:alpha-feature"]
    assert feature_node["upstream_refs"] == [
        "page:alpha-page",
        "persona:alpha-persona",
        "story_map:alpha-journey",
    ]
    assert feature_node["downstream_refs"] == ["gwt:alpha-feature"]
    assert feature_node["layout"] == {
        "column": 3,
        "row": 0,
        "x": 860,
        "y": 90,
        "width": 180,
        "height": 56,
    }
    assert payload["summary"]["layout"]["card_width"] == 180
    assert payload["summary"]["layout"]["lanes"]["feature"] == {
        "column": 3,
        "x": 860,
        "label": "Feature",
    }
    assert {
        edge["from"] + "->" + edge["to"] for edge in payload["edges"]
    } == {
        "story_map:alpha-journey->persona:alpha-persona",
        "page:alpha-page->story_map:alpha-journey",
        "feature:alpha-feature->page:alpha-page",
        "gwt:alpha-feature->feature:alpha-feature",
    }


def test_relations_export_covers_all_features_and_gwts_in_each_matrix(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)

    artifacts = [
        ("persona", "alpha-persona", 1, "docs/personas/alpha-persona.md"),
        ("persona", "beta-persona", 1, "docs/personas/beta-persona.md"),
        ("story_map", "alpha-journey", 2, "docs/story-maps/alpha-journey.md"),
        ("story_map", "beta-journey", 2, "docs/story-maps/beta-journey.md"),
        ("page", "alpha-page", 3, "docs/pages/alpha-page.md"),
        ("page", "beta-page", 3, "docs/pages/beta-page.md"),
        ("feature", "alpha-feature", 4, "docs/features/alpha-feature.md"),
        ("feature", "beta-feature", 4, "docs/features/beta-feature.md"),
    ]
    for artifact_type, slug, round_number, relative_path in artifacts:
        _write_markdown_artifact(tmp_path / relative_path, artifact_type, slug, round_number)
    _write_gwt_artifact(tmp_path / "docs/gwt/alpha-feature.feature", "alpha-feature", "alpha-feature")
    _write_gwt_artifact(tmp_path / "docs/gwt/beta-feature.feature", "beta-feature", "beta-feature")

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        for artifact_type, slug, _round_number, relative_path in artifacts:
            _register_artifact(
                session,
                project,
                ArtifactType(artifact_type),
                slug,
                relative_path,
            )
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.GWT,
            slug="alpha-feature",
            title="Alpha Feature",
            source_path="docs/gwt/alpha-feature.feature",
            status=ArtifactStatus.DRAFT,
            metadata={"feature": "alpha-feature"},
            created_by="test",
        )
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.GWT,
            slug="beta-feature",
            title="Beta Feature",
            source_path="docs/gwt/beta-feature.feature",
            status=ArtifactStatus.DRAFT,
            metadata={"feature": "beta-feature"},
            created_by="test",
        )

        add_dependency(
            session,
            project,
            "story_map:alpha-journey",
            "persona:alpha-persona",
            DependencyType.REQUIRES,
            True,
        )
        add_dependency(
            session,
            project,
            "story_map:beta-journey",
            "persona:beta-persona",
            DependencyType.REQUIRES,
            True,
        )
        add_dependency(
            session, project, "page:alpha-page", "story_map:alpha-journey", DependencyType.REQUIRES, True
        )
        add_dependency(
            session, project, "page:beta-page", "story_map:beta-journey", DependencyType.REQUIRES, True
        )
        add_dependency(
            session, project, "feature:alpha-feature", "page:alpha-page", DependencyType.REQUIRES, True
        )
        add_dependency(
            session, project, "feature:beta-feature", "page:beta-page", DependencyType.REQUIRES, True
        )
        add_dependency(
            session,
            project,
            "gwt:alpha-feature",
            "feature:alpha-feature",
            DependencyType.REQUIRES,
            True,
        )
        add_dependency(
            session,
            project,
            "gwt:beta-feature",
            "feature:beta-feature",
            DependencyType.REQUIRES,
            True,
        )

        render_relations_markdown(session, project, tmp_path)

    expected_refs = {
        "feature:alpha-feature",
        "feature:beta-feature",
        "gwt:alpha-feature",
        "gwt:beta-feature",
        "page:alpha-page",
        "page:beta-page",
    }
    for path in (
        tmp_path / "analysis" / "relations" / "persona-story-page-matrix.md",
        tmp_path / "analysis" / "relations" / "feature-coverage-matrix.md",
        tmp_path / "analysis" / "relations" / "gwt-feature-matrix.md",
    ):
        text = path.read_text(encoding="utf-8")
        for ref in expected_refs:
            assert ref in text


def test_relations_export_fails_when_gwt_feature_reference_is_missing_from_project(
    tmp_path: Path,
) -> None:
    paths = prepare_database(tmp_path)
    feature_path = tmp_path / "docs" / "features" / "alpha-feature.md"
    gwt_path = tmp_path / "docs" / "gwt" / "alpha-feature.feature"
    _write_markdown_artifact(feature_path, "feature", "alpha-feature", 4)
    _write_gwt_artifact(gwt_path, "alpha-feature", "missing-feature")

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        _register_artifact(
            session, project, ArtifactType.FEATURE, "alpha-feature", "docs/features/alpha-feature.md"
        )
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.GWT,
            slug="alpha-feature",
            title="Alpha Feature",
            source_path="docs/gwt/alpha-feature.feature",
            status=ArtifactStatus.DRAFT,
            metadata={"feature": "missing-feature"},
            created_by="test",
        )

        with pytest.raises(WorkflowStateError, match="references missing Feature"):
            render_relations_markdown(session, project, tmp_path)


def test_relations_export_fails_when_gwt_frontmatter_disagrees_with_hard_dependency(
    tmp_path: Path,
) -> None:
    paths = prepare_database(tmp_path)
    alpha_feature_path = tmp_path / "docs" / "features" / "alpha-feature.md"
    beta_feature_path = tmp_path / "docs" / "features" / "beta-feature.md"
    gwt_path = tmp_path / "docs" / "gwt" / "alpha-feature.feature"
    _write_markdown_artifact(alpha_feature_path, "feature", "alpha-feature", 4)
    _write_markdown_artifact(beta_feature_path, "feature", "beta-feature", 4)
    _write_gwt_artifact(gwt_path, "alpha-feature", "alpha-feature")

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        _register_artifact(
            session, project, ArtifactType.FEATURE, "alpha-feature", "docs/features/alpha-feature.md"
        )
        _register_artifact(
            session, project, ArtifactType.FEATURE, "beta-feature", "docs/features/beta-feature.md"
        )
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.GWT,
            slug="alpha-feature",
            title="Alpha Feature",
            source_path="docs/gwt/alpha-feature.feature",
            status=ArtifactStatus.DRAFT,
            metadata={"feature": "alpha-feature"},
            created_by="test",
        )
        add_dependency(
            session,
            project,
            "gwt:alpha-feature",
            "feature:beta-feature",
            DependencyType.REQUIRES,
            True,
        )

        with pytest.raises(WorkflowStateError, match="does not match hard dependency"):
            render_relations_markdown(session, project, tmp_path)


def test_export_graph_json_command_writes_graph_payload(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)

    graph_json_result = invoke_with_root(
        tmp_path,
        [
            "export",
            "graph-json",
            "--project",
            "crm-web",
        ],
    )
    assert graph_json_result.exit_code == 0, graph_json_result.output

    graph_json_path = tmp_path / ".frontend-project-analysis" / "exports" / "crm-web-graph.json"
    payload = json.loads(graph_json_path.read_text(encoding="utf-8"))
    assert payload["project"]["key"] == "crm-web"
    assert any(node["ref"] == "persona:alpha-persona" for node in payload["nodes"])
    assert any(node["ref"] == "feature:alpha-feature" for node in payload["nodes"])
    assert any(edge["from"] == "feature:alpha-feature" for edge in payload["edges"])
    assert payload["summary"]["node_count"] >= 2


def test_export_graph_html_command_writes_clickable_graph_page(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)

    graph_html_result = invoke_with_root(
        tmp_path,
        [
            "export",
            "graph-html",
            "--project",
            "crm-web",
        ],
    )
    assert graph_html_result.exit_code == 0, graph_html_result.output

    graph_html_path = tmp_path / "analysis" / "relations" / "graph.html"
    html = graph_html_path.read_text(encoding="utf-8")
    assert "<svg id=\"graph\"" in html
    assert "feature:alpha-feature" in html
    assert "persona:alpha-persona" in html
    assert "../features/alpha-feature.md" in html
    assert "Persona Focus" in html
    assert "Feature Focus" in html
    assert "Path Scope" in html
    assert "new URLSearchParams(window.location.search)" in html
    assert 'params.get("focus_ref")' in html
    assert 'params.get("persona")' in html
    assert 'params.get("feature")' in html
    assert 'params.get("path_scope")' in html
    assert "collectPathContext" in html
    assert 'pathScope.value' in html
    assert "window.history.replaceState" in html
    assert "nodeLayout.set(node.ref, node.layout)" in html
    assert "seedNode.upstream_refs" in html
    assert "seedNode.downstream_refs" in html
    assert "from.width" in html
    assert "point.width" in html
    assert 'next.set("persona", personaFocus.value)' in html
    assert 'next.set("feature", featureFocus.value)' in html
    assert 'next.set("focus_ref", activeRef)' in html
    assert 'next.set("path_scope", pathScope.value)' in html
    assert 'entry.el.classList.toggle("path-active"' in html
    assert 'entry.el.classList.toggle("active", Boolean(isSeed))' in html
    assert 'entry.el.classList.toggle("path-active", Boolean(inPath))' in html
    assert "application/json" in html


def test_render_graph_html_escapes_html_sensitive_project_and_payload_content() -> None:
    payload = {
        "project": {
            "key": 'crm-<unsafe>"key"',
            "name": 'CRM </script><b>Unsafe</b>',
            "root_path": "/tmp/project",
        },
        "summary": {
            "node_count": 1,
            "edge_count": 0,
            "row_count": 1,
            "coverage": {
                "feature": {"artifact_count": 1, "row_count": 1},
            },
            "layout": {"card_width": 180, "card_height": 56, "top_padding": 90, "vertical_gap": 86, "lanes": {}},
        },
        "nodes": [
            {
                "ref": "feature:unsafe",
                "type": "feature",
                "type_label": "Feature",
                "slug": "unsafe",
                "title": 'Unsafe </script><i>Title</i>',
                "round": 4,
                "status": "draft",
                "source_path": 'analysis/features/unsafe-<b>.md',
                "analysis_link": "../features/unsafe.md",
                "adjacent_refs": [],
                "direct_upstream_refs": [],
                "direct_downstream_refs": [],
                "upstream_refs": [],
                "downstream_refs": [],
                "group": {"lane": "feature", "lane_label": "Feature", "column": 3},
                "layout": {"column": 3, "row": 0, "x": 860, "y": 90, "width": 180, "height": 56},
            }
        ],
        "edges": [],
        "rows": [
            {
                "persona": "",
                "story_map": "",
                "page": "",
                "feature": "feature:unsafe",
                "gwt": "",
            }
        ],
    }

    html = render_graph_html(payload)

    assert "CRM &lt;\\/script&gt;&lt;b&gt;Unsafe&lt;/b&gt;" not in html
    assert "CRM &lt;/script&gt;&lt;b&gt;Unsafe&lt;/b&gt;" in html
    assert 'crm-&lt;unsafe&gt;&quot;key&quot;' in html
    assert "<script id=\"graph-data\" type=\"application/json\">" in html
    assert "</script><b>Unsafe</b>" not in html
    assert "Unsafe <\\/script><i>Title<\\/i>" in html
    assert "function escapeHtml(value)" in html
    assert "escapeHtml(node.source_path)" in html
    assert "escapeHtml(edge.from)" in html


def test_refresh_document_indexes_adds_relations_index_links(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)

    root_index = (tmp_path / "analysis" / "index.md").read_text(encoding="utf-8")
    relations_index = (tmp_path / "analysis" / "relations" / "index.md").read_text(
        encoding="utf-8"
    )

    assert "./relations/index.md" in root_index
    assert "./relations/graph.html" in root_index
    assert "./graph.html" in relations_index
    assert "./persona-story-page-matrix.md" in relations_index
