import sys
import os

# Add the backend directory to sys.path so app modules can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "/backend")

from app.core.db import SessionLocal
from app.models.brand import Brand

def seed_brands():
    db = SessionLocal()
    
    # Check if brands already exist to prevent duplicates
    if db.query(Brand).count() > 0:
        print("Brands already seeded.")
        return

    brands = [
        Brand(
            name="Jade",
            voice_description="Jade provides specialized jewellery insurance tailored for small retailers. Our voice is professional and reassuring, designed to instill trust and confidence in business owners seeking to protect their valuable inventory. We avoid overly salesy language and focus on providing clear, supportive information."
        ),
        Brand(
            name="Jaguar Transit",
            voice_description="Jaguar Transit offers comprehensive logistics and transit insurance for high-value goods. Our communication style is authoritative, secure, and robust, reflecting our commitment to fail-safe protection during transport. We emphasize reliability and our deep expertise in risk management."
        ),
        Brand(
            name="DoctorShield",
            voice_description="DoctorShield specializes in professional indemnity insurance for medical practitioners. Our tone is clinical, precise, and empathetic, understanding the unique pressures faced by healthcare professionals. We prioritize clear, factual information while maintaining a supportive and understanding demeanor."
        )
    ]

    db.add_all(brands)
    db.commit()
    print(f"Successfully seeded {len(brands)} brands.")

if __name__ == "__main__":
    seed_brands()
