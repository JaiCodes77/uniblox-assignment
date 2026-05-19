from fastapi import FastAPI

app = FastAPI(title="Ecommerce Store")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
