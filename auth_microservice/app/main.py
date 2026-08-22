from fastapi import FastAPI

app = FastAPI(title="Auth Microservice")


@app.get("/")
async def root():
    return {"service": "auth_microservice", "status": "running"}
