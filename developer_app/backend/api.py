import asyncio
import logging
import uuid
import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] BACKEND: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Developer Backend Dummy App - Appointment System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MOCK STATE REGISTRY (HIDDEN FROM VOXCORE) ---
class MockState:
    def __init__(self):
        self.create_sys_failure = None  
        self.booking_outcome = None
        self.read_failure = None
        self.delete_failure = None

mock_state = MockState()

# In-memory database for appointments
appointments_db: Dict[str, dict] = {}

# --- MODELS ---
class AppointmentCreate(BaseModel):
    patient_name: str
    specialty: str
    date: str
    time: str

class TestControlRequest(BaseModel):
    target: str 
    failure_mode: Optional[str] = None 

# --- HELPERS ---
DOCTORS = {
    "Cardiology": ["Dr. Alan Grant", "Dr. Ellie Sattler", "Dr. Henry Wu"],
    "Neurology": ["Dr. Ian Malcolm", "Dr. Sarah Harding"],
    "General Practice": ["Dr. John Hammond", "Dr. Ray Arnold"],
    "Orthopedics": ["Dr. Lex Murphy", "Dr. Tim Murphy"]
}

# --- BUSINESS LOGIC API ENDPOINTS ---

@app.post("/api/appointments")
async def create_appointment(req: AppointmentCreate):
    logger.info(f"Creating appointment for {req.patient_name} in {req.specialty}")
    
    # 1. System/Network Failures
    if mock_state.create_sys_failure == "timeout":
        logger.info("Test Control: Simulating network timeout on create...")
        await asyncio.sleep(5)
        raise HTTPException(status_code=504, detail="Network timeout contacting scheduling system.")
    elif mock_state.create_sys_failure == "db_error":
        logger.info("Test Control: Simulating database lock...")
        raise HTTPException(status_code=500, detail="Database insertion failed due to deadlock.")
    
    # Simulating the time it takes to search for doctors
    await asyncio.sleep(1.2) 
    
    app_id = f"APT-{str(uuid.uuid4())[:8].upper()}"
    
    # 2. Business Logic Outcomes (Doctor availability & Status)
    if mock_state.booking_outcome == "no_doctor":
        logger.info("Test Control: Forcing No-Doctor-Available business failure.")
        status = "FAILED"
        assigned_doctor = "None Available"
        location = "N/A"
        notes = "Booking failed: No doctors available for the selected date and time."
    else:
        status = "PENDING" if mock_state.booking_outcome == "pending" else "CONFIRMED"
        assigned_doctor = random.choice(DOCTORS.get(req.specialty, ["Dr. Unknown"]))
        location = "Main Campus, Building A"
        notes = "Please arrive 15 minutes early to fill out missing forms."

    record = {
        "id": app_id,
        "patient_name": req.patient_name,
        "specialty": req.specialty,
        "date": req.date,
        "time": req.time,
        "status": status,
        "assigned_doctor": assigned_doctor,
        "location": location,
        "notes": notes
    }
    
    appointments_db[app_id] = record
    logger.info(f"Creation process finished: {app_id} ended with status {status}")
    return record

@app.get("/api/appointments/{appointment_id}")
async def get_appointment(appointment_id: str):
    logger.info(f"Fetching appointment {appointment_id}")
    
    if mock_state.read_failure == "timeout":
        logger.info("Test Control: Simulating database timeout...")
        await asyncio.sleep(5)
        raise HTTPException(status_code=504, detail="Database timeout while fetching records.")
    elif mock_state.read_failure == "corrupt":
        logger.info("Test Control: Simulating data corruption...")
        raise HTTPException(status_code=500, detail="Data corruption detected in appointment record.")
        
    await asyncio.sleep(0.4) 
    if appointment_id not in appointments_db:
        raise HTTPException(status_code=404, detail=f"Appointment {appointment_id} not found.")
    
    return appointments_db[appointment_id]

@app.delete("/api/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str):
    logger.info(f"Deleting appointment {appointment_id}")
    
    if mock_state.delete_failure == "timeout":
        logger.info("Test Control: Simulating billing system timeout...")
        await asyncio.sleep(5)
        raise HTTPException(status_code=504, detail="Timeout communicating with billing system for cancellation.")
    elif mock_state.delete_failure == "locked":
        logger.info("Test Control: Simulating locked record...")
        raise HTTPException(status_code=403, detail="Appointment is locked and cannot be cancelled at this time.")
        
    await asyncio.sleep(0.5) 
    if appointment_id not in appointments_db:
        raise HTTPException(status_code=404, detail=f"Appointment {appointment_id} not found.")
    
    del appointments_db[appointment_id]
    logger.info(f"Deleted successfully: {appointment_id}")
    return {"status": "DELETED", "id": appointment_id}

# --- TEST CONTROLS ENDPOINT (For the UI Sidebar) ---
@app.post("/api/test_controls/set_failure")
async def set_test_failure(req: TestControlRequest):
    if req.target == "create_sys":
        mock_state.create_sys_failure = req.failure_mode
    elif req.target == "booking_outcome":
        mock_state.booking_outcome = req.failure_mode
    elif req.target == "read":
        mock_state.read_failure = req.failure_mode
    elif req.target == "delete":
        mock_state.delete_failure = req.failure_mode
        
    logger.info(f"TEST CONTROL: Set {req.target} mode to {req.failure_mode}")
    return {"status": "success", "state": req.model_dump()}
