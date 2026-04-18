<template>
  <div class="page-wrapper">
    <nav class="navbar">
      <span class="logo__text">Onephrase.tech</span>
      <router-link to="/files" class="nav-link">Файлы</router-link>
    </nav>

    <div class="main__content">
      <div class="form-header">
        <div>
          <p class="form-eyebrow">Новый товар</p>
          <h1 class="form-title">Создать карточку</h1>
        </div>
        <button class="btn btn--ghost btn--sm" @click="resetForm">Сбросить</button>
      </div>

      <div class="form-grid">
        <div class="field field--full">
          <label class="field__label">Фраза</label>
          <textarea
            class="field__input field__textarea"
            v-model="phrase"
            placeholder="Введите фразу..."
            @blur="recalculateAllTextX"
          ></textarea>
        </div>

        <div class="field">
          <label class="field__label">Номер дизайна</label>
          <input class="field__input" type="text" v-model="designNumber" placeholder="например, 42">
        </div>

        <div class="field">
          <label class="field__label">Description ID</label>
          <input class="field__input" type="number" v-model.number="description_id" placeholder="ID">
        </div>

        <div class="field field--full field--row">
          <div class="field" style="flex:1">
            <label class="field__label">Категория 1</label>
            <input class="field__input" type="text" v-model="categories[0]" placeholder="категория">
          </div>
          <div class="field" style="flex:1">
            <label class="field__label">Категория 2</label>
            <input class="field__input" type="text" v-model="categories[1]" placeholder="категория">
          </div>
        </div>
      </div>

      <div class="section-label">Товары</div>
      <div class="products-grid">
        <div v-for="(item, index) in images" :key="index" class="product-card" @click="openModal(index)">
          <img class="product-card__img" :src="item.src" alt="">
          <div class="product-card__overlay">
            <span class="product-card__edit-icon">✎</span>
          </div>
        </div>
      </div>

      <div class="form-footer">
        <span class="phrase-badge" v-if="phraseCount > 0">{{ phraseCount }} {{ phraseCount === 1 ? 'фраза' : phraseCount < 5 ? 'фразы' : 'фраз' }}</span>
        <div class="footer-actions">
          <button class="btn btn--secondary" @click="addPhrase">+ Добавить фразу</button>
          <button class="btn btn--primary" @click="generateFile">Сгенерировать файл</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно -->
    <div v-if="isModalOpen" class="modal">
      <div class="modal__content">
        <button class="modal__close" @click="closeModal">&times;</button>
        <canvas ref="canvas" class="modal__canvas"></canvas>
        <div :style="{
          transform: 'scale(0.5)',
          transformOrigin: 'top left',
          position: 'absolute',
          left: textX * 0.5 + 'px',
          top: textY * 0.5 + 'px'
        }">
          <div v-if="isModalOpen" ref="editableText" class="editable-text" :style="{ fontSize: fontSize + 'px' }"
               contenteditable="true" @mousedown="startDragging" @input="updateText"
               @keydown="handleKeyDown" @blur="saveText">
            {{ phrase }}
          </div>
        </div>
        <div class="font-size-controls">
          <button class="btn btn--ghost btn--sm" @click="decreaseFontSize">−</button>
          <span class="font-display">{{ fontSize }}px</span>
          <button class="btn btn--ghost btn--sm" @click="increaseFontSize">+</button>
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
        {src: "hoodie.png", bigSrc: "hoodie_big.png"},
        {src: "sweatshirt.png", bigSrc: "sweatshirt_big.png"},
        {src: "longsleeve.png", bigSrc: "longsleeve_big.png"},
        {src: "tshirt-basic.png", bigSrc: "tshirt-basic_big.png"},
        {src: "tshirt-trueover.png", bigSrc: "tshirt-trueover_big.png"}
      ],
      imagesTextCoordinates: [
        {x: 188, y: 894},
        {x: 180, y: 872},
        {x: 185, y: 632},
        {x: 180, y: 850},
        {x: 185, y: 600}
      ],
      imagesFontSizes: [32, 32, 14, 34, 17], // Начальные размеры шрифта для каждой картинки
      selectedImageIndex: null, // Индекс выбранной картинки
      isModalOpen: false,
      selectedImage: "",
      textX: 180,
      textY: 365,
      isDragging: false,
      canvas: null,
      ctx: null,
      dragOffsetX: 0,
      dragOffsetY: 0,
      backgroundImage: null,
      fontSize: 32,  // Начальный размер шрифта
      currentEditingPhraseIndex: null, // индекс фразы, которую редактируем сейчас
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

      fetch('/api/products/generate', {
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
    showGeneratedData(data) {
      // Преобразуем данные в строку для отображения
      const dataString = JSON.stringify(this.phrasesDataList, null, 2);

      // Создаем модальное окно для отображения данных
      alert("Сгенерированные данные:\n" + dataString);
    },
    updateText(e) {
      // При вводе текста сохраняем HTML с тегами <br> для переноса строк
      this.phrase = e.target.innerHTML;
      this.$nextTick(() => {
        const editableEl = this.$refs.editableText;
        // const canvasRect = this.canvas.getBoundingClientRect();
        // const textRect = editableEl.getBoundingClientRect();
        console.log(this.canvas.width)
        // const newTextX = (540 - textRect.width) / 2;
        // this.textX = newTextX;
        this.imagesTextCoordinates = this.imagesTextCoordinates.map(coord => ({
          ...coord,
          x: newTextX
        }));
      });
    },
    measureTextWidth(text, fontSize, fontFamily = 'OnePhraseFont') {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      ctx.font = `${fontSize}px ${fontFamily}`;

      // Учитываем возможные переносы строк: и \n, и <br>
      const lines = text
        .replace(/<br\s*\/?>/gi, '\n')  // превращаем <br> в \n
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
        let newX = (1200 - width) / 2;

        const product = this.images[index].src;
        if (product.includes('hoodie')) {
          newX -= 5;
        }
        if (product.includes('tshirt-basic')) {
          newX -= 22;
        }
        if (product.includes('tshirt-trueover')) {
          newX -= 5;
        }

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
      this.text = this.$refs.editable.innerText;
      this.edit = false;
    },
    decreaseFontSize() {
      if (this.imagesFontSizes[this.selectedImageIndex] > 2) {  // Минимальный размер шрифта
        this.imagesFontSizes[this.selectedImageIndex] -= 2;
        this.fontSize = this.imagesFontSizes[this.selectedImageIndex]; // Обновляем текущий размер шрифта
      }
    },
    increaseFontSize() {
      this.imagesFontSizes[this.selectedImageIndex] += 2;  // Увеличиваем размер шрифта
      this.fontSize = this.imagesFontSizes[this.selectedImageIndex]; // Обновляем текущий размер шрифта
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
        this.currentEditingPhraseIndex = this.phrasesDataList.length - 1; // теперь редактируем последнюю фразу
      }

      this.phraseCount = this.phrasesDataList.length;
      this.phrase = "";
      this.designNumber = "";
      this.categories = ["", ""];
      this.description_id = "";
    },
    openModal(index) {
      this.selectedImageIndex = index; // Сохраняем индекс выбранной картинки
      this.selectedImage = this.images[index].bigSrc;
      this.isModalOpen = true;
      document.body.style.overflow = "hidden"; // Отключаем прокрутку фона
      this.$nextTick(() => {
        this.canvas = this.$refs.canvas;
        if (this.canvas) {
          this.ctx = this.canvas.getContext("2d");
          this.loadImageAndDraw();
        }
      });

      // Загружаем размер шрифта для выбранной картинки
      this.fontSize = this.imagesFontSizes[this.selectedImageIndex];
    },
    loadImageAndDraw() {
      const img = new Image();
      img.onload = () => {
        // Устанавливаем размер canvas
        this.canvas.width = img.width * 0.5;
        this.canvas.height = img.height * 0.5;

        // Сохраняем изображение как фон
        this.backgroundImage = img;

        // Рисуем фон
        this.ctx.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);

        // Загружаем координаты и размер шрифта для текста
        const savedCoordinates = this.imagesTextCoordinates[this.selectedImageIndex];
        this.textX = savedCoordinates.x;
        this.textY = savedCoordinates.y;

        // Устанавливаем размер шрифта
        this.ctx.font = `${this.fontSize}px AvantGardeC`;
        this.ctx.fillStyle = "white";
        // this.ctx.fillText(this.phrase, this.textX, this.textY);
      };
      img.src = this.selectedImage;
    },
    async generateTextImagesForPhrases() {
      const tempDiv = document.createElement('div');
      tempDiv.style.position = 'absolute';
      tempDiv.style.left = '-9999px';
      tempDiv.style.top = '0';
      tempDiv.style.width = '600px';
      // // Центрирование текста физически через flexbox
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
          // Белый вариант
          tempDiv.style.color = 'white';
          const canvasWhite = await html2canvas(tempDiv, {
            backgroundColor: null,
            scale: 2,
            useCORS: true
          });
          item.text_image_white = canvasWhite.toDataURL('image/png');
          // Черный вариант
          tempDiv.style.color = '#222222';
          const canvasBlack = await html2canvas(tempDiv, {
            backgroundColor: null,
            scale: 2,
            useCORS: true
          });
          item.text_image_black = canvasBlack.toDataURL('image/png');
          // темно-красный
          tempDiv.style.color = '#80081B';
          const canvasRed = await html2canvas(tempDiv, {
            backgroundColor: null,
            scale: 2,
            useCORS: true
          });
          item.text_image_red = canvasRed.toDataURL('image/png');
          // темно-красный
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
    downloadImage(dataURL, filename) {
      const link = document.createElement('a');
      link.href = dataURL;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },
    closeModal() {
      this.isModalOpen = false;
      document.body.style.overflow = ""; // Включаем прокрутку фона
    },
    startDragging(e) {
      this.isDragging = true;
      // Получаем координаты canvas относительно окна браузера
      const rect = this.canvas.getBoundingClientRect();
      // Масштаб canvas
      const scale = 0.5;
      // Рассчитываем смещение мыши относительно текста с учетом масштаба
      this.dragOffsetX = (e.clientX - rect.left) / scale - this.textX;
      this.dragOffsetY = (e.clientY - rect.top) / scale - this.textY;

      // Добавляем обработчики событий для перемещения и остановки
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

      // Обновляем координаты для выбранного изображения
      this.imagesTextCoordinates[this.selectedImageIndex] = {x: this.textX, y: this.textY};

      // Обновляем координаты только в текущей редактируемой фразе
      // if (this.currentEditingPhraseIndex != null) {
      //   const phrase = this.phrasesDataList[this.currentEditingPhraseIndex];
      //   if (phrase && phrase.items && phrase.items[this.selectedImageIndex]) {
      //     phrase.items[this.selectedImageIndex].coordinates = {
      //       x: this.textX - 30,
      //       y: this.textY - 30
      //     };
      //   }
      // }

      console.log("textX:", this.textX, "textY:", this.textY);
    },
    stopDragging() {
      this.isDragging = false;
      // Убираем обработчики событий
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
@font-face {
  font-family: 'OnePhraseFont';
  src: url('@/assets/fonts/AvantGardeC_regular.otf') format('opentype');
  font-weight: normal;
  font-style: normal;
  font-display: swap;
}

/* ── Layout ── */
.page-wrapper {
  width: 100%;
  min-height: 100vh;
  background: #f5f5f7;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

/* ── Navbar ── */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
  height: 56px;
  background: #1a1a1a;
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo__text {
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.nav-link {
  color: rgba(255,255,255,0.65);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.15s;
}

.nav-link:hover { color: #fff; }

/* ── Card ── */
.main__content {
  max-width: 780px;
  margin: 40px auto;
  padding: 36px 40px 40px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 8px 24px rgba(0,0,0,0.06);
}

/* ── Form header ── */
.form-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
}

.form-eyebrow {
  margin: 0 0 4px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: #999;
}

.form-title {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  color: #111;
  letter-spacing: -0.4px;
}

/* ── Form grid ── */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 32px;
}

.field { display: flex; flex-direction: column; gap: 6px; }
.field--full { grid-column: 1 / -1; }
.field--row { flex-direction: row; gap: 16px; align-items: flex-end; }

.field__label {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: #666;
}

.field__input {
  padding: 10px 14px;
  font-size: 15px;
  font-family: inherit;
  border: 1.5px solid #e5e5e5;
  border-radius: 8px;
  background: #fafafa;
  color: #111;
  outline: none;
  transition: border-color 0.15s, background 0.15s, box-shadow 0.15s;
  width: 100%;
  box-sizing: border-box;
}

.field__input:focus {
  border-color: #111;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(0,0,0,0.06);
}

.field__textarea {
  resize: vertical;
  min-height: 80px;
  line-height: 1.5;
}

/* ── Section label ── */
.section-label {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: #666;
  margin-bottom: 14px;
}

/* ── Products grid ── */
.products-grid {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 36px;
}

.product-card {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  border: 1.5px solid #e8e8e8;
  transition: transform 0.15s, border-color 0.15s, box-shadow 0.15s;
}

.product-card:hover {
  transform: translateY(-2px);
  border-color: #111;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
}

.product-card__img {
  display: block;
  width: 120px;
  height: 144px;
  object-fit: cover;
}

.product-card__overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}

.product-card:hover .product-card__overlay {
  background: rgba(0,0,0,0.35);
}

.product-card__edit-icon {
  color: #fff;
  font-size: 22px;
  opacity: 0;
  transform: scale(0.8);
  transition: opacity 0.15s, transform 0.15s;
}

.product-card:hover .product-card__edit-icon {
  opacity: 1;
  transform: scale(1);
}

/* ── Footer ── */
.form-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

.phrase-badge {
  margin-right: auto;
  font-size: 13px;
  font-weight: 600;
  color: #555;
  background: #f0f0f0;
  padding: 4px 12px;
  border-radius: 20px;
}

.footer-actions { display: flex; gap: 10px; }

/* ── Buttons ── */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 8px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  padding: 10px 20px;
  transition: background 0.15s, opacity 0.15s, transform 0.1s;
  white-space: nowrap;
}

.btn:active { transform: scale(0.97); }

.btn--primary {
  background: #111;
  color: #fff;
}
.btn--primary:hover { background: #333; }

.btn--secondary {
  background: #f0f0f0;
  color: #111;
}
.btn--secondary:hover { background: #e5e5e5; }

.btn--ghost {
  background: transparent;
  color: #555;
  border: 1.5px solid #e0e0e0;
}
.btn--ghost:hover { background: #f5f5f5; color: #111; }

.btn--sm { padding: 6px 14px; font-size: 13px; }

/* ── Modal ── */
.modal {
  display: flex;
  position: fixed;
  inset: 0;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal__backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.55);
  backdrop-filter: blur(2px);
  z-index: 1;
}

.modal__content {
  position: relative;
  background: #fff;
  border-radius: 12px;
  padding: 36px 36px 44px;
  z-index: 2;
  box-shadow: 0 20px 60px rgba(0,0,0,0.25);
}

.modal__close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: #f0f0f0;
  color: #555;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}
.modal__close:hover { background: #e0e0e0; color: #111; }

.modal__canvas {
  display: block;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.font-size-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 14px;
  justify-content: center;
}

.font-display {
  font-size: 13px;
  font-weight: 600;
  color: #444;
  min-width: 56px;
  text-align: center;
}

/* ── Editable text on canvas ── */
.editable-text {
  position: absolute;
  cursor: move;
  user-select: none;
  color: white;
  text-align: center;
  font-family: "OnePhraseFont", "Century Gothic", AppleGothic, sans-serif;
  font-weight: 400;
  line-height: 110%;
  letter-spacing: 0.7px;
  background: transparent;
  border: none;
  outline: none;
  white-space: pre;
}
</style>
