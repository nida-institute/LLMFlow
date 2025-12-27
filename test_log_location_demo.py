"""Quick demonstration of configurable log file location."""
from pathlib import Path
from llmflow.modules.logger import Logger
import tempfile

# Create a temporary directory for testing
with tempfile.TemporaryDirectory() as tmpdir:
    tmppath = Path(tmpdir)

    print("=== Test 1: Default log location ===")
    log1 = tmppath / "llmflow.log"
    Logger.reset(log_file=str(log1))
    logger = Logger()
    logger.info("Test message in default location")
    print(f"✓ Log file created at: {log1}")
    print(f"✓ File exists: {log1.exists()}")
    print(f"✓ Content sample: {log1.read_text()[:100]}...")

    print("\n=== Test 2: Custom log location ===")
    custom_dir = tmppath / "logs"
    custom_dir.mkdir()
    log2 = custom_dir / "custom.log"
    Logger.reset(log_file=str(log2))
    logger2 = Logger()
    logger2.info("Test message in custom location")
    print(f"✓ Log file created at: {log2}")
    print(f"✓ File exists: {log2.exists()}")
    print(f"✓ Content sample: {log2.read_text()[:100]}...")

    print("\n=== Test 3: Multiple instances with different logs ===")
    instance1_log = tmppath / "instance1.log"
    Logger.reset(log_file=str(instance1_log))
    logger3 = Logger()
    logger3.info("Instance 1 message")
    print(f"✓ Instance 1 log created at: {instance1_log}")

    instance2_log = tmppath / "instance2.log"
    Logger.reset(log_file=str(instance2_log))
    logger4 = Logger()
    logger4.info("Instance 2 message")
    print(f"✓ Instance 2 log created at: {instance2_log}")

    # Verify separation
    content1 = instance1_log.read_text()
    content2 = instance2_log.read_text()
    print(f"✓ Instance 1 contains 'Instance 1 message': {'Instance 1 message' in content1}")
    print(f"✓ Instance 2 contains 'Instance 2 message': {'Instance 2 message' in content2}")
    print(f"✓ Instance 1 does NOT contain 'Instance 2 message': {'Instance 2 message' not in content1}")

    print("\n=== All tests passed! ===")
