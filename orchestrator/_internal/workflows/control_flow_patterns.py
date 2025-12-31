"""
Control flow patterns for code generation.

Provides standard patterns for loops, parallel execution, conditionals,
and error handling that can be injected into generated code.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PatternType(Enum):
    """Types of control flow patterns"""
    LOOP = "loop"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    RETRY = "retry"
    SEQUENTIAL = "sequential"


@dataclass
class ControlFlowPattern:
    """A reusable control flow pattern"""
    type: PatternType
    code_template: str
    description: str
    required_params: list[str]
    example: str | None = None


class ControlFlowPatterns:
    """Library of standard control flow patterns"""

    # Polling/waiting pattern
    POLL_PATTERN = ControlFlowPattern(
        type=PatternType.LOOP,
        code_template='''
# Poll until condition met
while True:
    status = await {check_function}({check_params})
    if {completion_condition}:
        {on_complete}
        break
    await asyncio.sleep({poll_interval})
''',
        description="Poll a resource until condition is met",
        required_params=["check_function", "check_params", "completion_condition", "poll_interval"],
        example='''
# Wait for CI to complete
while True:
    status = await check_ci_status(run_id="abc123")
    if status.state == "completed":
        result = status.result
        break
    await asyncio.sleep(10)
'''
    )

    # Parallel execution pattern
    PARALLEL_PATTERN = ControlFlowPattern(
        type=PatternType.PARALLEL,
        code_template='''
# Process items in parallel
{items_var} = await {list_function}({list_params})
results = await asyncio.gather(*[
    {process_function}({item_param}) for item in {items_var}
])
''',
        description="Process multiple items concurrently",
        required_params=["items_var", "list_function", "list_params", "process_function", "item_param"],
        example='''
# Process all documents in folder
documents = await list_documents(folder_id="folder123")
results = await asyncio.gather(*[
    process_document(doc_id=doc.id) for doc in documents
])
'''
    )

    # Conditional branching pattern
    CONDITIONAL_PATTERN = ControlFlowPattern(
        type=PatternType.CONDITIONAL,
        code_template='''
# Conditional branching
if {condition}:
    {true_action}
else:
    {false_action}
''',
        description="Execute different actions based on condition",
        required_params=["condition", "true_action", "false_action"],
        example='''
# Check CI result and act accordingly
if ci_result.success:
    await merge_pull_request(pr_id=pr.id)
else:
    await notify_team(message=f"CI failed: {ci_result.error}")
'''
    )

    # Retry with exponential backoff pattern
    RETRY_PATTERN = ControlFlowPattern(
        type=PatternType.RETRY,
        code_template='''
# Retry with exponential backoff
{result_var} = None
max_retries = {max_retries}
for attempt in range(max_retries):
    try:
        {result_var} = await {operation}
        break
    except Exception as e:
        if attempt == max_retries - 1:
            raise
        backoff = {base_backoff} * (2 ** attempt)
        await asyncio.sleep(backoff)
''',
        description="Retry operation with exponential backoff",
        required_params=["result_var", "max_retries", "operation", "base_backoff"],
        example='''
# Retry API call with backoff
result = None
max_retries = 3
for attempt in range(max_retries):
    try:
        result = await call_api(endpoint="/data")
        break
    except Exception as e:
        if attempt == max_retries - 1:
            raise
        backoff = 1 * (2 ** attempt)
        await asyncio.sleep(backoff)
'''
    )

    # Sequential with early exit pattern
    SEQUENTIAL_EARLY_EXIT_PATTERN = ControlFlowPattern(
        type=PatternType.SEQUENTIAL,
        code_template='''
# Sequential execution with early exit
{result_var} = None
for {item_var} in {items}:
    {action}
    if {exit_condition}:
        break
''',
        description="Process items sequentially, exit early if condition met",
        required_params=["result_var", "item_var", "items", "action", "exit_condition"],
        example='''
# Search for document by content
found = None
for doc in documents:
    content = await get_document(doc_id=doc.id)
    if "target phrase" in content:
        found = doc
        break
'''
    )

    # Batch processing with limit pattern
    BATCH_LIMIT_PATTERN = ControlFlowPattern(
        type=PatternType.PARALLEL,
        code_template='''
# Batch processing with concurrency limit
from asyncio import Semaphore

async def process_with_limit(item, sem):
    async with sem:
        return await {process_function}({item_param})

{items_var} = await {list_function}({list_params})
sem = Semaphore({max_concurrent})
results = await asyncio.gather(*[
    process_with_limit(item, sem) for item in {items_var}
])
''',
        description="Process items in parallel with concurrency limit",
        required_params=["items_var", "list_function", "list_params", "process_function", "item_param", "max_concurrent"],
        example='''
# Process 100 documents with max 10 concurrent
from asyncio import Semaphore

async def process_with_limit(doc, sem):
    async with sem:
        return await process_document(doc_id=doc.id)

documents = await list_documents(folder_id="folder123")
sem = Semaphore(10)
results = await asyncio.gather(*[
    process_with_limit(doc, sem) for doc in documents
])
'''
    )

    @classmethod
    def get_pattern(cls, pattern_type: PatternType) -> ControlFlowPattern | None:
        """Get a specific pattern by type"""
        patterns = {
            PatternType.LOOP: cls.POLL_PATTERN,
            PatternType.PARALLEL: cls.PARALLEL_PATTERN,
            PatternType.CONDITIONAL: cls.CONDITIONAL_PATTERN,
            PatternType.RETRY: cls.RETRY_PATTERN,
            PatternType.SEQUENTIAL: cls.SEQUENTIAL_EARLY_EXIT_PATTERN,
        }
        return patterns.get(pattern_type)

    @classmethod
    def list_patterns(cls) -> list[ControlFlowPattern]:
        """List all available patterns"""
        return [
            cls.POLL_PATTERN,
            cls.PARALLEL_PATTERN,
            cls.CONDITIONAL_PATTERN,
            cls.RETRY_PATTERN,
            cls.SEQUENTIAL_EARLY_EXIT_PATTERN,
            cls.BATCH_LIMIT_PATTERN,
        ]

    @classmethod
    def generate_code(cls, pattern: ControlFlowPattern, params: dict[str, Any]) -> str:
        """
        Generate code from pattern with parameters.
        
        Args:
            pattern: The pattern to use
            params: Dictionary of parameter values
            
        Returns:
            Generated code string
            
        Raises:
            ValueError: If required parameters are missing
        """
        # Validate required parameters
        missing = set(pattern.required_params) - set(params.keys())
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

        # Generate code from template
        try:
            code = pattern.code_template.format(**params)
            return code
        except KeyError as e:
            raise ValueError(f"Invalid parameter: {e}")

    @classmethod
    def detect_pattern_need(cls, task_description: str) -> PatternType | None:
        """
        Analyze task description to detect which pattern might be needed.
        
        Args:
            task_description: Natural language description of task
            
        Returns:
            Suggested pattern type, or None if no clear match
        """
        desc_lower = task_description.lower()

        # Check in order of specificity (most specific first)

        # Retry indicators (check first - more specific)
        if any(word in desc_lower for word in ["retry", "try again", "backoff", "attempt"]):
            return PatternType.RETRY

        # Loop indicators
        if any(word in desc_lower for word in ["wait", "poll", "until"]):
            return PatternType.LOOP

        # Conditional indicators
        if any(word in desc_lower for word in ["if ", " if", "else", "depending", "based on", "when "]):
            return PatternType.CONDITIONAL

        # Parallel indicators (check last - least specific)
        # Use more specific matches to avoid false positives
        if any(word in desc_lower for word in [" all ", "batch", "parallel", "concurrent", "each ", " each"]):
            return PatternType.PARALLEL

        return None


def create_polling_code(
    check_function: str,
    check_params: str,
    completion_condition: str,
    poll_interval: float = 5.0,
    on_complete: str = "pass"
) -> str:
    """
    Convenience function to create polling code.
    
    Args:
        check_function: Function name to call for status check
        check_params: Parameters for check function
        completion_condition: Condition that indicates completion
        poll_interval: Seconds between checks
        on_complete: Code to execute on completion
        
    Returns:
        Generated polling code
    """
    return ControlFlowPatterns.generate_code(
        ControlFlowPatterns.POLL_PATTERN,
        {
            "check_function": check_function,
            "check_params": check_params,
            "completion_condition": completion_condition,
            "poll_interval": poll_interval,
            "on_complete": on_complete
        }
    )


def create_parallel_code(
    items_var: str,
    list_function: str,
    list_params: str,
    process_function: str,
    item_param: str
) -> str:
    """
    Convenience function to create parallel processing code.
    
    Args:
        items_var: Variable name for items list
        list_function: Function to get items
        list_params: Parameters for list function
        process_function: Function to process each item
        item_param: Parameter expression for process function
        
    Returns:
        Generated parallel processing code
    """
    return ControlFlowPatterns.generate_code(
        ControlFlowPatterns.PARALLEL_PATTERN,
        {
            "items_var": items_var,
            "list_function": list_function,
            "list_params": list_params,
            "process_function": process_function,
            "item_param": item_param
        }
    )


def create_conditional_code(
    condition: str,
    true_action: str,
    false_action: str
) -> str:
    """
    Convenience function to create conditional code.
    
    Args:
        condition: Boolean expression
        true_action: Code to execute if true
        false_action: Code to execute if false
        
    Returns:
        Generated conditional code
    """
    return ControlFlowPatterns.generate_code(
        ControlFlowPatterns.CONDITIONAL_PATTERN,
        {
            "condition": condition,
            "true_action": true_action,
            "false_action": false_action
        }
    )


def create_retry_code(
    result_var: str,
    operation: str,
    max_retries: int = 3,
    base_backoff: float = 1.0
) -> str:
    """
    Convenience function to create retry code.
    
    Args:
        result_var: Variable name for result
        operation: Operation to retry
        max_retries: Maximum number of attempts
        base_backoff: Base seconds for exponential backoff
        
    Returns:
        Generated retry code
    """
    return ControlFlowPatterns.generate_code(
        ControlFlowPatterns.RETRY_PATTERN,
        {
            "result_var": result_var,
            "operation": operation,
            "max_retries": max_retries,
            "base_backoff": base_backoff
        }
    )
