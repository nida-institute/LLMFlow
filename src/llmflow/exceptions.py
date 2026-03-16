"""Custom exceptions for LLMFlow pipeline execution."""

class LLMFlowError(Exception):
    """Base exception for all LLMFlow errors."""
    pass


class PipelineExecutionError(LLMFlowError):
    """Error during pipeline execution."""

    def __init__(self, message: str, step_name: str = None, context: dict = None, original_error: Exception = None):
        self.step_name = step_name
        self.context = context
        self.original_error = original_error
        super().__init__(message)

    def __str__(self):
        parts = [super().__str__()]

        if self.step_name:
            parts.append(f"  Step: {self.step_name}")

        if self.context:
            # Show relevant context variables (not the whole thing)
            context_vars = ", ".join(f"{k}={type(v).__name__}" for k, v in list(self.context.items())[:5])
            parts.append(f"  Context: {context_vars}")

        if self.original_error:
            parts.append(f"  Caused by: {type(self.original_error).__name__}: {self.original_error}")

        return "\n".join(parts)


class StepExecutionError(PipelineExecutionError):
    """Error executing a specific step."""

    def __init__(self, message: str, step_name: str, step_type: str, context: dict = None, original_error: Exception = None):
        self.step_type = step_type
        super().__init__(message, step_name, context, original_error)

    def __str__(self):
        parts = [super().__str__()]
        if self.step_type:
            parts.insert(1, f"  Step type: {self.step_type}")
        return "\n".join(parts)


class ForEachIterationError(PipelineExecutionError):
    """Error during for-each loop iteration."""

    def __init__(self, message: str, step_name: str, iteration_index: int, item_value: any, context: dict = None, original_error: Exception = None):
        self.iteration_index = iteration_index
        self.item_value = item_value
        super().__init__(message, step_name, context, original_error)

    def __str__(self):
        parts = [super().__str__()]
        parts.insert(1, f"  Iteration: {self.iteration_index}")
        parts.insert(2, f"  Item value: {repr(self.item_value)[:100]}")  # Truncate long values
        return "\n".join(parts)


class StepRetryError(PipelineExecutionError):
    """Raised when a step exhausts its retry attempts without meeting the condition."""

    def __init__(
        self,
        message: str,
        step_name: str,
        attempts: int,
        condition: str | None = None,
        context: dict | None = None,
        original_error: Exception | None = None,
    ):
        self.attempts = attempts
        self.condition = condition
        super().__init__(message, step_name, context, original_error)

    def __str__(self):
        parts = [super().__str__()]
        parts.insert(1, f"  Attempts: {self.attempts}")
        if self.condition:
            parts.insert(2, f"  Condition: {self.condition}")
        return "\n".join(parts)


class StepRewindError(PipelineExecutionError):
    """Raised when a rewind checkpoint cannot be used."""

    def __init__(self, message: str, step_name: str, context: dict | None = None, original_error: Exception | None = None):
        super().__init__(message, step_name=step_name, context=context, original_error=original_error)

class VariableResolutionError(LLMFlowError):
    """Error resolving a variable expression."""

    def __init__(self, message: str, expression: str, context: dict = None, original_error: Exception = None):
        self.expression = expression
        self.context = context
        self.original_error = original_error
        super().__init__(message)

    def __str__(self):
        parts = [super().__str__()]
        parts.append(f"  Expression: {self.expression}")

        if self.context:
            available_vars = ", ".join(self.context.keys())
            parts.append(f"  Available variables: {available_vars}")

        if self.original_error:
            parts.append(f"  Caused by: {type(self.original_error).__name__}: {self.original_error}")

        return "\n".join(parts)


class LLMProviderError(LLMFlowError):
    """Error calling LLM provider."""

    def __init__(self, message: str, provider: str, model: str, original_error: Exception = None):
        self.provider = provider
        self.model = model
        self.original_error = original_error
        super().__init__(message)

    def __str__(self):
        parts = [super().__str__()]
        parts.append(f"  Provider: {self.provider}")
        parts.append(f"  Model: {self.model}")

        if self.original_error:
            parts.append(f"  Caused by: {type(self.original_error).__name__}: {self.original_error}")

        return "\n".join(parts)


class ModerationError(LLMProviderError):
    """Raised when a provider blocks content via moderation filters."""

    def __init__(
        self,
        message: str,
        provider: str,
        model: str,
        step_name: str | None = None,
        reason: str | None = None,
        explanation: str | None = None,
        details: dict | None = None,
        original_error: Exception | None = None,
    ):
        self.step_name = step_name
        self.reason = reason
        self.explanation = explanation
        self.details = details
        super().__init__(message, provider, model, original_error=original_error)

    def __str__(self):
        parts = [super().__str__()]
        if self.step_name:
            parts.append(f"  Step: {self.step_name}")
        if self.reason:
            parts.append(f"  Moderation reason: {self.reason}")
        if self.explanation:
            parts.append(f"  Explanation: {self.explanation}")
        if self.details:
            parts.append(f"  Details: {self.details}")
        return "\n".join(parts)


class PluginError(LLMFlowError):
    """Error executing a plugin."""

    def __init__(self, message: str, plugin_name: str, original_error: Exception = None):
        self.plugin_name = plugin_name
        self.original_error = original_error
        super().__init__(message)

    def __str__(self):
        parts = [super().__str__()]
        parts.append(f"  Plugin: {self.plugin_name}")

        if self.original_error:
            parts.append(f"  Caused by: {type(self.original_error).__name__}: {self.original_error}")

        return "\n".join(parts)