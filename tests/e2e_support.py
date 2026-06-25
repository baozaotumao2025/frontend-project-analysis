from __future__ import annotations

import json
from pathlib import Path

from frontend_project_analysis.workflow.briefs import render_brief_document
from tests.cli_support import invoke_with_root

PROJECT_KEY = "crm-web"
PROJECT_NAME = "CRM Web"


def create_existing_project_root(tmp_path: Path, name: str = "fpa-e2e-project") -> Path:
    root = tmp_path / name
    root.mkdir()
    (root / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    (root / "README.md").write_text("Existing project README.\n", encoding="utf-8")
    (root / "pyproject.toml").write_text('[project]\nname = "placeholder"\n', encoding="utf-8")
    return root


def prepare_brief_source(tmp_path: Path, name: str = "project-brief.md") -> Path:
    path = tmp_path.parent / f"{tmp_path.name}-{name}"
    path.write_text(
        render_brief_document(
            "# Project Brief\n\n"
            "## What does the product do?\n"
            "- Manage customer assignments.\n\n"
            "## Who are the main users?\n"
            "- Sales reps and operations leads.\n\n"
            "## What are the core usage scenarios?\n"
            "- Reassign customers and review ownership boundaries.\n",
            source_kind="user",
            status="confirmed",
            confirmed_by_user=True,
        ),
        encoding="utf-8",
    )
    return path


def run_fpa(root: Path, args: list[str]):
    return invoke_with_root(root, args)


def write_review_payload(root: Path, filename: str = "review-passed.json") -> Path:
    path = root / filename
    path.write_text(
        json.dumps(
            {
                "decision": "passed",
                "summary": "Semantic review passed for end-to-end validation.",
                "reviewer_ref": "e2e-test",
                "model": "e2e-mock",
                "counterexamples": [
                    "A passing review still needs a concrete alternative failure case."
                ],
                "findings": [
                    {
                        "severity": "INFO",
                        "code": "e2e_evidence",
                        "message": (
                            "The packet contains enough supporting evidence for the test flow."
                        ),
                        "evidence": ["end-to-end validation packet"],
                        "details": {},
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def run_review_cycle(root: Path, artifact_ref: str, review_path: Path) -> None:
    structural = run_fpa(
        root,
        [
            "review",
            "structural",
            "--project",
            PROJECT_KEY,
            "--artifact",
            artifact_ref,
        ],
    )
    assert structural.exit_code == 0, structural.output

    record = run_fpa(
        root,
        [
            "review",
            "semantic-record",
            "--project",
            PROJECT_KEY,
            "--artifact",
            artifact_ref,
            "--input",
            str(review_path),
        ],
    )
    assert record.exit_code == 0, record.output

    approve = run_fpa(
        root,
        [
            "review",
            "approve",
            "--project",
            PROJECT_KEY,
            "--artifact",
            artifact_ref,
        ],
    )
    assert approve.exit_code == 0, approve.output


def assert_round_gate(root: Path, round_number: int, *, should_pass: bool) -> None:
    result = run_fpa(
        root,
        [
            "workflow",
            "start",
            "--project",
            PROJECT_KEY,
            "--round",
            str(round_number),
        ],
    )
    if should_pass:
        assert result.exit_code == 0, result.output
        return

    assert result.exit_code != 0, result.output


def write_round_artifacts(
    root: Path,
    *,
    story_map_complete: bool = True,
    page_complete: bool = True,
    feature_complete: bool = True,
    gwt_complete: bool = True,
    feature_spec_complete: bool = True,
) -> None:
    _write_persona(root)
    _write_story_map(root, complete=story_map_complete)
    _write_page(root, complete=page_complete)
    _write_feature(root, complete=feature_complete)
    _write_gwt(root, complete=gwt_complete)
    _write_feature_spec(root, complete=feature_spec_complete)


def _write_persona(root: Path) -> None:
    path = root / "analysis" / "personas" / "alpha-persona.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "artifact_type: persona",
                "slug: alpha-persona",
                "round: 1",
                "status: draft",
                "project: crm-web",
                "title: Alpha Persona",
                "---",
                "",
                "| Persona Name | Core Goal | Key Difference From Other Persona | "
                "Permission Boundary | Invisible Pages Or Capabilities |",
                "| --- | --- | --- | --- | --- |",
                "| Alpha Persona | Review and update customer records in the test flow | "
                "Needs access to the core record and action controls | "
                "Can edit assignment data for assigned accounts only | "
                "Admin settings, billing, and system configuration |",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_story_map(root: Path, *, complete: bool) -> None:
    path = root / "analysis" / "story-maps" / "alpha-persona.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (
        "---\n"
        "artifact_type: story_map\n"
        "slug: alpha-persona\n"
        "round: 2\n"
        "status: draft\n"
        "project: crm-web\n"
        "title: Alpha Persona Story Map\n"
        "---\n"
        "\n"
        "## Start\n"
        "- Enter the customer workspace.\n"
        "\n"
        "## Activity 1: Review\n"
        "- Step 1: Open a customer record\n"
        "  - Story: View customer details before taking action\n"
        "\n"
        "- Step 2: Confirm the current owner\n"
        "  - Story: Check who is responsible for the account\n"
        "\n"
        "## Activity 2: Reassign\n"
        "- Step 1: Open assignment controls\n"
        "  - Story: Choose a new owner for the customer\n"
        "\n"
        "- Step 2: Save the change\n"
        "  - Story: Persist the updated assignment\n"
    )
    if complete:
        body += "\n## End\n- Leave the customer workspace.\n"
    path.write_text(body, encoding="utf-8")


def _write_page(root: Path, *, complete: bool) -> None:
    path = root / "analysis" / "pages" / "alpha-page.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (
        "---\n"
        "artifact_type: page\n"
        "slug: alpha-page\n"
        "round: 3\n"
        "status: draft\n"
        "project: crm-web\n"
        "title: Alpha Page\n"
        "---\n"
        "\n"
        "# Alpha Page\n"
        "\n"
        "## Route Information\n"
        "- Route: `/alpha-pages/:alphaPageId`\n"
        "\n"
        "## Accessible Persona\n"
        "- Alpha Persona\n"
        "\n"
    )
    if complete:
        body += (
            "\n"
            "## Story Steps Covered\n"
            "- Open the record\n"
            "- Confirm the current owner\n"
            "- Open the action controls\n"
            "- Save the change\n"
            "\n"
            "## Page Responsibility\n"
            "Shows a record and lets the test persona update ownership.\n"
            "\n"
            "## Related Features\n"
            "- Alpha Feature\n"
        )
    path.write_text(body, encoding="utf-8")


def _write_feature(root: Path, *, complete: bool) -> None:
    path = root / "analysis" / "features" / "alpha-feature.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (
        "---\n"
        "artifact_type: feature\n"
        "slug: alpha-feature\n"
        "round: 4\n"
        "status: draft\n"
        "project: crm-web\n"
        "title: Alpha Feature\n"
        "---\n"
        "\n"
        "# Alpha Feature\n"
        "\n"
        "## Page\n"
        "- Alpha Page\n"
        "\n"
    )
    if complete:
        body += (
            "## Persona Served\n"
            "- Alpha Persona\n"
            "\n"
            "## Business Responsibility\n"
            "Lets the test persona reassign a record to another owner.\n"
            "\n"
            "## State Type\n"
            "- both\n"
            "\n"
            "## Cross-Page Reuse\n"
            "- yes\n"
            "\n"
            "## Source Story\n"
            "- Save the change\n"
            "\n"
            "## Discovery And Evidence\n"
            "- The test suite needs a discrete capability to reassign ownership.\n"
            "- The brief assumes ownership changes are backed by the page data service.\n"
            "\n"
            "## Risks And Assumptions\n"
            "- Ownership conflicts can occur if two users edit the same record.\n"
            "- The assignment lookup is assumed to be stable during the release.\n"
            "\n"
            "## Accessibility\n"
            "- The action drawer must be keyboard reachable.\n"
            "- Screen readers need the selected owner and confirmation state announced.\n"
            "\n"
            "## Observability\n"
            "- Track success and failure counts.\n"
            "- Emit a trace or log entry when ownership changes are saved.\n"
            "\n"
            "## Release And Compliance\n"
            "- Ship behind a feature flag and support rollback.\n"
            "- Preserve audit-friendly ownership history for compliance review.\n"
        )
    path.write_text(body, encoding="utf-8")


def _write_gwt(root: Path, *, complete: bool) -> None:
    path = root / "analysis" / "gwt" / "alpha-feature.feature"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (
        "---\n"
        "artifact_type: gwt\n"
        "slug: alpha-feature\n"
        "round: 5\n"
        "status: draft\n"
        "project: crm-web\n"
        "feature: alpha-feature\n"
        "title: Alpha Feature\n"
        "---\n"
        "\n"
        "Feature: Alpha Feature\n\n"
    )
    if complete:
        body += (
            "  Scenario: Happy Path\n"
            "    Given the Alpha Persona can access the record\n"
            "    When the Alpha Persona reassigns the record\n"
            "    Then the owner is updated\n"
            "\n"
            "  Scenario: Permission Case\n"
            "    Given a user lacks assignment permission\n"
            "    When the user tries to reassign the record\n"
            "    Then the action is blocked\n"
            "\n"
            "  Scenario: Error Case\n"
            "    Given the page service is unavailable\n"
            "    When the Alpha Persona reassigns the record\n"
            "    Then an error is shown\n"
            "\n"
            "  Scenario: Edge Case\n"
            "    Given the record is already assigned to the selected owner\n"
            "    When the Alpha Persona reassigns the record\n"
            "    Then the assignment remains consistent\n"
            "\n"
            "  Scenario: Accessibility Case\n"
            "    Given a keyboard-only Alpha Persona is on the action drawer\n"
            "    When the Alpha Persona navigates and confirms the change with the keyboard\n"
            "    Then the change can be completed without a mouse\n"
        )
    else:
        body += (
            "  Scenario: Happy Path\n"
            "    Given the Alpha Persona can access the record\n"
            "    Then the owner is updated\n"
            "\n"
            "  Scenario: Permission Case\n"
            "    Given a user lacks assignment permission\n"
            "    When the user tries to reassign the record\n"
            "    Then the action is blocked\n"
            "\n"
            "  Scenario: Error Case\n"
            "    Given the page service is unavailable\n"
            "    When the Alpha Persona reassigns the record\n"
            "    Then an error is shown\n"
            "\n"
            "  Scenario: Edge Case\n"
            "    Given the record is already assigned to the selected owner\n"
            "    When the Alpha Persona reassigns the record\n"
            "    Then the assignment remains consistent\n"
            "\n"
            "  Scenario: Accessibility Case\n"
            "    Given a keyboard-only Alpha Persona is on the action drawer\n"
            "    When the Alpha Persona navigates and confirms the change with the keyboard\n"
            "    Then the change can be completed without a mouse\n"
        )
    path.write_text(body, encoding="utf-8")


def _write_feature_spec(root: Path, *, complete: bool) -> None:
    path = root / "analysis" / "specs" / "features" / "alpha-feature-spec.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (
        "---\n"
        "artifact_type: feature_spec\n"
        "slug: alpha-feature\n"
        "round: 6\n"
        "status: draft\n"
        "project: crm-web\n"
        "title: Alpha Feature Spec\n"
        "---\n"
        "\n"
        "# Alpha Feature - Feature Spec\n"
        "\n"
        "## Basic Information\n"
        "- Feature: Alpha Feature\n"
        "- Page: Alpha Page\n"
        "- Persona: Alpha Persona\n"
        "- Round: 6\n"
        "\n"
        "## Roles And Permissions\n"
        "- The Alpha Persona can update ownership for records they can access.\n"
        "- Unauthorized users cannot change ownership.\n"
        "\n"
        "## Component Breakdown\n"
        "- Customer profile shell\n"
        "- Assignment drawer\n"
        "- Ownership confirmation dialog\n"
        "\n"
        "## Discovery And Evidence\n"
        "\n"
        "## Risks And Assumptions\n"
        "\n"
        "## State Boundary\n"
        "\n"
        "## Accessibility\n"
        "\n"
        "## Observability\n"
        "\n"
        "## Release And Compliance\n"
        "\n"
        "## Cross-Feature Dependencies\n"
        "- Customer profile data\n"
        "- Assignment lookup data\n"
        "\n"
        "## Given-When-Then Acceptance Spec\n"
        "- Reuse the Alpha Feature GWT file as the acceptance contract.\n"
    )
    if complete:
        body = body.replace(
            "## Discovery And Evidence\n"
            "\n"
            "## Risks And Assumptions\n"
            "\n"
            "## State Boundary\n"
            "\n"
            "## Accessibility\n"
            "\n"
            "## Observability\n"
            "\n"
            "## Release And Compliance\n"
            "\n"
            "## Cross-Feature Dependencies\n"
            "- Customer profile data\n"
            "- Assignment lookup data\n",
            "\n".join(
                [
                    "## Discovery And Evidence",
                    "- Sales support and operations both need to reassign customer "
                    "ownership during handoffs.",
                    "- The brief assumes ownership changes are backed by the "
                    "customer profile service.",
                    "",
                    "## Risks And Assumptions",
                    "- Ownership conflicts can occur if two users edit the same record.",
                    "- The assignment lookup is assumed to be stable during the release.",
                    "",
                    "## State Boundary",
                    "- Server state:",
                    "  - Customer ownership is stored on the backend and updated through the "
                    "assignment request.",
                    "- Client state:",
                    "  - The assignment drawer keeps only the in-progress selection and "
                    "confirmation state.",
                    "- Do not store workspace-wide ownership cache in shared component state.",
                    "",
                    "## Accessibility",
                    "- The assignment drawer remains keyboard reachable.",
                    "- Screen readers announce the selected owner and confirmation state.",
                    "",
                    "## Observability",
                    "- Track assignment success and failure counts.",
                    "- Emit a trace or log entry when ownership changes are saved.",
                    "",
                    "## Release And Compliance",
                    "- Ship behind a feature flag and support rollback.",
                    "- Preserve audit-friendly ownership history for compliance review.",
                    "",
                    "## Cross-Feature Dependencies",
                    "- Customer profile data",
                    "- Assignment lookup data",
                ]
            ),
        )
    else:
        body = body.replace(
            "## Discovery And Evidence\n"
            "\n"
            "## Risks And Assumptions\n"
            "\n"
            "## State Boundary\n"
            "\n"
            "## Accessibility\n"
            "\n"
            "## Observability\n"
            "\n"
            "## Release And Compliance\n"
            "\n"
            "## Cross-Feature Dependencies\n"
            "- Customer profile data\n"
            "- Assignment lookup data\n",
            "\n".join(
                [
                    "## State Boundary",
                    "- Shared cache",
                    "",
                    "## Cross-Feature Dependencies",
                    "- Customer profile data",
                    "- Assignment lookup data",
                ]
            ),
        )
    path.write_text(body, encoding="utf-8")
