# Design: /create_new_product — Panama Hats Page

**Date:** 2026-05-12  
**Approach:** Duplication (Approach 1) — no changes to existing working code

## Overview

A new tab `/create_new_product` identical in functionality to `/create_product` but configured for two panama hat products instead of five clothing items. Uses a dedicated backend endpoint `/api/products/generate_panama`.

## Frontend

### New files

**`frontend/src/components/CreateProductPanama.vue`**  
Full copy of `CreateProduct.vue` with the following changes:
- `images` array contains exactly 2 items:
  - `{src: "panama.png", bigSrc: "panama_big.png"}`
  - `{src: "panama-unrolled.png", bigSrc: "panama-unrolled_big.png"}`
- `imagesTextCoordinates`: default starting coordinates for panama hats (e.g. `[{x: 185, y: 600}, {x: 185, y: 600}]`) — adjustable via drag in the modal editor
- `imagesFontSizes`: `[32, 32]`
- API call in `generateFile()` targets `/api/products/generate_panama` instead of `/api/products/generate`
- `recalculateAllTextX` — product-specific x-offsets for hoodie/tshirt-basic/tshirt-trueover are removed; panama hats use no offset (or a new offset once determined)

**`frontend/src/views/CreateNewProductView.vue`**  
Wrapper identical to `CreateProductView.vue` but imports and renders `CreateProductPanama`.

### Modified files

**`frontend/src/router/index.js`**  
New route added:
```js
{
  path: '/create_new_product',
  name: 'newProductCreation',
  component: CreateNewProductView
}
```

## Backend

### Modified files

**`products/products.py`**  
New Celery task `generate_product_xlsx_panama`:
- Identical to `generate_product_xlsx` 
- Does NOT call `add_additional_products` (that function adds `tshirt-trueover100` which is irrelevant for panama hats)

**`products/routes.py`**  
New route:
```python
@products_bp.route("/generate_panama", methods=["POST"])
@products_bp.arguments(ImageRequestSchema(many=True))
def generate_images_panama(data):
    generate_product_xlsx_panama.apply_async(args=[data], queue="email")
    return jsonify({"message": "process started"})
```

## Out of Scope

- Backend product images (`products/initial_images/panama_1/` and `products/initial_images/panama_2/` with color `.jpg` variants) — to be added manually as colors are finalized
- Google Sheets template row range for panama hats — to be configured separately
- Navigation link to the new page from UI (not requested)

## Success Criteria

- `/create_new_product` renders the same UI as `/create_product` with two panama hat images
- Modal editor opens for each panama hat image with drag-to-position text
- "Сгенерировать файл" POSTs to `/api/products/generate_panama`
- Backend accepts the request, queues the Celery task, returns `{"message": "process started"}`
- Existing `/create_product` page is unaffected
