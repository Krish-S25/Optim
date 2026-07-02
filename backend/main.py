import math
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import your local configuration utilities
import sandbox
import analyzer

app = FastAPI(
    title="optim API Engine",
    description="Empirical Algorithm Performance & Complexity Analyzer Backend"
)

# Open up CORS policies for local dev linking
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SubmissionRequest(BaseModel):
    code: str
    dataType: str = "integer"
    arrayState: str = "random"
    rangeStart: int = 0
    rangeEnd: int = 100
    mustHave: str = ""

def clean_infinity_values(data_payload):
    """Recursively converts JSON-breaking inf or nan floats into compliant values."""
    if isinstance(data_payload, dict):
        return {key: clean_infinity_values(val) for key, val in data_payload.items()}
    elif isinstance(data_payload, list):
        return [clean_infinity_values(val) for val in data_payload]
    elif isinstance(data_payload, float):
        if math.isinf(data_payload):
            return 999999.99
        if math.isnan(data_payload):
            return 0.0
    return data_payload

@app.post("/api/benchmark")
async def benchmark_endpoint(request_body: SubmissionRequest):
    try:
        # Step 1: Write raw string payload to disk and kickstart the compilation runtime
        sandbox.run_sandbox(
            request_body.code,
            request_body.dataType,
            request_body.arrayState,
            request_body.rangeStart,
            request_body.rangeEnd,
            request_body.mustHave
        )
        
        # Step 2: Extract generated metric arrays and process non-linear regression curves
        metrics, analysis_results = analyzer.estimate_complexity()
        
        response_payload = {
            "success": True,
            "status": "success",
            "metrics": metrics,
            "analysis": analysis_results
        }
        return clean_infinity_values(response_payload)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/dryrun")
async def dryrun_endpoint(request_body: SubmissionRequest):
    try:
        input_str, output_str = sandbox.run_dryrun(
            request_body.code,
            request_body.dataType,
            request_body.arrayState,
            request_body.rangeStart,
            request_body.rangeEnd,
            request_body.mustHave
        )
        return {"success": True, "input": input_str, "output": output_str}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))