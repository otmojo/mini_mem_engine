import subprocess
import uuid
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IMAGE_NAME = "secure-sandbox-base"
SANDBOX_MEMORY = os.getenv("SANDBOX_MEMORY", "512m")
SANDBOX_CPUS = os.getenv("SANDBOX_CPUS", "1.0")
SANDBOX_TIMEOUT = int(os.getenv("SANDBOX_TIMEOUT", "10"))

def build_image():
    """Build the sandbox base image."""
    try:
        logger.info(f"Building Docker image: {IMAGE_NAME}")
        result = subprocess.run(
            ["docker", "build", "-t", IMAGE_NAME, "."], 
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Docker image built successfully: {IMAGE_NAME}")
        return {"status": "success", "image": IMAGE_NAME}
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to build Docker image: {e.stderr}")
        raise Exception(f"Docker build failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Error building image: {e}")
        raise

def create_sandbox():
    """Create a new sandbox container."""
    container_id = f"sandbox-{uuid.uuid4().hex[:8]}"
    
    try:
        # Isolation parameters
        cmd = [
            "docker", "run", "-dit",
            "--name", container_id,
            "--network", "none",
            "--memory", SANDBOX_MEMORY,
            "--cpus", SANDBOX_CPUS,
            "--cap-drop", "ALL",
            IMAGE_NAME,
            "sleep", "infinity"
        ]
        
        logger.info(f"Creating sandbox container: {container_id}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Sandbox created successfully: {container_id}")
        return {"id": container_id}
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create sandbox {container_id}: {e.stderr}")
        raise Exception(f"Failed to create sandbox: {e.stderr}")
    except Exception as e:
        logger.error(f"Error creating sandbox: {e}")
        raise

def exec_cmd(container_id: str, command: str):
    """Execute a command inside the sandbox."""
    
    if not container_id or not command:
        logger.warning(f"Invalid parameters: container_id={container_id}, command={command}")
        return {"error": "Invalid container_id or command", "exit_code": 1}
    
    cmd = ["docker", "exec", container_id, "sh", "-c", command]
    
    try:
        logger.debug(f"Executing command in {container_id}: {command}")
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=SANDBOX_TIMEOUT
        )
        
        exit_code = result.returncode
        logger.debug(f"Command completed with exit code: {exit_code}")
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": exit_code
        }
        
    except subprocess.TimeoutExpired:
        error_msg = f"Execution timed out after {SANDBOX_TIMEOUT} seconds"
        logger.warning(error_msg)
        return {"error": error_msg, "exit_code": 124}
    except subprocess.CalledProcessError as e:
        logger.error(f"Docker exec failed: {e.stderr}")
        return {"error": str(e), "exit_code": 1}
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return {"error": str(e), "exit_code": 1}

def destroy_sandbox(container_id: str):
    """Force remove the sandbox container."""
    
    if not container_id:
        logger.warning("Invalid container_id provided to destroy_sandbox")
        return {"error": "Invalid container_id", "status": "failed"}
    
    try:
        logger.info(f"Destroying sandbox container: {container_id}")
        subprocess.run(
            ["docker", "rm", "-f", container_id], 
            check=False,
            capture_output=True,
            text=True
        )
        logger.info(f"Sandbox destroyed: {container_id}")
        return {"status": "destroyed", "id": container_id}
    except Exception as e:
        logger.error(f"Error destroying sandbox {container_id}: {e}")
        return {"error": str(e), "status": "failed", "id": container_id}
