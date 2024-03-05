from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette import status
import re
from database import crud
from database.model import get_session, close_session
from hashing import Hasher
from loguru import logger

SKIP_MIDDLEWARE_PATHS = ["/daftar"]
NOREK_ON_PATHS = ["/saldo", "/mutasi"]

async def set_body(request: Request, body: bytes):
    async def receive():
        return {"type": "http.request", "body": body}
    request._receive = receive

async def get_body(request: Request) -> bytes:
    body = await request.body()
    await set_body(request, body)
    return body

async def pin_validation(request: Request, call_next):
    if request.url.path not in SKIP_MIDDLEWARE_PATHS:
        pin = request.headers.get("pin")
        if pin is None:
            logger.error("PIN tidak ditemukan")
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"remark": "failed - PIN Tidak Ditemukan"})
        
        nomor_rekening = ""
        no_rek_found = False
        no_rek_on_path = False
        for path in NOREK_ON_PATHS:
            if path in request.url.path:
                no_rek_on_path = True
                break
        if no_rek_on_path:
            nomor_rekening = request.url.path.split("/")[-1]
            if nomor_rekening == "saldo" or nomor_rekening == "mutasi":
                nor_rek_found = False
            else:
                no_rek_found = True
        else:
            await set_body(request, await request.body())
            reqs = await get_body(request)
            body_raw = reqs.decode('utf-8')
            for body in body_raw.split():
                if ("no_rekening_asal" in body) or ("no_rekening" in body ):
                    no_rek_found = True
                    continue
                if no_rek_found:
                    nomor_rekening = body
                    break
            nomor_rekening = re.sub(r'\D', '', nomor_rekening)

        if not nomor_rekening or not no_rek_found:
            logger.error("No Rekening tidak ditemukan")
            return_msg = {
                "remark": "failed",
                "data": {
                    "reason": "No Rekening {} tidak ditemukan".format(nomor_rekening)
                }
            }
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=return_msg)

        session = get_session()        
        account = crud.account_by_no_rekening(session, nomor_rekening)
        if account is None:
            logger.error("No Rekening tidak ditemukan")
            return_msg = {
                "remark": "failed",
                "data": {
                    "reason": "No Rekening {} tidak ditemukan".format(nomor_rekening)
                }
            }
            close_session(session)
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=return_msg)

        if not Hasher.verify_password(pin.encode('utf-8'), account.pin):
            logger.error("PIN salah")
            return_msg = {
                "remark": "failed",
                "data": {
                    "reason": "PIN salah"
                }
            }
            close_session(session)
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=return_msg)

        response = await call_next(request)
        close_session(session)
        return response
    else:
        response = await call_next(request)
        return response