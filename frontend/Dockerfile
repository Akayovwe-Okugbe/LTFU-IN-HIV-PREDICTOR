# =========================================================
# MEDISCOPE React Frontend
#
# Stage 1:
#     Build the Vite/React application.
#
# Stage 2:
#     Serve the generated static files with Nginx.
# =========================================================


# ---------------------------------------------------------
# BUILD STAGE
# ---------------------------------------------------------

FROM node:22-alpine AS build


WORKDIR /app


# ---------------------------------------------------------
# DEPENDENCY INSTALLATION
#
# package*.json allows this to work whether package-lock
# is already present or not.
# ---------------------------------------------------------

COPY frontend/package*.json ./


RUN npm install


# ---------------------------------------------------------
# APPLICATION SOURCE
# ---------------------------------------------------------

COPY frontend/ ./


# ---------------------------------------------------------
# PUBLIC FRONTEND CONFIGURATION
#
# Vite replaces VITE_* values during the build.
# This is not a secret.
# ---------------------------------------------------------

ARG VITE_API_BASE_URL

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}


# ---------------------------------------------------------
# PRODUCTION BUILD
# ---------------------------------------------------------

RUN npm run build


# ---------------------------------------------------------
# NGINX RUNTIME STAGE
# ---------------------------------------------------------

FROM nginx:1.27-alpine


# Remove default static content.
RUN rm -rf /usr/share/nginx/html/*


# Copy the Vite production bundle.
COPY --from=build /app/dist /usr/share/nginx/html


# Replace the default Nginx site configuration.
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf


EXPOSE 80


CMD ["nginx", "-g", "daemon off;"]
