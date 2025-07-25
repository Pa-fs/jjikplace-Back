from fastapi import FastAPI
from starlette.config import Config
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.database import engine
from app import models
from app.routers import cluster, sns_auth, form_auth, review, studios, profile, form_signup, favorite

config = Config(".env")
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:3000","https://jjikplace.netlify.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session Middleware
app.add_middleware(SessionMiddleware, secret_key= config("JWT_SECRET_KEY"))

app.include_router(cluster.router, prefix="/cluster", tags=["지도 클러스터링 API"])
app.include_router(studios.router, tags=["셀프사진관 API"])
app.include_router(sns_auth.router, tags=["로그인 API"])
app.include_router(form_auth.router, tags=["로그인 API"])
app.include_router(form_signup.router, tags=["회원가입 API"])
app.include_router(profile.router, tags=["프로필 API"])
app.include_router(review.router, tags=["리뷰 API"])
app.include_router(favorite.router, tags=["찜하기 API"])