<template>
    <div>
      <nav class="navbar">
        <h1 class="logo__text">Onephrase.tech</h1>
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
          <input class="input__phrase" type="text" v-model="phrase" placeholder="Введите фразу">
        </div>
        <div class="container__input_phrase">
          <h4 class="input__phrase__name">введите номер дизайна</h4>
          <input class="input__phrase" type="text" v-model="designNumber" placeholder="введите номер дизайна">
        </div>
        <div class="container__input_phrase">
          <h4 class="input__phrase__name">введите категории</h4>
          <input class="input__category" type="text" v-model="categories[0]" placeholder="категория">
          <input class="input__category" type="text" v-model="categories[1]" placeholder="категория">
          <input class="input__category" type="text" v-model="categories[2]" placeholder="категория">
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
          <canvas ref="canvas" class="modal__canvas" @mousedown="startDrag" @mousemove="onDrag" @mouseup="stopDrag"></canvas>
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
        categories: ["", "", ""],
        phraseCount: 0,
        images: [
          { src: "hoodie.png", bigSrc: "hoodie_big.png" },
          { src: "sweetshirt.png", bigSrc: "sweetshirt_big.png" },
          { src: "hoodie.png", bigSrc: "hoodie_big.png" },
          { src: "longsleeve.png", bigSrc: "longsleeve_big.png" },
          { src: "t_shirt_basic.png", bigSrc: "t_shirt_basic_big.png" },
          { src: "t_shirt_true_over.png", bigSrc: "t_shirt_true_over_big.png" }
        ],
        isModalOpen: false,
        selectedImage: "",
        textX: 50,
        textY: 50,
        isDragging: false,
        canvas: null,
        ctx: null
      };
    },
    methods: {
      resetForm() {
        this.phrase = "";
        this.designNumber = "";
        this.categories = ["", "", ""];
        this.phraseCount = 0;
      },
      addPhrase() {
        this.phraseCount++;
      },
      generateFile() {
        alert("Файл сгенерирован!");
      },
      openModal(index) {
        this.selectedImage = this.images[index].bigSrc;
        this.isModalOpen = true;
        this.$nextTick(this.drawCanvas);
      },
      closeModal() {
        this.isModalOpen = false;
      },
      drawCanvas() {
        this.canvas = this.$refs.canvas;
        this.ctx = this.canvas.getContext("2d");
        const img = new Image();
        img.src = this.selectedImage;
        img.onload = () => {
          this.canvas.width = img.width / 2;
          this.canvas.height = img.height / 2;
          this.ctx.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);
          this.drawText();
        };
      },
      drawText() {
        if (!this.ctx) return;
        this.ctx.font = "20px Arial";
        this.ctx.fillStyle = "black";
        this.ctx.fillText(this.phrase, this.textX, this.textY);
      },
      startDrag(event) {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        if (x >= this.textX && x <= this.textX + 100 && y >= this.textY - 20 && y <= this.textY) {
          this.isDragging = true;
        }
      },
      onDrag(event) {
        if (!this.isDragging) return;
        const rect = this.canvas.getBoundingClientRect();
        this.textX = event.clientX - rect.left;
        this.textY = event.clientY - rect.top;
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.drawCanvas();
      },
      stopDrag() {
        this.isDragging = false;
      }
    }
  };
  </script>
  
  <style scoped>
  @import '@/assets/styles.css';
  
  .modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .modal__content {
    background: white;
    padding: 20px;
    border-radius: 10px;
    position: relative;
  }
  
  .modal__canvas {
    width: 100%;
    max-width: 500px;
    cursor: grab;
  }
  
  .close {
    position: absolute;
    top: 10px;
    right: 10px;
    font-size: 24px;
    cursor: pointer;
  }
  </style>
  