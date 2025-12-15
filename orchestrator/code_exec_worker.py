import multiprocessing
from typing import Dict, Any
from .models import CodeExecInput, CodeExecOutput

def _exec_code(queue, code_str: str, input_data: Dict[str, Any]):
    # Safe builtins for common operations
    safe_builtins = {
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
        "tuple": tuple,
        "set": set,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "sorted": sorted,
    }
    safe_globals = {"__builtins__": safe_builtins}
    local_vars = {"input": input_data, "output": None}
    try:
        exec(code_str, safe_globals, local_vars)
        queue.put(local_vars.get("output"))
    except Exception as e:
        queue.put({"error": str(e)})

async def code_exec_worker(payload: Dict[str, Any]) -> Dict[str, Any]:
    validated = CodeExecInput(**payload)
    queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=_exec_code, args=(queue, validated.code, validated.input_data))
    p.start()
    p.join(timeout=5)
    if p.is_alive():
        p.terminate()
        raise TimeoutError("Code execution exceeded time limit")
    result = queue.get()
    if isinstance(result, dict) and "error" in result:
        raise RuntimeError(result["error"])
    return CodeExecOutput(output=result).model_dump()
