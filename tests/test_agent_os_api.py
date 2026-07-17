from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_os_api import (
    api_contract_manifest,
    runtime_adapter_contract,
    runtime_adapter_catalog,
    validate_runtime_adapter_catalog,
    validate_api_contract_manifest,
    validate_runtime_adapter_contract,
)


class AgentOSAPITests(unittest.TestCase):
    def test_api_contract_manifest_is_versioned(self) -> None:
        self.assertEqual([], validate_api_contract_manifest(api_contract_manifest()))

    def test_runtime_adapter_contract_is_provider_neutral(self) -> None:
        contract = runtime_adapter_contract(
            "codex",
            capabilities={"read_only": True, "workspace_write": False},
            enforcement="runtime-read-only",
        )
        self.assertEqual([], validate_runtime_adapter_contract(contract))

    def test_invalid_runtime_adapter_contract_is_rejected(self) -> None:
        self.assertTrue(validate_runtime_adapter_contract({"runtime": "Bad Name"}))

    def test_runtime_catalog_has_contract_parity_for_supported_providers(self) -> None:
        catalog = runtime_adapter_catalog()
        self.assertEqual({"codex", "claude", "antigravity"}, {item["runtime"] for item in catalog})
        self.assertEqual([], validate_runtime_adapter_catalog(catalog))


if __name__ == "__main__":
    unittest.main()
