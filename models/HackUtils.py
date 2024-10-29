from models.ExecuteUtils import ExecuteUtils

class HackUtils:
    HACK_SUCCESS = "Hack successful! Outputs mismatch."
    HACK_FAIL = "Hack unsuccessful. Outputs match."
    EXECUTION_FAILED = "Execution failed"
    GENERATOR_FAILED = "Generator failed"

    @staticmethod
    def manual_hack(test_case: str, correct_code: str, new_code: str, time_limit: int, memory_limit_mb: int) -> str:
        correct_output = ExecuteUtils.execute_py(correct_code, time_limit, memory_limit_mb, stdin=test_case) if correct_code.endswith('.py') else ExecuteUtils.execute_cpp(correct_code, time_limit=time_limit, memory_limit_mb=memory_limit_mb, stdin=test_case)
        new_output = ExecuteUtils.execute_py(new_code, time_limit, memory_limit_mb, stdin=test_case) if new_code.endswith('.py') else ExecuteUtils.execute_cpp(new_code, time_limit=time_limit, memory_limit_mb=memory_limit_mb, stdin=test_case)
        
        if isinstance(correct_output, str) or isinstance(new_output, str):
            return f"{HackUtils.EXECUTION_FAILED}: " + (correct_output if isinstance(correct_output, str) else new_output)
        
        correct_out, correct_time, correct_memory = correct_output
        new_out, new_time, new_memory = new_output
        
        if correct_out != new_out:
            return f"{HackUtils.HACK_SUCCESS}\nCorrect Code Output: {correct_out}\nNew Code Output: {new_out}\nCorrect Code Time: {correct_time:.2f}s, Memory: {correct_memory:.2f}MB\nNew Code Time: {new_time:.2f}s, Memory: {new_memory:.2f}MB"
        
        return f"{HackUtils.HACK_FAIL}\nCorrect Code Time: {correct_time:.2f}s, Memory: {correct_memory:.2f}MB\nNew Code Time: {new_time:.2f}s, Memory: {new_memory:.2f}MB"
    
    @staticmethod
    def generator_hack(generator_code: str, correct_code: str, new_code: str, time_limit: int, memory_limit_mb: int) -> str:
        generator_output = ExecuteUtils.execute_py(generator_code, time_limit, memory_limit_mb) if generator_code.endswith('.py') else ExecuteUtils.execute_cpp(generator_code, time_limit=time_limit, memory_limit_mb=memory_limit_mb)
        
        if isinstance(generator_output, str):
            return f"{HackUtils.GENERATOR_FAILED}: {generator_output}"
        
        test_case, _, _ = generator_output
        
        correct_output = ExecuteUtils.execute_py(correct_code, time_limit, memory_limit_mb, stdin=test_case) if correct_code.endswith('.py') else ExecuteUtils.execute_cpp(correct_code, time_limit=time_limit, memory_limit_mb=memory_limit_mb, stdin=test_case)
        new_output = ExecuteUtils.execute_py(new_code, time_limit, memory_limit_mb, stdin=test_case) if new_code.endswith('.py') else ExecuteUtils.execute_cpp(new_code, time_limit=time_limit, memory_limit_mb=memory_limit_mb, stdin=test_case)
        
        if isinstance(correct_output, str) or isinstance(new_output, str):
            return f"{HackUtils.EXECUTION_FAILED}: " + (correct_output if isinstance(correct_output, str) else new_output)
        
        correct_out, correct_time, correct_memory = correct_output
        new_out, new_time, new_memory = new_output
        
        if correct_out != new_out:
            return f"{HackUtils.HACK_SUCCESS}\nGenerated Test Case: {test_case}\nCorrect Code Output: {correct_out}\nNew Code Output: {new_out}\nCorrect Code Time: {correct_time:.2f}s, Memory: {correct_memory:.2f}MB\nNew Code Time: {new_time:.2f}s, Memory: {new_memory:.2f}MB"
        
        return f"{HackUtils.HACK_FAIL}\nGenerated Test Case: {test_case}\nCorrect Code Time: {correct_time:.2f}s, Memory: {correct_memory:.2f}MB\nNew Code Time: {new_time:.2f}s, Memory: {new_memory:.2f}MB"