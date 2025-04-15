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
        <textarea class='input__phrase' v-model="phrase" placeholder="Введите фразу"></textarea>
      </div>
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
      <span class="close" @click="closeModal">&times;</span>
      <div class="modal__content">
        <canvas ref="canvas" class="modal__canvas"></canvas>
        <!-- Редактируемый текст -->
        <div v-if="isModalOpen" ref="editableText" class="editable-text" :style="{
                    left: textX + 'px',
                    top: textY + 'px',
                    fontSize: fontSize + 'px'
                }" contenteditable="true" @mousedown="startDragging" @input="updateText"
             @keydown="handleKeyDown"
             @blur="saveText">
          {{ phrase }}
        </div>
      </div>
      <div class="font-size-controls">
        <button @click="decreaseFontSize">Уменьшить шрифт</button>
        <span>Размер шрифта: {{ fontSize }}px</span>
        <button @click="increaseFontSize">Увеличить шрифт</button>
      </div>
    </div>
  </div>
</template>


<script>
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
        {x: 188, y: 409},
        {x: 180, y: 365},
        {x: 185, y: 300},
        {x: 180, y: 365},
        {x: 185, y: 300}
      ],
      imagesFontSizes: [20, 20, 14, 20, 16], // Начальные размеры шрифта для каждой картинки
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
    };
  },
  methods: {
    createCurrentPhraseData() {
      return {
        items: this.images.map((image, index) => ({
          product: image.src,
          coordinates: this.imagesTextCoordinates[index],
          fontSize: this.imagesFontSizes[index],
        })),
        category_1: this.categories[0],
        category_2: this.categories[1],
        design_number: this.designNumber,
        text: this.phrase
      };
          },
    isDuplicate(data) {
      return this.phrasesDataList.some(
        item => JSON.stringify(item) === JSON.stringify(data)
      );
    },
    generateFile() {
      if (this.phrase.trim()) {
        const currentPhraseData = this.createCurrentPhraseData();
        if (!this.isDuplicate(currentPhraseData)) {
          this.phrasesDataList.push(currentPhraseData);
        }
      }

      fetch('/api/products/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(this.phrasesDataList),
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
        const canvasRect = this.canvas.getBoundingClientRect();
        const textRect = editableEl.getBoundingClientRect();
        const newTextX = (this.canvas.width - textRect.width) / 2;
        this.textX = newTextX;
        this.imagesTextCoordinates[this.selectedImageIndex].x = newTextX;
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
      if (this.imagesFontSizes[this.selectedImageIndex] > 10) {  // Минимальный размер шрифта
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
    },
    addPhrase() {
      const currentPhraseData = this.createCurrentPhraseData();

      if (!this.isDuplicate(currentPhraseData)) {
        this.phrasesDataList.push(currentPhraseData);
        this.phraseCount++;
      }

      this.phraseCount = this.phrasesDataList.length;
      this.phrase = "";
      this.designNumber = "";
      this.categories = ["", ""];
    },
    openModal(index) {
      this.selectedImageIndex = index; // Сохраняем индекс выбранной картинки
      this.selectedImage = this.images[index].bigSrc;
      this.isModalOpen = true;
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
    closeModal() {
      this.isModalOpen = false;
    },
    startDragging(e) {
      this.isDragging = true;
      // Получаем координаты canvas относительно окна браузера
      const rect = this.canvas.getBoundingClientRect();
      // Рассчитываем смещение мыши относительно текста
      this.dragOffsetX = e.clientX - rect.left - this.textX;
      this.dragOffsetY = e.clientY - rect.top - this.textY;

      // Добавляем обработчики событий для перемещения и остановки
      document.addEventListener("mousemove", this.dragText);
      document.addEventListener("mouseup", this.stopDragging);
    },
    dragText(e) {
      if (!this.isDragging || !this.canvas || !this.backgroundImage) return;

      // Получаем координаты canvas относительно окна браузера
      const rect = this.canvas.getBoundingClientRect();

      // Получаем координаты мыши внутри canvas
      let newX = e.clientX - rect.left - this.dragOffsetX;
      let newY = e.clientY - rect.top - this.dragOffsetY;

      // Ограничиваем координаты в пределах canvas
      const textWidth = this.ctx.measureText(this.phrase).width;

      newY = Math.max(0, Math.min(this.canvas.height - 32, newY)); // Ограничиваем по высоте

      this.textX = newX;
      this.textY = newY;

      // Сохраняем новые координаты в объекте imagesTextCoordinates
      this.imagesTextCoordinates[this.selectedImageIndex] = {x: this.textX, y: this.textY};

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
@import '@/assets/styles.css';

@font-face {
  font-family: 'OnePhraseFont';
  src: url('@/assets/fonts/AvantGardeC_regular.otf') format('opentype');
  font-weight: normal;
  font-style: normal;
}


.modal__content {
  position: relative;
  background-color: white;
  /* padding: 20px; */
  /* border-radius: 10px; */
  border: 1px solid black;
}

.modal__canvas {
  display: block;
  border: 1px solid #000000;
  /* max-width: 90%;
  max-height: 90%; */
  padding: 0;
  margin: 0;

}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.5);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.editable-text {
  position: absolute;
  /* font-size: 30px;
  font-family: Arial, sans-serif;
  color: white; */
  cursor: move;
  user-select: none;
  background-color: transparent;
  border: none;
  outline: none;
  position: absolute;
  color: white;
  /* color */
  text-align: center;
  /* text-align */
  font-family: "OnePhraseFont", "Century Gothic", CenturyGothic, AppleGothic, sans-serif;
  /* font-family */
  font-size: 32px;
  /* font-size */
  font-style: normal;
  /* font-style */
  font-weight: 400;
  /* font-weight */
  line-height: 115%;
  /* line-height */
  letter-spacing: 0.64px;
  /* letter-spacing */
  cursor: move;
  user-select: none;
  background-color: transparent;
  border: none;
  outline: none;
  white-space: pre-line;
  /* Отображает переносы строк */


}

.close {
  justify-self: left;
}
</style>
