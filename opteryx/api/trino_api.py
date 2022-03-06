from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
import os
import uvicorn

trino = FastAPI()

@trino.post("/v1/statement", response_class=ORJSONResponse)
async def read_main(request: Request):
    print(request)
    return {
        "id": 1,
        "stats": {},
        "infoUri": "",
        "columns": ["name", "age"],
        "data": [
            ['Justin', 42],
            ['Bec', 41],
            ['Lucie', 13],
            ['Alice', 11]
        ]
    }

# tell the server to start
if __name__ == "__main__":
    uvicorn.run(
        "trino_api:trino",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        lifespan="on",
    )