from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from support.runtime_bridge import (
    CODEX_DISPATCH_BRIDGE_PHRASE,
    LEGACY_RUNTIME_BRIDGE_BEGIN,
    LEGACY_RUNTIME_BRIDGE_END,
    RUNTIME_BRIDGE_BEGIN,
    RUNTIME_BRIDGE_END,
    RUNTIME_CAPSULE_BRIDGE_PHRASES,
    RUNTIME_FINISH_BRIDGE_PHRASE,
    RUNTIME_NATIVE_DELEGATION_PHRASES,
    RUNTIME_START_BRIDGE_PHRASE,
    merge_runtime_bridge,
    runtime_bridge_block,
    runtime_bridge_required_phrases,
)


class RuntimeExecutionCapsuleBridgeTests(unittest.TestCase):
    def test_all_runtime_bridges_share_start_and_capsule_contract(self) -> None:
        for runtime_name, instruction_file in (
            ("Codex", "AGENTS.md"),
            ("Claude", "CLAUDE.md"),
            ("Antigravity", "AGENTS.md"),
        ):
            with self.subTest(runtime=runtime_name):
                required = runtime_bridge_required_phrases(runtime_name, instruction_file)
                block = runtime_bridge_block(ROOT, runtime_name, instruction_file)

                self.assertIn(RUNTIME_START_BRIDGE_PHRASE, required)
                self.assertIn(RUNTIME_START_BRIDGE_PHRASE, block)
                self.assertIn(RUNTIME_FINISH_BRIDGE_PHRASE, required)
                self.assertIn(RUNTIME_FINISH_BRIDGE_PHRASE, block)
                for phrase in RUNTIME_CAPSULE_BRIDGE_PHRASES:
                    self.assertIn(phrase, required)
                    self.assertIn(phrase, block)

                self.assertIn(RUNTIME_NATIVE_DELEGATION_PHRASES[runtime_name], required)
                self.assertIn(RUNTIME_NATIVE_DELEGATION_PHRASES[runtime_name], block)
                self.assertIn("worker-specific evidence paths", block)
                self.assertNotIn("docs-read", block.lower())
                self.assertNotIn("receipt", block.lower())

    def test_codex_dispatch_is_conditional_and_does_not_require_a_fresh_process(self) -> None:
        codex_block = runtime_bridge_block(ROOT, "Codex", "AGENTS.md")
        claude_block = runtime_bridge_block(ROOT, "Claude", "CLAUDE.md")
        agy_block = runtime_bridge_block(ROOT, "Antigravity", "AGENTS.md")

        self.assertIn(CODEX_DISPATCH_BRIDGE_PHRASE, codex_block)
        self.assertIn("only when the selected model", CODEX_DISPATCH_BRIDGE_PHRASE)
        self.assertIn("instead of launching a fresh Codex process", CODEX_DISPATCH_BRIDGE_PHRASE)
        self.assertNotIn(
            "After the parent records the split decision, use workflow.py dispatch --execute",
            codex_block,
        )
        self.assertNotIn(CODEX_DISPATCH_BRIDGE_PHRASE, claude_block)
        self.assertNotIn(CODEX_DISPATCH_BRIDGE_PHRASE, agy_block)

    def test_managed_bridge_refresh_preserves_surrounding_runtime_instructions(self) -> None:
        for runtime_name, instruction_file in (
            ("Codex", "AGENTS.md"),
            ("Claude", "CLAUDE.md"),
            ("Antigravity", "AGENTS.md"),
        ):
            with self.subTest(runtime=runtime_name), tempfile.TemporaryDirectory() as temp_dir:
                target = Path(temp_dir) / instruction_file
                target.write_text(
                    "# user-owned before\n\n"
                    f"{RUNTIME_BRIDGE_BEGIN}\n"
                    "stale installer-managed bridge\n"
                    f"{RUNTIME_BRIDGE_END}\n\n"
                    "# user-owned after\n",
                    encoding="utf-8",
                )

                status = merge_runtime_bridge(
                    target,
                    dry_run=False,
                    block=runtime_bridge_block(ROOT, runtime_name, instruction_file),
                    required_phrases=runtime_bridge_required_phrases(runtime_name, instruction_file),
                )

                updated = target.read_text(encoding="utf-8")
                self.assertEqual("installed", status)
                self.assertIn("# user-owned before", updated)
                self.assertIn("# user-owned after", updated)
                self.assertNotIn("stale installer-managed bridge", updated)
                self.assertEqual(1, updated.count(RUNTIME_BRIDGE_BEGIN))
                self.assertEqual(1, updated.count(RUNTIME_BRIDGE_END))
                self.assertIn(RUNTIME_START_BRIDGE_PHRASE, updated)
                self.assertIn("worker-specific evidence paths", updated)

    def test_managed_bridge_removes_legacy_managed_block_without_touching_user_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "CLAUDE.md"
            current = runtime_bridge_block(ROOT, "Claude", "CLAUDE.md")
            target.write_text(
                "# user-owned before\n\n"
                f"{LEGACY_RUNTIME_BRIDGE_BEGIN}\n"
                "legacy direct workflow.py and agent-preflight.py instructions\n"
                f"{LEGACY_RUNTIME_BRIDGE_END}\n\n"
                f"{current}"
                "# user-owned after\n",
                encoding="utf-8",
            )

            self.assertEqual(
                "missing",
                merge_runtime_bridge(
                    target,
                    dry_run=True,
                    block=current,
                    required_phrases=runtime_bridge_required_phrases("Claude", "CLAUDE.md"),
                ),
            )
            self.assertEqual(
                "installed",
                merge_runtime_bridge(
                    target,
                    dry_run=False,
                    block=current,
                    required_phrases=runtime_bridge_required_phrases("Claude", "CLAUDE.md"),
                ),
            )

            updated = target.read_text(encoding="utf-8")
            self.assertIn("# user-owned before", updated)
            self.assertIn("# user-owned after", updated)
            self.assertNotIn(LEGACY_RUNTIME_BRIDGE_BEGIN, updated)
            self.assertNotIn("legacy direct workflow.py", updated)
            self.assertEqual(1, updated.count(RUNTIME_BRIDGE_BEGIN))

    def test_templates_use_one_start_and_direct_required_docs(self) -> None:
        repo_template = (ROOT / "templates" / "repo-agents-routing.md").read_text()
        prompt_template = (ROOT / "templates" / "use-agentplaybook-prompt.md").read_text()
        normalized_repo_template = " ".join(repo_template.split())

        self.assertIn("run `agent-hook.py start` once", repo_template)
        self.assertIn("read the route's `required_docs`", normalized_repo_template)
        self.assertIn("run `agent-hook.py handoff`", repo_template)
        self.assertEqual(1, repo_template.count("run `agent-hook.py start`"))

        self.assertIn("scripts/agent-hook.py start", prompt_template)
        self.assertIn("Read every `required_docs` entry", prompt_template)
        self.assertIn("scripts/agent-hook.py handoff", prompt_template)
        self.assertNotIn("scripts/workflow.py list", prompt_template)
        self.assertNotIn("scripts/workflow.py classify", prompt_template)
        self.assertNotIn("scripts/agent-preflight.py --project", prompt_template)
        self.assertNotIn("scripts/agent-finish-check.py --project", prompt_template)
        self.assertIn("scripts/agent-hook.py finish", prompt_template)
        self.assertNotIn("read <AGENTPLAYBOOK_ROOT>/AGENTS.md and <AGENTPLAYBOOK_ROOT>/index.md", prompt_template)
        for template in (repo_template, prompt_template):
            self.assertNotIn("docs-read", template.lower())
            self.assertNotIn("receipt", template.lower())
            self.assertRegex(template, r"worker-specific evidence\s+paths")

    def test_distributed_surfaces_use_one_canonical_start_lifecycle(self) -> None:
        surface_paths = (
            "AGENTS.md",
            "README.md",
            "common/skills/agent-operating-skill/references/current-guidance.md",
            "workflows/skills/agent-task-lifecycle/references/current-guidance.md",
            "workflows/skills/scripted-agent-workflow/references/current-guidance.md",
            "templates/apply-agentplaybook-request.md",
            "docs/index.html",
            "docs/ko/update-agentplaybook.md",
            "index.md",
            "docs/skills/agent-bootstrap/references/current-guidance.md",
            "common/skills/task-intake-effort-routing/references/current-guidance.md",
            "workflows/skills/prd-creation/references/current-guidance.md",
            "workflows/skills/product-architecture-delivery/references/current-guidance.md",
        )
        stale_sequences = (
            "for every multi-step task, run the shared workflow router",
            "for multi-step tasks, run `scripts/workflow.py route",
            "for multi-step work, run workflow.py route with --request before editing",
            "for any multi-step setup or follow-up task, run the workflow route",
            "when wrapper scripts exist, run agent-preflight.py before editing",
            "when wrapper scripts are available, run `agent-preflight.py` before edits",
        )

        for relative in surface_paths:
            with self.subTest(surface=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                normalized = " ".join(text.lower().split())

                self.assertIn("agent-hook.py start", normalized)
                self.assertIn("required_docs", normalized)
                self.assertIn("review hook", normalized)
                self.assertIn("finish hook", normalized)
                self.assertIn("lower-level", normalized)
                for stale in stale_sequences:
                    self.assertNotIn(stale, normalized)

        public_html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertIn(
            "For multi-step work, run agent-hook.py start once with --request",
            public_html,
        )
        self.assertIn(
            "여러 단계 작업이면 agent-hook.py start를 --request와 함께 한 번만 실행해줘",
            public_html,
        )
        self.assertIn('"evidence.body": "Use one start hook', public_html)
        self.assertIn('"evidence.body": "start hook 한 번으로', public_html)

    def test_runtime_guidance_is_canonical_capsule_policy(self) -> None:
        guidance = (
            ROOT
            / "docs"
            / "skills"
            / "agent-runtime-integration"
            / "references"
            / "current-guidance.md"
        ).read_text()

        self.assertIn("## Provider-Neutral Execution Capsule", guidance)
        self.assertIn("content-free", guidance)
        self.assertIn("run `agent-hook.py handoff`", guidance)
        self.assertIn("capsule status `ready`", guidance)
        self.assertIn("sole owner of the gate ledger", guidance)
        self.assertIn("successful fallback decision", guidance)
        self.assertRegex(guidance, r"worker-specific evidence\s+paths")
        self.assertIn("Claude passes the validated capsule to Agent/Task workers", guidance)
        self.assertIn("Gemini/Antigravity/AGY passes the validated capsule", guidance)
        self.assertNotIn("docs-read", guidance.lower())
        self.assertNotIn("receipt", guidance.lower())

    def test_direct_required_docs_reading_uses_existing_source_docs_evidence(self) -> None:
        for relative in (
            "AGENTS.md",
            "workflows/README.md",
            "workflows/skills/scripted-agent-workflow/references/current-guidance.md",
        ):
            with self.subTest(surface=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                normalized = " ".join(text.lower().split())

                self.assertIn("required_docs", normalized)
                self.assertIn("source docs", normalized)
                self.assertIn("takeaway", normalized)
                self.assertNotIn("no separate document-confirmation command, receipt artifact, or finish gate", normalized)


if __name__ == "__main__":
    unittest.main()
