from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import api, analytics, predictions, betting

app = FastAPI(
    title="NBA Analytics API",
    description="API para consulta de dados e estatísticas da NBA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Breno Braido",
        "email": "bsbraido@gmail.com"
    },
)

# CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(api.router, prefix="/api/v1", tags=["Data"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(predictions.router, prefix="/api/v1/predictions", tags=["Predictions"])
app.include_router(betting.router, prefix="/api/v1/bet", tags=["Bet"])
    
@app.get("/")
def read_root():
    return {"message": "NBA Analytics API is running"}
    
@app.get("/health", summary="Verificação de saúde da API")
def health_check():
    return {
        "status": "online",
        "message": "NBA Analytics API está funcionando corretamente",
        "version": "1.0.0"
    }
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)