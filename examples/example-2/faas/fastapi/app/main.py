from fastapi import FastAPI, HTTPException
import waitress
# from starlette.responses import Response

# from app.db.models import UserAnswer
# from app.api import api

app = FastAPI()


@app.get("/")
def root():
    print("hello")
    return {"message": "Fast API in Python"}


def run() -> None:  # pragma: no cover
    """Run the server."""
    print("here")
    uvicorn.run(
        "app.main:app", host="127.0.0.1", port=8000, reload=True
    )


if __name__ == "__main__":
    print("here")
    waitress.serve(app, host="127.0.0.1", port=8000)

# @app.get("/user")
# def read_user():
#     return api.read_user()


# @app.get("/question/{position}", status_code=200)
# def read_questions(position: int, response: Response):
#     question = api.read_questions(position)

#     if not question:
#         raise HTTPException(status_code=400, detail="Error")

#     return question


# @app.get("/alternatives/{question_id}")
# def read_alternatives(question_id: int):
#     return api.read_alternatives(question_id)


# @app.post("/answer", status_code=201)
# def create_answer(payload: UserAnswer):
#     payload = payload.dict()

#     return api.create_answer(payload)


# @app.get("/result/{user_id}")
# def read_result(user_id: int):
#     return api.read_result(user_id)
