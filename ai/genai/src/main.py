"""Entry point utama aplikasi FastAPI ROKKUS AI Inventory Assistant."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import api_router
from .core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "API Layanan AI Inventory Assistant untuk UMKM ROKKUS Mardani Raya. "
        "Menyediakan endpoint analisis stok, rekomendasi restock harian, dan ringkasan inventaris."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Konfigurasi CORS agar frontend (React/Vite/Next) dapat mengakses API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pada production dapat dibatasi ke domain frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Daftarkan Router API v1
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
def read_root():
    """Endpoint root untuk verifikasi dasar status server."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
        "status": "online",
        "active_provider": "mock",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)

