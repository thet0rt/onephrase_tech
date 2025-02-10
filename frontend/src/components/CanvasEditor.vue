<template>
    <div class="editor-container">
      <input type="file" @change="loadImage" accept="image/*" />
      <canvas ref="canvas"></canvas>
    </div>
  </template>
  
  <script>
  import { ref, onMounted } from "vue";
  
  export default {
    setup() {
      const canvas = ref(null);
      const ctx = ref(null);
      const image = ref(null);
  
      const loadImage = (event) => {
        const file = event.target.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = (e) => {
            image.value = new Image();
            image.value.src = e.target.result;
            image.value.onload = () => drawCanvas();
          };
          reader.readAsDataURL(file);
        }
      };
  
      const drawCanvas = () => {
        if (canvas.value && image.value) {
          const ctx = canvas.value.getContext("2d");
          canvas.value.width = image.value.width;
          canvas.value.height = image.value.height;
          ctx.clearRect(0, 0, canvas.value.width, canvas.value.height);
          ctx.drawImage(image.value, 0, 0);
        }
      };
  
      onMounted(() => {
        ctx.value = canvas.value.getContext("2d");
      });
  
      return {
        canvas,
        loadImage,
      };
    },
  };
  </script>
  
  <style scoped>
  .editor-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
  }
  
  canvas {
    border: 1px solid #ccc;
  }
  </style>
  