# /create_new_product — Panama Hats Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/create_new_product` page identical to `/create_product` but configured for two panama hat products, with a dedicated `/api/products/generate_panama` backend endpoint.

**Architecture:** Duplicate-and-configure approach — `CreateProduct.vue` is copied as `CreateProductPanama.vue` with panama-specific images and endpoint, no changes to existing working code. A matching Celery task skips the `tshirt-trueover100` duplication step irrelevant for panama hats.

**Tech Stack:** Vue 3, Vue Router, Flask, Flask-Smorest, Celery, marshmallow

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `frontend/src/components/CreateProductPanama.vue` | UI component for panama hat product creation |
| Create | `frontend/src/views/CreateNewProductView.vue` | Route-level wrapper for `CreateProductPanama` |
| Modify | `frontend/src/router/index.js` | Register `/create_new_product` route |
| Modify | `products/products.py` | Add `generate_product_xlsx_panama` Celery task |
| Modify | `products/routes.py` | Add `POST /generate_panama` route |

---

## Task 1: Create `CreateProductPanama.vue`

**Files:**
- Create: `frontend/src/components/CreateProductPanama.vue`

- [ ] **Step 1: Create the file as a full copy of `CreateProduct.vue` with panama-specific changes**

Create `frontend/src/components/CreateProductPanama.vue` with the following complete content:

```vue
<template>
  <div>
    <nav class="navbar">
      <h1 class="logo__text">Onephrase.tech</h1>
      <router-link to="/files" class="nav-link">Файлы</router-link>
    </nav>
    <div class="main__content">
      <div class="container__reset">
        <button class="button__reset" @click="resetForm">Сбросить</button>
      </div>
      <div class="container__title">
        <h1 class="title">>><br>Создать новый товар</h1>
      </div>
      <div class="container__input_phrase">
        <h4 class="input__phrase__name">введите фразу</h4>
        <textarea class='input__phrase' v-model="phrase" placeholder="Введите фразу"
                  @blur="recalculateAllTextX"></textarea></div>
      <div class="container__input_phrase">
        <h4 class="input__phrase__name">введите номер дизайна</h4>
        <input class="input__phrase" type="text" v-model="designNumber"
               placeholder="введите номер дизайна">
      </div>
      <div class="container__input_phrase">
        <h4 class="input__phrase__name">введите категории</h4>
        <input class="input__category" type="text" v-model="categories[0]" placeholder="категория">
        <input class="input__category" type="text" v-model="categories[1]" placeholder="категория">

      </div>
      <div class="container__input_phrase">
        <h4 class="input__phrase__name">Введите description_id</h4>
        <input class="input__phrase" type="number" v-model.number="description_id"
               placeholder="description_id">
      </div>
      <div class="components">
        <div v-for="(item, index) in images" :key="index" class="img__button">
          <img class="component_image" :src="item.src" alt="">
          <button class="button__change" @click="openModal(index)">изменить</button>
        </div>
      </div>
      <div class="getfile__container">
        <p class="phrase__counter">количество фраз ({{ phraseCount }})</p>
        <button class="button_bottom" @click="addPhrase">Добавить ещё фразу</button>
        <button class="button_bottom" @click="generateFile">Сгенерировать файл</button>
      </div>
    </div>

    <!-- Модальное окно -->
    <div v-if="isModalOpen" class="modal">
      <div class="modal__content">
        <span class="close" @click="closeModal">&times;</span>
        <canvas ref="canvas" class="modal__canvas"></canvas>
        <!-- Редактируемый текст -->
        <div :style="{
          transform: 'scale(0.5)',
          transformOrigin: 'top left',
          position: 'absolute',
          left: textX * 0.5 + 'px',
          top: textY * 0.5 + 'px'
        }">
          <div v-if="isModalOpen" ref="editableText" class="editable-text" :style="{
                      fontSize: fontSize + 'px'
                  }" contenteditable="true" @mousedown="startDragging" @input="updateText"
               @keydown="handleKeyDown"
               @blur="saveText">
            {{ phrase }}
          </div>
        </div>
        <div class="font-size-controls">
          <button @click="decreaseFontSize">Уменьшить шрифт</button>
          <span class="fontDisplay">Размер шрифта: {{ fontSize }}px</span>
          <button @click="increaseFontSize">Увеличить шрифт</button>
        </div>
      </div>
      <div class="modal__backdrop" @click="closeModal"></div>
    </div>
  </div>
</template>


<script>
import html2canvas from 'html2canvas';

export default {
  data() {
    return {
      phrase: "",
      designNumber: "",
      categories: ["", ""],
      phraseCount: 0,
      phrasesDataList: [],
      images: [
        {src: "panama_1.png", bigSrc: "panama_1_big.png"},
        {src: "panama_2.png", bigSrc: "panama_2_big.png"},
      ],
      imagesTextCoordinates: [
        {x: 185, y: 600},
        {x: 185, y: 600},
      ],
      imagesFontSizes: [32, 32],
      selectedImageIndex: null,
      isModalOpen: false,
      selectedImage: "",
      textX: 185,
      textY: 600,
      isDragging: false,
      canvas: null,
      ctx: null,
      dragOffsetX: 0,
      dragOffsetY: 0,
      backgroundImage: null,
      fontSize: 32,
      currentEditingPhraseIndex: null,
      description_id: ""
    };
  },
  methods: {
    fixCoordinates(coordinates) {
      return {
        x: coordinates.x - 30,
        y: coordinates.y - 30
      };
    },
    createCurrentPhraseData() {
      const coords = JSON.parse(JSON.stringify(this.imagesTextCoordinates))
      const data = {
        items: this.images.map((image, index) => ({
          product: image.src,
          coordinates: this.fixCoordinates(coords[index]),
          fontSize: this.imagesFontSizes[index],
          textWidth: this.measureTextWidth(this.phrase, this.imagesFontSizes[index]),
        })),
        category_1: this.categories[0],
        category_2: this.categories[1],
        design_number: this.designNumber,
        text: this.phrase,
        description_id: this.description_id.toString()
      };
      return JSON.parse(JSON.stringify(data))
    },
    isDuplicate(data) {
      return this.phrasesDataList.some(
        item => JSON.stringify(item) === JSON.stringify(data)
      );
    },
    async generateFile() {
      if (this.phrase.trim()) {
        const currentPhraseData = this.createCurrentPhraseData();
        if (!this.isDuplicate(currentPhraseData)) {
          this.phrasesDataList.push(currentPhraseData);
        }
      }

      await this.generateTextImagesForPhrases();

      fetch('/api/products/generate_panama', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(this.phrasesDataList),
      })
        .then(response => {
          if (!response.ok) {
            throw new Error('Ошибка при генерации файла');
          }
          return response.json();
        })
        .then(data => {
          console.log("Ответ от сервера:", data);
          alert(data.message || "Процесс начат");
        })
        .catch(error => {
          console.error("Ошибка при отправке данных:", error);
          alert("Ошибка при генерации файла");
        });
    },
    updateText(e) {
      this.phrase = e.target.innerHTML;
      this.$nextTick(() => {
        this.imagesTextCoordinates = this.imagesTextCoordinates.map(coord => ({
          ...coord,
        }));
      });
    },
    measureTextWidth(text, fontSize, fontFamily = 'OnePhraseFont') {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      ctx.font = `${fontSize}px ${fontFamily}`;

      const lines = text
        .replace(/<br\s*\/?>/gi, '\n')
        .split('\n');

      let maxWidth = 0;
      for (const line of lines) {
        const lineWidth = ctx.measureText(line).width;
        if (lineWidth > maxWidth) maxWidth = lineWidth;
      }

      return maxWidth;
    },
    recalculateAllTextX() {
      this.imagesTextCoordinates = this.imagesFontSizes.map((fontSize, index) => {
        const width = this.measureTextWidth(this.phrase, fontSize);
        const newX = (1200 - width) / 2;

        return {
          ...this.imagesTextCoordinates[index],
          x: newX
        };
      });
    },
    handleKeyDown(e) {
      if (e.key === 'Enter') {
        e.preventDefault();

        const selection = window.getSelection();
        if (!selection.rangeCount) return;

        const range = selection.getRangeAt(0);
        range.deleteContents();

        const textNode = document.createTextNode('\n');
        range.insertNode(textNode);

        range.setStartAfter(textNode);
        range.setEndAfter(textNode);
        selection.removeAllRanges();
        selection.addRange(range);
      }
    },
    saveText() {
      this.text = this.$refs.editable ? this.$refs.editable.innerText : this.phrase;
      this.edit = false;
    },
    decreaseFontSize() {
      if (this.imagesFontSizes[this.selectedImageIndex] > 2) {
        this.imagesFontSizes[this.selectedImageIndex] -= 2;
        this.fontSize = this.imagesFontSizes[this.selectedImageIndex];
      }
    },
    increaseFontSize() {
      this.imagesFontSizes[this.selectedImageIndex] += 2;
      this.fontSize = this.imagesFontSizes[this.selectedImageIndex];
    },
    resetForm() {
      this.phrase = "";
      this.designNumber = "";
      this.categories = ["", ""];
      this.phraseCount = 0;
      this.phrasesDataList = [];
      this.description_id = "";
    },
    addPhrase() {
      const currentPhraseData = this.createCurrentPhraseData();
      const snapshot = JSON.parse(JSON.stringify(currentPhraseData));

      if (!this.isDuplicate(snapshot)) {
        this.phrasesDataList.push(snapshot);
        this.currentEditingPhraseIndex = this.phrasesDataList.length - 1;
      }

      this.phraseCount = this.phrasesDataList.length;
      this.phrase = "";
      this.designNumber = "";
      this.categories = ["", ""];
      this.description_id = "";
    },
    openModal(index) {
      this.selectedImageIndex = index;
      this.selectedImage = this.images[index].bigSrc;
      this.isModalOpen = true;
      document.body.style.overflow = "hidden";
      this.$nextTick(() => {
        this.canvas = this.$refs.canvas;
        if (this.canvas) {
          this.ctx = this.canvas.getContext("2d");
          this.loadImageAndDraw();
        }
      });

      this.fontSize = this.imagesFontSizes[this.selectedImageIndex];
    },
    loadImageAndDraw() {
      const img = new Image();
      img.onload = () => {
        this.canvas.width = img.width * 0.5;
        this.canvas.height = img.height * 0.5;

        this.backgroundImage = img;

        this.ctx.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);

        const savedCoordinates = this.imagesTextCoordinates[this.selectedImageIndex];
        this.textX = savedCoordinates.x;
        this.textY = savedCoordinates.y;

        this.ctx.font = `${this.fontSize}px AvantGardeC`;
        this.ctx.fillStyle = "white";
      };
      img.src = this.selectedImage;
    },
    async generateTextImagesForPhrases() {
      const tempDiv = document.createElement('div');
      tempDiv.style.position = 'absolute';
      tempDiv.style.left = '-9999px';
      tempDiv.style.top = '0';
      tempDiv.style.width = '600px';
      tempDiv.style.display = 'flex';
      tempDiv.style.justifyContent = 'left';
      tempDiv.style.alignItems = 'center';
      tempDiv.style.textAlign = 'center';
      tempDiv.style.height = 'auto';
      tempDiv.style.padding = '0';
      tempDiv.style.margin = '0';
      tempDiv.style.backgroundColor = 'transparent';
      tempDiv.style.fontFamily = 'OnePhraseFont';
      tempDiv.style.whiteSpace = 'pre-wrap';
      tempDiv.style.lineHeight = '110%';
      tempDiv.style.letterSpacing = '0.7px';
      document.body.appendChild(tempDiv);

      for (const phraseData of this.phrasesDataList) {
        for (const item of phraseData.items) {
          tempDiv.style.fontSize = `${item.fontSize}px`;
          tempDiv.innerText = phraseData.text;
          tempDiv.style.color = 'white';
          const canvasWhite = await html2canvas(tempDiv, {
            backgroundColor: null,
            scale: 2,
            useCORS: true
          });
          item.text_image_white = canvasWhite.toDataURL('image/png');
          tempDiv.style.color = '#222222';
          const canvasBlack = await html2canvas(tempDiv, {
            backgroundColor: null,
            scale: 2,
            useCORS: true
          });
          item.text_image_black = canvasBlack.toDataURL('image/png');
          tempDiv.style.color = '#80081B';
          const canvasRed = await html2canvas(tempDiv, {
            backgroundColor: null,
            scale: 2,
            useCORS: true
          });
          item.text_image_red = canvasRed.toDataURL('image/png');
          tempDiv.style.color = '#10366C';
          const canvasNavy = await html2canvas(tempDiv, {
            backgroundColor: null,
            scale: 2,
            useCORS: true
          });
          item.text_image_navy = canvasNavy.toDataURL('image/png');
        }
      }

      document.body.removeChild(tempDiv);
    },
    closeModal() {
      this.isModalOpen = false;
      document.body.style.overflow = "";
    },
    startDragging(e) {
      this.isDragging = true;
      const rect = this.canvas.getBoundingClientRect();
      const scale = 0.5;
      this.dragOffsetX = (e.clientX - rect.left) / scale - this.textX;
      this.dragOffsetY = (e.clientY - rect.top) / scale - this.textY;

      document.addEventListener("mousemove", this.dragText);
      document.addEventListener("mouseup", this.stopDragging);
    },
    dragText(e) {
      if (!this.isDragging || !this.canvas || !this.backgroundImage) return;

      const rect = this.canvas.getBoundingClientRect();
      const scale = 0.5;

      let newX = (e.clientX - rect.left) / scale - this.dragOffsetX;
      let newY = (e.clientY - rect.top) / scale - this.dragOffsetY;

      this.textX = newX;
      this.textY = newY;

      this.imagesTextCoordinates[this.selectedImageIndex] = {x: this.textX, y: this.textY};
    },
    stopDragging() {
      this.isDragging = false;
      document.removeEventListener("mousemove", this.dragText);
      document.removeEventListener("mouseup", this.stopDragging);
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.canvas = this.$refs.canvas;
      if (this.canvas) {
        this.ctx = this.canvas.getContext("2d");
      }
    });
  },
};

</script>

<style scoped>
@import '@/assets/styles.css';

@font-face {
  font-family: 'OnePhraseFont';
  src: url('@/assets/fonts/AvantGardeC_regular.otf') format('opentype');
  font-weight: normal;
  font-style: normal;
  font-display: swap;
}

.modal__backdrop {
  position: absolute;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  top: 0;
  left: 0;
  z-index: 1;
  pointer-events: auto;
}

.modal__content {
  position: absolute;
  background-color: white;
  border: 1px solid black;
  z-index: 2;
  padding: 30px 30px 35px 30px;
  border-radius: 8px;
}

.modal__canvas {
  display: block;
  border: 1px solid #000000;
  padding: 0;
  margin: 0;
}

.modal {
  display: flex;
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: transparent;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 20px;
  gap: 10px;
  z-index: 1000;
}

.editable-text {
  position: absolute;
  cursor: move;
  user-select: none;
  background-color: transparent;
  border: none;
  outline: none;
  color: white;
  text-align: center;
  font-family: "OnePhraseFont", "Century Gothic", CenturyGothic, AppleGothic, sans-serif;
  font-size: 32px;
  font-style: normal;
  font-weight: 400;
  line-height: 110%;
  letter-spacing: 0.7px;
  cursor: move;
  user-select: none;
  background-color: transparent;
  border: none;
  outline: none;
  white-space: pre;
}

.close {
  font-size: 16px;
  color: #333;
  background-color: #f2f2f2;
  border: none;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  top: 5px;
  left: 5px;
  position: absolute;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: background-color 0.2s ease, transform 0.2s ease;
  cursor: pointer;
}

.close:hover {
  background-color: #ddd;
  transform: scale(1.1);
}

.font-size-controls {
  padding-top: 5px;
  display: flex;
  gap: 5px;
  position: absolute;
  left: 80px;
  z-index: 5;
}

.fontDisplay {
  color: black;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/CreateProductPanama.vue
git commit -m "feat: add CreateProductPanama component for panama hat products"
```

---

## Task 2: Create `CreateNewProductView.vue`

**Files:**
- Create: `frontend/src/views/CreateNewProductView.vue`

- [ ] **Step 1: Create the view wrapper**

Create `frontend/src/views/CreateNewProductView.vue`:

```vue
<template>
    <CreateProductPanama />
  </template>
  
  <script>
  import CreateProductPanama from "@/components/CreateProductPanama.vue";
  
  export default {
    components: { CreateProductPanama },
  };
  </script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/CreateNewProductView.vue
git commit -m "feat: add CreateNewProductView wrapper"
```

---

## Task 3: Register `/create_new_product` route

**Files:**
- Modify: `frontend/src/router/index.js`

- [ ] **Step 1: Add import and route**

In `frontend/src/router/index.js`, add the import after the existing imports:

```js
import CreateNewProductView from "../views/CreateNewProductView.vue"
```

Then add the route inside the `routes` array (after the `/create_product` entry):

```js
{
  path: '/create_new_product',
  name: 'newProductCreation',
  component: CreateNewProductView
},
```

The full file after changes:

```js
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import TextOnImageView from "../views/TextOnImageView.vue"
import GoodsView from "../views/GoodsView.vue"
import CreateProductView from "../views/CreateProductView.vue"
import DownloadFilesView from "../views/DownloadFilesView.vue"
import CreateNewProductView from "../views/CreateNewProductView.vue"




const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
    {
      path: '/images',
      name: 'images',
      component: TextOnImageView,
    },
    {
      path: '/dev',
      name: 'goods',
      component: GoodsView
    },
    {
      path: '/create_product',
      name: 'productCreation',
      component: CreateProductView
    },
    {
      path: '/create_new_product',
      name: 'newProductCreation',
      component: CreateNewProductView
    },
    {
      path: '/files',
      name: 'downloadFiles',
      component: DownloadFilesView
    }
  ],
})


export default router
```

- [ ] **Step 2: Verify the dev server starts without errors**

```bash
cd frontend && npm run dev
```

Expected: server starts, no compilation errors in console.

Open `http://localhost:8080/create_new_product` in the browser. Expected: page renders with two panama hat images and all form fields.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/router/index.js
git commit -m "feat: register /create_new_product route"
```

---

## Task 4: Add `generate_product_xlsx_panama` Celery task

**Files:**
- Modify: `products/products.py`

- [ ] **Step 1: Add the new Celery task at the end of `products/products.py`**

Append the following after the existing `generate_product_xlsx` function (after line 305):

```python
@celery.task()
def generate_product_xlsx_panama(items):
    rows = []
    for i, data in enumerate(items):
        product_data = generate_images(data)
        product = Products(product_data)
        new_rows = product.generate_xlsx(i)
        rows = rows + new_rows
    generate_csv(rows)
    log.info("Panama products file generated successfully")
    return 200, "Panama products file generated successfully"
```

Note: unlike `generate_product_xlsx`, this task does NOT call `add_additional_products` — that function adds `tshirt-trueover100` which is specific to the clothing line and irrelevant for panama hats.

- [ ] **Step 2: Commit**

```bash
git add products/products.py
git commit -m "feat: add generate_product_xlsx_panama Celery task"
```

---

## Task 5: Add `POST /generate_panama` route

**Files:**
- Modify: `products/routes.py`

- [ ] **Step 1: Add the import for the new task**

In `products/routes.py`, update the import line:

```python
from .products import generate_product_xlsx, generate_product_xlsx_panama
```

- [ ] **Step 2: Add the new route**

Append after the existing `/generate` route handler:

```python
@products_bp.route("/generate_panama", methods=["POST"])
@products_bp.arguments(ImageRequestSchema(many=True))
def generate_images_panama(data):
    generate_product_xlsx_panama.apply_async(args=[data], queue="email")
    return jsonify({"message": "process started"})
```

- [ ] **Step 3: Commit**

```bash
git add products/routes.py
git commit -m "feat: add POST /api/products/generate_panama route"
```

---

## Task 6: End-to-end verification

- [ ] **Step 1: Start the dev stack**

```bash
docker-compose -f dc_develop.yml up --build
```

Or locally:
```bash
# Terminal 1: Redis + DB
docker-compose up redis db

# Terminal 2: Flask backend
export $(grep -v '^#' dev.env | xargs) && python wsgi.py

# Terminal 3: Celery worker
export $(grep -v '^#' dev.env | xargs) && celery -A celery_settings.celery worker -n worker1 -Q email

# Terminal 4: Frontend
export $(grep -v '^#' dev.env | xargs) && cd frontend && npm run dev
```

- [ ] **Step 2: Verify the new page renders**

Open `http://localhost:8080/create_new_product`.

Expected:
- Page renders with the same layout as `/create_product`
- Two images shown: `panama_1.png` and `panama_2.png`
- Form fields present: phrase textarea, design number, categories, description_id
- "Сбросить", "Добавить ещё фразу", "Сгенерировать файл" buttons present

- [ ] **Step 3: Verify the modal editor works**

Click "изменить" on either panama image.

Expected:
- Modal opens with the panama image rendered on canvas
- Phrase text is draggable
- Font size controls work (increase/decrease)
- Close button works

- [ ] **Step 4: Verify the original `/create_product` is unaffected**

Open `http://localhost:8080/create_product`.

Expected: page renders exactly as before with all 5 clothing items.

- [ ] **Step 5: Verify the backend endpoint is reachable**

```bash
curl -X POST http://localhost:8020/api/products/generate_panama \
  -H "Content-Type: application/json" \
  -d '[{
    "items": [
      {"product": "panama_1.png", "coordinates": {"x": 155, "y": 570}, "fontSize": 32, "textWidth": 100.0}
    ],
    "category_1": "test",
    "category_2": "",
    "design_number": "001",
    "text": "test phrase",
    "description_id": "1"
  }]'
```

Expected response: `{"message": "process started"}`
