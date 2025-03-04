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
            <button class="button__change" @click="changeImage(index)">изменить</button>
          </div>
        </div>
        <div class="getfile__container">
          <p class="phrase__counter">количество фраз ({{ phraseCount }})</p>
          <button class="button_bottom" @click="addPhrase">Добавить ещё фразу</button>
          <button class="button_bottom" @click="generateFile">Сгенерировать файл</button>
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
          { src: "hoodie.png" },
          { src: "sweetshirt.png" },
          { src: "hoodie.png" },
          { src: "longsleeve.png" },
          { src: "t_shirt_basic.png" },
          { src: "t_shirt_true_over.png" }
        ]
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
      changeImage(index) {
        alert(`Изменить изображение ${index + 1}`);
      }
    }
  };
  </script>
  
  <style scoped>
  @import '@/assets/styles.css';
  </style>
  