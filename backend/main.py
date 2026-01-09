from fastapi import FastAPI, status,Depends, HTTPException
from database import access_db
from pydantic import BaseModel
import pymysql.cursors


    
class Login(BaseModel):
    email: str
    password: str

class AgentRegister(BaseModel):
    team_leader_email : str
    name : str
    email : str
    mobile_number : str
    password : str

class ServicePersonRegister(BaseModel):
    agent_email : str
    name : str
    email : str 
    mobile_number : str 
    password : str 
    type : str 
    city : str 
    state : str 
    country : str

class CustomerRegister(BaseModel):
    agent_email : str
    name : str
    email : str
    mobile_number : str
    company_name : str
    city : str
    state : str
    country : str
    address : str

app = FastAPI()

# # -------------------------------------- Team Leader ----------------------------------------------
# @app.post("/login_team_leader")
# def team_leader_login(data: Login,db = Depends(access_db)):
#     try:
#         c = db.cursor()
#         c.execute("select team_leader_email,team_leader_password from team_leader where team_leader_email = %s",(data.email,))
#         d = c.fetchone()
        
#         if d is None:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid email"
#             )

#         if data.password != d["team_leader_password"]:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid password"
#             )

#         print("success")
#         return {"message": "Login successful"}
#     except Exception as e:
#         return e

# @app.get("/all_team_leaders")
# def fetch_all_team_leaders(db = Depends(access_db)):
#     try:
#         with db:
#             with db.cursor() as cursor:
#                 team_leader = cursor.execute("select * from team_leader")
#                 if team_leader:
#                     d = cursor.fetchall()
#                     return d
#                 else:
#                     raise HTTPException(
#                             status_code=status.HTTP_404_NOT_FOUND,
#                             detail="Team Leader not found"
#                         )
#     except Exception as e:
#         return e

# # -------------------------------------- Agent ----------------------------------------------
# @app.post("/employee_registration")
# def agent_registration(data:AgentRegister,db = Depends(access_db)):
#     try:
#         with db:
#             with db.cursor() as cursor:
#                 team_leader = cursor.execute("select * from team_leader where team_leader_email = %s",(data.team_leader_email,))
#                 if team_leader:
#                     cursor.execute("select * from agent where agent_email = %s",(data.email,))
#                     d = cursor.fetchone()
#                     if d:
#                         raise HTTPException(
#                             status_code=status.HTTP_409_CONFLICT,
#                             detail="Email already exist"
#                         )
#                     cursor.execute("insert into agent(agent_name,agent_email,agent_mobile_number,agent_password, agent_ticket_count,agent_rating) values (%s,%s,%s,%s,0,0)",(data.name,data.email,data.mobile_number,data.password))
#                     db.commit()
#                     return {"status_code":status.HTTP_201_CREATED, "message":"Agent registered"}
#                 else:
#                     raise HTTPException(
#                             status_code=status.HTTP_404_NOT_FOUND,
#                             detail="Team Leader not found"
#                         )
#     except Exception as e:
#         return e

# @app.get("/all_agents")
# def fetch_all_agents(db = Depends(access_db)):
#     try:
#         with db:
#             with db.cursor() as cursor:
#                 agent = cursor.execute("select * from agent")
#                 if agent:
#                     d = cursor.fetchall()
#                     return d
#                 else:
#                     raise HTTPException(
#                             status_code=status.HTTP_404_NOT_FOUND,
#                             detail="Agent not found"
#                         )
#     except Exception as e:
#         return e
    
# @app.post("/agent_login")
# def agent_login(data: Login,db = Depends(access_db)):
#     try:
#         c = db.cursor()
#         c.execute("select agent_email,agent_password from agent where agent_email = %s",(data.email,))
#         d = c.fetchone()
        
#         if d is None:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid email"
#             )

#         if data.password != d["agent_password"]:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid password"
#             )

#         print("success")
#         return {"message": "Login successful"}
#     except Exception as e:
#         return 

# @app.put("/agent_update")
# def update_agent(data : AgentRegister,db = Depends(access_db)):
#     try:
#         with db:
#             with db.cursor() as cursor:
#                 team_leader = cursor.execute("select * from team_leader where team_leader_email = %s",(data.team_leader_email,))
#                 if team_leader:
#                     cursor.execute("select agent_email from agent where agent_email = %s",(data.email,))
#                     d = cursor.fetchone()
#                     if d:
#                         cursor.execute("update agent set agent_name=%s,agent_mobile_number=%s,agent_password=%s where agent_email = %s",(data.name,data.mobile_number,data.password,data.email))
#                         db.commit()
#                         return status.HTTP_202_ACCEPTED
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail="Email not exist"
#                     )
#                 raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail="Team Leader not found"
#                     )    
#     except Exception as e:
#         return e
    
# @app.delete("/agent_remove")
# def remove_agent(team_leader_email:str,email:str,db = Depends(access_db)):
#     try:
#         with db:
#             with db.cursor() as cursor:
#                 team_leader = cursor.execute("select * from team_leader where team_leader_email = %s",(team_leader_email,))
#                 if team_leader:
#                     cursor.execute("select agent_email from agent where agent_email = %s",(email,))
#                     d = cursor.fetchone()
#                     if d:
#                         cursor.execute("delete from agent where agent_email = %s",(email))
#                         db.commit()
#                         return status.HTTP_200_OK
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail="Email not exist"
#                     )
#                 raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail="Team Leader not found"
#                     )    
#     except Exception as e:
#         return e

# # -------------------------------------- Service person ----------------------------------------------

# @app.get("/all_service_person")
# def fetch_all_service_person(db = Depends(access_db)):
#     try:
#         with db:
#             with db.cursor() as cursor:
#                 service_person = cursor.execute("select * from service_person")
#                 if service_person:
#                     d = cursor.fetchall()
#                     return d
#                 else:
#                     raise HTTPException(
#                             status_code=status.HTTP_404_NOT_FOUND,
#                             detail="Service person not found"
#                         )
#     except Exception as e:
#         return e

# @app.post("/service_person_registration")
# def service_person_registration(data:ServicePersonRegister,db = Depends(access_db)):
#     try:
#         with db:
#             with db.cursor() as cursor:
#                 agent = cursor.execute("select * from agent where agent_email = %s",(data.agent_email,))
#                 if agent:
#                     cursor.execute("select * from service_person where service_person_email = %s",(data.email,))
#                     d = cursor.fetchone()
#                     if d:
#                         raise HTTPException(
#                             status_code=status.HTTP_409_CONFLICT,
#                             detail="Email already exist"
#                         )
#                     query = '''insert into service_person(
#                     service_person_name,
#                     service_person_email,
#                     service_person_mobile_number,
#                     service_person_password, 
#                     service_person_type,
#                     service_person_ticket_count,
#                     service_person_rating, 
#                     service_person_city,
#                     service_person_state, 
#                     service_person_country
#                     ) values (%s,%s,%s,%s,%s,0,0,%s,%s,%s)'''
#                     values = (data.name,
#                               data.email,
#                               data.mobile_number,
#                               data.password,
#                               data.type,
#                               data.city,
#                               data.state,
#                               data.country)
#                     cursor.execute(query,values)
#                     db.commit()
#                     return {"status_code":status.HTTP_201_CREATED, "message":"Agent registered"}
#                 else:
#                     raise HTTPException(
#                             status_code=status.HTTP_404_NOT_FOUND,
#                             detail="Agent not found"
#                         )
#     except Exception as e:
#         return e


# @app.post("/serice_person_login")
# def service_person_login(data: Login,db = Depends(access_db)):
#     try:
#         c = db.cursor()
#         c.execute("select service_person_email,service_person_password from service_person where service_person_email = %s",(data.email,))
#         d = c.fetchone()
        
#         if d is None:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid email"
#             )

#         if data.password != d["service_person_password"]:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid password"
#             )

#         print("success")
#         return {"message": "Login successful"}
#     except Exception as e:
#         return e

# @app.put("/update_service_person")
# def update_service_person(data : ServicePersonRegister,db = Depends(access_db)):
#     try:
#         with db:
#             with db.cursor() as cursor:
#                 agent = cursor.execute("select * from agent where agent_email = %s",(data.agent_email,))
#                 if agent:
#                     cursor.execute("select service_person_email from service_person where service_person_email = %s",(data.email,))
#                     d = cursor.fetchone()
#                     if d:
#                         query = '''update service_person set 
#                         service_person_name = %s,
#                         service_person_mobile_number = %s,
#                         service_person_password = %s, 
#                         service_person_type = %s,
#                         service_person_city = %s,
#                         service_person_state = %s, 
#                         service_person_country = %s
#                         where service_person_email = %s'''
#                         values = (data.name,
#                                   data.mobile_number,
#                                   data.password,
#                                   data.type,
#                                   data.city,
#                                   data.state,
#                                   data.country,
#                                   data.email)
#                         cursor.execute(query,values)
#                         db.commit()
#                         return status.HTTP_202_ACCEPTED
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail="Email not exist"
#                     )
#                 raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail="Agent not found"
#                     )    
#     except Exception as e:
#         return e

# @app.delete("/remove_service_person")
# def remove_service_person(email:str,agent_email:str,db = Depends(access_db)):
#     try:
#         with db:
#             with db.cursor() as cursor:
#                 agent = cursor.execute("select * from agent where agent_email = %s",(agent_email,))
#                 if agent:
#                     cursor.execute("select service_person_email from service_person where service_person_email = %s",(email,))
#                     d = cursor.fetchone()
#                     if d:
#                         cursor.execute("delete from service_person where service_person_email = %s",(email))
#                         db.commit()
#                         return status.HTTP_200_OK
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail="Email not exist"
#                     )
#                 raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail="Agent not found"
#                     )    
#     except Exception as e:
#         return e


# # -------------------------------------- customer ----------------------------------------------

# @app.get("/all_customers")
# def fetch_all_customers(db = Depends(access_db)):
#     try:
#         with db:
#             with db.cursor() as cursor:
#                 cursor.execute("select * from customer")
#                 d = cursor.fetchall()
#                 if d:
#                     return d
#                 else:
#                     raise HTTPException(
#                             status_code=status.HTTP_404_NOT_FOUND,
#                             detail="Customer not found"
#                         )
#     except Exception as e:
#         return e
    

# @app.post("/customer_registration")
# def customer_registration(data:CustomerRegister,db = Depends(access_db)):
#     try:
#         with db:
#             with db.cursor() as cursor:
#                 agent = cursor.execute("select * from agent where agent_email = %s",(data.agent_email,))
#                 if agent:
#                     cursor.execute("select * from customer where customer_email = %s",(data.email,))
#                     d = cursor.fetchone()
#                     if d:
#                         raise HTTPException(
#                             status_code=status.HTTP_409_CONFLICT,
#                             detail="Email already exist"
#                         )
#                     query = '''insert into customer(
#                     customer_name, 
#                     customer_email, 
#                     customer_mobile_number, 
#                     customer_company_name, 
#                     customer_city, 
#                     customer_state, 
#                     customer_country, 
#                     customer_address
#                     ) values (%s,%s,%s,%s,%s,%s,%s,%s)'''
#                     values = (data.name,
#                               data.email,
#                               data.mobile_number,
#                               data.company_name,
#                               data.city,
#                               data.state,
#                               data.country,
#                               data.address)
#                     cursor.execute(query,values)
#                     db.commit()
#                     return {"status_code":status.HTTP_201_CREATED, "message":"Customer registered"}
#                 else:
#                     raise HTTPException(
#                             status_code=status.HTTP_404_NOT_FOUND,
#                             detail="Agent not found"
#                         )
#     except Exception as e:
#         return e


# # @app.post("/customer_login")
# # def customer_login(data: Login,db = Depends(access_db)):
# #     try:
# #         c = db.cursor()
# #         c.execute("select customer_email,customer_password from customer where customer_email = %s",(data.email,))
# #         d = c.fetchone()
        
# #         if d is None:
# #             raise HTTPException(
# #                 status_code=status.HTTP_401_UNAUTHORIZED,
# #                 detail="Invalid email"
# #             )

# #         if data.password != d["customer_password"]:
# #             raise HTTPException(
# #                 status_code=status.HTTP_401_UNAUTHORIZED,
# #                 detail="Invalid password"
# #             )

# #         print("success")
# #         return {"message": "Login successful"}
# #     except Exception as e:
# #         return e

# # @app.put("/update_service_person")
# # def update_service_person(data : ServicePersonRegister,db = Depends(access_db)):
# #     try:
# #         with db:
# #             with db.cursor() as cursor:
# #                 agent = cursor.execute("select * from agent where agent_email = %s",(data.agent_email,))
# #                 if agent:
# #                     cursor.execute("select service_person_email from service_person where service_person_email = %s",(data.email,))
# #                     d = cursor.fetchone()
# #                     if d:
# #                         query = '''update service_person set 
# #                         service_person_name = %s,
# #                         service_person_mobile_number = %s,
# #                         service_person_password = %s, 
# #                         service_person_type = %s,
# #                         service_person_city = %s,
# #                         service_person_state = %s, 
# #                         service_person_country = %s
# #                         where service_person_email = %s'''
# #                         values = (data.name,
# #                                   data.mobile_number,
# #                                   data.password,
# #                                   data.type,
# #                                   data.city,
# #                                   data.state,
# #                                   data.country,
# #                                   data.email)
# #                         cursor.execute(query,values)
# #                         db.commit()
# #                         return status.HTTP_202_ACCEPTED
# #                     raise HTTPException(
# #                         status_code=status.HTTP_404_NOT_FOUND,
# #                         detail="Email not exist"
# #                     )
# #                 raise HTTPException(
# #                         status_code=status.HTTP_404_NOT_FOUND,
# #                         detail="Agent not found"
# #                     )    
# #     except Exception as e:
# #         return e

# # @app.delete("/remove_service_person")
# # def remove_service_person(email:str,agent_email:str,db = Depends(access_db)):
# #     try:
# #         with db:
# #             with db.cursor() as cursor:
# #                 agent = cursor.execute("select * from agent where agent_email = %s",(agent_email,))
# #                 if agent:
# #                     cursor.execute("select service_person_email from service_person where service_person_email = %s",(email,))
# #                     d = cursor.fetchone()
# #                     if d:
# #                         cursor.execute("delete from service_person where service_person_email = %s",(email))
# #                         db.commit()
# #                         return status.HTTP_200_OK
# #                     raise HTTPException(
# #                         status_code=status.HTTP_404_NOT_FOUND,
# #                         detail="Email not exist"
# #                     )
# #                 raise HTTPException(
# #                         status_code=status.HTTP_404_NOT_FOUND,
# #                         detail="Agent not found"
# #                     )    
# #     except Exception as e:
# #         return e

