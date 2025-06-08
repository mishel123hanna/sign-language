from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.settings import settings
from app.db.config import init_db
from app.auth.routes import auth_router
from app.sign_to_text.routes import sign_to_text_router
from app.text_to_sign.routes import text_to_sign_router

# Import these once you implement them
# from app.core.errors import register_all_errors
# from app.core.middleware import register_middleware


app = FastAPI(
    lifespan=init_db,
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.API_VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    contact={
        "name": settings.CONTACT_NAME,
        "url": settings.CONTACT_URL,
        "email": settings.CONTACT_EMAIL,
    },
    # terms_of_service=settings.TERMS_OF_SERVICE,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
# register_all_errors(app)

# Register middleware
# register_middleware(app)

# Include routers
app.include_router(
    auth_router, prefix=settings.API_PREFIX + "/auth", tags=["Authentication"]
)
app.include_router(
    sign_to_text_router, prefix=settings.API_PREFIX,
     include_in_schema=True, tags=["Translate Sign to Text via Websocket"]
)
app.include_router(
    text_to_sign_router, prefix=settings.API_PREFIX, tags=["المخاطبة"]
)

# Health check endpoint
@app.get("/health", include_in_schema=False)
async def health_check():
    return JSONResponse(content={"status": "ok"})


