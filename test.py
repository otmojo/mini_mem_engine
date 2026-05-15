#!/usr/bin/env python3
"""
Comprehensive test suite for SecureLocalAgentSandbox.
Tests sandbox creation, command execution, and API endpoints.
"""

import os
import json
import time
import logging
import subprocess
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SandboxTestSuite:
    """Test suite for SecureLocalAgentSandbox."""
    
    def __init__(self):
        self.docker_available = self._check_docker()
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        
    def _check_docker(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            is_available = result.returncode == 0
            if is_available:
                logger.info(f"Docker available: {result.stdout.strip()}")
            else:
                logger.warning("Docker not available")
            return is_available
        except Exception as e:
            logger.warning(f"Docker check failed: {e}")
            return False
    
    def test_imports(self):
        """Test that all modules can be imported."""
        logger.info("\n=== Testing Module Imports ===")
        try:
            import sandbox
            import agent
            import app
            logger.info("✓ All modules imported successfully")
            self.passed += 1
        except ImportError as e:
            logger.error(f"✗ Import failed: {e}")
            self.failed += 1
    
    def test_env_loading(self):
        """Test that environment variables are loaded correctly."""
        logger.info("\n=== Testing Environment Loading ===")
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
            if not api_key or api_key in ["your_api_key_here", "sk-your-api-key-here"]:
                logger.warning("⚠ OPENAI_API_KEY not configured (expected in test environment)")
                self.skipped += 1
            else:
                logger.info("✓ OPENAI_API_KEY is configured")
                self.passed += 1
        except Exception as e:
            logger.error(f"✗ Environment loading failed: {e}")
            self.failed += 1
    
    def test_docker_image_build(self):
        """Test Docker image building."""
        if not self.docker_available:
            logger.warning("⊘ Skipping Docker image build test (Docker not available)")
            self.skipped += 1
            return
        
        logger.info("\n=== Testing Docker Image Build ===")
        try:
            import sandbox
            result = sandbox.build_image()
            logger.info("✓ Docker image built successfully")
            self.passed += 1
        except Exception as e:
            logger.error(f"✗ Docker image build failed: {e}")
            self.failed += 1
    
    def test_sandbox_creation(self):
        """Test sandbox container creation."""
        if not self.docker_available:
            logger.warning("⊘ Skipping sandbox creation test (Docker not available)")
            self.skipped += 1
            return
        
        logger.info("\n=== Testing Sandbox Creation ===")
        container_id = None
        try:
            import sandbox
            result = sandbox.create_sandbox()
            container_id = result.get("id")
            
            if container_id:
                logger.info(f"✓ Sandbox created: {container_id}")
                self.passed += 1
                return container_id
            else:
                logger.error("✗ No container ID in response")
                self.failed += 1
        except Exception as e:
            logger.error(f"✗ Sandbox creation failed: {e}")
            self.failed += 1
        finally:
            if container_id:
                self._cleanup_sandbox(container_id)
        
        return None
    
    def test_command_execution(self):
        """Test command execution in sandbox."""
        if not self.docker_available:
            logger.warning("⊘ Skipping command execution test (Docker not available)")
            self.skipped += 1
            return
        
        logger.info("\n=== Testing Command Execution ===")
        import sandbox
        container_id = None
        
        try:
            # Create sandbox
            result = sandbox.create_sandbox()
            container_id = result.get("id")
            
            if not container_id:
                logger.error("✗ Failed to create sandbox")
                self.failed += 1
                return
            
            # Test basic command
            exec_result = sandbox.exec_cmd(container_id, "echo 'Hello Sandbox'")
            
            if exec_result.get("exit_code") == 0 and "Hello Sandbox" in exec_result.get("stdout", ""):
                logger.info("✓ Command execution successful")
                self.passed += 1
            else:
                logger.error(f"✗ Command execution failed: {exec_result}")
                self.failed += 1
            
            # Test command with error
            exec_result = sandbox.exec_cmd(container_id, "exit 1")
            if exec_result.get("exit_code") == 1:
                logger.info("✓ Error exit code captured correctly")
                self.passed += 1
            else:
                logger.error(f"✗ Error exit code not captured: {exec_result}")
                self.failed += 1
                
        except Exception as e:
            logger.error(f"✗ Command execution test failed: {e}")
            self.failed += 1
        finally:
            if container_id:
                self._cleanup_sandbox(container_id)
    
    def test_command_timeout(self):
        """Test command timeout handling."""
        if not self.docker_available:
            logger.warning("⊘ Skipping timeout test (Docker not available)")
            self.skipped += 1
            return
        
        logger.info("\n=== Testing Command Timeout ===")
        import sandbox
        container_id = None
        
        try:
            result = sandbox.create_sandbox()
            container_id = result.get("id")
            
            # Run a command that takes too long (exceeds timeout)
            exec_result = sandbox.exec_cmd(container_id, "sleep 20")
            
            if exec_result.get("exit_code") == 124 or "timed out" in exec_result.get("error", "").lower():
                logger.info("✓ Timeout handled correctly")
                self.passed += 1
            else:
                logger.error(f"✗ Timeout not detected: {exec_result}")
                self.failed += 1
                
        except Exception as e:
            logger.error(f"✗ Timeout test failed: {e}")
            self.failed += 1
        finally:
            if container_id:
                self._cleanup_sandbox(container_id)
    
    def test_sandbox_destruction(self):
        """Test sandbox container destruction."""
        if not self.docker_available:
            logger.warning("⊘ Skipping sandbox destruction test (Docker not available)")
            self.skipped += 1
            return
        
        logger.info("\n=== Testing Sandbox Destruction ===")
        import sandbox
        
        try:
            # Create and destroy sandbox
            result = sandbox.create_sandbox()
            container_id = result.get("id")
            
            if not container_id:
                logger.error("✗ Failed to create sandbox")
                self.failed += 1
                return
            
            # Destroy the sandbox
            destroy_result = sandbox.destroy_sandbox(container_id)
            
            if destroy_result.get("status") == "destroyed":
                logger.info("✓ Sandbox destroyed successfully")
                self.passed += 1
            else:
                logger.error(f"✗ Sandbox destruction failed: {destroy_result}")
                self.failed += 1
                
        except Exception as e:
            logger.error(f"✗ Sandbox destruction test failed: {e}")
            self.failed += 1
    
    def test_api_endpoints(self):
        """Test API endpoints (requires server running)."""
        logger.info("\n=== Testing API Endpoints ===")
        logger.info("⊘ API endpoint tests require running server (manual test)")
        logger.info("  Start server: python app.py")
        logger.info("  Then run: curl http://localhost:8000/health")
        self.skipped += 1
    
    def _cleanup_sandbox(self, container_id: str):
        """Clean up a sandbox container."""
        try:
            import sandbox
            sandbox.destroy_sandbox(container_id)
        except Exception as e:
            logger.warning(f"Failed to cleanup sandbox {container_id}: {e}")
    
    def run_all_tests(self):
        """Run all tests."""
        logger.info("=" * 60)
        logger.info("SecureLocalAgentSandbox Test Suite")
        logger.info("=" * 60)
        
        self.test_imports()
        self.test_env_loading()
        
        if self.docker_available:
            self.test_docker_image_build()
            self.test_sandbox_creation()
            self.test_command_execution()
            self.test_command_timeout()
            self.test_sandbox_destruction()
        else:
            logger.warning("\n⚠ Docker not available - skipping Docker-dependent tests")
        
        self.test_api_endpoints()
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("Test Summary")
        logger.info("=" * 60)
        logger.info(f"Passed:  {self.passed}")
        logger.info(f"Failed:  {self.failed}")
        logger.info(f"Skipped: {self.skipped}")
        logger.info("=" * 60)
        
        return self.failed == 0

if __name__ == "__main__":
    suite = SandboxTestSuite()
    success = suite.run_all_tests()
    exit(0 if success else 1)
