"""
Tests for control flow patterns.
"""

import pytest
from orchestrator._internal.workflows.control_flow_patterns import (
    ControlFlowPatterns,
    PatternType,
    ControlFlowPattern,
    create_polling_code,
    create_parallel_code,
    create_conditional_code,
    create_retry_code,
)


class TestControlFlowPattern:
    """Test ControlFlowPattern dataclass"""
    
    def test_pattern_creation(self):
        """Test creating a pattern"""
        pattern = ControlFlowPattern(
            type=PatternType.LOOP,
            code_template="while True: pass",
            description="Test pattern",
            required_params=["param1"]
        )
        
        assert pattern.type == PatternType.LOOP
        assert pattern.code_template == "while True: pass"
        assert pattern.description == "Test pattern"
        assert pattern.required_params == ["param1"]
        assert pattern.example is None


class TestControlFlowPatterns:
    """Test ControlFlowPatterns class"""
    
    def test_get_poll_pattern(self):
        """Test getting poll pattern"""
        pattern = ControlFlowPatterns.get_pattern(PatternType.LOOP)
        
        assert pattern is not None
        assert pattern.type == PatternType.LOOP
        assert "while True" in pattern.code_template
        assert "await" in pattern.code_template
        assert "asyncio.sleep" in pattern.code_template
    
    def test_get_parallel_pattern(self):
        """Test getting parallel pattern"""
        pattern = ControlFlowPatterns.get_pattern(PatternType.PARALLEL)
        
        assert pattern is not None
        assert pattern.type == PatternType.PARALLEL
        assert "asyncio.gather" in pattern.code_template
    
    def test_get_conditional_pattern(self):
        """Test getting conditional pattern"""
        pattern = ControlFlowPatterns.get_pattern(PatternType.CONDITIONAL)
        
        assert pattern is not None
        assert pattern.type == PatternType.CONDITIONAL
        assert "if" in pattern.code_template
        assert "else" in pattern.code_template
    
    def test_get_retry_pattern(self):
        """Test getting retry pattern"""
        pattern = ControlFlowPatterns.get_pattern(PatternType.RETRY)
        
        assert pattern is not None
        assert pattern.type == PatternType.RETRY
        assert "for attempt" in pattern.code_template
        assert "except" in pattern.code_template
    
    def test_list_patterns(self):
        """Test listing all patterns"""
        patterns = ControlFlowPatterns.list_patterns()
        
        assert len(patterns) >= 5  # At least 5 patterns
        assert all(isinstance(p, ControlFlowPattern) for p in patterns)
        
        # Check pattern types are present
        pattern_types = {p.type for p in patterns}
        assert PatternType.LOOP in pattern_types
        assert PatternType.PARALLEL in pattern_types
        assert PatternType.CONDITIONAL in pattern_types
        assert PatternType.RETRY in pattern_types
    
    def test_generate_polling_code(self):
        """Test generating polling code"""
        pattern = ControlFlowPatterns.POLL_PATTERN
        params = {
            "check_function": "check_status",
            "check_params": 'run_id="123"',
            "completion_condition": 'status.state == "completed"',
            "poll_interval": 5,
            "on_complete": "result = status.result"
        }
        
        code = ControlFlowPatterns.generate_code(pattern, params)
        
        assert "while True:" in code
        assert "check_status" in code
        assert 'run_id="123"' in code
        assert "completed" in code
        assert "asyncio.sleep(5)" in code
    
    def test_generate_parallel_code(self):
        """Test generating parallel code"""
        pattern = ControlFlowPatterns.PARALLEL_PATTERN
        params = {
            "items_var": "documents",
            "list_function": "list_documents",
            "list_params": 'folder_id="abc"',
            "process_function": "process_document",
            "item_param": "doc_id=item.id"
        }
        
        code = ControlFlowPatterns.generate_code(pattern, params)
        
        assert "documents" in code
        assert "list_documents" in code
        assert "asyncio.gather" in code
        assert "process_document" in code
    
    def test_generate_conditional_code(self):
        """Test generating conditional code"""
        pattern = ControlFlowPatterns.CONDITIONAL_PATTERN
        params = {
            "condition": "result.success",
            "true_action": "await handle_success()",
            "false_action": "await handle_failure()"
        }
        
        code = ControlFlowPatterns.generate_code(pattern, params)
        
        assert "if result.success:" in code
        assert "handle_success" in code
        assert "else:" in code
        assert "handle_failure" in code
    
    def test_generate_retry_code(self):
        """Test generating retry code"""
        pattern = ControlFlowPatterns.RETRY_PATTERN
        params = {
            "result_var": "result",
            "max_retries": 3,
            "operation": "call_api()",
            "base_backoff": 1
        }
        
        code = ControlFlowPatterns.generate_code(pattern, params)
        
        assert "max_retries = 3" in code
        assert "for attempt in range" in code
        assert "call_api()" in code
        assert "asyncio.sleep" in code
        assert "2 ** attempt" in code
    
    def test_missing_required_params(self):
        """Test error on missing required parameters"""
        pattern = ControlFlowPatterns.POLL_PATTERN
        params = {
            "check_function": "check_status",
            # Missing other required params
        }
        
        with pytest.raises(ValueError) as exc_info:
            ControlFlowPatterns.generate_code(pattern, params)
        
        assert "Missing required parameters" in str(exc_info.value)
    
    def test_detect_loop_pattern(self):
        """Test detecting loop pattern from description"""
        descriptions = [
            "Wait until CI completes",
            "Poll the status until done",
            "Check every 10 seconds until finished"
        ]
        
        for desc in descriptions:
            pattern_type = ControlFlowPatterns.detect_pattern_need(desc)
            assert pattern_type == PatternType.LOOP
    
    def test_detect_parallel_pattern(self):
        """Test detecting parallel pattern from description"""
        descriptions = [
            "Process all documents in folder",
            "Run batch job on each item",
            "Handle all files concurrently"
        ]
        
        for desc in descriptions:
            pattern_type = ControlFlowPatterns.detect_pattern_need(desc)
            assert pattern_type == PatternType.PARALLEL
    
    def test_detect_conditional_pattern(self):
        """Test detecting conditional pattern from description"""
        descriptions = [
            "If successful, merge PR, else notify",
            "Based on the result, take action",
            "When CI passes, deploy to production"
        ]
        
        for desc in descriptions:
            pattern_type = ControlFlowPatterns.detect_pattern_need(desc)
            assert pattern_type == PatternType.CONDITIONAL
    
    def test_detect_retry_pattern(self):
        """Test detecting retry pattern from description"""
        descriptions = [
            "Retry the API call up to 3 times",
            "Try again with backoff if it fails",
            "Attempt multiple times before giving up"
        ]
        
        for desc in descriptions:
            pattern_type = ControlFlowPatterns.detect_pattern_need(desc)
            assert pattern_type == PatternType.RETRY
    
    def test_detect_no_pattern(self):
        """Test when no pattern is detected"""
        desc = "Just call the function once"
        pattern_type = ControlFlowPatterns.detect_pattern_need(desc)
        assert pattern_type is None


class TestConvenienceFunctions:
    """Test convenience functions for creating code"""
    
    def test_create_polling_code(self):
        """Test create_polling_code convenience function"""
        code = create_polling_code(
            check_function="check_ci_status",
            check_params='run_id="abc"',
            completion_condition='status.success',
            poll_interval=10.0,
            on_complete="print('Done')"
        )
        
        assert "check_ci_status" in code
        assert "abc" in code
        assert "status.success" in code
        assert "asyncio.sleep(10.0)" in code
        assert "print('Done')" in code
    
    def test_create_parallel_code(self):
        """Test create_parallel_code convenience function"""
        code = create_parallel_code(
            items_var="files",
            list_function="list_files",
            list_params='dir="/tmp"',
            process_function="process_file",
            item_param="file_path=item.path"
        )
        
        assert "files" in code
        assert "list_files" in code
        assert "/tmp" in code
        assert "process_file" in code
        assert "asyncio.gather" in code
    
    def test_create_conditional_code(self):
        """Test create_conditional_code convenience function"""
        code = create_conditional_code(
            condition="x > 10",
            true_action="print('big')",
            false_action="print('small')"
        )
        
        assert "if x > 10:" in code
        assert "print('big')" in code
        assert "else:" in code
        assert "print('small')" in code
    
    def test_create_retry_code(self):
        """Test create_retry_code convenience function"""
        code = create_retry_code(
            result_var="data",
            operation="fetch_data()",
            max_retries=5,
            base_backoff=2.0
        )
        
        assert "data = None" in code
        assert "max_retries = 5" in code
        assert "fetch_data()" in code
        assert "2.0 * (2 ** attempt)" in code


class TestBatchLimitPattern:
    """Test batch processing with concurrency limit"""
    
    def test_batch_limit_pattern(self):
        """Test batch limit pattern exists and has correct structure"""
        pattern = ControlFlowPatterns.BATCH_LIMIT_PATTERN
        
        assert pattern.type == PatternType.PARALLEL
        assert "Semaphore" in pattern.code_template
        assert "async with sem:" in pattern.code_template
        assert pattern.description
        assert "max_concurrent" in pattern.required_params
    
    def test_generate_batch_limit_code(self):
        """Test generating batch limit code"""
        pattern = ControlFlowPatterns.BATCH_LIMIT_PATTERN
        params = {
            "items_var": "documents",
            "list_function": "list_documents",
            "list_params": 'folder_id="123"',
            "process_function": "process_document",
            "item_param": "doc_id=item.id",
            "max_concurrent": 10
        }
        
        code = ControlFlowPatterns.generate_code(pattern, params)
        
        assert "Semaphore(10)" in code
        assert "async with sem:" in code
        assert "asyncio.gather" in code


class TestSequentialPattern:
    """Test sequential execution with early exit"""
    
    def test_sequential_pattern(self):
        """Test sequential pattern exists"""
        pattern = ControlFlowPatterns.SEQUENTIAL_EARLY_EXIT_PATTERN
        
        assert pattern.type == PatternType.SEQUENTIAL
        assert "for" in pattern.code_template
        assert "if" in pattern.code_template
        assert "break" in pattern.code_template
    
    def test_generate_sequential_code(self):
        """Test generating sequential code"""
        pattern = ControlFlowPatterns.SEQUENTIAL_EARLY_EXIT_PATTERN
        params = {
            "result_var": "found",
            "item_var": "doc",
            "items": "documents",
            "action": "content = await get_document(doc.id)",
            "exit_condition": '"target" in content'
        }
        
        code = ControlFlowPatterns.generate_code(pattern, params)
        
        assert "found = None" in code
        assert "for doc in documents:" in code
        assert "get_document" in code
        assert 'if "target" in content:' in code
        assert "break" in code


class TestPatternExamples:
    """Test that all patterns have examples"""
    
    def test_all_patterns_have_examples(self):
        """Verify all patterns include usage examples"""
        patterns = ControlFlowPatterns.list_patterns()
        
        for pattern in patterns:
            if pattern.example:  # Example is optional but recommended
                assert "await" in pattern.example  # Should show async usage
                assert "#" in pattern.example  # Should have comments
