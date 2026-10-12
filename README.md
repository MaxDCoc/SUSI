# SUSI

Sistema Universitario de Sustentabilidad Integral: plataforma para sistematizar prácticas sostenibles en la UTN
(práctica → indicador → medición → evidencia → validación → tablero), con medición del propio software (SCI).

- Diseño: [`docs/superpowers/specs/2026-10-12-susi-mvp-design.md`](docs/superpowers/specs/2026-10-12-susi-mvp-design.md)
- Guion de la demo: [`docs/demo-runbook.md`](docs/demo-runbook.md)

## Levantarlo con Docker (recomendado)

```bash
cp .env.example .env   # completar POSTGRES_PASSWORD, DJANGO_SECRET_KEY y SUSI_DEMO_PASSWORD
docker compose up --build -d
docker compose exec app python manage.py seed_demo
```

Abrir http://localhost:8000. Usuarios de demo: `admin.demo`, `responsable.demo`, `validador.demo`
(contraseña: la de `SUSI_DEMO_PASSWORD`).

## Publicarlo en internet (gratis)

Guía paso a paso con Render + Supabase + UptimeRobot, para que los usuarios solo abran una URL:
[`docs/deploy-render-supabase.md`](docs/deploy-render-supabase.md). El Blueprint está en [`render.yaml`](render.yaml).

## Desarrollo

```bash
# Backend (desde backend/, con el entorno virtual activado)
pip install -r requirements-dev.txt
python manage.py migrate && python manage.py seed_demo   # requiere SUSI_DEMO_PASSWORD en el entorno
python manage.py runserver
python -m pytest

# Frontend (desde frontend/, en otra terminal)
npm install && npm run dev      # http://localhost:5173 (proxy a :8000)
npm test
```
