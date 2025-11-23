"""
Sandbox executor for safe plugin execution
"""
import asyncio
import time
import resource
import signal
from typing import Dict, Any, Optional, Tuple
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class SandboxTimeoutError(Exception):
    """Exception raised when code execution exceeds timeout"""
    pass


class SandboxMemoryError(Exception):
    """Exception raised when code execution exceeds memory limit"""
    pass


class SandboxSecurityError(Exception):
    """Exception raised when code violates security policies"""
    pass


class PluginSandboxExecutor:
    """
    Sandbox executor for safe plugin code execution
    Implements resource limits and security measures
    """

    def __init__(
        self,
        timeout_seconds: int = 30,
        memory_limit_mb: int = 100,
        max_processes: int = 10
    ):
        """
        Initialize sandbox executor

        Args:
            timeout_seconds: Maximum execution time
            memory_limit_mb: Maximum memory usage in MB
            max_processes: Maximum number of subprocesses
        """
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        self.max_processes = max_processes

    @contextmanager
    def _resource_limits(self):
        """
        Context manager to set resource limits for execution
        """
        # Save original limits
        original_limits = {}

        try:
            # Set CPU time limit (in seconds)
            original_limits['CPU'] = resource.getrlimit(resource.RLIMIT_CPU)
            resource.setrlimit(resource.RLIMIT_CPU, (self.timeout_seconds, self.timeout_seconds))

            # Set memory limit (in bytes)
            memory_bytes = self.memory_limit_mb * 1024 * 1024
            original_limits['AS'] = resource.getrlimit(resource.RLIMIT_AS)
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))

            # Set number of processes limit
            original_limits['NPROC'] = resource.getrlimit(resource.RLIMIT_NPROC)
            resource.setrlimit(resource.RLIMIT_NPROC, (self.max_processes, self.max_processes))

            yield

        finally:
            # Restore original limits
            for limit_type, limit_value in original_limits.items():
                try:
                    if limit_type == 'CPU':
                        resource.setrlimit(resource.RLIMIT_CPU, limit_value)
                    elif limit_type == 'AS':
                        resource.setrlimit(resource.RLIMIT_AS, limit_value)
                    elif limit_type == 'NPROC':
                        resource.setrlimit(resource.RLIMIT_NPROC, limit_value)
                except Exception as e:
                    logger.warning(f"Failed to restore resource limit {limit_type}: {e}")

    async def execute_plugin_action(
        self,
        plugin_code: str,
        action_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute plugin action in sandbox

        Args:
            plugin_code: Plugin module code to import
            action_name: Name of action method to execute
            parameters: Parameters for the action
            context: Execution context

        Returns:
            Dict: Execution result
        """
        start_time = time.time()

        try:
            # Create execution environment
            exec_globals = {
                '__builtins__': {
                    # Safe builtins
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'range': range,
                    'enumerate': enumerate,
                    'zip': zip,
                    'sorted': sorted,
                    'min': min,
                    'max': max,
                    'sum': sum,
                    'abs': abs,
                    'round': round,
                    'print': print,  # Allow print for debugging
                    'isinstance': isinstance,
                    'type': type,
                    'Exception': Exception,
                    'ValueError': ValueError,
                    'KeyError': KeyError,
                    'TypeError': TypeError,
                },
                # Safe modules
                'asyncio': asyncio,
                'time': time,
                'json': __import__('json'),
                'uuid': __import__('uuid'),
                'random': __import__('random'),
                'datetime': __import__('datetime'),
                're': __import__('re'),
                # Plugin execution utilities
                '__parameters__': parameters,
                '__context__': context or {},
                '__action_name__': action_name,
            }

            # Execute plugin code
            with self._resource_limits():
                # Compile code to check for syntax errors
                try:
                    compiled_code = compile(plugin_code, '<plugin>', 'exec')
                except SyntaxError as e:
                    raise SandboxSecurityError(f"Syntax error in plugin code: {e}")

                # Check for dangerous operations
                self._check_security(compiled_code)

                # Execute in controlled environment
                exec_namespace = {}
                exec(compiled_code, exec_globals, exec_namespace)

                # Get plugin instance
                plugin_instance = None
                for name, obj in exec_namespace.items():
                    if hasattr(obj, 'info') and hasattr(obj, action_name):
                        plugin_instance = obj()
                        break

                if not plugin_instance:
                    raise SandboxSecurityError(f"Plugin instance with action '{action_name}' not found")

                # Execute action with timeout
                result = await self._execute_with_timeout(
                    plugin_instance,
                    action_name,
                    parameters,
                    context
                )

                execution_time = time.time() - start_time

                return {
                    'success': True,
                    'result': result,
                    'execution_time': execution_time,
                    'memory_used': self._get_memory_usage(),
                }

        except SandboxTimeoutError:
            execution_time = time.time() - start_time
            logger.warning(f"Plugin execution timeout after {execution_time:.2f}s")
            return {
                'success': False,
                'error': 'Execution timeout',
                'error_type': 'timeout',
                'execution_time': execution_time,
            }

        except SandboxMemoryError:
            execution_time = time.time() - start_time
            return {
                'success': False,
                'error': 'Memory limit exceeded',
                'error_type': 'memory',
                'execution_time': execution_time,
            }

        except SandboxSecurityError as e:
            execution_time = time.time() - start_time
            return {
                'success': False,
                'error': str(e),
                'error_type': 'security',
                'execution_time': execution_time,
            }

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Plugin execution error: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'execution',
                'execution_time': execution_time,
            }

    async def _execute_with_timeout(
        self,
        plugin_instance,
        action_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute plugin action with timeout protection
        """
        def signal_handler(signum, frame):
            raise SandboxTimeoutError("Execution timeout")

        # Set signal handler for timeout
        old_handler = signal.signal(signal.SIGALRM, signal_handler)
        signal.alarm(self.timeout_seconds)

        try:
            # Get action method
            action_method = getattr(plugin_instance, action_name, None)
            if not action_method or not callable(action_method):
                raise SandboxSecurityError(f"Action method '{action_name}' not found or not callable")

            # Execute action
            if asyncio.iscoroutinefunction(action_method):
                result = await action_method(parameters, context)
            else:
                # Run synchronous method in thread pool to prevent blocking
                import concurrent.futures
                import functools

                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    result = await loop.run_in_executor(
                        executor,
                        functools.partial(action_method, parameters, context)
                    )

            return result

        finally:
            # Restore signal handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    def _check_security(self, compiled_code):
        """
        Check compiled code for security violations

        Args:
            compiled_code: Compiled code object to check

        Raises:
            SandboxSecurityError: If security violation detected
        """
        import dis

        # Get bytecode
        bytecode = dis.Bytecode(compiled_code)

        # Dangerous operations to check for
        dangerous_opcodes = {
            'IMPORT_NAME',  # import statements
            'IMPORT_FROM',
            'IMPORT_STAR',
            'EXEC_STMT',    # exec() calls
            'EVAL',         # eval() calls
            'OPEN',         # file operations
            'FILE_INPUT',
        }

        # Dangerous imports
        dangerous_imports = {
            'os', 'sys', 'subprocess', 'shutil', 'socket', 'urllib',
            'http', 'ftplib', 'smtplib', 'imaplib', 'poplib',
            'sqlite3', 'psycopg2', 'mysql', 'redis',
            '__import__', '__builtins__'
        }

        for instruction in bytecode:
            opname = instruction.opname

            # Check for dangerous opcodes
            if opname in dangerous_opcodes:
                raise SandboxSecurityError(f"Dangerous operation detected: {opname}")

            # Check for import operations
            if opname == 'LOAD_CONST' and instruction.argval in dangerous_imports:
                # This is a simple check - in production, you'd need more sophisticated analysis
                raise SandboxSecurityError(f"Dangerous import detected: {instruction.argval}")

    def _get_memory_usage(self) -> Optional[float]:
        """
        Get current memory usage in MB

        Returns:
            Optional[float]: Memory usage in MB or None if unavailable
        """
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return None

    async def validate_plugin_code(self, plugin_code: str) -> Dict[str, Any]:
        """
        Validate plugin code without executing it

        Args:
            plugin_code: Plugin code to validate

        Returns:
            Dict: Validation result
        """
        try:
            # Check syntax
            compile(plugin_code, '<plugin>', 'exec')

            # Basic security check
            compiled_code = compile(plugin_code, '<plugin>', 'exec')
            self._check_security(compiled_code)

            return {
                'valid': True,
                'message': 'Plugin code is valid'
            }

        except SyntaxError as e:
            return {
                'valid': False,
                'error': f'Syntax error: {e}',
                'error_type': 'syntax'
            }

        except SandboxSecurityError as e:
            return {
                'valid': False,
                'error': str(e),
                'error_type': 'security'
            }

        except Exception as e:
            return {
                'valid': False,
                'error': f'Validation error: {e}',
                'error_type': 'unknown'
            }


# Global sandbox executor instance
plugin_sandbox = PluginSandboxExecutor()


async def execute_plugin_in_sandbox(
    plugin_code: str,
    action_name: str,
    parameters: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute plugin action in sandbox environment

    Args:
        plugin_code: Plugin source code
        action_name: Action method name
        parameters: Action parameters
        context: Execution context

    Returns:
        Dict: Execution result
    """
    return await plugin_sandbox.execute_plugin_action(
        plugin_code, action_name, parameters, context
    )


async def validate_plugin_sandbox(plugin_code: str) -> Dict[str, Any]:
    """
    Validate plugin code for sandbox execution

    Args:
        plugin_code: Plugin code to validate

    Returns:
        Dict: Validation result
    """
    return await plugin_sandbox.validate_plugin_code(plugin_code)
