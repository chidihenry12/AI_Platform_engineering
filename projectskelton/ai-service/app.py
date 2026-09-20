from fastapi import FastAPI

app = FastAPI(title="AI Service", description="A simple AI service API", version="1.0.0")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/predict")
async def predict():
    # Placeholder for AI prediction logic
    return {"prediction": "This is a dummy prediction."}

@app.get("/info")
async def info():
    return {"service": "AI Service", "version": "1.0.0", "description": "A simple AI service API"}


@app.get("/metrics")
async def metrics():
    # Placeholder for metrics logic
    return {"requests": 100, "errors": 5}