<template>
  <div class="container">
    <h1>UFROCoin</h1>
    <h2>Módulo 1: Hash Blockchain Test</h2>
    
    <div class="card">
      <p>Simulador de transacciones. Envía un texto al Backend (FastAPI) para generar su Hash seguro (SHA-256) y guardarlo de forma inmutable en MongoDB.</p>
      
      <div class="input-group">
        <input 
          v-model="inputText" 
          type="text" 
          placeholder="Escribe el dato a asegurar..."
          @keyup.enter="generateHash"
        />
        <button @click="generateHash" :disabled="isLoading">
          {{ isLoading ? 'Procesando en Red...' : 'Generar Hash' }}
        </button>
      </div>

      <div v-if="error" class="error-msg">
        ⚠ {{ error }}
      </div>

      <div v-if="result" class="result-box">
        <div class="success-header">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="#42b883"/>
          </svg>
          <h3>{{ result.message }}</h3>
        </div>
        
        <div class="data-row">
          <span class="label">Texto Original:</span>
          <span class="value">{{ result.original }}</span>
        </div>
        <div class="data-row">
          <span class="label">Hash Criptográfico (SHA-256):</span>
          <span class="value hash-text">{{ result.hash }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

// Estados reactivos fundamentales de Vue
const inputText = ref('')
const result = ref(null)
const isLoading = ref(false)
const error = ref(null)

// Vite permite leer variables del sistema prefijadas con VITE_ a través de import.meta.env
// Usamos como fallback localhost:8000 en caso que el entorno falle
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const generateHash = async () => {
  // Validación básica del lado del cliente
  if (!inputText.value.trim()) {
    error.value = "Ingresa un texto válido para continuar."
    return
  }

  // Preparamos entorno de carga
  isLoading.value = true
  error.value = null
  result.value = null

  try {
    // Comunicándose asíncronamente con FastAPI usando fetch API nativo
    const response = await fetch(`${apiUrl}/hash`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ text: inputText.value })
    })

    if (!response.ok) {
      // Intentar leer el mensaje de error de FastAPI (si lo configuró)
      let defaultErr = "Error del servidor."
      try {
        const errData = await response.json()
        defaultErr = errData.detail || defaultErr
      } catch (e) {}
      throw new Error(`Código ${response.status}: ${defaultErr}`)
    }

    // Almacenamos respuesta exitosa para reflejar reactivamente en la UI
    result.value = await response.json()
    inputText.value = '' // Vaciamos por limpieza

  } catch (err) {
    console.error("Fetch Error:", err)
    error.value = err.message
  } finally {
    isLoading.value = false // Finaliza la carga tanto en éxito como fallo
  }
}
</script>

<style>
/* 
   Estilos limpios, sin librerías externas para evitar dependencias innecesarias, 
   aplicando modo oscuro y diseño minimalista
*/
:root {
  font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  color: #e0e0e0;
  background-color: #121212;
}

body {
  margin: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

.container {
  width: 100%;
  max-width: 600px;
  padding: 20px;
  box-sizing: border-box;
  text-align: center;
}

h1 {
  color: #42b883; /* Color temático Vue/Verde */
  margin-bottom: 5px;
  font-size: 2.5em;
}

h2 {
  color: #888;
  font-size: 1.1em;
  margin-top: 0;
  margin-bottom: 30px;
  font-weight: 500;
}

.card {
  background: #1e1e1e;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 8px 16px rgba(0,0,0,0.5);
  border: 1px solid #333;
}

p {
  color: #aaa;
  line-height: 1.5;
  margin-bottom: 20px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-top: 25px;
}

@media (min-width: 480px) {
  .input-group {
    flex-direction: row;
  }
}

input {
  flex: 1;
  padding: 12px 15px;
  border-radius: 8px;
  border: 1px solid #444;
  background: #252525;
  color: #fff;
  font-size: 16px;
  transition: all 0.3s;
}

input:focus {
  outline: none;
  border-color: #42b883;
  box-shadow: 0 0 0 2px rgba(66, 184, 131, 0.2);
}

button {
  padding: 12px 24px;
  border-radius: 8px;
  border: none;
  background: #42b883;
  color: #121212;
  font-weight: bold;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

button:hover:not(:disabled) {
  background: #33a06f;
  transform: translateY(-1px);
}

button:active:not(:disabled) {
  transform: translateY(1px);
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-msg {
  color: #ff6b6b;
  margin-top: 20px;
  padding: 10px;
  background: rgba(255, 107, 107, 0.1);
  border-radius: 6px;
  border-left: 3px solid #ff6b6b;
  font-weight: 500;
}

.result-box {
  margin-top: 30px;
  text-align: left;
  background: #252525;
  padding: 20px;
  border-radius: 10px;
  border: 1px solid #333;
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.success-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
  border-bottom: 1px solid #444;
  padding-bottom: 15px;
}

.success-header h3 {
  margin: 0;
  color: #42b883;
  font-size: 1.1em;
}

.data-row {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
}

.label {
  font-size: 0.85em;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.value {
  color: #e0e0e0;
  font-size: 1em;
}

.hash-text {
  font-family: 'Consolas', 'Courier New', monospace;
  color: #64b5f6;
  word-break: break-all;
  background: #1e1e1e;
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #333;
  margin-top: 5px;
  display: block;
}
</style>
