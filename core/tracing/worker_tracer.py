from __future__ import annotations
import functools
from typing import Any, Callable, Optional
from core.tracing.buffer import new_trace
from core.tracing.structured_logger import tlog

class WorkerTracerMixin:
    """
    Mixin for Worker classes to provide easy access to tracing.
    """
    def trace_stage(self, ctx: Any, stage: str, **kwargs):
        tlog.worker_stage(ctx, stage=stage, **kwargs)

def traced_worker_task(func: Callable):
    """
    Decorator for worker task execution.
    Creates a new trace for the worker job.
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        # Flexible task_id and trace_id extraction
        task_id = kwargs.get("task_id")
        trace_id = None
        root_trace_id = None
        depth = 0
        
        if len(args) > 0:
            task_obj = args[0]
            if hasattr(task_obj, "id"):
                task_id = task_obj.id
            if hasattr(task_obj, "trace_id"):
                trace_id = task_obj.trace_id
            if hasattr(task_obj, "root_trace_id"):
                root_trace_id = task_obj.root_trace_id
            if hasattr(task_obj, "depth"):
                depth = task_obj.depth
        
        ctx = new_trace(
            parent_trace_id=trace_id,
            root_trace_id=root_trace_id,
            depth=depth + 1,
            metadata={"task_id": task_id, "worker_id": getattr(self, "worker_id", None)}
        )
        
        tlog.worker_stage(ctx, stage="STARTED", task_id=task_id)
        
        try:
            # Check if func accepts trace_ctx
            import inspect
            sig = inspect.signature(func)
            if "trace_ctx" in sig.parameters:
                result = await func(self, *args, **kwargs, trace_ctx=ctx)
            else:
                result = await func(self, *args, **kwargs)
                
            tlog.worker_stage(ctx, stage="COMPLETED", task_id=task_id)
            return result
        except Exception as e:
            tlog.worker_stage(ctx, stage="FAILED", task_id=task_id, error=str(e))
            raise
            
    return wrapper
