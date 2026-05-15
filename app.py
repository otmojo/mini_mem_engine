from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sandbox
import agent
import uvicorn
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="SecureLocalAgentSandbox API", version="1.0.0")

class ExecRequest(BaseModel):
    id: str
    cmd: str

class AgentRequest(BaseModel):
    id: str
    prompt: str

@app.on_event("startup")
def startup_event():
    """Initialize application on startup."""
    logger.info("Starting SecureLocalAgentSandbox API...")
    try:
        # Check if Docker is available
        import subprocess
        result = subprocess.run(
            ["docker", "--version"], 
            check=False, 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            logger.info(f"Docker detected: {result.stdout.strip()}")
            sandbox.build_image()
        else:
            logger.warning("Docker is not available on this system")
    except Exception as e:
        logger.error(f"Error during startup: {e}")

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "SecureLocalAgentSandbox"}

@app.post("/sandbox/create")
def create():
    """Create a new sandbox container."""
    try:
        logger.info("Creating new sandbox...")
        result = sandbox.create_sandbox()
        logger.info(f"Sandbox created: {result['id']}")
        return result
    except Exception as e:
        logger.error(f"Error creating sandbox: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sandbox/exec")
def execute(data: ExecRequest):
    """Execute a command in the sandbox."""
    try:
        logger.info(f"Executing command in {data.id}: {data.cmd}")
        result = sandbox.exec_cmd(data.id, data.cmd)
        logger.debug(f"Execution result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/chat")
def agent_chat(data: AgentRequest):
    """Run AI agent to execute tasks."""
    try:
        logger.info(f"Agent chat requested for sandbox {data.id}: {data.prompt}")
        response = agent.run_agent(data.prompt, data.id)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in agent chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sandbox/destroy/{container_id}")
def destroy(container_id: str):
    """Destroy a sandbox container."""
    try:
        logger.info(f"Destroying sandbox: {container_id}")
        result = sandbox.destroy_sandbox(container_id)
        logger.info(f"Sandbox destroyed: {container_id}")
        return result
    except Exception as e:
        logger.error(f"Error destroying sandbox: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    """Root endpoint with API documentation link."""
    return {
        "message": "SecureLocalAgentSandbox API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
