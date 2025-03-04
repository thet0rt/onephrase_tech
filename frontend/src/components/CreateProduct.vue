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

                <canvas v-if="isModalOpen" ref="canvas" class="modal__canvas" @mousedown="startDragging"
                    @mousemove="dragText" @mouseup="stopDragging" @mouseleave="stopDragging">
                </canvas>
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
            textX: 100,
            textY: 100,
            isDragging: false,
            canvas: null,
            ctx: null,
            dragOffsetX: 0,
            dragOffsetY: 0
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
                this.canvas.width = img.width;
                this.canvas.height = img.height;
                this.ctx.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);
                this.drawText();
            };
            img.src = this.selectedImage;
        },
        closeModal() {
            this.isModalOpen = false;
        },
        drawText() {
            if (!this.ctx) return;
            this.ctx.font = "30px Arial";
            this.ctx.fillStyle = "black";
            this.ctx.fillText(this.phrase, this.textX, this.textY);
        },
        startDragging(e) {
            const rect = this.canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;

            if (this.isMouseOverText(mouseX, mouseY)) {
                this.isDragging = true;
                this.dragOffsetX = mouseX - this.textX;
                this.dragOffsetY = mouseY - this.textY;
            }
        },
        dragText(e) {
            if (this.isDragging) {
                const rect = this.canvas.getBoundingClientRect();
                const mouseX = e.clientX - rect.left;
                const mouseY = e.clientY - rect.top;

                this.textX = mouseX - this.dragOffsetX;
                this.textY = mouseY - this.dragOffsetY;
                this.redrawCanvas();
            }
        },
        stopDragging() {
            this.isDragging = false;
        },
        isMouseOverText(mouseX, mouseY) {
            const textWidth = this.ctx.measureText(this.phrase).width;
            const textHeight = 30; // высота шрифта
            return (
                mouseX >= this.textX &&
                mouseX <= this.textX + textWidth &&
                mouseY >= this.textY - textHeight &&
                mouseY <= this.textY
            );
        },
        redrawCanvas() {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            const img = new Image();
            img.onload = () => {
                this.ctx.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);
                this.drawText();
            };
            img.src = this.selectedImage;
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
    background-color: #ffffff;
    padding: 20px;
    border-radius: 10px;
    border: 1px solid black;
}

.modal__canvas {
    display: block;
    border: 2px solid #000000;
    max-width: 90%;
    max-height: 90%;
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
</style>