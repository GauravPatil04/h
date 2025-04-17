from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from supabase import create_client, Client
import uuid
from datetime import date

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Replace with your Supabase project credentials
SUPABASE_URL = "https://evqpuqeucgsqafflseug.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV2cXB1cWV1Y2dzcWFmZmxzZXVnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NDgyNzM2MywiZXhwIjoyMDYwNDAzMzYzfQ.vBDY4VXNOgNFFk9MMYgf9aAGgSAtgFMMY_fzPI49QQg"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Simple session storage
sessions = {}

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    result = supabase.auth.sign_in_with_password({"email": email, "password": password})
    if result.user:
        sessions[email] = result.session.access_token
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(key="email", value=email)
        return response
    return RedirectResponse(url="/", status_code=302)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    email = request.cookies.get("email")
    if not email or email not in sessions:
        return RedirectResponse(url="/", status_code=302)

    user = supabase.auth.get_user(sessions[email])
    user_id = user.user.id
    data = supabase.table("expenses").select("*").eq("user_id", user_id).execute()
    return templates.TemplateResponse("dashboard.html", {"request": request, "expenses": data.data, "email": email})

@app.post("/add")
def add_expense(
    request: Request,
    income: float = Form(...),
    expense_amount: float = Form(...),
    expense_date: date = Form(...),
    category: str = Form(...)
):
    email = request.cookies.get("email")
    if not email or email not in sessions:
        return RedirectResponse(url="/", status_code=302)

    user = supabase.auth.get_user(sessions[email])
    user_id = user.user.id
    supabase.table("expenses").insert({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "income": income,
        "expense_amount": expense_amount,
        "expense_date": expense_date,
        "category": category
    }).execute()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/delete/{id}")
def delete_expense(id: str):
    supabase.table("expenses").delete().eq("id", id).execute()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/update/{id}")
def update_expense(
    id: str,
    income: float = Form(...),
    expense_amount: float = Form(...),
    expense_date: date = Form(...),
    category: str = Form(...)
):
    supabase.table("expenses").update({
        "income": income,
        "expense_amount": expense_amount,
        "expense_date": expense_date,
        "category": category
    }).eq("id", id).execute()
    return RedirectResponse(url="/dashboard", status_code=302)
