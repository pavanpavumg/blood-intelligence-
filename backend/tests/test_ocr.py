from app.intelligence.normalizers.unit_converter import UnitConverter
from app.intelligence.medical_ref.reference_engine import MedicalReferenceEngine

def test_unit_converter_name_normalization():
    assert UnitConverter.normalize_name("HbA1c Glycated Hemoglobin") == "HBA1C"
    assert UnitConverter.normalize_name("Fasting Glucose") == "GLUCOSE_FASTING"

def test_glucose_unit_conversion():
    val, unit = UnitConverter.convert_to_standard("GLUCOSE_FASTING", 5.5, "mmol/L")
    assert unit == "mg/dL"
    assert round(val, 1) == 99.1

def test_medical_reference_evaluator():
    engine = MedicalReferenceEngine()
    result = engine.evaluate("HBA1C", 5.8)
    assert result["status"] == "HIGH"
    assert result["flag"] == "ABNORMAL"
