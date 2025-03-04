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
                <span class="close" @click="closeModal">&times;</span>

            <div class="modal__content">
                <canvas ref="canvas" class="modal__canvas"></canvas>
                <!-- Редактируемый текст -->
                <div v-if="isModalOpen" ref="editableText" class="editable-text"
                    :style="{ left: textX + 'px', top: textY + 'px' }" contenteditable="true" @mousedown="startDragging"
                    @input="updateText">
                    {{ phrase }}
                </div>
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
                { src: "longsleeve.png", bigSrc: "longsleeve_big.png" },
                { src: "t_shirt_basic.png", bigSrc: "t_shirt_basic_big.png" },
                { src: "t_shirt_true_over.png", bigSrc: "t_shirt_true_over_big.png" }
            ],
            isModalOpen: false,
            selectedImage: "",
            textX: 100,
            textY: 100,
            isDragging: false,
            canvas: null,
            ctx: null,
            dragOffsetX: 0,
            dragOffsetY: 0,
            backgroundImage: null
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
            this.$nextTick(() => {
                this.canvas = this.$refs.canvas;
                if (this.canvas) {
                    this.ctx = this.canvas.getContext("2d");
                    this.loadImageAndDraw();
                }
            });
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

                // Устанавливаем текст по центру canvas
                this.centerText();
            };
            img.src = this.selectedImage;
        },
        centerText() {
            if (!this.ctx || !this.phrase) return;

            // Устанавливаем шрифт и цвет текста
            // this.ctx.font = "30px Arial";
            // this.ctx.fillStyle = "white";

            // Рассчитываем размер текста
            const textWidth = this.ctx.measureText(this.phrase).width;
            const textHeight = 32; // Высота текста (размер шрифта)

            // Рассчитываем начальные координаты текста
            this.textX = (this.canvas.width - textWidth) / 2;
            this.textY = (this.canvas.height + textHeight) / 2;

        //     // Рисуем текст
        //     this.drawText();
        // },
        // drawText() {
        //     if (!this.ctx) return;
        //     this.ctx.font = "30px Arial";
        //     this.ctx.fillStyle = "white";
        //     this.ctx.fillText(this.phrase, this.textX, this.textY);
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

            newX = Math.max(0, Math.min(this.canvas.width - 100, newX)); // 100 — примерная ширина текста
            // newX = Math.max(0, Math.min(this.canvas.width - 100, newX)); // 100 — примерная ширина текста

            newY = Math.max(0, Math.min(this.canvas.height - 32, newY)); // 32 — примерная высота текста

            this.textX = newX;
            this.textY = newY;
            console.log("textX:", this.textX, "textY:", this.textY);

        },
        stopDragging() {
            this.isDragging = false;

            // Убираем обработчики событий
            document.removeEventListener("mousemove", this.dragText);
            document.removeEventListener("mouseup", this.stopDragging);
        },
        updateText(e) {
            this.phrase = e.target.innerText;
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
    beforeDestroy() {
        if (this.canvas) {
            this.canvas.removeEventListener("mousedown", this.startDragging);
            this.canvas.removeEventListener("mousemove", this.dragText);
            this.canvas.removeEventListener("mouseup", this.stopDragging);
        }
    }
};
</script>

<style scoped>
@import '@/assets/styles.css';

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
    color: #dd1212;
    /* color */
    text-align: center;
    /* text-align */
    font-family: AvantGardeC, serif;
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

}

</style>