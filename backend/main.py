from fastapi import FastAPI, status,Depends, HTTPException
from database import get_db
from pydantic import BaseModel

class Login(BaseModel):
    email: str
    password: str

app = FastAPI()

# em = "dharmikmodi@gmail.com"
# pw = "12345678"

@app.post("/login_admin")
def admin_login(data: Login,db = Depends(get_db)):
    c = db.cursor()
    c.execute("select team_leader_email,team_leader_password from team_leader where team_leader_email = %s",(data.email,))
    d = c.fetchone()
    
    if d is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email"
        )

    if data.password != d["team_leader_password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )

    print("success")
    return {"message": "Login successful"}