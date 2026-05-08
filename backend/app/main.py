from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.db.session import Base, engine
from app.services.seed import seed_demo_data


def create_app() -> FastAPI:
    app = FastAPI(
        title="LoanPilot API",
        description="Conversational banking loan AI agent demo API.",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=settings.cors_allow_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix="/api")
    Base.metadata.create_all(bind=engine)
    seed_demo_data()

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)
        seed_demo_data()

    return app


app = create_app()
