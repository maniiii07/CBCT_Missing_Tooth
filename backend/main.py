import base64
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import get_settings
from models import DentalAnalysisResponse, HealthResponse
from ai_clients import GPT4OClient, GeminiClient, AnthropicClient, DecidingModelClient


# Initialize clients
gpt4o_client: GPT4OClient = None
gemini_client: GeminiClient = None
anthropic_client: AnthropicClient = None
deciding_client: DecidingModelClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global gpt4o_client, gemini_client, anthropic_client, deciding_client
    
    # Initialize all AI clients on startup
    gpt4o_client = GPT4OClient()
    gemini_client = GeminiClient()
    anthropic_client = AnthropicClient()
    deciding_client = DecidingModelClient()
    
    print("✓ All AI clients initialized")
    yield
    
    # Cleanup on shutdown
    print("Shutting down...")


app = FastAPI(
    title="Dental OPG Analysis API",
    description="""
    API for analyzing dental OPG (Orthopantomogram) X-ray images to identify missing teeth.
    
    Uses three AI models (GPT-4o, Gemini, Anthropic Claude) for initial analysis,
    then a deciding model (GPT-5.2) to determine the most accurate result.
    
    ## Dental Quadrant System:
    - **Quadrant 1** (Upper Right): Teeth 11-18
    - **Quadrant 2** (Upper Left): Teeth 21-28
    - **Quadrant 3** (Lower Left): Teeth 31-38
    - **Quadrant 4** (Lower Right): Teeth 41-48
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ALLOWED_MIME_TYPES = {
    "image/jpeg": "image/jpeg",
    "image/jpg": "image/jpeg",
    "image/png": "image/png",
    "image/gif": "image/gif",
    "image/webp": "image/webp",
}


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint."""
    return HealthResponse()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse()


@app.post("/analyze", response_model=DentalAnalysisResponse)
async def analyze_dental_image(
    image: UploadFile = File(..., description="OPG dental X-ray image (JPEG, PNG, GIF, or WebP)")
):
    """
    Analyze a dental OPG image to identify missing teeth in each quadrant.
    
    The image is analyzed by three AI models (GPT-4o, Gemini, Anthropic Claude),
    and then a deciding model (GPT-5.2) determines which analysis is most accurate.
    
    **Parameters:**
    - **image**: OPG dental X-ray image file (supported formats: JPEG, PNG, GIF, WebP)
    
    **Returns:**
    - Analysis results from all three models
    - Final decision from the deciding model (GPT-5.2)
    - Missing teeth identified in each of the four dental quadrants
    """
    
    # Validate file type
    content_type = image.content_type
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {content_type}. Allowed types: {list(ALLOWED_MIME_TYPES.keys())}"
        )
    
    mime_type = ALLOWED_MIME_TYPES[content_type]
    
    # Read and encode image
    try:
        image_content = await image.read()
        import hashlib
        image_hash = hashlib.sha256(image_content).hexdigest()
        print(f"📊 Analyzing Image: {image.filename} | Size: {len(image_content)} bytes | SHA256: {image_hash[:8]}...")
        
        image_base64 = base64.b64encode(image_content).decode("utf-8")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read image file: {str(e)}"
        )
    
    # Validate image size (max 20MB)
    if len(image_content) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Image file too large. Maximum size is 20MB."
        )
    
    # Run all three models in parallel
    try:
        gpt4o_result, gemini_result, anthropic_result = await asyncio.gather(
            gpt4o_client.analyze_dental_image(image_base64, mime_type),
            gemini_client.analyze_dental_image(image_base64, mime_type),
            anthropic_client.analyze_dental_image(image_base64, mime_type)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during model analysis: {str(e)}"
        )
    
    # Run deciding model with all results
    try:
        final_decision = await deciding_client.decide(
            image_base64=image_base64,
            mime_type=mime_type,
            gpt4o_result=gpt4o_result,
            gemini_result=gemini_result,
            anthropic_result=anthropic_result
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in deciding model: {str(e)}"
        )
    
    return DentalAnalysisResponse(
        gpt4o_result=gpt4o_result,
        gemini_result=gemini_result,
        anthropic_result=anthropic_result,
        final_decision=final_decision,
        image_filename=image.filename or "unknown"
    )


@app.post("/analyze/simple")
async def analyze_dental_image_simple(
    image: UploadFile = File(..., description="OPG dental X-ray image")
):
    """
    Simplified endpoint that returns only the final decision with missing teeth summary.
    
    **Returns:**
    A simplified response with just the final missing teeth analysis.
    """
    
    full_result = await analyze_dental_image(image)
    
    final = full_result.final_decision.final_analysis
    
    return {
        "image_filename": full_result.image_filename,
        "selected_model": full_result.final_decision.selected_model,
        "reasoning": full_result.final_decision.reasoning,
        "agreement_score": full_result.final_decision.agreement_score,
        "confidence": final.confidence,
        "missing_teeth": {
            "quadrant_1_upper_right": final.quadrant_1.missing_teeth,
            "quadrant_2_upper_left": final.quadrant_2.missing_teeth,
            "quadrant_3_lower_left": final.quadrant_3.missing_teeth,
            "quadrant_4_lower_right": final.quadrant_4.missing_teeth,
        },
        "total_missing": (
            len(final.quadrant_1.missing_teeth) +
            len(final.quadrant_2.missing_teeth) +
            len(final.quadrant_3.missing_teeth) +
            len(final.quadrant_4.missing_teeth)
        )
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
