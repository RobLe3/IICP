"""Python consumer to Node A2A/AAP server interoperability proof."""

from __future__ import annotations

import copy
import json
import subprocess
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from check_a2a_execution_binding import FIXTURE, canonical_digest, evaluate


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "research/pre-normative-profiles/prototypes/a2a-aap-loopback-server.mjs"


class A2ACrossRuntimeLoopbackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.process = subprocess.Popen(
            ["node", str(SERVER)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert cls.process.stdout
        line = cls.process.stdout.readline().strip()
        if not line:
            stderr = cls.process.stderr.read() if cls.process.stderr else ""
            raise RuntimeError(f"Node A2A fixture failed to start: {stderr}")
        cls.runtime = json.loads(line)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.process.terminate()
        cls.process.wait(timeout=5)

    def fetch_card(self) -> dict:
        with urllib.request.urlopen(self.runtime["cardUrl"], timeout=5) as response:
            self.assertEqual(response.status, 200)
            return json.load(response)

    def bound_document(self, card: dict) -> dict:
        document = json.loads(FIXTURE.read_text(encoding="utf-8"))
        document["agent_card"] = card
        binding = document["selected_provider"]["binding"]
        binding["agent_card_url"] = self.runtime["cardUrl"]
        binding["agent_card_sha256"] = self.runtime["cardDigest"]
        binding["card_expires_at"] = "2099-01-01T00:00:00Z"
        binding["interface_url"] = self.runtime["interfaceUrl"]
        document["authorization"]["a2a_credential_audience"] = self.runtime["origin"]
        document["authorization"]["expected_a2a_credential_audience"] = self.runtime["origin"]
        return document

    def send_message(self, authorization: str = "Bearer a2a-loopback-audience") -> tuple[int, dict]:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "SendMessage",
            "params": {
                "message": {
                    "messageId": "loopback-request-1",
                    "role": "ROLE_USER",
                    "parts": [{
                        "data": {"type": "dealer.information.request"},
                        "mediaType": "application/vnd.autoagent.dealer-information-request+json",
                    }],
                },
                "configuration": {"acceptedOutputModes": ["application/vnd.autoagent.dealer-information-response+json"]},
            },
        }
        request = urllib.request.Request(
            self.runtime["interfaceUrl"],
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": authorization,
                "A2A-Version": "1.0",
                "A2A-Extensions": "https://autoagentprotocol.org/extensions/aap/v1.2",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            with error:
                return error.code, json.load(error)

    def test_iicp_selection_then_direct_aap_send_message(self) -> None:
        card = self.fetch_card()
        self.assertEqual(canonical_digest(card), self.runtime["cardDigest"])
        self.assertEqual(evaluate(self.bound_document(card)), "accept")
        status, response = self.send_message()
        self.assertEqual(status, 200)
        message = response["result"]["message"]
        self.assertEqual(message["role"], "ROLE_AGENT")
        self.assertEqual(message["parts"][0]["data"]["type"], "dealer.information.response")

    def test_a2a_auth_failure_is_not_retried_as_iicp_ticket(self) -> None:
        status, response = self.send_message("Bearer wrong-audience")
        self.assertEqual(status, 401)
        self.assertEqual(response["error"], "invalid_a2a_credential")

    def test_fetched_card_substitution_is_rejected_before_send(self) -> None:
        card = self.fetch_card()
        document = self.bound_document(card)
        document["agent_card"] = copy.deepcopy(card)
        document["agent_card"]["skills"][0]["id"] = "substituted.skill"
        self.assertEqual(evaluate(document), "card_digest_mismatch")


if __name__ == "__main__":
    unittest.main()
