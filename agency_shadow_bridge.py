"""SHADOW Agency Bridge — Connects SHADOW's Coral Protocol agents to the SAHIIXX ecosystem.

Registers SHADOW's agents (Shadow, Reviewer, Whisper, Notion, Slack) as A2A
services and connects them to:
- sovereign-swarm SafetyCouncil for code scanning before execution
- agency-agents for security review delegation
- friday-os voice pipeline for Whisper agent

Usage:
    from agency_shadow_bridge import ShadowBridge
    bridge = ShadowBridge()
    await bridge.init()
    result = await bridge.scan_code("rm -rf /")
    result = await bridge.dispatch_review("Check this code for vulnerabilities")
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add paths
sys.path.insert(0, "/mnt/c/Users/Sahil Khan/Downloads")
sys.path.insert(0, "/home/sahiix/sahiixx-bus")

from sovereign_swarm import SafetyCouncil, RBACGuard, RBACPermission, SwarmBus, SwarmMemory
from sahiixx_bus.a2a_router import A2ARouter
from sahiixx_bus.bridge import AgencyBridge, FridayBridge

logger = logging.getLogger("shadow.bridge")


class ShadowBridge:
    """Bridge between SHADOW (Coral Protocol) and the SAHIIXX ecosystem.

    Provides:
    - SafetyCouncil scanning for all code before execution
    - Agency-agents security review delegation
    - FRIDAY-OS voice pipeline for Whisper agent
    - SwarmBus for inter-system event streaming
    """

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.safety = SafetyCouncil()
        self.rbac = RBACGuard()
        self.rbac.assign("shadow_agent", "operator")
        self.rbac.assign("reviewer_agent", "operator")
        self.rbac.assign("whisper_agent", "viewer")
        self.bus = SwarmBus(self.data_dir / "shadow_bus.db")
        self.memory = SwarmMemory(self.data_dir / "shadow_memory.db")
        self.router = A2ARouter()
        self._initialized = False

        # Register ecosystem bridges
        self.router.register("agency", AgencyBridge(), priority=10)
        self.router.register("friday", FridayBridge(), priority=5)

    async def init(self):
        """Initialize subsystems."""
        if self._initialized:
            return
        await self.bus.init()
        await self.memory.init()
        await self.router.discover()
        self._initialized = True

    async def scan_code(self, code: str, system_load: float = 0.0) -> Dict:
        """Scan code for safety violations before execution.

        Used by Shadow Agent before running any generated code.
        """
        result = self.safety.scan(code, system_load)
        await self.bus.publish("shadow.scan", {
            "agent": "shadow",
            "code_preview": code[:200],
            "result": result,
        })
        return result

    async def dispatch_review(self, code: str, context: str = "") -> Dict:
        """Send code to agency-agents security review.

        Used by Reviewer Agent for deeper security analysis.
        """
        if not self._initialized:
            await self.init()

        results = await self.router.route(
            f"Security review: {context}\n\nCode:\n{code[:1000]}",
            skills=["security", "qa"],
            preferred_service="agency",
        )
        return results[0] if results else {"error": "no_security_agents_available"}

    async def dispatch_voice(self, audio_text: str) -> Dict:
        """Send transcribed voice to FRIDAY-OS for processing.

        Used by Whisper Agent for voice command routing.
        """
        if not self._initialized:
            await self.init()

        results = await self.router.route(
            audio_text,
            skills=["voice", "conversational"],
            preferred_service="friday",
        )
        return results[0] if results else {"error": "friday_unavailable"}

    async def log_to_notion(self, content: str, page: str = "shadow-log") -> None:
        """Store a log entry in shared memory (Notion agent can pick it up)."""
        if not self._initialized:
            await self.init()
        await self.memory.store(f"notion:{page}", {"content": content, "timestamp": __import__('time').time()}, tags="notion shadow-log")

    async def notify_slack(self, message: str) -> Dict:
        """Publish a notification event for the Slack agent."""
        if not self._initialized:
            await self.init()
        await self.bus.publish("shadow.slack", {"message": message})
        return {"status": "published", "topic": "shadow.slack"}

    def authorize(self, agent_id: str, permission: str) -> bool:
        """Check if a SHADOW agent has a specific permission."""
        try:
            perm = RBACPermission(permission)
            return self.rbac.check(agent_id, perm)
        except ValueError:
            return False

    async def shutdown(self):
        """Gracefully shutdown."""
        await self.bus.close()
        await self.memory.close()