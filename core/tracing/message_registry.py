from __future__ import annotations
import json
import time
import logging
from typing import Optional, Dict, Any, List
from redis.asyncio import Redis

logger = logging.getLogger("webook_registry")

class MessageRegistry:
    """
    AUTHORITATIVE MESSAGE LIFECYCLE REGISTRY (Flight Recorder)
    
    Tracks:
    - Ownership with Heartbeat (Auto-recovery of abandoned flows)
    - Tombstoning (Stale message protection)
    - Full Mutation History (Event log per message)
    """
    def __init__(self, redis: Optional[Redis] = None):
        self.redis = redis
        self._prefix = "bot:msg_registry:"
        self._memory_fallback: Dict[str, str] = {}
        self._owner_ttl = 300  # 5 minutes without heartbeat = abandoned

    async def register_mutation(self, chat_id: int, message_id: int, trace_id: str, payload: Dict[str, Any]):
        """
        Records a mutation event and updates authoritative ownership.
        """
        data = await self.check_ownership(chat_id, message_id) or {
            "created_at": time.time(),
            "events": [],
            "is_stale": False
        }
        
        # 1. Update State
        data["last_trace_id"] = trace_id
        data["last_heartbeat"] = time.time()
        
        # 2. Record Event (Flight Recorder)
        event = {
            "ts": time.time(),
            "trace_id": trace_id,
            "method": payload.get("method", "unknown"),
            "markup_hash": hash(str(payload.get("reply_markup"))),
            "text_preview": str(payload.get("text", ""))[:50]
        }
        data["events"].append(event)
        
        # Limit history to last 20 mutations to save memory/redis space
        if len(data["events"]) > 20:
            data["events"] = data["events"][-20:]
            
        await self._save(chat_id, message_id, data)
        logger.debug(f"[REGISTRY_WRITE] chat={chat_id} msg={message_id} owner={trace_id} events={len(data['events'])}")

    async def mark_stale(self, chat_id: int, message_id: int, reason: str = "superseded"):
        """
        Tombstoning: Mark a message as no longer authoritative.
        """
        data = await self.check_ownership(chat_id, message_id)
        if data:
            data["is_stale"] = True
            data["stale_reason"] = reason
            data["stale_at"] = time.time()
            data["events"].append({
                "ts": time.time(),
                "trace_id": "system",
                "method": "tombstone",
                "reason": reason
            })
            await self._save(chat_id, message_id, data)
            logger.info(f"[REGISTRY_TOMBSTONE] chat={chat_id} msg={message_id} reason={reason}")

    async def validate_mutation(self, chat_id: int, message_id: int, trace_id: Optional[str], force: bool = False) -> bool:
        """
        Enforce ownership boundaries and handle flow recovery.
        """
        if force:
            return True
        
        data = await self.check_ownership(chat_id, message_id)
        if not data:
            return True # Unowned
            
        if data.get("is_stale"):
            logger.warning(f"[REGISTRY_VIOLATION] Mutation rejected: STALE message {message_id}")
            return False

        last_owner = data.get("last_trace_id")
        last_heartbeat = data.get("last_heartbeat", 0)
        
        # Heartbeat Check (Abandoned Flow Recovery)
        if time.time() - last_heartbeat > self._owner_ttl:
            logger.info(f"[REGISTRY_RECOVERY] Abandoned flow detected for msg {message_id} (last owner {last_owner}). Auto-releasing.")
            return True

        if trace_id and last_owner and last_owner != trace_id:
            logger.error(f"[REGISTRY_VIOLATION] Mutation REJECTED: msg {message_id} owned by {last_owner}")
            return False
            
        return True

    async def validate_callback(self, chat_id: int, message_id: int) -> bool:
        """
        Protects against stale/tombstoned callbacks.
        """
        data = await self.check_ownership(chat_id, message_id)
        if not data:
            return True # No record, assume valid
            
        if data.get("is_stale"):
            logger.warning(f"[REGISTRY_CALLBACK_REJECTED] Stale callback on msg {message_id}")
            return False
            
        return True

    async def check_ownership(self, chat_id: int, message_id: int) -> Optional[Dict[str, Any]]:
        key = f"{self._prefix}{chat_id}:{message_id}"
        val = None
        if self.redis:
            try:
                val = await self.redis.get(key)
            except:
                val = self._memory_fallback.get(key)
        else:
            val = self._memory_fallback.get(key)
            
        if val:
            return json.loads(val)
        return None

    async def _save(self, chat_id: int, message_id: int, data: Dict[str, Any]):
        key = f"{self._prefix}{chat_id}:{message_id}"
        serialized = json.dumps(data)
        if self.redis:
            try:
                await self.redis.set(key, serialized, ex=86400) # 24h retention for forensic review
            except:
                self._memory_fallback[key] = serialized
        else:
            self._memory_fallback[key] = serialized

# Singleton instance
message_registry = MessageRegistry()

def init_registry(redis: Redis):
    global message_registry
    message_registry.redis = redis
