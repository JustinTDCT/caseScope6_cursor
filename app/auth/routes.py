from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from itsdangerous import TimestampSigner, BadSignature

router = APIRouter()
signer = TimestampSigner("CHANGE_ME_SECRET")

@router.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if username == "Admin" and password == "ChangeMe!":
        resp = RedirectResponse(url="/dashboard", status_code=302)
        resp.set_cookie("username", username, httponly=True, samesite="lax")
        resp.set_cookie("role", "Admin", httponly=False, samesite="lax")
        return resp
    return RedirectResponse(url="/", status_code=302)

@router.post("/logout")
def logout():
    resp = RedirectResponse(url="/", status_code=302)
    resp.delete_cookie("username")
    resp.delete_cookie("role")
    return resp
