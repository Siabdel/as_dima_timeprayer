# syntax=docker/dockerfile:1
# Image multi-stage du frontend « Prière & Coran ».
#   --target dev  : serveur Vite de développement (utilisateur non root)
#   --target prod : build statique servi par nginx 1.27

# ---------------------------------------------------------------------------
# Stage « dev » : node 22 alpin, Vite en écoute sur 0.0.0.0:5173
# ---------------------------------------------------------------------------
FROM node:22-alpine AS dev

WORKDIR /app

# Installation des dépendances d'abord (meilleur cache de couches Docker)
COPY package.json ./
RUN npm install

# Copie du code, puis passage en utilisateur non root « node »
COPY . .
RUN chown -R node:node /app
USER node

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

# ---------------------------------------------------------------------------
# Stage « build » : génération du bundle statique de production
# ---------------------------------------------------------------------------
FROM node:22-alpine AS build

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .
RUN npm run build

# ---------------------------------------------------------------------------
# Stage « prod » : nginx sert le build et proxifie /api/ vers le backend
# ---------------------------------------------------------------------------
FROM nginx:1.27-alpine AS prod

# Configuration nginx (SPA fallback + proxy /api/ → backend:8000)
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# Fichiers statiques générés par le stage « build »
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
