# Nekazari Module Template

Starter template for building **external modules** for the Nekazari platform.

Modules compile to a single IIFE bundle (`dist/nkz-module.js`) that is uploaded to MinIO and loaded at runtime by the host via `<script>` injection. No build-time coupling to the host.

---

## Quick start

```bash
git clone https://github.com/nkz-os/nkz-module-template.git my-module
cd my-module
npm install
```

Do a **find-and-replace** across the repo for these placeholders:

| Placeholder | Example value | Where |
|-------------|---------------|-------|
| `MODULE_NAME` | `soil-sensor` | package.json, vite.config.ts, k8s/, SQL |
| `MODULE_DISPLAY_NAME` | `Soil Sensor` | App.tsx, k8s/, SQL, manifest.json |
| `MODULE_ROUTE` | `/soil-sensor` | manifest.json, SQL |
| `YOUR_ORG` | `acme-corp` | k8s/backend-deployment.yaml, SQL |

Then update `manifest.json` with your module's metadata.

---

## Structure

```
my-module/
├── src/
│   ├── moduleEntry.ts          # IIFE entry — calls window.__NKZ__.register()
│   ├── slots/index.ts          # Declare which host slots you occupy
│   ├── components/slots/       # Slot React components
│   ├── hooks/                  # Custom hooks
│   ├── services/               # API client
│   └── types/global.d.ts       # Host globals (window.__NKZ__, etc.)
├── backend/                    # FastAPI backend (optional, delete if unused)
├── k8s/
│   ├── backend-deployment.yaml # K8s Deployment + Service for backend
│   └── registration.sql        # Insert/update marketplace_modules
├── manifest.json               # Module metadata
├── vite.config.ts              # Uses @nekazari/module-builder preset
└── dist/nkz-module.js          # Build output — upload this to MinIO
```

---

## Build

```bash
npm run build:module
# → dist/nkz-module.js  (~50–300 KB depending on your dependencies)
```

The `@nekazari/module-builder` preset enforces:
- **IIFE format** — single self-executing bundle
- **Classic JSX runtime** — `React.createElement()`, not `_jsx()` (required for UMD React global)
- **Externalized dependencies** — React, ReactDOM, react-router-dom, @nekazari/sdk, @nekazari/ui-kit are mapped to window globals provided by the host. Never bundle them.

---

## Deploy

### 1. Upload bundle to MinIO

```bash
# From the server (port-forward MinIO first):
sudo kubectl port-forward -n nekazari svc/minio-service 9000:9000 &
mc alias set minio http://localhost:9000 minioadmin minioadmin
mc cp dist/nkz-module.js minio/nekazari-frontend/modules/MODULE_NAME/nkz-module.js \
   --attr "Content-Type=application/javascript"
```

Never write directly to MinIO's `/data/` filesystem — use the S3 API.

### 2. Register in the database

```bash
# Run registration.sql once per environment:
kubectl exec -n nekazari deployment/postgresql -- \
  psql -U postgres -d nekazari -f /tmp/registration.sql
```

Or insert manually and update `remote_entry_url = '/modules/MODULE_NAME/nkz-module.js'`.

### 3. Deploy backend (if your module has one)

```bash
docker build -t ghcr.io/YOUR_ORG/MODULE_NAME-backend:v1.0.0 ./backend
docker push ghcr.io/YOUR_ORG/MODULE_NAME-backend:v1.0.0
kubectl apply -f k8s/backend-deployment.yaml -n nekazari
```

Add an ingress rule routing `/api/MODULE_NAME` → `MODULE_NAME-api-service:8000` before the generic `/api` catch-all.

---

## Slots

Edit `src/slots/index.ts` to register your components in host slots:

| Slot | Where it renders |
|------|-----------------|
| `context-panel` | Side panel when an entity is selected |
| `bottom-panel` | Tabbed panel at the bottom of the viewer |
| `map-layer` | Overlay or toolbar button on the 3D map |
| `layer-toggle` | Toggle entry in the layer panel |
| `entity-tree` | Context menu in the entity tree |
| `dashboard-widget` | Card in the tenant dashboard |

---

## Build rules (critical)

- **JSX runtime must be `classic`** — `tsconfig.json` has `"jsx": "react"` and vite preset uses `jsxRuntime: 'classic'`. The automatic runtime emits `_jsx()` which doesn't exist on the UMD `window.React` global.
- **Never bundle externalized deps** — React, ReactDOM, react-router-dom, @nekazari/sdk, @nekazari/ui-kit. They come from the host. Bundling them creates two React instances and breaks hooks.
- **Web workers must use `?worker&inline`** — e.g. `import MyWorker from './worker?worker&inline'`. Without `&inline`, Vite generates a separate file with an absolute path that breaks when loaded from MinIO.
- **No Module Federation** — the host uses IIFE-only loading. `@originjs/vite-plugin-federation` is dead, do not use it.

---

## Local development

```bash
npm run dev
# Starts a Vite dev server at http://localhost:5003
# Full integration (slots, auth) requires the host app.
# Set VITE_PROXY_TARGET=https://your-api-domain in .env to proxy API calls.
```

Copy `env.example` to `.env` and fill in your values.

---

## DataHub compatibility

If your module collects timeseries data, the DataHub module can visualise it in a Data Canvas without extra frontend work.

- **Data in platform TimescaleDB**: nothing needed — DataHub finds it automatically.
- **Data in an external system**: implement a `GET /api/timeseries/entities/{id}/data` endpoint returning **Apache Arrow IPC** (`float64` epoch seconds, `float64` value), declare `source` in the NGSI-LD entity attribute, and set `TIMESERIES_ADAPTER_<SOURCE>_URL` in the DataHub BFF.

Full contract: [ADAPTER_SPEC.md](https://github.com/nkz-os/nkz-module-data-hub/blob/main/ADAPTER_SPEC.md)

---

## License

AGPL-3.0
