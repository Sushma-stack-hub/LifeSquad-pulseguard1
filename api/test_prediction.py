
import sys
import os

# Add the current directory to path so we can import utils
sys.path.append(os.getcwd())

try:
    from utils.ml_engine import predict_hypertension
    
    print("Successfully imported predict_hypertension")

    dummy_data = {
        "age": 45,
        "gender": 1,
        "bmi": 28.5,
        "systolic_bp": 145,
        "diastolic_bp": 92,
        "heart_rate": 78,
        "cholesterol": 220,
        "glucose": 100,
        "smoking": 0,
        "alcohol": 1,
        "physical_activity": 3,
        "stress_level": 7
    }

    print("Running prediction...")
    result = predict_hypertension(dummy_data)
    print("Prediction Result:", result)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
