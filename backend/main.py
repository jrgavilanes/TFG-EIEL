from fastapi import FastAPI

# Crea una instancia de la aplicación FastAPI
app = FastAPI()

# Define una ruta raíz que responde con un mensaje
@app.get("/")
def read_root():
    return {"message": "¡Hola, mundo!"}

# Define una ruta que recibe un parámetro y lo devuelve
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

# Ejecuta el servidor solo si este archivo se ejecuta directamente
if __name__ == "__main__":
    import uvicorn

    # Inicia el servidor con Uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)