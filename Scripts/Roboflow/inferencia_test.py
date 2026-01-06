#!/usr/bin/env python3
from roboflow import Roboflow

# === Configuración ===
rf = Roboflow(api_key="6CpctoE5C7mQOrwSaDWt")
project = rf.workspace("notengoidea").project("Arcoiris")
model = project.version(1).model

# === Inferencia ===
result = model.predict("foto_prueba.jpg", confidence=40, overlap=30)
result.save("prediccion.jpg")

print("✅ Detección completada. Imagen guardada como prediccion.jpg")
