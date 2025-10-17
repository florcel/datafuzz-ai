from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Dashboard API"}

@app.get("/status")
def read_status():
    return {"status": "Dashboard is running"}

# Additional routes can be added here as needed.