Abajo tienes un **guion 100% por terminal (curl)** para demoear el flujo completo del MVP **sin UI**:

* Crear campaña
* Listar campañas
* Generar 3 variantes (prompt natural → OpenAI)
* Ver campaign detail (con variants)
* Publicar 1 variante (Facebook Page)
* Refrescar métricas
* (Opcional) forzar métricas “mock” para garantizar duplicar/kill en demo
* Ejecutar Darwin
* Ver resultados + logs / overview

> Asumo servidor en `http://127.0.0.1:8000`. Cambia `BASE_URL` si aplica.

---

## 0) Variables base

```bash
export BASE_URL="http://127.0.0.1:8000"
```

---

## 1) Healthcheck

```bash
curl -s "$BASE_URL/health" | jq
```

---

## 2) Crear una Campaign (contexto fijo)

```bash
CAMPAIGN_ID=$(
  curl -s -X POST "$BASE_URL/campaigns" \
    -H "Content-Type: application/json" \
    -d '{
      "name": "Promo Hamburguesa Cali",
      "channel": "facebook_page",
      "country": "CO",
      "product": { "name": "Hamburguesa Doble", "price_cop": 22000 },
      "objective": "engagement",
      "status": "active"
    }' | jq -r '.id'
)

echo "CAMPAIGN_ID=$CAMPAIGN_ID"
```

---

## 3) Listar campañas

```bash
curl -s "$BASE_URL/campaigns" | jq
```

---

## 4) Generar Variants (prompt natural → OpenAI → 3 drafts en DB)

```bash
curl -s -X POST "$BASE_URL/campaigns/$CAMPAIGN_ID/variants/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_prompt": "Quiero promocionar mi hamburguesa doble en Cali con una promo 2x1 solo por hoy. Tono cercano, directo, con llamado a WhatsApp."
  }' | jq
```

Guarda 1 `VARIANT_ID` (de los 3) para publicar:

```bash
VARIANT_ID=$(
  curl -s "$BASE_URL/campaigns/$CAMPAIGN_ID" | jq -r '.variants[0].id'
)
echo "VARIANT_ID=$VARIANT_ID"
```

---

## 5) Ver detalle de campaña (campaign + variants + latest_metric)

```bash
curl -s "$BASE_URL/campaigns/$CAMPAIGN_ID" | jq
```

---

## 6) Publicar una Variant (Facebook Page)

```bash
curl -s -X POST "$BASE_URL/variants/$VARIANT_ID/publish" | jq
```

Tip: si quieres mostrar rápido el link del post (si está disponible):

```bash
curl -s "$BASE_URL/campaigns/$CAMPAIGN_ID" | jq -r '.variants[] | select(.id=="'"$VARIANT_ID"'") | .external.post_url'
```

---

## 7) Refrescar métricas (crea snapshot en `variant_metrics` + fitness)

```bash
curl -s -X POST "$BASE_URL/variants/$VARIANT_ID/metrics/refresh" | jq
```

Repite si quieres mostrar que “cada refresh agrega una fila” (IDs distintos):

```bash
curl -s -X POST "$BASE_URL/variants/$VARIANT_ID/metrics/refresh" | jq
```

---

# 8) Ejecutar Darwin (modo real)

Esto toma todas las variants `published`, lee su última métrica y decide duplicate/kill/skip.

```bash
curl -s -X POST "$BASE_URL/darwin/run" \
  -H "Content-Type: application/json" \
  -d '{
    "threshold_up": 5,
    "threshold_down": -3,
    "dry_run": false,
    "delete_remote_post": true
  }' | jq
```

Luego mira la campaña para ver:

* nuevas variantes hijas `draft` (si duplicó)
* variantes `killed` (si eliminó)

```bash
curl -s "$BASE_URL/campaigns/$CAMPAIGN_ID" | jq
```

---

# 9) Mostrar overview de métricas generales (lo que espera tu frontend)

```bash
curl -s "$BASE_URL/metrics/overview" | jq
```

---

# 10) (MUY recomendado para demo) Garantizar duplicar/kill aunque no haya likes reales

En vivo puede que no alcances `fitness >= 5` o `<= -3` con métricas reales. Para demo, usa un “modo controlado”.

### Opción A: Si ya tienes `POST /variants/{id}/metrics/mock`

Si lo implementaste, úsalo así (ejemplo para forzar DUPLICATE):

```bash
curl -s -X POST "$BASE_URL/variants/$VARIANT_ID/metrics/mock" \
  -H "Content-Type: application/json" \
  -d '{"likes":10,"comments":2,"shares":2,"clicks":0}' | jq
```

Y para forzar KILL en otra variante (ejemplo, toma otra id):

```bash
OTHER_VARIANT_ID=$(curl -s "$BASE_URL/campaigns/$CAMPAIGN_ID" | jq -r '.variants[1].id')
curl -s -X POST "$BASE_URL/variants/$OTHER_VARIANT_ID/publish" | jq >/dev/null

curl -s -X POST "$BASE_URL/variants/$OTHER_VARIANT_ID/metrics/mock" \
  -H "Content-Type: application/json" \
  -d '{"likes":0,"comments":0,"shares":0,"clicks":0}' | jq
```

Luego:

```bash
curl -s -X POST "$BASE_URL/darwin/run" \
  -H "Content-Type: application/json" \
  -d '{"threshold_up":5,"threshold_down":-3,"dry_run":false,"delete_remote_post":true}' | jq
```

### Opción B (si NO tienes metrics/mock): fuerza `dry_run` y explica

Si no quieres tocar nada más, puedes demoear la lógica con `dry_run=true`:

```bash
curl -s -X POST "$BASE_URL/darwin/run" \
  -H "Content-Type: application/json" \
  -d '{"threshold_up":5,"threshold_down":-3,"dry_run":true,"delete_remote_post":true}' | jq
```

---

# 11) (Opcional) Control del scheduler desde API (si ya lo montaste)

Ver config:

```bash
curl -s "$BASE_URL/scheduler/config" | jq
```

Cambiar a 60s y activar:

```bash
curl -s -X PUT "$BASE_URL/scheduler/config" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "interval_seconds": 60}' | jq
```

Run inmediato (refresh metrics + darwin en un solo llamado):

```bash
curl -s -X POST "$BASE_URL/scheduler/run-now" \
  -H "Content-Type: application/json" \
  -d '{"threshold_up":5,"threshold_down":-3,"dry_run":false,"delete_remote_post":true}' | jq
```

---

## Script “todo en uno” (si quieres copiar y correr de una)

Si te sirve, te lo empaqueto en un `demo.sh` con checks y prints bonitos.

Dime si tu backend **sí tiene** `POST /variants/{id}/metrics/mock`; si no lo tienes aún, te lo paso en 10-15 líneas para que el demo sea infalible.
