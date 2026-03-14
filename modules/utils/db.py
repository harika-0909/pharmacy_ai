"""
MongoDB Database Connection & CRUD Operations
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
from bson import ObjectId

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "smart_pharmacy_ai")

_client = None
_db = None


def get_db():
    """Get MongoDB database connection (singleton)."""
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_URI)
        _db = _client[MONGO_DB_NAME]
    return _db


def get_collection(name):
    """Get a MongoDB collection."""
    return get_db()[name]


# ==================== USERS ====================

def create_user(username, password_hash, role):
    """Create a new user."""
    users = get_collection("users")
    if users.find_one({"username": username}):
        return False, "Username already exists"
    users.insert_one({
        "username": username,
        "password_hash": password_hash,
        "role": role,
        "created_at": datetime.utcnow()
    })
    return True, "Registration successful"


def get_user(username):
    """Get user by username."""
    users = get_collection("users")
    return users.find_one({"username": username})


def get_all_users():
    """Get all users."""
    users = get_collection("users")
    return list(users.find({}, {"password_hash": 0}))


def delete_user(username):
    """Delete a user by username."""
    users = get_collection("users")
    result = users.delete_one({"username": username})
    return result.deleted_count > 0


# ==================== PATIENTS ====================

def create_patient(patient_data):
    """Create a new patient."""
    patients = get_collection("patients")
    patient_data["created_at"] = datetime.utcnow()
    patient_data["updated_at"] = datetime.utcnow()
    if "medications" not in patient_data:
        patient_data["medications"] = []
    if "medical_history" not in patient_data:
        patient_data["medical_history"] = []
    result = patients.insert_one(patient_data)
    return str(result.inserted_id)


def get_patient(patient_id):
    """Get patient by ID."""
    patients = get_collection("patients")
    return patients.find_one({"_id": ObjectId(patient_id)})


def get_patient_by_name(name):
    """Get patient by name (case-insensitive)."""
    patients = get_collection("patients")
    return patients.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})


def get_all_patients():
    """Get all patients."""
    patients = get_collection("patients")
    return list(patients.find({}))


def update_patient(patient_id, update_data):
    """Update patient data."""
    patients = get_collection("patients")
    update_data["updated_at"] = datetime.utcnow()
    patients.update_one(
        {"_id": ObjectId(patient_id)},
        {"$set": update_data}
    )


def add_medication_to_patient(patient_id, medication):
    """Add a medication to a patient's medication list."""
    patients = get_collection("patients")
    medication["added_at"] = datetime.utcnow()
    patients.update_one(
        {"_id": ObjectId(patient_id)},
        {
            "$push": {"medications": medication},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )


def remove_medication_from_patient(patient_id, medication_name):
    """Remove a medication from a patient's medication list."""
    patients = get_collection("patients")
    patients.update_one(
        {"_id": ObjectId(patient_id)},
        {
            "$pull": {"medications": {"name": medication_name}},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )


def search_patients(query):
    """Search patients by name or phone."""
    patients = get_collection("patients")
    return list(patients.find({
        "$or": [
            {"name": {"$regex": query, "$options": "i"}},
            {"phone": {"$regex": query, "$options": "i"}}
        ]
    }))


# ==================== PRESCRIPTIONS ====================

def insert_prescription(prescription_data):
    """Insert a new prescription."""
    prescriptions = get_collection("prescriptions")
    prescription_data["created_at"] = datetime.utcnow()
    prescription_data["status"] = prescription_data.get("status", "active")
    result = prescriptions.insert_one(prescription_data)
    return str(result.inserted_id)


def get_all_prescriptions():
    """Get all prescriptions."""
    prescriptions = get_collection("prescriptions")
    return list(prescriptions.find({}))


def get_prescription_by_id(prescription_id):
    """Get prescription by prescription_id field."""
    prescriptions = get_collection("prescriptions")
    return prescriptions.find_one({"prescription_id": prescription_id})


def get_prescriptions_by_doctor(doctor_name):
    """Get prescriptions by doctor name."""
    prescriptions = get_collection("prescriptions")
    return list(prescriptions.find({
        "doctor_name": {"$regex": doctor_name, "$options": "i"}
    }))


def get_prescriptions_by_patient(patient_name):
    """Get prescriptions by patient name."""
    prescriptions = get_collection("prescriptions")
    return list(prescriptions.find({
        "patient_name": {"$regex": patient_name, "$options": "i"}
    }))


def get_prescriptions_by_caregiver(caregiver_name):
    """Get prescriptions by caregiver."""
    prescriptions = get_collection("prescriptions")
    return list(prescriptions.find({
        "caregiver": {"$regex": f"^{caregiver_name}$", "$options": "i"}
    }))


def update_prescription(prescription_id, update_data):
    """Update a prescription."""
    prescriptions = get_collection("prescriptions")
    update_data["updated_at"] = datetime.utcnow()
    prescriptions.update_one(
        {"prescription_id": prescription_id},
        {"$set": update_data}
    )


# ==================== ORDERS ====================

def create_order(order_data):
    """Create a new order from a prescription."""
    orders = get_collection("orders")
    order_data["created_at"] = datetime.utcnow()
    order_data["updated_at"] = datetime.utcnow()
    order_data["status"] = order_data.get("status", "pending")
    order_data["pharmacy_notes"] = order_data.get("pharmacy_notes", "")
    result = orders.insert_one(order_data)
    return str(result.inserted_id)


def get_all_orders():
    """Get all orders."""
    orders = get_collection("orders")
    return list(orders.find({}).sort("created_at", -1))


def get_order_by_prescription(prescription_id):
    """Get order by prescription ID."""
    orders = get_collection("orders")
    return orders.find_one({"prescription_id": prescription_id})


def get_orders_by_status(status):
    """Get orders filtered by status."""
    orders = get_collection("orders")
    return list(orders.find({"status": status}).sort("created_at", -1))


def update_order(order_id, update_data):
    """Update an order."""
    orders = get_collection("orders")
    update_data["updated_at"] = datetime.utcnow()
    orders.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": update_data}
    )


def update_order_status(prescription_id, status, updated_by, notes=""):
    """Update order status by prescription ID."""
    orders = get_collection("orders")
    update_data = {
        "status": status,
        "updated_by": updated_by,
        "updated_at": datetime.utcnow()
    }
    if notes:
        update_data["pharmacy_notes"] = notes
    orders.update_one(
        {"prescription_id": prescription_id},
        {"$set": update_data}
    )


# ==================== MEDICINE CATALOG ====================

def add_medicine(medicine_data):
    """Add a medicine to the catalog (admin only)."""
    catalog = get_collection("medicine_catalog")
    # Check if medicine already exists
    if catalog.find_one({"name": {"$regex": f"^{medicine_data['name']}$", "$options": "i"}}):
        return False, "Medicine already exists"
    medicine_data["created_at"] = datetime.utcnow()
    medicine_data["active"] = True
    catalog.insert_one(medicine_data)
    return True, "Medicine added successfully"


def get_all_medicines():
    """Get all medicines from catalog."""
    catalog = get_collection("medicine_catalog")
    return list(catalog.find({"active": True}).sort("name", 1))


def get_medicine_names():
    """Get just the medicine names for dropdowns."""
    medicines = get_all_medicines()
    return [m["name"] for m in medicines]


def update_medicine(medicine_id, update_data):
    """Update a medicine in the catalog."""
    catalog = get_collection("medicine_catalog")
    update_data["updated_at"] = datetime.utcnow()
    catalog.update_one(
        {"_id": ObjectId(medicine_id)},
        {"$set": update_data}
    )


def delete_medicine(medicine_id):
    """Soft delete a medicine."""
    catalog = get_collection("medicine_catalog")
    catalog.update_one(
        {"_id": ObjectId(medicine_id)},
        {"$set": {"active": False, "updated_at": datetime.utcnow()}}
    )


def seed_medicine_catalog():
    """Seed default medicine catalog if empty."""
    catalog = get_collection("medicine_catalog")
    if catalog.count_documents({}) == 0:
        default_medicines = [
            {"name": "Paracetamol", "category": "Pain Relief", "dosage_form": "Tablet", "strength": "500mg"},
            {"name": "Ibuprofen", "category": "Pain Relief", "dosage_form": "Tablet", "strength": "400mg"},
            {"name": "Aspirin", "category": "Pain Relief", "dosage_form": "Tablet", "strength": "300mg"},
            {"name": "Amoxicillin", "category": "Antibiotic", "dosage_form": "Capsule", "strength": "500mg"},
            {"name": "Azithromycin", "category": "Antibiotic", "dosage_form": "Tablet", "strength": "250mg"},
            {"name": "Ciprofloxacin", "category": "Antibiotic", "dosage_form": "Tablet", "strength": "500mg"},
            {"name": "Metformin", "category": "Diabetes", "dosage_form": "Tablet", "strength": "500mg"},
            {"name": "Insulin", "category": "Diabetes", "dosage_form": "Injection", "strength": "100IU/ml"},
            {"name": "Omeprazole", "category": "Gastrointestinal", "dosage_form": "Capsule", "strength": "20mg"},
            {"name": "Pantoprazole", "category": "Gastrointestinal", "dosage_form": "Tablet", "strength": "40mg"},
            {"name": "Amlodipine", "category": "Cardiovascular", "dosage_form": "Tablet", "strength": "5mg"},
            {"name": "Losartan", "category": "Cardiovascular", "dosage_form": "Tablet", "strength": "50mg"},
            {"name": "Atorvastatin", "category": "Cardiovascular", "dosage_form": "Tablet", "strength": "10mg"},
            {"name": "Cetirizine", "category": "Antihistamine", "dosage_form": "Tablet", "strength": "10mg"},
            {"name": "Loratadine", "category": "Antihistamine", "dosage_form": "Tablet", "strength": "10mg"},
            {"name": "Salbutamol", "category": "Respiratory", "dosage_form": "Inhaler", "strength": "100mcg"},
            {"name": "Montelukast", "category": "Respiratory", "dosage_form": "Tablet", "strength": "10mg"},
            {"name": "Sertraline", "category": "Psychiatric", "dosage_form": "Tablet", "strength": "50mg"},
            {"name": "Vitamin D3", "category": "Supplement", "dosage_form": "Tablet", "strength": "1000IU"},
            {"name": "Vitamin B12", "category": "Supplement", "dosage_form": "Tablet", "strength": "1500mcg"},
        ]
        for med in default_medicines:
            med["created_at"] = datetime.utcnow()
            med["active"] = True
        catalog.insert_many(default_medicines)


# ==================== INVENTORY ====================

def get_inventory():
    """Get all inventory items."""
    inventory = get_collection("inventory")
    return list(inventory.find({}))


def update_inventory_stock(medicine_name, new_stock):
    """Update stock for a medicine."""
    inventory = get_collection("inventory")
    inventory.update_one(
        {"medicine_name": medicine_name},
        {"$set": {"stock": new_stock, "updated_at": datetime.utcnow()}}
    )


def add_inventory_item(item_data):
    """Add a new inventory item."""
    inventory = get_collection("inventory")
    item_data["created_at"] = datetime.utcnow()
    inventory.insert_one(item_data)


def seed_inventory(inventory_dict):
    """Seed inventory from a dictionary if collection is empty."""
    inventory = get_collection("inventory")
    if inventory.count_documents({}) == 0:
        items = []
        for name, stock in inventory_dict.items():
            items.append({
                "medicine_name": name,
                "stock": stock,
                "reorder_level": 15,
                "category": "General",
                "created_at": datetime.utcnow()
            })
        if items:
            inventory.insert_many(items)


def get_low_stock_items(threshold=15):
    """Get items below stock threshold."""
    inventory = get_collection("inventory")
    return list(inventory.find({"stock": {"$lte": threshold}}))


# ==================== SEED DATA ====================

def seed_default_data():
    """Seed default admin user if no users exist."""
    import bcrypt
    users = get_collection("users")
    if users.count_documents({}) == 0:
        # Create default admin
        password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        users.insert_one({
            "username": "admin",
            "password_hash": password_hash,
            "role": "admin",
            "created_at": datetime.utcnow()
        })

        # Create default doctor
        doc_hash = bcrypt.hashpw("doctor123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        users.insert_one({
            "username": "doctor1",
            "password_hash": doc_hash,
            "role": "doctor",
            "created_at": datetime.utcnow()
        })

        # Create default pharmacy
        pharm_hash = bcrypt.hashpw("pharmacy123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        users.insert_one({
            "username": "pharmacy1",
            "password_hash": pharm_hash,
            "role": "pharmacy",
            "created_at": datetime.utcnow()
        })

        # Create default caregiver
        care_hash = bcrypt.hashpw("caregiver123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        users.insert_one({
            "username": "caregiver1",
            "password_hash": care_hash,
            "role": "caregiver",
            "created_at": datetime.utcnow()
        })

        print("✅ Default users seeded: admin/admin123, doctor1/doctor123, pharmacy1/pharmacy123, caregiver1/caregiver123")