FROM node:20-alpine

# El directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos primero el package.json para aprovechar la caché de capas de Docker
COPY package*.json ./

# Instalamos dependencias
RUN npm install

# Exponemos el puerto por defecto de Vite
EXPOSE 5173

# CMD por defecto. El --host es CRUCIAL en docker para exponer la red a la máquina host.
CMD ["npm", "run", "dev", "--", "--host"]
