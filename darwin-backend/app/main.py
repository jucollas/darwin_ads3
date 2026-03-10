from fastapi import FastAPI

from app.core.errors import setup_exception_handlers
from app.api.routers.campaigns import router as campaigns_router
from app.api.routers.debug import router as debug_router
from app.api.routers.variants import router as variants_router
from app.api.routers.darwin import router as darwin_router
from app.api.routers.scheduler import router as scheduler_router
from app.services.scheduler_manager import scheduler_manager
from app.api.routers.metrics_overview import router as metrics_overview_router

app = FastAPI(title="Darwin Ads MVP", version="0.1.0")
setup_exception_handlers(app)


@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(campaigns_router)
app.include_router(debug_router)
app.include_router(variants_router)
app.include_router(darwin_router)
app.include_router(scheduler_router)
app.include_router(metrics_overview_router)

@app.on_event("startup")
async def _startup():
    await scheduler_manager.start()

@app.on_event("shutdown")
async def _shutdown():
    await scheduler_manager.shutdown()