<template>
  <div>
    <nav class="navbar">
      <h1 class="logo__text">Onephrase.tech</h1>
      <router-link to="/create_product" class="nav-link">Одежда</router-link>
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
        {src: "panama.png", bigSrc: "panama_big.png"},
        {src: "panama-unrolled.png", bigSrc: "panama-unrolled_big.png"},
        {src: "cap.png", bigSrc: "cap_big.png"},
      ],
      imagesTextCoordinates: [
        {x: 185, y: 600},
        {x: 185, y: 600},
        {x: 185, y: 600},
      ],
      imagesFontSizes: [38, 38, 38],
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
